from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
import base64
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Инициализация клиента Google Drive
credentials_json = base64.b64decode(os.getenv("GOOGLE_CREDENTIALS_JSON_B64")).decode('utf-8')
credentials = service_account.Credentials.from_service_account_info(eval(credentials_json))
drive_service = build('drive', 'v3', credentials=credentials)

def get_guide(program, arcana):
    folder_id = os.getenv(f"GDRIVE_FOLDER_{program.upper()}")
    if not folder_id:
        logger.error(f"Не найдена переменная окружения GDRIVE_FOLDER_{program.upper()}")
        return None
    file_name = f"{arcana:02d}.pdf"
    try:
        response = drive_service.files().list(q=f"'{folder_id}' in parents and name='{file_name}'", fields="files(id, name)").execute()
        files = response.get('files', [])
        if files:
            request = drive_service.files().get_media(fileId=files[0]['id'])
            with open(file_name, 'wb') as f:
                f.write(request.execute())
            return file_name
        logger.warning(f"Файл {file_name} не найден в папке {folder_id}")
        return None
    except Exception as e:
        logger.error(f"Ошибка при доступе к Google Drive: {str(e)}")
        return None

def list_missing_guides():
    folders = {
        "kapusta": os.getenv("GDRIVE_FOLDER_KAPUSTA"),
        "avatar": os.getenv("GDRIVE_FOLDER_AVATAR"),
        "amourchik": os.getenv("GDRIVE_FOLDER_AMOURCHIK")
    }
    missing = []
    for program, folder_id in folders.items():
        if folder_id:
            try:
                response = drive_service.files().list(q=f"'{folder_id}' in parents", fields="files(name)").execute()
                existing = {f['name'] for f in response.get('files', [])}
                for i in range(1, 23):
                    file_name = f"{i:02d}.pdf"
                    if file_name not in existing:
                        missing.append(f"{program}/{file_name}")
            except Exception as e:
                logger.error(f"Ошибка при сканировании {program}: {str(e)}")
    return missing

def list_existing_guides():
    folders = {
        "kapusta": os.getenv("GDRIVE_FOLDER_KAPUSTA"),
        "avatar": os.getenv("GDRIVE_FOLDER_AVATAR"),
        "amourchik": os.getenv("GDRIVE_FOLDER_AMOURCHIK")
    }
    existing = []
    for program, folder_id in folders.items():
        if folder_id:
            try:
                response = drive_service.files().list(q=f"'{folder_id}' in parents", fields="files(name)").execute()
                files = response.get('files', [])
                for file in files:
                    existing.append(f"{program}/{file['name']}")
            except Exception as e:
                logger.error(f"Ошибка при сканировании {program} для существующих файлов: {str(e)}")
    return existing