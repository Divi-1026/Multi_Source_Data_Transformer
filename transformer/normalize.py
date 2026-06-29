
import re
#for Phone Number
def normalize_phone(raw):
    """Best-effort E.164 
    Rules ---->
     Case1 - if the value already carries a '+', trust its country code
     Case2  - 10 digits             -> assume India (+91)
      Case3 - 11 digits leading 0   -> India STD prefix, drop the 0 (+91)
      Case 4 - 12 digits leading 91  -> already has the India code
    """
    if not raw:
        return None
    raw = str(raw).strip()
    has_plus = raw.startswith("+")
    digits = re.sub(r"\D", "", raw)
    if not digits:
        return None
    if has_plus:
        return "+" + digits
    if len(digits) == 10:
        return "+91" + digits
    if len(digits) == 11 and digits.startswith("0"):
        return "+91" + digits[1:]
    if len(digits) == 12 and digits.startswith("91"):
        return "+" + digits
    if len(digits) == 11 and digits.startswith("1"):  # US/Canada
        return "+" + digits
    return "+" + digits  # last resort, still deterministic


# Dates

_MONTHS = {
    "jan": "01", "feb": "02", "mar": "03", "apr": "04", "may": "05", "jun": "06",
    "jul": "07", "aug": "08", "sep": "09", "oct": "10", "nov": "11", "dec": "12",
}


def normalize_date(raw):
   #Return in YYYY-MM format
    if not raw:
        return None
    s = str(raw).strip().lower()
    # 2024-03 or 2024/03
    m = re.match(r"^(\d{4})[-/](\d{1,2})$", s)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}"
    # 03/2024 or 03-2024
    m = re.match(r"^(\d{1,2})[-/](\d{4})$", s)
    if m:
        return f"{m.group(2)}-{int(m.group(1)):02d}"
    # mar 2024 / march 2024
    m = re.match(r"^([a-z]{3,})\.?\s+(\d{4})$", s)
    if m and m.group(1)[:3] in _MONTHS:
        return f"{m.group(2)}-{_MONTHS[m.group(1)[:3]]}"
    # bare year
    m = re.match(r"^(\d{4})$", s)
    if m:
        return m.group(1)
    return None


# --- Country -----------------------------------------------------------------

_COUNTRY = {
    "india": "IN", "in": "IN", "bharat": "IN",
    "united states": "US", "usa": "US", "us": "US", "america": "US",
    "united kingdom": "GB", "uk": "GB", "england": "GB",
    "canada": "CA", "australia": "AU", "germany": "DE", "france": "FR",
}


def normalize_country(raw):
#Return in ISO Code
    if not raw:
        return None
    return _COUNTRY.get(str(raw).strip().lower())


# --- Skills ------------------------------------------------------------------

_SKILL_ALIASES = {
    "js": "JavaScript", "javascript": "JavaScript",
    "react": "React", "reactjs": "React", "react.js": "React",
    "py": "Python", "python": "Python",
    "ml": "Machine Learning", "machine learning": "Machine Learning",
    "dl": "Deep Learning", "deep learning": "Deep Learning",
    "sql": "SQL", "databases": "Databases", "database": "Databases",
    "java": "Java", "spring": "Spring", "spring boot": "Spring Boot",
    "pandas": "Pandas", "system design": "System Design",
    "node": "Node.js", "nodejs": "Node.js",
}


def normalize_skill(raw):
#Map skill
    if not raw:
        return None
    key = str(raw).strip().lower()
    if key in _SKILL_ALIASES:
        return _SKILL_ALIASES[key]
    return str(raw).strip().title()
#Normalize Email
def normalize_email(raw):
    """Lowercase + trim; return None if it does not look like an email."""
    if not raw:
        return None
    e = str(raw).strip().lower()
    return e if re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", e) else None
