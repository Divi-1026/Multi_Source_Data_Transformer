
import re

from . import normalize as N


def resolve_path(record, path):
  
    cur = record
    for seg in path.split("."):
        m = re.match(r"^(\w+)(\[(\d*)\])?$", seg)
        if not m:
            return None
        key, has_idx, idx = m.group(1), m.group(2), m.group(3)
        if isinstance(cur, list):           # mapping a key over a list
            cur = [(e.get(key) if isinstance(e, dict) else None) for e in cur]
        elif isinstance(cur, dict):
            cur = cur.get(key)
        else:
            return None
        if has_idx is not None:
            if idx == "":                    # [] -> stay a list (map mode)
                cur = cur if isinstance(cur, list) else ([] if cur is None else [cur])
            else:                            # [n] -> pick one element
                i = int(idx)
                cur = cur[i] if isinstance(cur, list) and 0 <= i < len(cur) else None
    return cur


def _apply_normalize(value, kind):
    if value is None:
        return None
    if kind == "E164":
        return N.normalize_phone(value)
    if kind == "canonical":
        if isinstance(value, list):
            return [N.normalize_skill(v) for v in value]
        return N.normalize_skill(value)
    return value


def _is_missing(v):
    return v is None or v == [] or v == "" or v == {}


def project(record, config):
    """Project one canonical record into the config's output shape."""
    out = {}
    on_missing = config.get("on_missing", "null")
    for f in config.get("fields", []):
        name = f["path"]
        src = f.get("from", name)
        val = resolve_path(record, src)
        if f.get("normalize"):
            val = _apply_normalize(val, f["normalize"])
        if _is_missing(val):
            if on_missing == "error" and f.get("required"):
                raise ValueError(f"required field missing: {name}")
            if on_missing == "omit":
                continue
            val = None                       # default: null
        out[name] = val
    if config.get("include_confidence"):
        out["overall_confidence"] = record.get("overall_confidence")
    if config.get("include_provenance"):
        out["provenance"] = record.get("provenance")
    return out
