# ingest/skills_extract.py
import re
import json
from typing import Iterable, List, Tuple
import spacy
from spacy.matcher import PhraseMatcher
from sqlalchemy.orm import Session
from db.models import Skill

_NLP = None
_MATCHER = None
_ALIAS2CANON = {}

def _norm(s: str) -> str:
    """Lowercase, trim, collapse spaces, and normalize hyphen spacing."""
    s = (s or "").lower().strip()
    s = re.sub(r"\s*-\s*", "-", s)   # "scikit - learn" -> "scikit-learn"
    s = re.sub(r"\s+", " ", s)
    return s

def _ensure_nlp():
    global _NLP
    if _NLP is None:
        _NLP = spacy.load("en_core_web_sm", disable=["ner", "tagger", "parser", "lemmatizer"])
        _NLP.max_length = 2_000_000
    return _NLP

def _skills_from_db(db: Session) -> List[Tuple[str, str]]:
    out: List[Tuple[str, str]] = []
    for s in db.query(Skill).all():
        canon = _norm(s.name_canonical)
        out.append((canon, canon))
        try:
            aliases = json.loads(s.aliases_json or "[]")
        except Exception:
            aliases = []
        for a in aliases:
            a = _norm(a)
            if a and a != canon:
                out.append((a, canon))
    return out

def build_matcher(db: Session) -> None:
    global _MATCHER, _ALIAS2CANON
    nlp = _ensure_nlp()
    m = PhraseMatcher(nlp.vocab, attr="LOWER")

    _ALIAS2CANON = {}
    seen = set()
    docs = []
    for alias, canon in _skills_from_db(db):
        if alias in seen:
            continue
        seen.add(alias)
        _ALIAS2CANON[alias] = canon
        docs.append(nlp.make_doc(alias))

    if docs:
        m.add("SKILL", docs)
    _MATCHER = m

def extract(text: str) -> List[Tuple[str, float]]:
    if not text or _MATCHER is None:
        return []
    nlp = _ensure_nlp()
    doc = nlp(text)
    found: dict[str, float] = {}
    for _, start, end in _MATCHER(doc):
        phrase = _norm(doc[start:end].text)
        canon = _ALIAS2CANON.get(phrase)
        if canon:
            found[canon] = max(found.get(canon, 0.0), 0.9)
    return sorted(found.items(), key=lambda x: (-x[1], x[0]))
