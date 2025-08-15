import datetime
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def _reduce22(n: int) -> int:
    while n > 22:
        n = sum(int(x) for x in str(n))
    return 22 if n == 0 else n

def _sumdigits(n: int) -> int:
    return sum(int(x) for x in str(n))

def _parse(date_str: str):
    d, m, y = map(int, date_str.split("."))
    _ = datetime.date(y, m, d)  # валидация
    return d, m, y

def calc_points(date_str: str):
    """
    Матрица (русские буквы):
    А = редукция суммы цифр ДНЯ
    Б = редукция суммы цифр МЕСЯЦА
    В = редукция суммы цифр ГОДА
    Г = редукция(А + Б + В)            — деньги
    Д = редукция(А + Б + В + Г)        — восприятие
    Е = редукция(Д + Г)                — любовь
    """
    d, m, y = _parse(date_str)
    А = _reduce22(_sumdigits(d))
    Б = _reduce22(_sumdigits(m))
    В = _reduce22(_sumdigits(y))
    Г = _reduce22(А + Б + В)
    Д = _reduce22(А + Б + В + Г)
    Е = _reduce22(Д + Г)
    return {"А": А, "Б": Б, "В": В, "Г": Г, "Д": Д, "Е": Е}

# соответствие направления и точки
_PROGRAM_POINT = {
    "kapusta": "Г",
    "avatar": "Д",
    "amourchik": "Е",
}

def calculate_arcana(date_str: str, program: str = "kapusta") -> int:
    pts = calc_points(date_str)
    key = _PROGRAM_POINT.get((program or "kapusta").lower(), "Г")
    return pts[key]
