
import sys

from . import parsers
from .merge import normalize_record, group_by_identity, merge_group
from .project import project
from .validate import validate_canonical, validate_projection

# source name -> parser function
_PARSERS = {
    "csv": parsers.parse_csv,
    "ats": parsers.parse_ats,
    "notes": parsers.parse_notes,
}


def _warn(msg):
    print(f"[warn] {msg}", file=sys.stderr)

def parse_all(sources):
    """sources: {"csv": path, "ats": path, "notes": path}"""
    raw = []
    for kind, path in sources.items():
        parser = _PARSERS.get(kind)
        if not parser:
            _warn(f"unknown source type '{kind}', skipping")
            continue
        try:
            got = parser(path)
            raw.extend(got)
        except Exception as exc:                       # robust: never crash
            _warn(f"could not parse {kind} source '{path}': {exc}")
    return raw


def run(sources, config=None):
    """Return a dict: {"profiles": [...], "warnings": [...]}.

    Without config -> canonical profiles. With config -> projected profiles.
    """
    warnings = []
    raw = parse_all(sources)
    normalized = [normalize_record(sr) for sr in raw]
    groups = group_by_identity(normalized)

    canonical = []
    for g in groups:
        rec = merge_group(g)
        problems = validate_canonical(rec)
        if problems:
            warnings.append({"candidate_id": rec.get("candidate_id"), "problems": problems})
        canonical.append(rec)

    if config is None:
        return {"profiles": canonical, "warnings": warnings}

    projected = []
    for rec in canonical:
        out = project(rec, config)
        problems = validate_projection(out, config)
        if problems:
            warnings.append({"candidate_id": rec.get("candidate_id"), "problems": problems})
        projected.append(out)
    return {"profiles": projected, "warnings": warnings}
