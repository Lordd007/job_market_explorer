import json, re
from typing import Dict, Iterable, List, Tuple
import spacy
from spacy.matcher import PhraseMatcher
from sqlalchemy.orm import Session
from db.models import Skill

# Lazy, module-level caches to call build_matcher(db) once per run.
_NLP = None          # type: ignore
_MATCHER = None      # type: ignore
_CANON_MAP: Dict[str, str] = {}  # normalized phrase -> canonical skill

def _norm(s: str) -> str:
    """Normalize for matching: lowercase, single spaces, strip."""
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def build_matcher(db: Session) -> None:
    """
    Build a PhraseMatcher from skills in DB.
    Call this once at the start of an ingest run (or whenever skills change).
    """
    global _NLP, _MATCHER, _CANON_MAP

    if _NLP is None:
        # Small English pipeline is enough for PhraseMatcher
        _NLP = spacy.load("en_core_web_sm")

    _MATCHER = PhraseMatcher(_NLP.vocab, attr="LOWER")
    _CANON_MAP.clear()

    patterns = []
    skills: Iterable[Skill] = db.query(Skill).all()
    for sk in skills:
        names = [sk.name_canonical]
        try:
            aliases = json.loads(sk.aliases_json or "[]")
            if isinstance(aliases, list):
                names.extend(aliases)
        except Exception:
            # If aliases_json is malformed, ignore it (keep going)
            pass

        for raw in names:
            name = _norm(raw)
            if not name:
                continue
            # Avoid duplicate patterns
            if name in _CANON_MAP:
                continue
            patterns.append(_NLP.make_doc(name))
            _CANON_MAP[name] = sk.name_canonical

    if patterns:
        _MATCHER.add("SKILL", patterns)


def extract(text: str) -> List[Tuple[str, float]]:
    """
    Extract canonical skills from text.
    Returns list of (skill_name, confidence).
    """
    if not text or _MATCHER is None:
        return []
    doc = _NLP(text)
    hits = set()
    for _, start, end in _MATCHER(doc):
        phrase = _norm(doc[start:end].text)
        hits.add(_CANON_MAP.get(phrase, phrase))

    # simple fixed-confidence for dict hits; you can evolve this later
    return [(h, 0.95) for h in sorted(hits)]