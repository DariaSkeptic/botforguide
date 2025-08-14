import os
import re

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0"))

CODEWORDS = {
    "kapusta": "kapusta",
    "avatar": "avatar",
    "amourchik": "amourchik",
}

DATE_RE = re.compile(r"^\s*\d{2}\.\d{2}\.\d{4}\s*$")
DATE_REGEX_STR = r"^\s*\d{2}\.\d{2}\.\d{4}\s*$"

GDRIVE_FOLDERS = {
    "kapusta": os.getenv("GDRIVE_FOLDER_KAPUSTA"),
    "avatar": os.getenv("GDRIVE_FOLDER_AVATAR"),
    "amourchik": os.getenv("GDRIVE_FOLDER_AMOURCHIK"),
}

GOOGLE_CREDENTIALS_JSON_B64 = os.getenv("GOOGLE_CREDENTIALS_JSON_B64")
