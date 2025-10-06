# ingest/dedupe.py
import hashlib, re, urllib.parse as up

TRACKING_PARAMS = {"utm_source","utm_medium","utm_campaign","utm_term","utm_content","gh_src","gh_jid"}

def canonicalize_url(url: str) -> str:
    if not url: return ""
    u = up.urlsplit(url)
    # lowercase scheme + host, remove fragment, drop tracking params
    host = u.netloc.lower()
    query = up.parse_qsl(u.query, keep_blank_values=False)
    query = [(k,v) for (k,v) in query if k.lower() not in TRACKING_PARAMS]
    query.sort()  # deterministic order
    path = u.path.rstrip("/")  # drop trailing slash
    return up.urlunsplit((u.scheme.lower(), host, path, up.urlencode(query), ""))

def sha256_bytes(s: str) -> bytes:
    return hashlib.sha256((s or "").encode("utf-8")).digest()

def normalize_text(s: str) -> str:
    s = (s or "").lower()
    s = re.sub(r"\s+", " ", s).strip()
    return s

def desc_hash(text: str) -> bytes:
    # hash only the normalized description text (title/company can vary)
    return sha256_bytes(normalize_text(text))
