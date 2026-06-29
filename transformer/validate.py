
from .schema import CANONICAL_TYPES


def validate_canonical(record):
    problems = []
    for field, types in CANONICAL_TYPES.items():
        if field not in record:
            problems.append(f"missing field: {field}")
            continue
        if not isinstance(record[field], types):
            problems.append(f"{field}: wrong type {type(record[field]).__name__}")
    # confidence in range
    oc = record.get("overall_confidence")
    if isinstance(oc, (int, float)) and not (0.0 <= oc <= 1.0):
        problems.append(f"overall_confidence out of range: {oc}")
    # skills inner shape
    for s in record.get("skills", []):
        if not isinstance(s, dict) or "name" not in s:
            problems.append("skill entry missing 'name'")
            break
    return problems


_PY_TYPES = {
    "string": str, "number": (int, float), "boolean": bool,
    "string[]": list, "number[]": list,
}


def validate_projection(out, config):
    problems = []
    for f in config.get("fields", []):
        name = f["path"]
        if name not in out:
            if f.get("required"):
                problems.append(f"required field missing: {name}")
            continue
        val = out[name]
        if val is None:
            if f.get("required"):
                problems.append(f"required field is null: {name}")
            continue
        expected = _PY_TYPES.get(f.get("type", "string"))
        if expected and not isinstance(val, expected):
            problems.append(f"{name}: expected {f.get('type')}, got {type(val).__name__}")
    return problems
