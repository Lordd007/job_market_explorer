# scripts/nightly_ingest.py
import os, subprocess, sys

SOURCE = os.getenv("JME_SOURCE", "seed")   # e.g. greenhouse:acme or lever:acme
DAYS   = os.getenv("JME_DAYS", "1")

def run(cmd: str):
    print(f"$ {cmd}")
    rc = subprocess.call(cmd, shell=True)
    if rc != 0:
        sys.exit(rc)

# Always refresh demo data, then run one live source
run("python -m ingest.pipeline --source=seed --days=90")
run(f"python -m ingest.pipeline --source={SOURCE} --days={DAYS}")
print("✅ nightly ingest done")
