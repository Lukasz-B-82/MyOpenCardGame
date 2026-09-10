# dice.py
import os
import random
from typing import Dict, List, Optional

DICE_FILE = os.path.join("defines", "dice.lua")

# Struktura: { "d6[0,1,2,3,4,5]": {"main_image": str, "values": [0..5], "faces": {0: "d6(0).png", ...}} }
DICE_DEFS: Dict[str, dict] = {}


def load_dice():
    """Wczytuje definicje kości z defines/dice.lua."""
    global DICE_DEFS
    DICE_DEFS = {}

    if not os.path.exists(DICE_FILE):
        print(f"Nie znaleziono pliku {DICE_FILE} – brak definicji kości.")
        return

    try:
        import lupa
        from lupa import LuaRuntime
        lua = LuaRuntime(unpack_returned_tuples=True)
        with open(DICE_FILE, "r", encoding="utf-8") as f:
            result = lua.execute(f.read())

        # W zależności od tego, czy Lua zwraca tabelę, czy jest w globalnej przestrzeni
        dice_table = result
        if dice_table is None:
            dice_table = lua.globals().get("dice")
        if dice_table is None:
            raise ValueError("Nie znaleziono tabeli 'dice' w dice.lua")

        for key, defn in dice_table.items():
            if defn is None:
                continue

            main_image = defn["main_image"]
            faces_lua = defn["faces"]

            values = []
            faces = {}
            # faces_lua jest tabelą Lua z kluczami 1, 2, 3, ...
            for _, face in faces_lua.items():
                v = int(face["value"])
                img = str(face["image"])
                values.append(v)
                faces[v] = img

            DICE_DEFS[str(key)] = {
                "main_image": str(main_image),
                "values": values,
                "faces": faces,
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
            }

        print(f"Wczytano {len(DICE_DEFS)} definicji kości z {DICE_FILE}")

    except Exception as e:
        print(f"Nie udało się wczytać {DICE_FILE}: {e}")
        import traceback
        traceback.print_exc()


# ---------- API ----------

def get_dice(dice_key: str) -> Optional[dict]:
    """Zwraca definicję kości po kluczu (np. 'd6[0,1,2,3,4,5]') lub None."""
    return DICE_DEFS.get(dice_key)


def get_values(dice_key: str) -> List[int]:
    """Zwraca listę wartości ścian kości."""
    d = get_dice(dice_key)
    return d["values"] if d else []


def get_faces(dice_key: str) -> Dict[int, str]:
    """Zwraca mapę wartość → nazwa pliku obrazka."""
    d = get_dice(dice_key)
    return d["faces"] if d else {}


def expected_value(dice_key: str, count: int = 1) -> float:
    """Zwraca wartość oczekiwaną sumy rzutów N kościami."""
    d = get_dice(dice_key)
    if not d:
        return 0.0
    return d["avg"] * count


def max_value(dice_key: str, count: int = 1) -> int:
    """Zwraca maksymalną możliwą sumę rzutów N kościami."""
    d = get_dice(dice_key)
    if not d:
        return 0
    return d["max"] * count


def min_value(dice_key: str, count: int = 1) -> int:
    """Zwraca minimalną możliwą sumę rzutów N kościami."""
    d = get_dice(dice_key)
    if not d:
        return 0
    return d["min"] * count


def roll(dice_key: str, count: int = 1) -> int:
    """Rzuca N kościami i zwraca sumę wyników."""
    d = get_dice(dice_key)
    if not d:
        return 0
    return sum(random.choice(d["values"]) for _ in range(count))


def roll_each(dice_key: str, count: int = 1) -> List[int]:
    """Rzuca N kościami i zwraca listę wyników (przydatne do animacji)."""
    d = get_dice(dice_key)
    if not d:
        return [0] * count
    return [random.choice(d["values"]) for _ in range(count)]


def is_valid_dice(dice_key: str) -> bool:
    """Sprawdza, czy klucz kości istnieje."""
    return dice_key in DICE_DEFS

# ---------- ROZKŁADY I PRAWDOPODOBIEŃSTWA ----------

def dice_distribution(dice_key: str, count: int = 1) -> Dict[int, float]:
    """
    Zwraca rozkład prawdopodobieństwa sumy rzutów N kościami.
    Np. dla 2×d6[0..5] zwraca {0: 1/36, 1: 2/36, ..., 10: 1/36}
    """
    values = get_values(dice_key)
    if not values:
        return {0: 1.0}

    # Pojedyncza kość – równomierny rozkład
    dist = {v: 1.0 / len(values) for v in values}

    # Konwolucja count-1 razy
    for _ in range(count - 1):
        new_dist: Dict[int, float] = {}
        for s1, p1 in dist.items():
            for v in values:
                new_dist[s1 + v] = new_dist.get(s1 + v, 0.0) + p1 / len(values)
        dist = new_dist
    return dist


def static_distribution(value: int) -> Dict[int, float]:
    """Rozkład deterministyczny – pojedyncza wartość z prawdopodobieństwem 1.0."""
    return {int(value): 1.0}


def combined_distribution(distributions: List[Dict[int, float]]) -> Dict[int, float]:
    """Łączy kilka rozkładów przez konwolucję (suma zmiennych losowych)."""
    result: Dict[int, float] = {0: 1.0}
    for dist in distributions:
        new_result: Dict[int, float] = {}
        for s1, p1 in result.items():
            for s2, p2 in dist.items():
                new_result[s1 + s2] = new_result.get(s1 + s2, 0.0) + p1 * p2
        result = new_result
    return result


def probability_greater(dist_a: Dict[int, float], dist_b: Dict[int, float]) -> float:
    """Zwraca P(sum_a > sum_b)."""
    # Zamiast O(n²) można by użyć dystrybuanty, ale dla naszych zakresów to OK.
    total = 0.0
    for sa, pa in dist_a.items():
        for sb, pb in dist_b.items():
            if sa > sb:
                total += pa * pb
    return total

def probability_less_equal(dist_a: Dict[int, float], dist_b: Dict[int, float]) -> float:
    """Zwraca P(A ≤ B) dla niezależnych zmiennych A i B."""
    total = 0.0
    for a, pa in dist_a.items():
        for b, pb in dist_b.items():
            if a <= b:
                total += pa * pb
    return total


def distribution_average(dist: Dict[int, float]) -> float:
    """Zwraca wartość oczekiwaną rozkładu."""
    return sum(s * p for s, p in dist.items())

# ---------- AUTO-LOAD ----------
# Automatycznie ładujemy definicje przy imporcie modułu.
load_dice()