import json, sys
from collections import defaultdict
from pathlib import Path

def main(path="data/seed_skills.json"):
    items = json.loads(Path(path).read_text(encoding="utf-8"))
    seen = set()
    alias_to_canon = {}
    errs = []

    for i, it in enumerate(items, 1):
        canon = it["name_canonical"].strip().lower()
        if canon in seen:
            errs.append(f"duplicate canonical: {canon}")
        seen.add(canon)

        for a in it.get("aliases", []):
            a = a.strip().lower()
            if a in alias_to_canon and alias_to_canon[a] != canon:
                errs.append(f"alias mapped to multiple canon: {a} -> {alias_to_canon[a]} / {canon}")
            alias_to_canon[a] = canon

    if errs:
        print("❌ Validation errors:")
        for e in errs: print(" -", e)
        sys.exit(1)
    print(f"✅ OK: {len(items)} skills, {len(alias_to_canon)} aliases")


if __name__ == "__main__":
    main()
