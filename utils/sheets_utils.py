import os
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from config.config import SHEET_ID, SHEET_NAME_PLACEMENTS, SHEET_NAME_GBY

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

SHEETS_CREDENTIALS_PATH = 'sheets_credentials.json'
SHEETS_TOKEN_PATH = 'sheets_token.pickle'


def get_sheets_service():
    creds = None
    if os.path.exists(SHEETS_TOKEN_PATH):
        with open(SHEETS_TOKEN_PATH, 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                SHEETS_CREDENTIALS_PATH, SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open(SHEETS_TOKEN_PATH, 'wb') as token:
            pickle.dump(creds, token)
    service = build('sheets', 'v4', credentials=creds)
    return service


def build_campus_placement_row(parsed, sr_no: str = "", status: str = ""):
    """
    Column order:
    0:  Sr.No
    1:  Company Name
    2:  Category
    3:  Eligible Branches
    4:  10th%
    5:  12th%
    6:  CGPA
    7:  CTC
    8:  Stipend
    9:  Last Date for Registration
    10: Application Source
    11: Application Status
    12: Registration Links
    13: Mail Date
    14: Mail Time
    """

    # Handle both "10th"/"12th" and "10th%"/"12th%"
    tenth = parsed.get("10th") or parsed.get("10th%", "") or ""
    twelfth = parsed.get("12th") or parsed.get("12th%", "") or ""

    # Make sure tenth/twelfth are strings (sometimes LLM may return list)
    if isinstance(tenth, (list, dict)):
        tenth = str(tenth)
    if isinstance(twelfth, (list, dict)):
        twelfth = str(twelfth)

    # Branches may be list or string
    branches = parsed.get("branches", "")
    if isinstance(branches, list):
        branches = ", ".join(str(b) for b in branches)

    # Category may be list or string
    category = parsed.get("category", "")
    if isinstance(category, list):
        category = ", ".join(str(c) for c in category)

    # CGPA: may be string, list, or dict (we only want a flat string)
    cgpa_raw = parsed.get("cgpa", "")
    if isinstance(cgpa_raw, dict):
        # take first value
        cgpa = next(iter(cgpa_raw.values())) if cgpa_raw else ""
    elif isinstance(cgpa_raw, list):
        # join all into one string
        cgpa = ", ".join(str(x) for x in cgpa_raw)
    elif cgpa_raw is None:
        cgpa = ""
    else:
        cgpa = str(cgpa_raw)

    # Stipend may be string or dict (e.g., {"BTech": "Rs 30,000", "MTech/MSc": "Rs 40,000"})
    stipend_raw = parsed.get("stipend", "")
    stipend = ""

    if isinstance(stipend_raw, dict):
        # Prefer BTech stipend if present (case-insensitive)
        chosen = None
        for k, v in stipend_raw.items():
            if "btech" in k.lower():
                chosen = v
                break
        # If no explicit BTech key, just take the first value
        if chosen is None and stipend_raw:
            chosen = next(iter(stipend_raw.values()))
        stipend = str(chosen) if chosen is not None else ""
    elif isinstance(stipend_raw, list):
        stipend = ", ".join(str(x) for x in stipend_raw)
    elif stipend_raw is None:
        stipend = ""
    else:
        stipend = str(stipend_raw)

    # Clean registration links: list → string, strip < >
    raw_links = parsed.get("registration_links", [])
    links_clean = []
    for l in raw_links:
        s = str(l).strip()
        # remove angle brackets if present, e.g. "<https://...>"
        if s.startswith("<") and s.endswith(">"):
            s = s[1:-1].strip()
        links_clean.append(s)

    # Infer application source if missing
    app_source = parsed.get("application_source", "")
    if not app_source:
        joined = " ".join(links_clean).lower()
        if "forms.gle" in joined:
            app_source = "Google Form"
        elif "neopat" in joined:
            app_source = "NEOPAT portal"
        elif links_clean:
            app_source = "Company Portal"

    # Mail date & time (filled in main.py from email_utils)
    mail_date = parsed.get("mail_date", "")
    mail_time = parsed.get("mail_time", "")

    return [
        sr_no,                          # 0 Sr.No
        parsed.get("company", ""),      # 1 Company Name
        category,                       # 2 Category (cleaned)
        branches,                       # 3 Eligible Branches
        str(tenth),                     # 4 10th%
        str(twelfth),                   # 5 12th%
        cgpa,                           # 6 CGPA (always string now)
        str(parsed.get("ctc", "")),     # 7 CTC
        stipend,                        # 8 Stipend
        str(parsed.get("last_date", "")),  # 9 Last Date for Registration
        app_source,                     # 10 Application Source
        status,                         # 11 Application Status
        ", ".join(links_clean),         # 12 Registration Links
        mail_date,                      # 13 Mail Date
        mail_time,                      # 14 Mail Time
    ]


def append_to_sheet(rows, sheet_name=SHEET_NAME_PLACEMENTS, sheet_id=SHEET_ID):
    """
    Appends a list of lists (rows) to the selected Google Sheet tab.
    """
    service = get_sheets_service()
    sheet = service.spreadsheets()
    if not rows:
        print("No data to write.")
        return
    request = sheet.values().append(
        spreadsheetId=sheet_id,
        range=f"{sheet_name}!A1",
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body={"values": rows},
    )
    response = request.execute()
    print("✅ Data written to Google Sheet:", response)