
import hashlib

from . import normalize as N
from .schema import empty_record

#  ats >>> recruiter>>> recruiter_notes
SOURCE_RELIABILITY = {
    "ats_json": 0.85,   
    "recruiter_csv": 0.80,   
    "recruiter_notes": 0.55,
}


#normalize a single SourceRecord 

def normalize_record(sr):
    """Return a new SourceRecord with canonical formats applied to its data."""
    d = sr["data"]
    out = {}
    if "full_name" in d:
        out["full_name"] = d["full_name"]
    if "headline" in d:
        out["headline"] = d["headline"]
    if "years_experience" in d:
        out["years_experience"] = d["years_experience"]
    if "emails" in d:
        out["emails"] = [e for e in (N.normalize_email(x) for x in d["emails"]) if e]
    if "phones" in d:
        out["phones"] = [p for p in (N.normalize_phone(x) for x in d["phones"]) if p]
    if "skills" in d:
        out["skills"] = [s for s in (N.normalize_skill(x) for x in d["skills"]) if s]
    if "location" in d:
        loc = d["location"] or {}
        out["location"] = {
            "city": (loc.get("city") or None),
            "region": (loc.get("region") or None),
            "country": N.normalize_country(loc.get("country")),
        }
    if "links" in d:
        out["links"] = d["links"]
    if "experience" in d:
        exp = []
        for e in d["experience"]:
            exp.append({
                "company": e.get("company"),
                "title": e.get("title"),
                "start": N.normalize_date(e.get("start")),
                "end": N.normalize_date(e.get("end")),
                "summary": e.get("summary"),
            })
        out["experience"] = exp
    return {"source": sr["source"], "method": sr["method"], "data": out}


#identity grouping
def _identity_key(sr):
    """Match key: primary email if present, else lowercased name."""
    d = sr["data"]
    if d.get("emails"):
        return d["emails"][0]
    if d.get("full_name"):
        return d["full_name"].strip().lower()
    return None


def group_by_identity(records):
    groups = {}
    for sr in records:
        key = _identity_key(sr)
        if key is None:
            continue
        groups.setdefault(key, []).append(sr)
    return list(groups.values())


# merge one group into a canonical record
def merge_group(group):
    rec = empty_record()
    prov = []
    confidences = []

    # order sources strongest-first so the winner is just "first non-empty"
    group = sorted(group, key=lambda s: -SOURCE_RELIABILITY.get(s["source"], 0.5))

    def reliability(sr):
        return SOURCE_RELIABILITY.get(sr["source"], 0.5)


    for field in ("full_name", "headline", "years_experience"):
        winner = None
        agree = 0
        for sr in group:
            val = sr["data"].get(field)
            if val in (None, "", []):
                continue
            if winner is None:
                winner = sr
                rec[field] = val
            elif _same(sr["data"].get(field), winner["data"].get(field)):
                agree += 1
        if winner is not None:
            conf = min(0.99, reliability(winner) + 0.1 * agree)
            confidences.append(conf)
            prov.append({"field": field, "source": winner["source"], "method": winner["method"]})

    
    for sub in ("city", "region", "country"):
        for sr in group:
            val = (sr["data"].get("location") or {}).get(sub)
            if val:
                rec["location"][sub] = val
                prov.append({"field": f"location.{sub}", "source": sr["source"], "method": sr["method"]})
                confidences.append(reliability(sr))
                break


    for field in ("emails", "phones"):
        seen, merged = set(), []
        for sr in group:
            for v in sr["data"].get(field, []):
                if v not in seen:
                    seen.add(v)
                    merged.append(v)
                    prov.append({"field": field, "source": sr["source"], "method": sr["method"]})
        rec[field] = merged
        if merged:
            confidences.append(max(reliability(s) for s in group))

    # links: first non-null--highest priority record
    for sr in group:
        links = sr["data"].get("links") or {}
        for k in ("linkedin", "github", "portfolio"):
            if links.get(k) and not rec["links"][k]:
                rec["links"][k] = links[k]
                prov.append({"field": f"links.{k}", "source": sr["source"], "method": sr["method"]})

    # skills: union; per skill, confidence from the sources that mentioned it
    skill_sources = {}
    for sr in group:
        for name in sr["data"].get("skills", []):
            skill_sources.setdefault(name, set()).add(sr["source"])
    skills = []
    for name, srcs in skill_sources.items():
        base = max(SOURCE_RELIABILITY.get(s, 0.5) for s in srcs)
        conf = min(0.99, base + (0.1 if len(srcs) > 1 else 0.0))
        skills.append({"name": name, "confidence": round(conf, 2), "sources": sorted(srcs)})
        confidences.append(conf)
    rec["skills"] = sorted(skills, key=lambda s: -s["confidence"])
    if skills:
        prov.append({"field": "skills", "source": "+".join(sorted({s for v in skill_sources.values() for s in v})), "method": "merge_union"})

    exp_by_company, order = {}, []
    for sr in group:
        for e in sr["data"].get("experience", []):
            company, title = e.get("company"), e.get("title")
            if not company and not title:
                continue
            ckey = (company or "").strip().lower() or (title or "").strip().lower()
            if ckey not in exp_by_company:
                exp_by_company[ckey] = dict(e)
                order.append(ckey)
                prov.append({"field": "experience", "source": sr["source"], "method": sr["method"]})
            else:
                cur = exp_by_company[ckey]
                for k in ("start", "end", "summary", "title"):
                    if not cur.get(k) and e.get(k):
                        cur[k] = e[k]
    rec["experience"] = [exp_by_company[k] for k in order]

    rec["provenance"] = prov
    rec["overall_confidence"] = round(sum(confidences) / len(confidences), 2) if confidences else 0.0

    # deterministic id from the match key
    key = rec["emails"][0] if rec["emails"] else (rec["full_name"] or "unknown")
    rec["candidate_id"] = "cand_" + hashlib.sha1(key.encode("utf-8")).hexdigest()[:10]
    return rec


def _same(a, b):
    if isinstance(a, str) and isinstance(b, str):
        return a.strip().lower() == b.strip().lower()
    return a == b
