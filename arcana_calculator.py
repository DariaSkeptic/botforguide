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
    day, month, year = map(int, date_str.split("."))
    _ = datetime.date(year, month, day)  # валидация даты
    return day, month, year

def calc_points(date_str: str):
    """
    Возвращает точки матрицы {'A','B','V','G','D','E'}:
    A = редукция суммы цифр ДНЯ
    B = редукция суммы цифр МЕСЯЦА
    V = редукция суммы цифр ГОДА
    G = редукция(A+B+V)            — деньги / «капуста»
    D = редукция(A+B+V+G)          — восприятие / «аватар»
    E = редукция(D+G)              — любовь / «амурчик»
    """
    d, m, y = _parse(date_str)
    A = _reduce22(_sumdigits(d))
    B = _reduce22(_sumdigits(m))
    V = _reduce22(_sumdigits(y))
    G = _reduce22(A + B + V)
    D = _reduce22(A + B + V + G)
    E = _reduce22(D + G)
    return {"A": A, "B": B, "V": V, "G": G, "D": D, "E": E}

_PROGRAM_POINT = {
    "kapusta": "G",
    "avatar": "D",
    "amourchik": "E",
}

def calculate_arcana(date_str: str, program: str = "kapusta") -> int:
    """
    Возвращает аркан по программе:
    - kapusta  -> G
    - avatar   -> D
    - amourchik-> E
    """
    pts = calc_points(date_str)
    key = _PROGRAM_POINT.get((program or "kapusta").lower(), "G")
    return pts[key]
