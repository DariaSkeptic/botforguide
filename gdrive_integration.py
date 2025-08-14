import json
import base64
from io import BytesIO
from typing import Optional, List

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from telegram import InputFile

from config import PROGRAM_FOLDERS, GOOGLE_CREDENTIALS_JSON_B64

def _gclient():
    info = json.loads(base64.b64decode(GOOGLE_CREDENTIALS_JSON_B64))
    creds = Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/drive.readonly"])
    return build("drive", "v3", credentials=creds, cache_discovery=False)

def find_file_id(folder_id: str, filename: str) -> Optional[str]:
    svc = _gclient()
    q = f"'{folder_id}' in parents and name = '{filename}' and trashed = false"
    res = svc.files().list(q=q, fields="files(id,name)", pageSize=1).execute()
    files = res.get("files", [])
    return files[0]["id"] if files else None

def download_bytes(file_id: str) -> bytes:
    svc = _gclient()
    req = svc.files().get_media(fileId=file_id)
    buf = BytesIO()
    dl = MediaIoBaseDownload(buf, req)
    done = False
    while not done:
        _, done = dl.next_chunk()
    buf.seek(0)
    return buf.read()

def list_filenames(folder_id: str) -> List[str]:
    svc = _gclient()
    files: List[str] = []
    page_token = None
    while True:
        res = svc.files().list(
            q=f"'{folder_id}' in parents and trashed = false",
            fields="nextPageToken, files(name)",
            pageSize=1000,
            pageToken=page_token
        ).execute()
        files.extend([f["name"] for f in res.get("files", []) if "name" in f])
        page_token = res.get("nextPageToken")
        if not page_token:
            break
    return files

async def get_pdf(program: str, arcana: int) -> InputFile:
    filename = f"{arcana:02}.pdf"
    folder_id = PROGRAM_FOLDERS[program]
    file_id = await utils._to_thread(find_file_id, folder_id, filename)
    if not file_id:
        raise FileNotFoundError(f"Нет {filename} в папке {program}")
    data = await utils._to_thread(download_bytes, file_id)
    return InputFile(BytesIO(data), filename=filename)