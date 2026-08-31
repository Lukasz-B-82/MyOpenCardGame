# card.py
import uuid
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

# ---------- ENUMY ----------
class CardType(Enum):
    SOLDIER = "SOLDIER"
    WORKER = "WORKER"
    VEHICLE = "VEHICLE"
    TANK = "TANK"
    CAR = "CAR"
    PLANE = "PLANE"
    WEAPON = "WEAPON"
    TERRAIN = "TERRAIN"
    CITY = "CITY"
    BUILDING = "BUILDING"
    ARTILLERY = "ARTILLERY"

class Faction(Enum):
    NEUTRAL = "NEUTRAL"
    RED = "RED"
    BLUE = "BLUE"
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    WHITE = "WHITE"
    BLACK = "BLACK"

class Zone(Enum):
    FRONT = "front"
    SECOND = "second"
    BACK = "back"
    STATE = "state"

# ---------- KLASA CARD ----------
@dataclass
class Card:
    """
    Klasa reprezentująca pojedynczą kartę w grze.
    Każda karta ma unikalne ID (UUID) i może być modyfikowana w trakcie gry.
    """
    # ---------- PODSTAWOWE DANE ----------
    name: str = "Bez nazwy"
    name_key: Optional[str] = None  # klucz do tłumaczeń (np. "card_0")
    card_type: CardType = CardType.SOLDIER
    faction: Faction = Faction.NEUTRAL
    max_in_deck: int = 6
    
    # ---------- KOSZTY I STATYSTYKI ----------
    cost_initiative: int = 1      # koszt w inicjatywie
    initiative: int = 0           # punkty inicjatywy generowane
    cost_production: int = 0      # koszt produkcji
    production: int = 0           # punkty produkcji generowane
    extra_cost: Dict[str, int] = field(default_factory=dict)  # np. {"surowce": 2}
    
    # ---------- ZASOBY I PRODUKCJA ----------
    max_workers: int = 0          # maksymalna liczba robotników
    food_production: int = 0      # produkcja żywności
    iron_ore_production: int = 0  # produkcja rudy żelaza
    oil_production: int = 0       # produkcja ropy
    steal_production: int = 0     # produkcja stali
    fuel_production: int = 0      # produkcja paliwa
    logistics: int = 0
    
    # ---------- KONSUMPCJA ----------
    food_consumption: int = 0     # konsumpcja żywności na turę
    fuel_consumption: int = 0      # konsumpcja ropy na turę
    cost_steal: int = 0           # koszt w stali (przy zagrywaniu)
    
    # ---------- ZAŁĄCZNIKI I EFEKTY ----------
    attached_cards: List['Card'] = field(default_factory=list)
    
    # ---------- DOZWOLONE STREFY I ZAŁĄCZNIKI ----------
    allowed_zones: List[Zone] = field(default_factory=list)
    allowed_attachments: List[CardType] = field(default_factory=list)
    
    # ---------- WYMAGANIA ----------
    requirements: List[Tuple[Zone, CardType, int]] = field(default_factory=list)
    # np. [("state", CardType.CITY, 1), ("state", CardType.TERRAIN, 3)]
    
    # ---------- GRAFIKA ----------
    image_path: Optional[str] = None  # ścieżka do obrazka karty
    frame_key: Optional[str] = None   # klucz ramki z frames.lua
    
    # ---------- IDENTYFIKATOR ----------
    id: str = field(default_factory=lambda: uuid.uuid4().hex, init=False)
    # Unikalny 32-znakowy identyfikator (UUID bez myślników)

    # ---------- WALKA ----------
    attack: Dict[str, int] = field(default_factory=dict)  # np. {"soft": 2, "hard": 0, "air": 0}
    attack_range: int = 0
    target_type: List[str] = field(default_factory=list)  # np. ["soft"]
    defense: int = 0
    
    # ---------- METODY ----------
    def can_attach_to(self, target_card: 'Card') -> bool:
        """
        Sprawdza, czy tę kartę (self) można dołączyć do karty docelowej (target_card).
        Np. robotnik (self) do terenu (target_card) – sprawdzamy, czy typ robotnika
        jest w allowed_attachments terenu.
        """
        return self.card_type in target_card.allowed_attachments
    
    def can_be_played_in_zone(self, zone: Zone) -> bool:
        """
        Sprawdza, czy kartę można zagrać w danej strefie.
        """
        return zone in self.allowed_zones
    
    def attach(self, card: 'Card'):
        """
        Dołącza kartę do tej karty.
        """
        if card not in self.attached_cards:
            self.attached_cards.append(card)
    
    def detach(self, card: 'Card'):
        """
        Odłącza kartę od tej karty.
        """
        if card in self.attached_cards:
            self.attached_cards.remove(card)
    
    def get_total_initiative(self) -> int:
        """
        Zwraca całkowitą inicjatywę tej karty wraz z załącznikami.
        """
        total = self.initiative
        for attached in self.attached_cards:
            total += attached.initiative
        return total
    
    def get_total_production(self) -> int:
        """
        Zwraca całkowitą produkcję tej karty wraz z załącznikami.
        """
        total = self.production
        for attached in self.attached_cards:
            total += attached.production
        return total
    
    def count_attachments(self, card_type: Optional[CardType] = None) -> int:
        """
        Zwraca liczbę załączników (opcjonalnie filtrując po typie).
        """
        if card_type is None:
            return len(self.attached_cards)
        return sum(1 for c in self.attached_cards if c.card_type == card_type)
    
    def get_stat(self, stat_name: str) -> int:
        """
        Pobiera statystykę po nazwie (uwzględniając załączniki).
        Dostępne statystyki:
        - initiative, production, food_production, iron_ore_production,
          oil_production, steal_production, fuel_production
        """
        stat_map = {
            'initiative': self.initiative,
            'production': self.production,
            'food_production': self.food_production,
            'iron_ore_production': self.iron_ore_production,
            'oil_production': self.oil_production,
            'steal_production': self.steal_production,
            'fuel_production': self.fuel_production,
        }
        total = stat_map.get(stat_name, 0)
        for attached in self.attached_cards:
            total += attached.get_stat(stat_name)
        return total
    
    def copy(self):
        """Tworzy kopię karty (nowy obiekt z tymi samymi danymi)."""
        import copy
        return Card(
            name=self.name,
            name_key=self.name_key,
            card_type=self.card_type,
            faction=self.faction,
            max_in_deck=self.max_in_deck,
            cost_initiative=self.cost_initiative,
            initiative=self.initiative,
            cost_production=self.cost_production,
            production=self.production,
            extra_cost=self.extra_cost.copy(),
            max_workers=self.max_workers,
            food_production=self.food_production,
            iron_ore_production=self.iron_ore_production,
            oil_production=self.oil_production,
            steal_production=self.steal_production,
            fuel_production=self.fuel_production,
            food_consumption=self.food_consumption,
            fuel_consumption=self.fuel_consumption,
            cost_steal=self.cost_steal,
            allowed_zones=self.allowed_zones.copy(),
            allowed_attachments=self.allowed_attachments.copy(),
            requirements=self.requirements.copy(),
            image_path=self.image_path,
            frame_key=self.frame_key,
            logistics=self.logistics,
            attack=self.attack.copy() if self.attack else {},
            attack_range=self.attack_range,
            target_type=self.target_type.copy() if self.target_type else [],
            defense=self.defense,            
        )
    
    def __repr__(self):
        return f"Card({self.name}, {self.card_type.value}, id={self.id[:8]}...)"

# ---------- FUNKCJE POMOCNICZE ----------
# card.py – funkcja create_card_from_lua z debugowaniem
def create_card_from_lua(defn, name_key: str = None) -> Card:
    """
    Tworzy kartę z definicji Lua.
    """
    from card import CardType, Faction, Zone
    
    def safe_get(defn, key, default=None):
        try:
            value = defn[key] if hasattr(defn, '__getitem__') else default
            if value is None:
                return default
            return value
        except Exception:
            return default
    
    def lua_table_to_list(table):
        if table is None:
            return []
        if isinstance(table, (list, tuple)):
            return list(table)
        if hasattr(table, 'values'):
            return list(table.values())
        return []
    
    def to_str(value):
        if value is None:
            return ""
        if hasattr(value, 'value'):
            return str(value)
        return str(value)
    
    # ---------- PODSTAWOWE DANE ----------
    type_str = to_str(safe_get(defn, "type", "SOLDIER"))
    faction_str = to_str(safe_get(defn, "faction", "NEUTRAL"))
    
    # ---------- KONWERSJA ENUMÓW (używamy konstruktora z wartością) ----------
    try:
        card_type = CardType(type_str)  # np. CardType("SOLDIER") -> CardType.SOLDIER
    except ValueError:
        print(f"  Ostrzeżenie: nieznany typ '{type_str}', używam SOLDIER")
        card_type = CardType.SOLDIER
    
    try:
        faction = Faction(faction_str)
    except ValueError:
        print(f"  Ostrzeżenie: nieznana frakcja '{faction_str}', używam NEUTRAL")
        faction = Faction.NEUTRAL
    
    # ---------- DOZWOLONE STREFY ----------
    allowed_zones = []
    zones_data = safe_get(defn, "allowed_zones", [])
    if zones_data:
        zones_list = lua_table_to_list(zones_data)
        for z in zones_list:
            try:
                z_str = to_str(z)
                allowed_zones.append(Zone(z_str))  # np. Zone("back") -> Zone.BACK
            except ValueError:
                print(f"  Ostrzeżenie: nieznana strefa '{z_str}'")
    
    # ---------- DOZWOLONE ZAŁĄCZNIKI ----------
    allowed_attachments = []
    attachments_data = safe_get(defn, "allowed_attachments", [])
    if attachments_data:
        attachments_list = lua_table_to_list(attachments_data)
        for a in attachments_list:
            try:
                a_str = to_str(a)
                allowed_attachments.append(CardType(a_str))  # np. CardType("WEAPON")
            except ValueError:
                print(f"  Ostrzeżenie: nieznany typ załącznika '{a_str}'")
    
    # ---------- WYMAGANIA ----------
    requirements = []
    req_data = safe_get(defn, "requirements", [])
    if req_data:
        req_list = lua_table_to_list(req_data)
        for req in req_list:
            try:
                # Pobieramy wartości z tabeli Lua
                zone_str = to_str(req["zone"] if hasattr(req, '__getitem__') and "zone" in req else None)
                type_str_req = to_str(req["type"] if hasattr(req, '__getitem__') and "type" in req else None)
                count = int(req["count"] if hasattr(req, '__getitem__') and "count" in req else 0)
                
                if zone_str and type_str_req:
                    zone = Zone(zone_str)
                    req_type = CardType(type_str_req)
                    requirements.append((zone, req_type, count))
            except Exception as e:
                print(f"  Błąd konwersji wymagania: {req}")
                
    frame_key = safe_get(defn, "frame_key", None)  # pobieramy frame_key

    attack_data = safe_get(defn, "attack", {})
    # Konwersja słownika Lua na słownik Pythona (klucze to stringi)
    attack = {}
    if attack_data:
        for k, v in attack_data.items():
            attack[str(k)] = int(v) if v is not None else 0

    target_type_data = safe_get(defn, "target_type", [])
    target_type = []
    if target_type_data:
        for t in lua_table_to_list(target_type_data):
            target_type.append(str(t))
    
    # ---------- TWORZENIE KARTY ----------
    return Card(
        name="",
        name_key=name_key,
        card_type=card_type,
        faction=faction,
        cost_initiative=int(safe_get(defn, "cost_initiative", 1)),
        initiative=int(safe_get(defn, "initiative", 0)),
        cost_production=int(safe_get(defn, "cost_production", 0)),
        production=int(safe_get(defn, "production", 0)),
        extra_cost=safe_get(defn, "extra_cost", {}),
        max_workers=int(safe_get(defn, "max_workers", 0)),
        food_production=int(safe_get(defn, "food_production", 0)),
        iron_ore_production=int(safe_get(defn, "iron_ore_production", 0)),
        oil_production=int(safe_get(defn, "oil_production", 0)),
        steal_production=int(safe_get(defn, "steal_production", 0)),
        fuel_production=int(safe_get(defn, "fuel_production", 0)),
        food_consumption=int(safe_get(defn, "food_consumption", 0)),
        fuel_consumption=int(safe_get(defn, "fuel_consumption", 0)),
        cost_steal=int(safe_get(defn, "cost_steal", 0)),
        allowed_zones=allowed_zones,
        allowed_attachments=allowed_attachments,
        requirements=requirements,
        image_path=safe_get(defn, "image"),
        frame_key=frame_key,
        logistics=int(safe_get(defn, "logistics", 0)),
        attack=attack,
        attack_range=int(safe_get(defn, "attack_range", 0)),
        target_type=target_type,
        defense=int(safe_get(defn, "defense", 0)),
    )

# Jeśli potrzebujesz singletonu dla wszystkich kart, możesz dodać:
ALL_CARDS: List[Card] = []