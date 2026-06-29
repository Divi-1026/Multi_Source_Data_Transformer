
CANONICAL_TYPES = {
    "candidate_id": str,
    "full_name": (str, type(None)),
    "emails": list,
    "phones": list,
    "location": dict,
    "links": dict,
    "headline": (str, type(None)),
    "years_experience": (int, float, type(None)),
    "skills": list,
    "experience": list,
    "education": list,
    "provenance": list,
    "overall_confidence": (int, float),
}

#Single value fields 
SINGLE_VALUE_FIELDS = ["full_name", "headline", "years_experience"]

# Multiple Values Field take union
LIST_FIELDS = ["emails", "phones"]


def empty_record():
    """Return a fresh canonical record with all fields at their empty default."""
    return {
        "candidate_id": None,
        "full_name": None,
        "emails": [],
        "phones": [],
        "location": {"city": None, "region": None, "country": None},
        "links": {"linkedin": None, "github": None, "portfolio": None, "other": []},
        "headline": None,
        "years_experience": None,
        "skills": [],          # [{"name", "confidence", "sources": [...]}]
        "experience": [],      # [{"company", "title", "start", "end", "summary"}]
        "education": [],        # [{"institution", "degree", "field", "end_year"}]
        "provenance": [],       # [{"field", "source", "method"}]
        "overall_confidence": 0.0,
    }
