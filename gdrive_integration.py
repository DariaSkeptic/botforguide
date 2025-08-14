import os
import io
import json
import base64
import logging
from typing import Optional, List

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def _drive():
    b64 = os.getenv("GOOGLE_CREDENTIALS_JSON_B64")
    if not b64:
        raise RuntimeError("GOOGLE_CREDENTIALS_JSON_B64 не задан")
    try:
        info = json.loads(base64.b64decode(b64).decode("utf-8"))
    except Exception as e:
        raise RuntimeError(f"Невалидный GOOGLE_CREDENTIALS_JSON_B64: {e}")
    creds = service_account.Credentials.from_service_account_info(
        info, scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    return build("drive", "v3", credentials=creds)

def _find_file_id(service, folder_id: str, filename: str) -> Optional[str]:
    q = f"'{folder_id}' in parents and name = '{filename}' and trashed = false"
    res = service.files().list(q=q, fields="files(id,name)", pageSize=1).execute()
    files = res.get("files", [])
    return files[0]["id"] if files else None

def get_guide(program: str, arcana: int) -> Optional[str]:
    folder_id = os.getenv(f"GDRIVE_FOLDER_{program.upper()}")
    if not folder_id:
        logger.error(f"Не найдена переменная окружения GDRIVE_FOLDER_{program.upper()}")
        return None

    service = _drive()
    candidates = [f"{arcana}.pdf", f"{arcana:02d}.pdf"]

    file_id = None
    picked_name = None
    for name in candidates:
        file_id = _find_file_id(service, folder_id, name)
        if file_id:
            picked_name = name
            break

    if not file_id:
        logger.warning(f"Файл {candidates} не найден в папке {folder_id}")
        return None

    buf = io.BytesIO()
    request = service.files().get_media(fileId=file_id)
    downloader = MediaIoBaseDownload(buf, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()

    out_path = f"/tmp/{program}_{picked_name}"
    with open(out_path, "wb") as f:
        f.write(buf.getvalue())
    return out_path

# Доп. функции для /admin — если используешь
def list_missing_guides() -> List[str]:
    service = _drive()
    result = []
    for program in ("kapusta", "avatar", "amourchik"):
        folder_id = os.getenv(f"GDRIVE_FOLDER_{program.upper()}")
        if not folder_id:
            continue
        existing = set()
        res = service.files().list(q=f"'{folder_id}' in parents and trashed = false",
                                   fields="files(name)", pageSize=200).execute()
        for f in res.get("files", []):
            existing.add(f.get("name"))
        for n in range(1, 23):
            if f"{n}.pdf" not in existing and f"{n:02d}.pdf" not in existing:
                result.append(f"{program}/{n}.pdf")
    return result

def list_existing_guides() -> List[str]:
    service = _drive()
    items = []
    for program in ("kapusta", "avatar", "amourchik"):
        folder_id = os.getenv(f"GDRIVE_FOLDER_{program.upper()}")
        if not folder_id:
            continue
        res = service.files().list(q=f"'{folder_id}' in parents and trashed = false",
                                   fields="files(name)", pageSize=200).execute()
        for f in res.get("files", []):
            items.append(f"{program}/{f.get('name')}")
    return items
