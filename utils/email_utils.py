import os
import pickle
import base64
from datetime import datetime, timezone, timedelta

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from config.config import COLLEGE_PLACEMENT_EMAIL
import html2text

# Path to Gmail API credentials for your UNIVERSITY account
CREDENTIALS_PATH = 'gmail_credentials.json'
TOKEN_PATH = 'gmail_token.pickle'
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


def get_gmail_service():
    """Authenticate and return Gmail service object."""
    creds = None

    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)
    return service


def _safe_b64_decode(data: str) -> str:
    """Safely decode URL-safe base64 Gmail payloads."""
    if not data:
        return ""
    # Fix padding if needed
    missing = len(data) % 4
    if missing:
        data += "=" * (4 - missing)
    return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")


def get_message_body(service, message_id):
    """Get the full body content of an email message."""
    try:
        message = service.users().messages().get(
            userId='me',
            id=message_id,
            format='full'
        ).execute()

        def extract_body(payload):
            body = ""
            if 'parts' in payload:
                for part in payload['parts']:
                    body += extract_body(part)
            else:
                data = payload['body'].get('data')
                if payload['mimeType'] == 'text/plain' and data:
                    decoded_data = _safe_b64_decode(data)
                    body += decoded_data
                elif payload['mimeType'] == 'text/html' and data:
                    html_content = _safe_b64_decode(data)
                    body += html2text.html2text(html_content)
            return body

        return extract_body(message['payload'])
    except Exception as e:
        print(f"Error getting message body: {e}")
        return ""


def fetch_emails(
    limit=50,
    subject_filter=None,
    sender_filter=COLLEGE_PLACEMENT_EMAIL,
    include_all=False,
    start_date=None,
):
    """
    Fetch emails from Gmail with optional filtering for subject, sender, and start_date.

    - limit: max number of emails to fetch (e.g. 3000 for backfill).
    - subject_filter: filter by subject substring.
    - sender_filter: filter by sender email (default: college placement email).
    - include_all: if True, ignore subject/sender filters.
    - start_date: string "YYYY/MM/DD", used in Gmail query as 'after:YYYY/MM/DD'.
    """
    print("🔐 Authenticating with Gmail...")
    service = get_gmail_service()
    print("✅ Gmail authentication successful!\n")

    # Build query string for Gmail search
    query_parts = []
    if not include_all:
        if sender_filter:
            query_parts.append(f"from:{sender_filter}")
        if subject_filter:
            query_parts.append(f"subject:{subject_filter}")
    if start_date:
        # Gmail query format: after:YYYY/MM/DD
        query_parts.append(f"after:{start_date}")

    query = " ".join(query_parts)
    print(f"Using Gmail search query: '{query}'")  # Debug print

    try:
        emails = []
        page_token = None
        fetched = 0

        while True:
            # Gmail allows maxResults up to 500
            batch_size = 500
            if limit:
                remaining = limit - fetched
                if remaining <= 0:
                    break
                batch_size = min(batch_size, remaining)

            results = service.users().messages().list(
                userId='me',
                q=query,
                maxResults=batch_size,
                pageToken=page_token
            ).execute()

            messages = results.get('messages', [])
            if not messages:
                break

            print(f"Processing batch of {len(messages)} messages from Gmail...")

            for i, msg in enumerate(messages):
                try:
                    # Fetch metadata: subject, sender, date + internalDate
                    meta = service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='metadata',
                        metadataHeaders=['From', 'Subject', 'Date']
                    ).execute()

                    headers = meta['payload']['headers']
                    subject, sender, date_header = "", "", ""
                    for header in headers:
                        name = header['name']
                        if name == 'Subject':
                            subject = header['value']
                        elif name == 'From':
                            sender = header['value']
                            if '<' in sender and '>' in sender:
                                sender = sender.split('<')[1].split('>')[0]
                        elif name == 'Date':
                            date_header = header['value']

                    # internalDate is epoch ms in UTC
                    internal_ts_str = meta.get('internalDate')
                    internal_ts = None
                    received_date_str = ""
                    received_time_str = ""
                    if internal_ts_str is not None:
                        try:
                            internal_ts = int(internal_ts_str)
                            dt_utc = datetime.fromtimestamp(internal_ts / 1000.0, tz=timezone.utc)
                            india_tz = timezone(timedelta(hours=5, minutes=30))
                            dt_local = dt_utc.astimezone(india_tz)
                            received_date_str = dt_local.strftime("%d-%m-%Y")
                            received_time_str = dt_local.strftime("%H:%M")
                        except Exception as e:
                            print("Error parsing internalDate:", e)

                    # Get full email body (text or html as fallback)
                    body = get_message_body(service, msg['id'])

                    emails.append({
                        "id": msg['id'],                  # Gmail message ID
                        "subject": subject,
                        "from": sender,
                        "body": body,
                        "received_date": received_date_str,  # e.g. "10-12-2025"
                        "received_time": received_time_str,  # e.g. "14:35"
                        "date_header": date_header,          # raw header for debugging
                        "internal_ts": internal_ts,          # int: epoch ms
                    })

                    if (i + 1) % 10 == 0:
                        print(f"Processed {i + 1}/{len(messages)} emails in this batch...")

                except Exception as e:
                    print(f"Error processing message: {e}")
                    continue

            fetched += len(messages)
            print(f"✅ Accumulated {fetched} emails so far.")

            page_token = results.get('nextPageToken')
            if not page_token:
                break

        print(f"✅ Successfully fetched {len(emails)} emails from Gmail.")
        return emails

    except Exception as e:
        print(f"❌ Failed to fetch emails: {e}")
        return []