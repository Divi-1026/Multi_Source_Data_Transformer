
import csv
import json
import re
def _source_record(source, method, data):
    return {"source": source, "method": method, "data": data}


#Structured source -- Recruiter CSV 

def parse_csv(path):
    """Recruiter CSV export. Columns: name,email,phone,company,title,location,skills"""
    records = []
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            row = {(k or "").strip(): (v or "").strip() for k, v in row.items()}
            # skip empty / garbage rows (no name and no email) -> never invent data
            if not row.get("name") and not row.get("email"):
                continue
            city, country = _split_location(row.get("location", ""))
            data = {
                "full_name": row.get("name") or None,
                "emails": [row["email"]] if row.get("email") else [],
                "phones": [row["phone"]] if row.get("phone") else [],
                "headline": row.get("title") or None,
                "location": {"city": city, "region": None, "country": country},
                "skills": _split_list(row.get("skills", "")),
                "experience": _one_experience(row.get("company"), row.get("title"), None),
            }
            records.append(_source_record("recruiter_csv", "csv_column", data))
    return records


#Structured source 2: ATS JSON

def parse_ats(path):
   
    records = []
    with open(path, encoding="utf-8") as fh:
        blobs = json.load(fh)
    if isinstance(blobs, dict):
        blobs = [blobs]
    for b in blobs:
        if not isinstance(b, dict):
            continue
        if not b.get("candidateName") and not b.get("primaryEmail"):
            continue
        years = b.get("experienceYears")
        data = {
            "full_name": b.get("candidateName") or None,
            "emails": [b["primaryEmail"]] if b.get("primaryEmail") else [],
            "phones": [b["mobile"]] if b.get("mobile") else [],
            "headline": b.get("jobTitle") or None,
            "years_experience": years if isinstance(years, (int, float)) else None,
            "location": {"city": b.get("city"), "region": None, "country": b.get("country")},
            "skills": b.get("skillTags") or [],
            "experience": _one_experience(b.get("currentEmployer"), b.get("jobTitle"), b.get("since")),
        }
        records.append(_source_record("ats_json", "ats_field_map", data))
    return records


# Unstructured source: recruiter notes (.txt free text)

_SKILL_KEYWORDS = [
    "machine learning", "deep learning", "system design", "spring boot",
    "javascript", "python", "react", "java", "sql", "databases", "pandas",
]


def parse_notes(path):
    """Free-text recruiter notes. Blocks separated by a line of '---'."""
    records = []
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    for block in re.split(r"\n-{3,}\n", text):
        block = block.strip()
        if not block:
            continue
        name = _search(r"candidate:\s*([^\(\n]+)", block)
        if name:
            name = name.strip()
        email = _search(r"[\w.\-]+@[\w.\-]+\.\w+", block, group=0)
        if not name and not email:
            continue
        low = block.lower()
        skills = [kw for kw in _SKILL_KEYWORDS if kw in low]
        links = {"linkedin": None, "github": None, "portfolio": None, "other": []}
        gh = _search(r"(github\.com/[\w\-]+)", block)
        li = _search(r"(linkedin\.com/in/[\w\-]+)", block)
        if gh:
            links["github"] = "https://" + gh
        if li:
            links["linkedin"] = "https://" + li
        data = {
            "full_name": name,
            "emails": [email] if email else [],
            "skills": skills,
            "links": links,
        }
        records.append(_source_record("recruiter_notes", "text_extraction", data))
    return records

def _split_list(s):
    return [p.strip() for p in re.split(r"[;,]", s or "") if p.strip()]


def _split_location(s):

    s = (s or "").strip()
    if not s:
        return None, None
    parts = s.split()
    if len(parts) >= 2:
        return " ".join(parts[:-1]), parts[-1]
    return s, None


def _one_experience(company, title, start):
    if not company and not title:
        return []
    return [{
        "company": company or None,
        "title": title or None,
        "start": start,   # raw; normalized later
        "end": None,
        "summary": None,
    }]


def _search(pattern, text, group=1):
    m = re.search(pattern, text, re.IGNORECASE)
    if not m:
        return None
    return m.group(group)
