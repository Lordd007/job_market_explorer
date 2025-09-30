import pytest
from db.session import SessionLocal
from ingest.skills_extract import build_matcher, extract

@pytest.fixture(scope="module", autouse=True)
def _build():
    with SessionLocal() as db:
        build_matcher(db)
    yield

def test_basic_match():
    txt = "We use Python, Pandas and scikit-learn on Kubernetes."
    skills = dict(extract(txt))
    for k in ["python", "pandas", "scikit-learn", "kubernetes"]:
        assert k in skills and skills[k] >= 0.9

def test_aliases_work():
    txt = "We love sklearn and k8s."
    skills = dict(extract(txt))
    assert "scikit-learn" in skills
    assert "kubernetes" in skills
