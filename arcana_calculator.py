import datetime
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def calculate_arcana(date_str):
    try:
        day, month, year = map(int, date_str.split('.'))
        birth_date = datetime.date(year, month, day)
        total = sum(int(x) for x in str(birth_date.year) + str(birth_date.month) + str(birth_date.day))
        while total > 22:
            total = sum(int(x) for x in str(total))
        return total if total != 0 else 22  # 22 - ноль арканов
    except ValueError:
        logger.error(f"Некорректный формат даты: {date_str}")
        raise