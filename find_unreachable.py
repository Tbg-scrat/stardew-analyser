#!/usr/bin/env python3
"""Reachability analysis for Python files (stdlib only).

Starting from the given entry points, follow imports transitively and report
which project files are never reached.

Usage (run from the project root, or pass it as the first argument):
    python find_unreachable.py
    python find_unreachable.py --entry src.core.extractor.router --entry watch.py --entry parse.py
    python find_unreachable.py --chain src/core/asset_extractor.py

Entries may be file paths (script mode) or dotted module names (python -m).
Results are CANDIDATES: verify before deleting anything.
"""
import argparse
import ast
import os
import re
from collections import deque
from pathlib import Path

DEFAULT_ENTRIES = ["src.core.extractor.router", "watch.py", "parse.py"]
DEFAULT_EXCLUDE = [
    ".venv", "venv", ".git", "__pycache__", "htmlcov", "saves",
    "node_modules", ".mypy_cache", ".pytest_cache", "scripts",
]
TEXT_SUFFIXES = {".sh", ".yml", ".yaml", ".toml", ".cfg", ".ini", ".conf"}
TEXT_PREFIXES = ("Dockerfile", "Makefile")
ALL = "*"  # sentinel: every name a package exports counts as demanded
DYNAMIC_CALLS = {
    "import_module", "__import__", "iter_modules", "walk_packages",
    "run_module", "run_path", "spec_from_file_location",
}


# ---------------------------------------------------------------- scanning
def scan(root, exclude):
    names = {e for e in exclude if "/" not in e}
    paths = {e.strip("/") for e in exclude if "/" in e}
    py, txt = [], []
    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = Path(dirpath).relative_to(root)
        dirnames[:] = [
            d for d in dirnames
            if d not in names and (rel_dir / d).as_posix() not in paths
        ]
        for fn in filenames:
            rel = (rel_dir / fn).as_posix()
            if fn.endswith(".py"):
                py.append(rel)
            elif Path(fn).suffix in TEXT_SUFFIXES or fn.startswith(TEXT_PREFIXES):
                txt.append(rel)
    return sorted(py), sorted(txt)


def module_name(rel):
    parts = list(Path(rel).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def package_of(rel):
    """Dotted package a file lives in (used for relative imports)."""
    p = Path(rel)
    if p.name == "__init__.py":
        return module_name(rel)
    return ".".join(p.parent.parts)


def resolve(name, mod2file):
    """A dotted import also executes every parent package's __init__.py."""
    parts = name.split(".")
    found = set()
    for i in range(1, len(parts) + 1):
        f = mod2file.get(".".join(parts[:i]))
        if f:
            found.add(f)
    return found


# ---------------------------------------------------------------- per-file analysis
def has_main_guard(tree):
    for n in tree.body:
        if (isinstance(n, ast.If) and isinstance(n.test, ast.Compare)
                and isinstance(n.test.left, ast.Name) and n.test.left.id == "__name__"):
            return True
    return False


def analyse(rel, tree, mod2file, py_files):
    """Returns edges, dynamic calls, string refs, demands, init bindings.

    demands:  [(package __init__ file, names | None)] -> what this file takes FROM a package
    bindings: (only for __init__.py) [(edges, bound names | None)] -> what the init imports
    """
    pkg = package_of(rel)
    pkg_parts = pkg.split(".") if pkg else []
    is_init = Path(rel).name == "__init__.py"
    edges, dyn, strs, demands, bindings = set(), [], [], [], []

    def find(cand, sibling):
        hit = resolve(cand, mod2file)
        if not hit and sibling and pkg:  # script-mode fallback: `import helper` next to the script
            hit = resolve(f"{pkg}.{cand}", mod2file)
        return hit

    def pkg_init(mod, sibling):
        f = mod2file.get(mod) or (mod2file.get(f"{pkg}.{mod}") if sibling and pkg else None)
        return f if f and Path(f).name == "__init__.py" else None

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                hit = find(a.name, True)
                edges |= hit
                init = pkg_init(a.name, True)
                if init:
                    demands.append((init, None))  # `import pkg` -> any attribute may be used
                if is_init:
                    bindings.append((hit, None))
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                cut = node.level - 1
                if cut > len(pkg_parts):
                    continue
                base = pkg_parts[:len(pkg_parts) - cut]
                mod = ".".join(base + ([node.module] if node.module else []))
            else:
                mod = node.module or ""
            sibling = node.level == 0
            mod_hit = find(mod, sibling) if mod else set()
            edges |= mod_hit
            init = pkg_init(mod, sibling) if mod else None
            for a in node.names:
                if a.name == "*":
                    if init:
                        demands.append((init, None))
                    if is_init:
                        bindings.append((mod_hit, None))
                    continue
                hit = find(f"{mod}.{a.name}" if mod else a.name, sibling)
                edges |= hit
                if init:
                    demands.append((init, {a.name}))
                if is_init:
                    bindings.append((mod_hit | hit, {a.asname or a.name}))
        elif isinstance(node, ast.Call):
            fn = node.func
            name = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", None)
            if name in DYNAMIC_CALLS:
                dyn.append((node.lineno, name))
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            s = node.value
            if len(s) < 200:
                if s.endswith(".py"):
                    for f in py_files:
                        if f == s or f.endswith("/" + s):
                            strs.append((node.lineno, f))
                elif "." in s and s in mod2file:
                    strs.append((node.lineno, mod2file[s]))

    edges.discard(rel)
    bindings = [(e - {rel}, n) for e, n in bindings]
    return edges, dyn, strs, demands, bindings


# ---------------------------------------------------------------- graph walk
def reach(entries, graph):
    parent = {e: None for e in entries}
    queue = deque(entries)
    while queue:
        cur = queue.popleft()
        for nxt in graph.get(cur, ()):
            if nxt not in parent:
                parent[nxt] = cur
                queue.append(nxt)
    return parent


def reach_strict(entries, graph, inits, demands):
    """Like reach(), but an __init__.py only passes on an import when something
    reached actually takes the bound name from that package (re-export is used)."""
    parent = {e: None for e in entries}
    demanded = {}
    changed = True
    while changed:
        changed = False
        for f in list(parent):
            if f in inits:
                dem = demanded.get(f, set())
                out = set()
                for edges, names in inits[f]:
                    if names is None or ALL in dem or (names & dem):
                        out |= edges
            else:
                out = graph.get(f, set())
            for t in out:
                if t not in parent:
                    parent[t] = f
                    changed = True
            for init, names in demands.get(f, ()):
                d = demanded.setdefault(init, set())
                new = {ALL} if names is None else names
                if not new <= d:
                    d |= new
                    changed = True
    return parent


def chain(parent, target):
    out = []
    while target is not None:
        out.append(target)
        target = parent[target]
    return " -> ".join(reversed(out))


def resolve_entry(e, root, mod2file):
    if e.endswith(".py") or (root / e).is_file():
        p = Path(e)
        rel = (p.relative_to(root) if p.is_absolute() else p).as_posix()
        return {rel}
    return resolve(e, mod2file)  # `python -m pkg.mod` also runs parent __init__s


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--entry", action="append", help="file path or dotted module (repeatable)")
    ap.add_argument("--exclude", action="append", default=[], help="extra dir name or relative path to skip")
    ap.add_argument("--tests-dir", default="tests", help="folder treated as test roots (default: tests)")
    ap.add_argument("--chain", action="append", default=[], help="print the import chain for this file")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    py_files, txt_files = scan(root, DEFAULT_EXCLUDE + args.exclude)
    try:
        me = Path(__file__).resolve().relative_to(root).as_posix()
        py_files = [f for f in py_files if f != me]
    except ValueError:
        pass
    mod2file = {module_name(f): f for f in py_files}

    trees, errors = {}, []
    for rel in py_files:
        try:
            trees[rel] = ast.parse((root / rel).read_text(encoding="utf-8", errors="replace"), filename=rel)
        except SyntaxError as e:
            errors.append((rel, str(e)))

    graph, dyn_calls, str_refs, has_main = {}, {}, {}, set()
    demands, inits = {}, {}
    for rel, tree in trees.items():
        edges, dyn, strs, dem, binds = analyse(rel, tree, mod2file, py_files)
        graph[rel] = edges
        demands[rel] = dem
        if Path(rel).name == "__init__.py":
            inits[rel] = binds
        if dyn:
            dyn_calls[rel] = dyn
        for lineno, target in strs:
            str_refs.setdefault(target, []).append((rel, lineno))
        if has_main_guard(tree):
            has_main.add(rel)

    entries = set()
    for e in (args.entry or DEFAULT_ENTRIES):
        found = resolve_entry(e, root, mod2file)
        found = {f for f in found if f in trees}
        if not found:
            print(f"[WARN] entry '{e}' not found, skipping")
        entries |= found

    tests_prefix = args.tests_dir.strip("/") + "/"
    test_files = {f for f in py_files if f.startswith(tests_prefix)}

    reach_a = reach(entries, graph)
    strict_a = reach_strict(entries, graph, inits, demands)
    reach_b = reach(entries | (test_files & set(trees)), graph)

    non_test = [f for f in py_files if f not in test_files]
    unreached_a = [f for f in non_test if f not in reach_a]
    test_only = [f for f in unreached_a if f in reach_b]
    dead = [f for f in unreached_a if f not in reach_b]

    # Mentions of candidate files in non-Python files (Dockerfile, compose, shell, ...)
    texts = {}
    for t in txt_files:
        try:
            texts[t] = (root / t).read_text(encoding="utf-8", errors="replace")
        except OSError:
            pass

    def text_hits(rel):
        pats = [re.escape(rel), re.escape(Path(rel).name)]
        if Path(rel).name != "__init__.py":
            pats.append(re.escape(module_name(rel)))
        rx = re.compile(r"(?<![\w])(?:" + "|".join(pats) + r")(?![\w])")
        return [t for t, body in texts.items() if rx.search(body)]

    def describe(rel):
        tags = []
        if rel in has_main:
            tags.append("[has __main__ guard]")
        refs = [(s, ln) for s, ln in str_refs.get(rel, []) if s in reach_b]
        if refs:
            tags.append("[string ref: " + ", ".join(f"{s}:{ln}" for s, ln in refs[:3]) + "]")
        th = text_hits(rel)
        if th:
            tags.append("[mentioned in: " + ", ".join(th[:3]) + "]")
        return f"  {rel} {' '.join(tags)}".rstrip()

    print(f"Project root: {root}")
    print(f"Entry files : {', '.join(sorted(entries))}")
    print(f"Python files: {len(py_files)} total, {len(test_files)} under {tests_prefix}")
    print(f"Reached from entry points: {len([f for f in reach_a if f not in test_files])}/{len(non_test)} non-test files "
          f"({len([f for f in strict_a if f not in test_files])} when __init__ re-exports must actually be used)\n")

    print(f"== REACHED ONLY BY TESTS ({len(test_only)}) ==")
    for f in test_only:
        print(describe(f))
    print(f"\n== NOT REACHED AT ALL ({len(dead)}) -- dead-code candidates ==")
    for f in dead:
        print(describe(f))

    init_only = [f for f in non_test if f in reach_a and f not in strict_a and f not in inits]
    print(f"\n== REACHED ONLY VIA __init__ RE-EXPORTS NOBODY USES ({len(init_only)}) ==")
    print("  (an __init__.py imports them, but nothing reached takes the re-exported names)")
    for f in init_only:
        via = []
        for init, binds in inits.items():
            if init in reach_a:
                names = sorted({n for e, ns in binds if f in e and ns for n in ns})
                if any(f in e for e, _ in binds):
                    via.append(f"{init} exports {', '.join(names) if names else '(side-effect/star)'}")
        tests = [t for t in sorted(test_files) if f in graph.get(t, ())]
        extra = " [via: " + "; ".join(via) + "]" if via else ""
        extra += f" [tests import it: {len(tests)}]" if tests else ""
        print(describe(f) + extra)

    if dyn_calls:
        print("\n== DYNAMIC IMPORT CALLS (may hide edges the graph cannot see) ==")
        for f, calls in sorted(dyn_calls.items()):
            print(f"  {f}: " + ", ".join(f"{n}@{ln}" for ln, n in calls))
    if errors:
        print("\n== FILES THAT FAILED TO PARSE ==")
        for f, msg in errors:
            print(f"  {f}: {msg}")

    for target in args.chain:
        t = Path(target).as_posix().lstrip("./")
        print(f"\n== CHAIN for {t} ==")
        if t in reach_a:
            print("  " + chain(reach_a, t))
        elif t in reach_b:
            print("  (tests only) " + chain(reach_b, t))
        else:
            print("  not reachable")


if __name__ == "__main__":
    main()
