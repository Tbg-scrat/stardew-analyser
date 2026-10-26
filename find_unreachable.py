#!/usr/bin/env python3
"""Match everything the router imports against the processors package (stdlib only).

Starting at the entry point (default: src/core/extractor/router.py) the script
  1. follows imports to find all files the router can reach,
  2. collects every import that points into the processors folder
     (resolving re-exports through __init__.py, aliases and `module.func` access),
  3. checks that each imported name exists and is actually used,
  4. walks the call graph INSIDE the processors folder, so a helper only counts as
     live if a live function (or module-level code) really references it.

Usage (from the project root):
    python find_unreachable.py
    python find_unreachable.py --entry src/core/extractor/router.py --target src/core/extractor/processors

Results are candidates: verify before deleting.
"""
import argparse
import ast
import os
from collections import deque
from pathlib import Path

DEFAULT_ENTRY = "src/core/extractor/router.py"
DEFAULT_TARGET = "src/core/extractor/processors"
DEFAULT_EXCLUDE = [
    ".venv", "venv", ".git", "__pycache__", "htmlcov", "saves",
    "node_modules", ".mypy_cache", ".pytest_cache", "scripts",
]
DYNAMIC_CALLS = {
    "import_module", "__import__", "iter_modules", "walk_packages",
    "run_module", "run_path", "spec_from_file_location",
}


# ------------------------------------------------------------ file / module helpers
def scan(root, exclude):
    names = {e for e in exclude if "/" not in e}
    paths = {e.strip("/") for e in exclude if "/" in e}
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = Path(dirpath).relative_to(root)
        dirnames[:] = [d for d in dirnames
                       if d not in names and (rel_dir / d).as_posix() not in paths]
        out += [(rel_dir / f).as_posix() for f in filenames if f.endswith(".py")]
    return sorted(out)


def module_name(rel):
    parts = list(Path(rel).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def package_of(rel):
    p = Path(rel)
    return module_name(rel) if p.name == "__init__.py" else ".".join(p.parent.parts)


def resolve(name, mod2file):
    """Importing a.b.c also executes the __init__.py of a and a.b."""
    parts = name.split(".")
    return {mod2file[".".join(parts[:i])] for i in range(1, len(parts) + 1)
            if ".".join(parts[:i]) in mod2file}


# ------------------------------------------------------------ imports
class Imp:
    """One imported name.
    kind 'module': `import a.b [as x]`   -> file = module file, local = alias or dotted name
    kind 'from'  : `from m import n [as x]` -> file = file of m, orig = n, sub = file of m.n (if a module)
    kind 'star'  : `from m import *`     -> file = file of m
    """
    def __init__(self, lineno, local, kind, file, orig=None, sub=None):
        self.lineno, self.local, self.kind = lineno, local, kind
        self.file, self.orig, self.sub = file, orig, sub


def imports_of(rel, tree, mod2file):
    pkg = package_of(rel)
    pkg_parts = pkg.split(".") if pkg else []
    imps, edges = [], set()

    def find(c, sib):
        hit = resolve(c, mod2file)
        if not hit and sib and pkg:  # script-mode: `import helper` next to the script
            hit = resolve(f"{pkg}.{c}", mod2file)
        return hit

    def modfile(c, sib):
        f = mod2file.get(c)
        if f is None and sib and pkg:
            f = mod2file.get(f"{pkg}.{c}")
        return f

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                edges |= find(a.name, True)
                f = modfile(a.name, True)
                if f:
                    imps.append(Imp(node.lineno, a.asname or a.name, "module", f))
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                cut = node.level - 1
                if cut > len(pkg_parts):
                    continue
                base = pkg_parts[:len(pkg_parts) - cut]
                mod = ".".join(base + ([node.module] if node.module else []))
            else:
                mod = node.module or ""
            sib = node.level == 0
            if mod:
                edges |= find(mod, sib)
            mf = modfile(mod, sib) if mod else None
            for a in node.names:
                if a.name == "*":
                    if mf:
                        imps.append(Imp(node.lineno, "*", "star", mf))
                    continue
                sub = f"{mod}.{a.name}" if mod else a.name
                edges |= find(sub, sib)
                imps.append(Imp(node.lineno, a.asname or a.name, "from", mf, a.name, modfile(sub, sib)))
    return imps, edges


# ------------------------------------------------------------ name usage
def dotted(node):
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return ".".join(reversed(parts)), node
    return None, None


def scope_uses(nodes):
    """(all loaded names, names used on their own, dotted attribute chains)"""
    walked = [n for node in nodes for n in ast.walk(node)]
    chains, bases = set(), set()
    for n in walked:
        if isinstance(n, ast.Attribute):
            d, base = dotted(n)
            if d:
                chains.add(d)
                bases.add(id(base))
    names, bare = set(), set()
    for n in walked:
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load):
            names.add(n.id)
            if id(n) not in bases:
                bare.add(n.id)
    return names, bare, chains


def is_main_guard(node):
    return (isinstance(node, ast.If) and isinstance(node.test, ast.Compare)
            and isinstance(node.test.left, ast.Name) and node.test.left.id == "__name__")


class Info:
    def __init__(self, rel, tree, mod2file):
        self.rel, self.tree = rel, tree
        self.is_init = Path(rel).name == "__init__.py"
        self.imports, self.edges = imports_of(rel, tree, mod2file)
        self.edges.discard(rel)
        self.defs, self.def_uses, self.decorated = {}, {}, set()
        module_nodes = []
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                is_cls = isinstance(node, ast.ClassDef)
                self.defs[node.name] = (node.lineno, "class" if is_cls else "function")
                self.def_uses[node.name] = scope_uses([node])
                if node.decorator_list:
                    self.decorated.add(node.name)
                module_nodes += node.decorator_list
                if is_cls:
                    module_nodes += node.bases + [k.value for k in node.keywords]
                else:
                    module_nodes += node.args.defaults + [d for d in node.args.kw_defaults if d]
            elif isinstance(node, (ast.Import, ast.ImportFrom)) or is_main_guard(node):
                continue
            else:
                module_nodes.append(node)
        self.module_uses = scope_uses(module_nodes)
        self.whole_uses = scope_uses([tree])


# ------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--entry", default=DEFAULT_ENTRY)
    ap.add_argument("--target", default=DEFAULT_TARGET)
    ap.add_argument("--exclude", action="append", default=[])
    args = ap.parse_args()

    root = Path(args.root).resolve()
    py_files = scan(root, DEFAULT_EXCLUDE + args.exclude)
    try:  # never analyse this script itself
        me = Path(__file__).resolve().relative_to(root).as_posix()
        py_files = [f for f in py_files if f != me]
    except ValueError:
        pass
    mod2file = {module_name(f): f for f in py_files}

    entry = Path(args.entry).as_posix()
    target_prefix = Path(args.target).as_posix().strip("/") + "/"
    if entry not in py_files:
        raise SystemExit(f"Entry point not found: {entry}")
    target_files = [f for f in py_files if f.startswith(target_prefix)]
    if not target_files:
        raise SystemExit(f"No Python files under {target_prefix}")
    target_set = set(target_files)

    infos, errors = {}, []
    for rel in py_files:
        try:
            tree = ast.parse((root / rel).read_text(encoding="utf-8", errors="replace"), filename=rel)
            infos[rel] = Info(rel, tree, mod2file)
        except SyntaxError as e:
            errors.append((rel, str(e)))

    # 1. everything reachable from the entry point (python -m also runs parent __init__s)
    seeds = {entry} | resolve(module_name(entry), mod2file)
    reached, queue = set(seeds), deque(seeds)
    while queue:
        cur = queue.popleft()
        for nxt in infos[cur].edges:
            if nxt not in reached:
                reached.add(nxt)
                queue.append(nxt)

    # 2. name binding: follow aliases and re-exports to the file that defines a name
    def resolve_binding(file, name, seen=None):
        seen = seen if seen is not None else set()
        if file is None or (file, name) in seen or file not in infos:
            return None
        seen.add((file, name))
        info = infos[file]
        if name in info.defs:
            return ("name", file, name)
        for imp in info.imports:
            if imp.local == name and imp.kind == "module":
                return ("module", imp.file)
            if imp.local == name and imp.kind == "from":
                r = resolve_binding(imp.file, imp.orig, seen)
                if r:
                    return r
                if imp.sub:
                    return ("module", imp.sub)
        for imp in info.imports:
            if imp.kind == "star":
                r = resolve_binding(imp.file, name, seen)
                if r:
                    return r
        return None

    def bind(imp):
        if imp.kind == "module":
            return ("module", imp.file)
        if imp.kind == "from":
            r = resolve_binding(imp.file, imp.orig)
            if r:
                return r
            if imp.sub:
                return ("module", imp.sub)
        return None

    # 3. liveness inside the processors package
    live, why, loaded, work = set(), {}, set(), deque()

    def mark(file, name, reason):
        if file in target_set and name in infos[file].defs and (file, name) not in live:
            live.add((file, name))
            why[(file, name)] = reason
            work.append((file, name))

    def mark_all(file, reason):
        for n in infos[file].defs:
            mark(file, n, reason)

    def load(file, reason):
        if file in target_set and file not in loaded:
            loaded.add(file)
            info = infos[file]
            if not info.is_init:  # an __init__ merely re-exports; that is not a use
                apply_uses(info, info.module_uses, f"module-level code of {file}")
                for n in info.decorated:
                    mark(file, n, f"decorated, runs at import ({file})")

    def apply_uses(info, uses, reason, report=None):
        """Mark what `uses` references. report: list collecting (imp, status, target)."""
        names, bare, chains = uses
        for n in names:
            if n in info.defs:
                mark(info.rel, n, reason)
        for imp in info.imports:
            if imp.kind == "star":
                continue
            t = bind(imp)
            in_target = (t is not None and t[1] in target_set) or (t is None and imp.file in target_set)
            if not in_target:
                continue
            if t is None:
                if report is not None:
                    report.append((imp, "NOT FOUND", None))
                continue
            load(t[1], reason)
            used = False
            if t[0] == "name":
                if imp.local in names:
                    used = True
                    mark(t[1], t[2], reason)
            else:
                prefix = imp.local
                for c in chains:
                    if c.startswith(prefix + "."):
                        used = True
                        r = resolve_binding(t[1], c[len(prefix) + 1:].split(".")[0])
                        if r and r[0] == "name":
                            mark(r[1], r[2], reason)
                if "." not in prefix and prefix in bare:
                    used = True
                    mark_all(t[1], reason + " (module used as object)")
            if report is not None:
                report.append((imp, "used" if used else "UNUSED IMPORT", t))

    external = sorted(f for f in reached if f in infos and f not in target_set
                      and not infos[f].is_init)
    rows = []  # (importer, imp, status, target)
    for f in external:
        info = infos[f]
        rep = []
        apply_uses(info, info.whole_uses, f"{f}", rep)
        rows += [(f, imp, st, t) for imp, st, t in rep]
    while work:
        f, name = work.popleft()
        load(f, "")
        apply_uses(infos[f], infos[f].def_uses[name], f"{f}::{name}")

    # who else (unreached files, e.g. tests) uses processor names -> relict detection
    other = {}
    for f, info in infos.items():
        if f in reached or f in target_set:
            continue
        rep = []
        names, bare, chains = info.whole_uses
        for imp in info.imports:
            if imp.kind == "star":
                continue
            t = bind(imp)
            if not t or t[1] not in target_set:
                continue
            if t[0] == "name" and imp.local in names:
                other.setdefault((t[1], t[2]), set()).add(f)
            elif t[0] == "module":
                for c in chains:
                    if c.startswith(imp.local + "."):
                        r = resolve_binding(t[1], c[len(imp.local) + 1:].split(".")[0])
                        if r and r[0] == "name":
                            other.setdefault((r[1], r[2]), set()).add(f)

    def others(file, name):
        users = sorted(other.get((file, name), ()))
        if not users:
            return ""
        shown = ", ".join(users[:2]) + (f" +{len(users) - 2}" if len(users) > 2 else "")
        return f"  [still used by unreached: {shown}]"

    # ---------------------------------------------------------- report
    print(f"Entry point : {entry}")
    print(f"Target      : {target_prefix}  ({len(target_files)} files)")
    print(f"Reachable   : {len(reached)} files, {len(external)} outside the target that can import from it\n")

    print("== IMPORTS FROM THE TARGET (matched against definitions) ==")
    if not rows:
        print("  none found")
    for f, imp, st, t in rows:
        what = imp.orig if imp.kind == "from" else imp.local
        if t and t[0] == "name":
            dest = f"{t[1]}::{t[2]} (line {infos[t[1]].defs[t[2]][0]})"
        elif t:
            dest = f"module {t[1]}"
        else:
            dest = f"no definition of '{what}' in {imp.file}"
        flag = "" if st == "used" else f"  <-- {st}"
        print(f"  {f}:{imp.lineno}  {what} -> {dest}{flag}")

    print("\n== PER FILE IN THE TARGET ==")
    for f in target_files:
        info = infos.get(f)
        if info is None or info.is_init:
            continue
        defs = sorted(info.defs.items(), key=lambda kv: kv[1][0])
        live_defs = [(n, m) for n, m in defs if (f, n) in live]
        dead_defs = [(n, m) for n, m in defs if (f, n) not in live]
        if f not in loaded:
            status = "NEVER IMPORTED by reachable code"
        elif not live_defs:
            status = "IMPORTED, but nothing from it is used"
        else:
            status = "IN USE"
        print(f"\n{f}  [{status}]")
        for n, (ln, kind) in live_defs:
            print(f"   live  {kind} {n} (line {ln})  <- {why[(f, n)]}")
        for n, (ln, kind) in dead_defs:
            print(f"   DEAD  {kind} {n} (line {ln}){others(f, n)}")
        if not defs:
            print("   (no top-level functions or classes)")

    dyn = []
    for f in sorted(reached):
        for node in ast.walk(infos[f].tree):
            if isinstance(node, ast.Call):
                fn = node.func
                name = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", None)
                if name in DYNAMIC_CALLS:
                    dyn.append(f"{f}:{node.lineno} {name}")
    if dyn:
        print("\n== DYNAMIC IMPORT CALLS in reachable code (may hide uses) ==")
        for d in dyn:
            print("  " + d)
    if errors:
        print("\n== FILES THAT FAILED TO PARSE ==")
        for f, msg in errors:
            print(f"  {f}: {msg}")


if __name__ == "__main__":
    main()
    