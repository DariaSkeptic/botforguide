import base64
import json
import io
import logging
from typing import Any

from google.oauth2 import service_account
from googleapiclient.discovery import Resource, build
from googleapiclient.http import MediaIoBaseDownload

from config import GDRIVE_FOLDERS, GOOGLE_CREDENTIALS_JSON_B64
from utils import _to_thread

logger = logging.getLogger(__name__)

async def get_drive_service() -> Resource | None:
    logger.info("Инициализация Google Drive сервиса")
    try:
        credentials_b64 = GOOGLE_CREDENTIALS_JSON_B64
        if not credentials_b64:
            logger.error("GOOGLE_CREDENTIALS_JSON_B64 не задан")
            return None
        credentials_json = base64.b64decode(credentials_b64).decode("utf-8")
        credentials_info = json.loads(credentials_json)
        credentials = service_account.Credentials.from_service_account_info(
            credentials_info,
            scopes=["https://www.googleapis.com/auth/drive.readonly"],
        )
        service = await _to_thread(build, "drive", "v3", credentials=credentials)
        logger.info("Google Drive сервис успешно инициализирован")
        return service
    except Exception as e:
        logger.error(f"Ошибка инициализации Google Drive: {str(e)}")
        return None

async def list_files_in_folder(folder_id: str) -> list[dict[str, Any]]:
    logger.info(f"Получение списка файлов в папке {folder_id}")
    service = await get_drive_service()
    if not service:
        logger.error("Google Drive сервис недоступен")
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
        files = results.get("files", [])
        logger.info(f"Найдено файлов: {len(files)}")
        return files
    except Exception as e:
        logger.error(f"Ошибка получения списка файлов: {str(e)}")
        return []

async def find_file_id(folder_id: str, filename: str) -> str | None:
    logger.info(f"Поиск файла {filename} в папке {folder_id}")
    files = await list_files_in_folder(folder_id)
    for file in files:
        if file.get("name") == filename:
            logger.info(f"Файл найден: {filename}, ID: {file.get('id')}")
            return file.get("id")
    logger.warning(f"Файл не найден: {filename}")
    return None

async def get_pdf(program: str, arcana: int) -> io.BytesIO:
    logger.info(f"Получение PDF для программы {program}, аркан {arcana}")
    folder_id = GDRIVE_FOLDERS.get(program)
    if not folder_id:
        logger.error(f"Папка не настроена для программы: {program}")
        raise FileNotFoundError(f"No folder configured for program: {program}")
    filename = f"{arcana:02d}.pdf"
    file_id = await find_file_id(folder_id, filename)
    if not file_id:
        logger.error(f"Файл не найден: {filename} в папке {folder_id}")
        raise FileNotFoundError(f"File not found: {filename} in folder {folder_id}")
    service = await get_drive_service()
    if not service:
        logger.error("Google Drive сервис недоступен")
        raise FileNotFoundError("Drive service unavailable")
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    logger.info(f"Загрузка файла {filename}")
    while not done:
        status, done = await _to_thread(downloader.next_chunk)
    fh.seek(0)
    logger.info(f"PDF успешно загружен для {program}, аркан {arcana}")
    return fh