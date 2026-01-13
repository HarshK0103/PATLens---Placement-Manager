# config/config.py

###############################
# Google Sheets Configuration #
###############################

# Put your SHEET_ID string (from the Sheets URL, between /d/ and /edit)
SHEET_ID = "1IGyhKhWUuVdHWl03VarGT7XIMsNkPSZvv3m7rlMNJgg"

# Name of the Campus Placement tab/sheet
SHEET_NAME_PLACEMENTS = "Campus Placements"

# Name of the God Bless You tab/sheet
SHEET_NAME_GBY = "God Bless You"

# Email address of the college placement cell sender
COLLEGE_PLACEMENT_EMAIL = "vitlions2026@vitbhopal.ac.in"

###############################
# Miscellaneous Configs       #
###############################

# If you want, define file/folder paths or additional global settings here
# Example: LOG_PATH = "./logs/"

# Backfill / incremental config
# Gmail date format: YYYY/MM/DD
BACKFILL_START_DATE = "2025/05/17"   # 17th May 2025
BACKFILL_LIMIT = 3000                # Max mails to fetch in first big run
# Set to None to disable backfill