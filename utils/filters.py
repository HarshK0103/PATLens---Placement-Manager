def is_first_round_placement_mail(email):
    """
    Returns True if the email is a first-round/initial campus placement offer announcement, else False.
    Parameter email is a dict with at least 'subject' and 'body'
    """

    OFFER_KEYWORDS = [
        "placement", "internship", "drive", "dream offer", "super dream", "opportunity", "registration",
        "category", "offer", "eligible branch", "campus program"
    ]
    EXCLUDE_KEYWORDS = [
    "shortlist", "short-listed", "shortlisted",
    "selected students", "selected", "selection list",
    "further round", "next round",
    "interview", "technical interview", "group discussion",
    "test scheduled", "online test",
    "pre-placement talk", "pre placement talk",
    "congratulations",
    "selection process",
    "technical round", "assessment", "round"
    ]

    subj = (email.get("subject") or "").lower()
    body = (email.get("body") or "").lower()

    # Exclude if any exclusion keyword matches subject or body
    for bad_kw in EXCLUDE_KEYWORDS:
        if bad_kw in subj or bad_kw in body:
            return False

    # Only accept if at least one offer keyword appears in subject or body
    for ok_kw in OFFER_KEYWORDS:
        if ok_kw in subj or ok_kw in body:
            return True

    return False