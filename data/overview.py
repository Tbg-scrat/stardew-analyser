import json
import sys
from pathlib import Path

N, MAXLEN = 2, 300  # examples per file, max characters per example

for f in sorted(Path(sys.argv[1] if len(sys.argv) > 1 else ".").glob("*.json")):
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"== {f.name}: unreadable ({e})\n")
        continue
    if not isinstance(d, dict):
        print(f"== {f.name}: top level is {type(d).__name__}, no _meta\n")
        continue
    items = d.get("items")
    wrapped = items is not None
    if not wrapped:
        items = {k: v for k, v in d.items() if k != "_meta"}
    print(f"== {f.name} | {'items wrapper' if wrapped else 'FLAT'} | {len(items)} entries")
    print("   _meta:", json.dumps(d.get("_meta"), ensure_ascii=False))
    for k, v in list(items.items())[:N]:
        print("   ", k, "->", json.dumps(v, ensure_ascii=False)[:MAXLEN])
    print()
