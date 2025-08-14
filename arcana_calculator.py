from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def reduce_arcana(n: int) -> int:
    n = abs(int(n))
    while n > 22:
        n = sum(int(d) for d in str(n))
        if n == 0:
            n = 22
    return 1 if n < 1 else n

def compute_points(date_str: str) -> dict:
    logger.info(f"compute_points получил date_str='{date_str}'")
    try:
        dt = datetime.strptime(date_str, "%d.%m.%Y")
        day, month, year = dt.day, dt.month, dt.year
        A = reduce_arcana(sum(int(d) for d in f"{day:02d}"))
        B = reduce_arcana(sum(int(d) for d in f"{month:02d}"))
        V = reduce_arcana(sum(int(d) for d in f"{year:04d}"))
        G = reduce_arcana(A + B + V)        # деньги
        D = reduce_arcana(A + B + V + G)    # восприятие
        E = reduce_arcana(D + G)            # любовь
        logger.info(f"Арканы: A={A}, B={B}, V={V}, G={G}, D={D}, E={E}")
        return {"A": A, "B": B, "V": V, "G": G, "D": D, "E": E}
    except ValueError as e:
        logger.error(f"Ошибка парсинга даты '{date_str}': {str(e)}")
        raise

def calc_arcana(program: str, date_str: str) -> int:
    logger.info(f"calc_arcana для программы {program}, дата {date_str}")
    pts = compute_points(date_str)
    if program == "kapusta":
        return pts["G"]
    if program == "avatar":
        return pts["D"]
    return pts["E"]  # amourchik