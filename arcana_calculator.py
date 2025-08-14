from datetime import datetime

def reduce_arcana(n: int) -> int:
    n = abs(int(n))
    while n > 22:
        n = sum(int(d) for d in str(n))
        if n == 0:
            n = 22
    return 1 if n < 1 else n

def compute_points(date_str: str) -> dict:
    dt = datetime.strptime(date_str, "%d.%m.%Y")
    day, month, year = dt.day, dt.month, dt.year
    A = reduce_arcana(sum(int(d) for d in f"{day:02d}"))
    B = reduce_arcana(sum(int(d) for d in f"{month:02d}"))
    V = reduce_arcana(sum(int(d) for d in f"{year:04d}"))
    G = reduce_arcana(A + B + V)        # деньги
    D = reduce_arcana(A + B + V + G)    # восприятие
    E = reduce_arcana(D + G)            # любовь
    return {"A": A, "B": B, "V": V, "G": G, "D": D, "E": E}

def calc_arcana(program: str, date_str: str) -> int:
    pts = compute_points(date_str)
    if program == "kapusta":
        return pts["G"]
    if program == "avatar":
        return pts["D"]
    return pts["E"]  # amourchik