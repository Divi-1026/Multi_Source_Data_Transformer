"""Run with:  python -m pytest -q   (or)  python tests/test_pipeline.py"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from transformer import normalize as N
from transformer.pipeline import run
from transformer.project import resolve_path

HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLES = os.path.join(os.path.dirname(HERE), "samples")
CONFIGS = os.path.join(os.path.dirname(HERE), "configs")


def test_normalize():
    assert N.normalize_phone("098765 43210") == "+919876543210"
    assert N.normalize_phone("+91 98765 43210") == "+919876543210"
    assert N.normalize_date("Mar 2024") == "2024-03"
    assert N.normalize_date("2021-06") == "2021-06"
    assert N.normalize_country("India") == "IN"
    assert N.normalize_country("Atlantis") is None        # unknown -> None, not invented
    assert N.normalize_skill("js") == "JavaScript"


def test_resolve_path():
    rec = {"emails": ["a@x.com"], "location": {"city": "Pune"},
           "skills": [{"name": "Python"}, {"name": "SQL"}]}
    assert resolve_path(rec, "emails[0]") == "a@x.com"
    assert resolve_path(rec, "location.city") == "Pune"
    assert resolve_path(rec, "skills[].name") == ["Python", "SQL"]
    assert resolve_path(rec, "phones[0]") is None         # missing -> None


def test_merge_and_conflict():
    sources = {
        "csv": os.path.join(SAMPLES, "recruiter.csv"),
        "ats": os.path.join(SAMPLES, "ats.json"),
        "notes": os.path.join(SAMPLES, "notes.txt"),
    }
    result = run(sources)
    profiles = {p["full_name"]: p for p in result["profiles"]}

    # garbage CSV row was dropped -> exactly two people
    assert len(result["profiles"]) == 2

    aman = profiles["Aman Patel"]
    # ATS (higher reliability) wins the title conflict
    assert aman["headline"] == "Data Science Intern"
    # phones from CSV + ATS dedupe to one E.164 value
    assert aman["phones"] == ["+919876543210"]
    # skills are canonical + unioned across all three sources
    names = {s["name"] for s in aman["skills"]}
    assert {"Python", "React", "JavaScript", "Machine Learning"} <= names
    # github link came from the unstructured notes
    assert aman["links"]["github"] == "https://github.com/amanpatel"
    # provenance is populated
    assert any(p["field"] == "headline" for p in aman["provenance"])
    # same job from CSV + ATS merges into ONE experience entry (not two)
    getpost = [e for e in aman["experience"] if e["company"] == "GetPost Labs"]
    assert len(getpost) == 1
    assert getpost[0]["title"] == "Data Science Intern"  # strongest source wins
    assert getpost[0]["start"] == "2024-03"               # date filled from ATS


def test_projection_and_edge_case():
    import json
    with open(os.path.join(CONFIGS, "compact.json")) as fh:
        config = json.load(fh)
    # only the notes source -> phone is missing; on_missing=null must not crash
    sources = {"notes": os.path.join(SAMPLES, "notes.txt")}
    result = run(sources, config)
    out = {p["full_name"]: p for p in result["profiles"]}["Aman Patel"]
    assert out["primary_email"] == "aman.patel@example.com"
    assert out["phone"] is None                           # honestly empty, not invented
    assert "overall_confidence" in out


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok  {name}")
    print("all tests passed")
