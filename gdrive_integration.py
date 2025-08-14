import base64
import json
import io
from typing import Any

from google.oauth2 import service_account
from googleapiclient.discovery import Resource, build
from googleapiclient.http import MediaIoBaseDownload

from config import GDRIVE_FOLDERS, GOOGLE_CREDENTIALS_JSON_B64
from utils import _to_thread

async def get_drive_service() -> Resource | None:
    try:
        credentials_b64 = GOOGLE_CREDENTIALS_JSON_B64
        if not credentials_b64:
            return None
        credentials_json = base64.b64decode(credentials_b64).decode("utf-8")
        credentials_info = json.loads(credentials_json)
        credentials = service_account.Credentials.from_service_account_info(
            credentials_info,
            scopes=["https://www.googleapis.com/auth/drive.readonly"],
        )
        return await _to_thread(build, "drive", "v3", credentials=credentials)
    except Exception:
        return None

async def list_files_in_folder(folder_id: str) -> list[dict[str, Any]]:
    service = await get_drive_service()
    if not service:
        return []
    try:
        results = await _to_thread(
            lambda: service.files()
            .list(
                q=f"'{folder_id}' in parents and mimeType='application/pdf'",
                fields="files(id, name)",
            )
            .execute()
        )
        return results.get("files", [])
    except Exception:
        return []

async def find_file_id(folder_id: str, filename: str) -> str | None:
    files = await list_files_in_folder(folder_id)
    for file in files:
        if file.get("name") == filename:
            return file.get("id")
    return None

async def get_pdf(program: str, arcana: int) -> io.BytesIO:
    folder_id = GDRIVE_FOLDERS.get(program)
    if not folder_id:
        raise FileNotFoundError(f"No folder configured for program: {program}")
    filename = f"{arcana:02d}.pdf"
    file_id = await _to_thread(find_file_id, folder_id, filename)
    if not file_id:
        raise FileNotFoundError(f"File not found: {filename} in folder {folder_id}")
    service = await get_drive_service()
    if not service:
        raise FileNotFoundError("Drive service unavailable")
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = await _to_thread(downloader.next_chunk)
    fh.seek(0)
    return fh