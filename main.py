import os
import json

from utils.email_utils import fetch_emails
from utils.ai_extractor import ai_extract_offer
from utils.filters import is_first_round_placement_mail
from utils.sheets_utils import build_campus_placement_row, append_to_sheet
from config.config import (
    COLLEGE_PLACEMENT_EMAIL,
    SHEET_NAME_PLACEMENTS,
    SHEET_ID,
    # Make sure these exist in config.py
    BACKFILL_START_DATE,   # e.g. "2025/05/17"
    BACKFILL_LIMIT,        # e.g. 3000
)

STATE_FILE = "run_state.json"


def load_state():
    """
    Load processed Gmail message IDs and last seen timestamp (internal_ts) from disk.
    Used to avoid re-processing old mails and to support incremental runs.
    """
    if not os.path.exists(STATE_FILE):
        return {"processed_ids": set(), "last_ts": 0}

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        processed_ids = set(data.get("processed_ids", []))
        last_ts = data.get("last_ts", 0)
        return {"processed_ids": processed_ids, "last_ts": last_ts}
    except Exception as e:
        print("Error loading state, starting fresh:", e)
        return {"processed_ids": set(), "last_ts": 0}


def save_state(processed_ids, last_ts):
    """
    Persist processed_ids and last_ts to disk so future runs only handle new mails.
    """
    try:
        data = {
            "processed_ids": list(processed_ids),
            "last_ts": int(last_ts) if last_ts else 0,
        }
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print("Error saving state:", e)


def main():
    state = load_state()
    processed_ids = state["processed_ids"]
    last_ts = state["last_ts"]  # last Gmail internal_ts (UTC ms) we saw

    # Decide mode: first run (backfill) vs incremental
    if last_ts == 0 and not processed_ids:
        # 🔹 First ever run: backfill from a given date and up to BACKFILL_LIMIT mails
        print("🚀 First run: Backfilling from", BACKFILL_START_DATE)
        emails = fetch_emails(
            limit=BACKFILL_LIMIT,
            sender_filter=COLLEGE_PLACEMENT_EMAIL,
            start_date=BACKFILL_START_DATE,
        )
    else:
        # 🔹 Subsequent runs: only care about new mails since last run
        print("🔁 Incremental run: processing only new emails.")
        # Fetch a recent window (e.g. last 500 messages); we will filter by internal_ts + processed_ids
        emails = fetch_emails(
            limit=500,
            sender_filter=COLLEGE_PLACEMENT_EMAIL,
            # no start_date here; internal_ts + processed_ids handle recency
        )

    print(f"Fetched {len(emails)} emails.")
    for e in emails[:10]:
        print(f"From: {e.get('from')} | Subject: {e.get('subject')}")

    placement_rows = []
    max_ts_seen = last_ts

    # Apply filtering and extraction
    for email in emails:
        msg_id = email.get("id")
        internal_ts = email.get("internal_ts") or 0  # Gmail internalDate in ms

        # Track maximum timestamp we've seen this run
        if internal_ts and internal_ts > max_ts_seen:
            max_ts_seen = internal_ts

        # Skip if we've already processed this message in a previous run
        if msg_id and msg_id in processed_ids:
            continue

        # For incremental runs, skip mails older than or equal to last_ts
        if last_ts and internal_ts and internal_ts <= last_ts:
            continue

        # Filter out shortlists, further rounds, result mails, etc.
        if not is_first_round_placement_mail(email):
            continue

        # LLM extraction
        extracted = ai_extract_offer(email)
        print(f"Subject: {email['subject']}")
        print("Extracted:", extracted)  # Debug

        if extracted:
            # Attach mail received date & time (filled in email_utils)
            extracted["mail_date"] = email.get("received_date", "")
            extracted["mail_time"] = email.get("received_time", "")

            row = build_campus_placement_row(extracted)
            placement_rows.append(row)

            # Mark this message as processed
            if msg_id:
                processed_ids.add(msg_id)

    if not placement_rows:
        print("⚠️ No valid company placement offer mails found.")
    else:
        for rec in placement_rows:
            print("=" * 60)
            for k, v in zip(
                [
                    "Sr.No",
                    "Company Name",
                    "Category",
                    "Eligible Branches",
                    "10th%",
                    "12th%",
                    "CGPA",
                    "CTC",
                    "Stipend",
                    "Last Date for Registration",
                    "Application Source",
                    "Application Status",
                    "Registration Links",
                    "Mail Date",
                    "Mail Time",
                ],
                rec,
            ):
                print(f"{k}: {v}")
            print("=" * 60)

        # Push all found placement rows to Google Sheet
        append_to_sheet(
            placement_rows,
            sheet_name=SHEET_NAME_PLACEMENTS,
            sheet_id=SHEET_ID,
        )

    # Save updated state for next 6-hour run
    save_state(processed_ids, max_ts_seen)


if __name__ == "__main__":
    main()