import re
from config.config import COLLEGE_PLACEMENT_EMAIL

def extract_placement_offer(text, sender=COLLEGE_PLACEMENT_EMAIL, subject=""):
    result = {}

    text = text or ""
    subject = subject or ""

    # Company - Most tolerant pattern, fallback to subject, remove decorations
    result['company'] = _extract_first([
        r"(?i)name of the company[\s:]*([\w ()./&,-]+)",
        r"(?i)company[\s:]*([\w ()./&,-]+)",
        r"\*\s*([\w ()./&,-]+)\s*\*",  # Handles *Company Name*
        r"^([A-Z][\w ()./&,-]+)[:\-]", # Header at line start
    ], text) or _extract_from_subject(subject)

    # Category - Be flexible
    result['category'] = _extract_first([
        r"(?i)category[\s:]*([A-Z][^\n\r|]*)",
        r"(Dream Offer|Super Dream|Dream Internship|Regular Placement|Internship|Placement)"
    ], text)

    # Eligible branches - tolerant, multiline
    result['branches'] = _extract_first([
        r"(?i)eligible (branches?|disciplines)[\s:]*([\s\S]*?)(?:[\n\r]{2,}|eligibility|criteria|category|$)",
        r"(?i)branches?[\s:]*([\w ,.|/&\-\n\r]+)"
    ], text).replace('\n', ' ').strip().strip('*,:;|-')

    # Eligibility block
    crit_block = _extract_first([
        r"Eligibility Criteria[\s:]*([\s\S]*?)(?:CTC|Stipend|Last date|Website|Contact|\n[A-Z][a-z]+|$)"
    ], text)
    result['10th'] = _extract_first([
        r"(?:10th|X)[^\d]{0,10}(\d{1,3})\s*%?",
        r"%\s*in\s*X[\s\-–:]*([0-9]{1,3})%?"
    ], crit_block)
    result['12th'] = _extract_first([
        r"(?:12th|XII)[^\d]{0,10}(\d{1,3})\s*%?",
        r"%\s*in\s*XII[\s\-–:]*([0-9]{1,3})%?"
    ], crit_block)
    result['cgpa'] = _extract_first([
        r"(\d+\.\d+)\s*CGPA",
        r"CGPA[^\d]{0,8}(\d+\.\d+)",
        r"(\d{1,2}\.\d{1,2})"
    ], crit_block)
    result['no_arrears'] = bool(re.search(r"no\s+(standing\s+)?arrears?", crit_block or "", re.IGNORECASE))

    # CTC (try both "CTC", "package", "LPA", variants)
    result['ctc'] = _extract_first([
        r"(?i)ctc[\s:\-]*([₹]?\d[\d,\. ]*(?:LPA|lpa)?|[₹]?\d[\d,\. ]+)",
        r"(?i)package[\s:\-]*([₹]?\d[\d,\. ]*LPA|[₹]?\d[\d,\. ]+)",
        r"(?i)annual[\s:\-]*([₹]?\d[\d,\. ]*LPA|[₹]?\d[\d,\. ]+)",
    ], text)

    # Stipend - Improve to handle /month, /per, etc
    result['stipend'] = _extract_first([
        r"(?i)stipend[\s:\-]*([₹]?\d[\d,\. ]*(?:/month|/per month|per month)?|[₹]?\d[\d,\. ]+)"
    ], text)

    # Last date - robust to space labels
    result['last_date'] = _extract_first([
        r"(?i)last date[^\w]{0,6}([^\n\r,\.]*)",
        r"(?i)deadline[^\w]{0,6}([^\n\r,\.]*)",
        r"(?i)to apply[^\w]{0,6}([^\n\r,\.]*)"
    ], text)

    # Registration links only for forms/actual applications
    links = re.findall(r'https?://[^\s\]\)\<\>,"\'|\n]+', text)
    reg_links = [l for l in links if any(x in l.lower() for x in ('forms.gle', 'form', 'neopat', 'apply', 'registration', 'career', 'register'))]
    result['registration_links'] = reg_links
    result['application_source'] = _extract_first([
        r"(Google Form|NeoPAT|career page|register|apply|application)",
    ], text)

    # Website (exclude google group/attachments)
    site_links = [l for l in links if (l.lower().startswith("http") and
                all(x not in l.lower() for x in ("group", "form", "registration", "neopat", "apply", "career", "register", "attachment")))]
    result['website'] = site_links[0] if site_links else ""

    # FINAL CLEANUP
    for k, v in result.items():
        if isinstance(v, str) and v:
            result[k] = v.strip().strip('*,:-')
        elif v is None:
            result[k] = ""

    def non_empty_fields(d): return [k for k, v in d.items() if v]
    # Print for debug - REMOVE in production
    print(f"Extracted: {result}")
    # Minimum: company or at least 1 key field
    if result['company'] or result['branches'] or result['category']:
        return result
    else:
        print(f"FAILED: {result}")
        return None

def _extract_first(patterns, text):
    if not text:
        return ""
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
        if m:
            group = next((g for g in m.groups()[::-1] if g and g.strip()), None)
            return group.strip() if group else ""
    return ""

def _extract_from_subject(subject):
    # Returns company name up to "-" or ":" or end
    if subject:
        return re.sub(r'Re[:\-]*\s*', '', subject).split("-")[0].split(":")[0].strip()
    return ""