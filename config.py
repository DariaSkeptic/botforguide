import os
import re
from typing import Dict

TOKEN = os.environ.get("BOT_TOKEN", "").strip()
GDRIVE_FOLDER_KAPUSTA   = os.environ.get("GDRIVE_FOLDER_KAPUSTA", "").strip()
GDRIVE_FOLDER_AVATAR    = os.environ.get("GDRIVE_FOLDER_AVATAR", "").strip()
GDRIVE_FOLDER_AMOURCHIK = os.environ.get("GDRIVE_FOLDER_AMOURCHIK", "").strip()
GOOGLE_CREDENTIALS_JSON_B64 = os.environ.get("GOOGLE_CREDENTIALS_JSON_B64", "").strip()

PROGRAM_FOLDERS: Dict[str, str] = {
    "kapusta":   GDRIVE_FOLDER_KAPUSTA,
    "avatar":    GDRIVE_FOLDER_AVATAR,
    "amourchik": GDRIVE_FOLDER_AMOURCHIK,
}

ADMIN_CHAT_ID = int(os.environ.get("ADMIN_CHAT_ID", "0") or "0")
ADMIN_USER_ID = int(os.environ.get("ADMIN_USER_ID", "0") or "0")

CODEWORDS = {
    "капуста": "kapusta", "kapusta": "kapusta",
    "аватар": "avatar",   "avatar":  "avatar",
    "амурчик": "amourchik", "amourchik": "amourchik", "amour": "amourchik",
}

DATE_REGEX_STR = r"^\s*\d{2}\.\d{2}\.\d{4}\s*$"
DATE_RE = re.compile(DATE_REGEX_STR)