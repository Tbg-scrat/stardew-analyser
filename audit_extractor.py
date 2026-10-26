# audit_extractor.py
import os
import ast
from glob import glob

PROJECT_ROOT = "."
TARGET_DIR = "src/core/extractor"

def file_to_module_path(file_path):
    """Converts a file path like src/core/extractor/router.py to dotted module paths."""
    clean_path = os.path.splitext(file_path)[0]
    parts = clean_path.split(os.sep)
    if parts[0] == ".":
        parts = parts[1:]
    return ".".join(parts)

def get_imports_from_file(file_path):
    """Parses a Python file and returns all imported module paths/names."""
    imports = set()
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            node = ast.parse(f.read(), filename=file_path)
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return imports, False

    has_main = False
    for subnode in ast.walk(node):
        # Check if file can act as a main script entry point
        if isinstance(subnode, ast.If):
            if isinstance(subnode.test, ast.Compare):
                # looks for __name__ == "__main__"
                pass # (Simplified check; can also check string constants)

        if isinstance(subnode, ast.Import):
            for alias in subnode.names:
                imports.add(alias.name)
        elif isinstance(subnode, ast.ImportFrom):
            if subnode.module:
                if subnode.level > 0:
                    parts = file_path.split(os.sep)
                    base_parts = parts[:-subnode.level]
                    if subnode.module:
                        mod = ".".join(base_parts + subnode.module.split("."))
                    else:
                        mod = ".".join(base_parts)
                    imports.add(mod)
                else:
                    imports.add(subnode.module)
                    for alias in subnode.names:
                        imports.add(f"{subnode.module}.{alias.name}")
            elif subnode.level > 0:
                parts = file_path.split(os.sep)
                base_parts = parts[:-subnode.level]
                for alias in subnode.names:
                    imports.add(".".join(base_parts + [alias.name]))
                    
    # Check for __main__ block explicitly via AST
    for node_body in node.body:
        if isinstance(node_body, ast.If):
            test = node_body.test
            if isinstance(test, ast.Compare):
                # Simple check for __name__ == "__main__"
                dump = ast.dump(test)
                if "__name__" in dump and "__main__" in dump:
                    has_main = True

    return imports, has_main

def audit_directory():
    all_py_files = glob(os.path.join(PROJECT_ROOT, "**", "*.py"), recursive=True)
    
    file_to_mod = {}
    mod_to_file = {}
    file_to_imports = {}
    entry_points = set()

    for fpath in all_py_files:
        if ".venv" in fpath or "__pycache__" in fpath:
            continue
        
        mod_path = file_to_module_path(fpath)
        file_to_mod[fpath] = mod_path
        mod_to_file[mod_path] = fpath
        
        imports, has_main = get_imports_from_file(fpath)
        file_to_imports[fpath] = imports

        # Define roots / entry points:
        # 1. Any file inside tests/
        # 2. Any file with if __name__ == "__main__":
        # 3. Known root scripts (watch.py, router.py invoked via -m)
        if "tests/" in fpath or has_main or "watch.py" in fpath or "router.py" in fpath:
            entry_points.add(fpath)

    # Build adjacency list for graph traversal (Forward reachability)
    # We want to see what files can be reached starting from entry_points
    visited = set()
    queue = list(entry_points)

    while queue:
        current_file = queue.pop(0)
        if current_file in visited:
            continue
        visited.add(current_file)

        current_imports = file_to_imports.get(current_file, set())
        for imp in current_imports:
            # Match import string to actual files in our project
            for fpath, mod in file_to_mod.items():
                if fpath in visited:
                    continue
                if mod == imp or mod.endswith("." + imp) or imp.startswith(mod):
                    queue.append(fpath)

    print(f"=== Dependency Reachability Audit for: {TARGET_DIR} ===\n")
    target_abs_dir = os.path.normpath(TARGET_DIR)
    target_files = [
        f for f in all_py_files 
        if os.path.normpath(f).startswith(target_abs_dir) and not f.endswith("__init__.py")
    ]

    orphaned_files = []

    for target_file in target_files:
        if target_file in visited:
            print(f"[ACTIVE]   {target_file} (Reachable from entry points/tests)")
        else:
            orphaned_files.append(target_file)
            print(f"[ORPHANED] {target_file} (Unreachable from any entry point or test)")

    print(f"\nAudit complete. Found {len(orphaned_files)} truly orphaned files out of {len(target_files)} in {TARGET_DIR}.")

if __name__ == "__main__":
    audit_directory()
    