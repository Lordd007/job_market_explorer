import json, re
from typing import List, Tuple
import spacy
from spacy.matcher import PhraseMatcher
from sqlalchemy.orm import Session
from db.models import Skill

_nlp = None
_matcher = None
_canon = {}

def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())

def build_matcher(db: Session):
    global _nlp, _matcher, _canon
    if _nlp is None:
        _nlp = spacy.load("en_core_web_sm")
    _matcher = PhraseMatcher(_nlp.vocab, attr="LOWER")
    _canon.clear()
    patterns = []
    for sk in db.query(Skill).all():
        names = [sk.name_canonical] + json.loads(sk.aliases_json or "[]")
        for name in names:
            name = _norm(name)
            if not name:
                continue
            patterns.append(_nlp.make_doc(name))
            _canon[name] = sk.name_canonical
    if patterns:
        _matcher.add("SKILL", patterns)

def extract(text: str) -> list[tuple[str, float]]:
    if not text or _matcher is None:
        return []
    doc = _nlp(text)
    hits = set()
    for _, start, end in _matcher(doc):
        phrase = _norm(doc[start:end].text)
        hits.add(_canon.get(phrase, phrase))
    return [(h, 0.95) for h in sorted(hits)]
