# game_ai/registry.py
"""Rejestr modeli AI.

Pozwala rejestrować klasy AI pod nazwą (np. "heuristic", "random")
i tworzyć je po nazwie, bez konieczności importowania konkretnych
klas w miejscu użycia (menu, game.py).

Użycie:
    # W module z AI:
    from game_ai.registry import register

    @register("heuristic")
    class HeuristicAI(BaseAI):
        ...

    # Gdzie indziej:
    from game_ai.registry import create_ai, list_models
    ai = create_ai("heuristic", logic)
    print(list_models())   # ['heuristic', 'random']
"""
from typing import Dict, Type, List
from game_ai.base import BaseAI


# Prywatny rejestr: nazwa → klasa
_REGISTRY: Dict[str, Type[BaseAI]] = {}


def register(name: str):
    """Dekorator rejestrujący klasę AI pod daną nazwą.

    Ustawia też cls.name = name, żeby AI „wiedziało", jak się nazywa
    (przydatne w logach).
    """
    def deco(cls: Type[BaseAI]):
        if name in _REGISTRY:
            print(f"[registry] Ostrzeżenie: '{name}' już zarejestrowane, "
                  f"nadpisuję ({_REGISTRY[name]} → {cls})")
        _REGISTRY[name] = cls
        cls.name = name
        return cls
    return deco


def create_ai(name: str, logic, **kwargs) -> BaseAI:
    """Tworzy instancję AI o danej nazwie.

    kwargs przekazywane do konstruktora klasy AI (np. weights=..., weights_path=...).
    Rzuca KeyError, jeśli nazwa nie jest zarejestrowana.
    """
    if name not in _REGISTRY:
        raise KeyError(
            f"Nieznany AI '{name}'. Dostępne: {list_models()}"
        )
    return _REGISTRY[name](logic, **kwargs)


def list_models() -> List[str]:
    """Zwraca posortowaną listę zarejestrowanych nazw AI."""
    return sorted(_REGISTRY.keys())


def is_registered(name: str) -> bool:
    """Sprawdza, czy AI o danej nazwie jest zarejestrowane."""
    return name in _REGISTRY