# Simple precision/recall on a tiny labeled file
import json
from pathlib import Path
from collections import Counter
from db.session import SessionLocal
from ingest.skills_extract import build_matcher, extract

def main(fi="data/eval_samples.jsonl"):
    lines = [json.loads(l) for l in Path(fi).read_text(encoding="utf-8").splitlines()]
    tp = fp = fn = 0
    with SessionLocal() as db:
        build_matcher(db)
    for ex in lines:
        pred = set(k for k,_ in extract(ex["text"]))
        gold = set(ex["labels"])  # canonical
        tp += len(pred & gold)
        fp += len(pred - gold)
        fn += len(gold - pred)
    prec = tp / (tp + fp) if tp+fp else 0
    rec  = tp / (tp + fn) if tp+fn else 0
    print(f"precision={prec:.3f} recall={rec:.3f} (tp={tp} fp={fp} fn={fn})")

if __name__ == "__main__":
    main()
