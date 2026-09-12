# game_logic.py
from typing import List, Optional, Dict, Tuple
from card import Card, Zone, CardType
from card_view import CardView
from player import Player
from localization import Localization

class GameLogic:
    def __init__(self, players_config, create_deck_func, language="pl"):
        self.language = language
        self.localization = Localization(language)

        # Wczytaj konfigurację z defines/game.lua
        self.game_config = self.load_game_config()

        self.players: List[Player] = []
        for cfg in players_config:
            player = Player(cfg["name"], config=self.game_config)
            player.deck = create_deck_func(cfg["deck"])
            player.reverse_deck()
            player.draw_initial_hand(self.game_config.get("initial_hand", 5))
            self.players.append(player)
        
        self.current_player_index = 0
        self.turn = 1
        
        # Stan gry
        self.selected_card: Optional[Card] = None
        self.allowed_zones: List[Zone] = []
        self.attachment_targets: List[Tuple[Card, Zone]] = []
        self.move_mode: bool = False
        self.move_targets: List[Zone] = []
        self.selected_soldier: Optional[Card] = None

        # NOWY SYSTEM ATAKU (przyciski zasięgu)
        self.attack_mode: bool = False
        self.attack_range: int = 0
        self.attack_zones: Dict[Player, List[Zone]] = {}

        self.attack_preview_data: Optional[Dict] = None
        self.attack_source_zone: Optional[Zone] = None

        self.view = None  # referencja do widoku

        self.selected_defender_index: int = 0  # indeks aktualnie wybranego obrońcy
        self.combat_result: Optional[Dict] = None

        # --- koszt ataku w bieżącej turze ---
        self.attack_count_this_turn: int = 0     # ile ataków już wykonano
        self.current_attack_cost: int = 0        # koszt zaplanowanego ataku (do pobrania)        

        # --- zwycięstwo ---
        self.victor: Optional[Player] = None

        
    @property
    def current_player(self) -> Player:
        return self.players[self.current_player_index]

    # ---------- PRZENOSZENIE (bez zmian) ----------
    def select_soldier_for_move(self, card: Card):
        if card.card_type != CardType.SOLDIER:
            self.add_message("Tylko żołnierze mogą być przenoszeni!", "error")
            return False
        player = self.current_player
        found_zone = None
        for zone, cards in player.zones.items():
            if card in cards:
                found_zone = zone
                break
        if found_zone is None:
            self.add_message("Żołnierz nie znajduje się w żadnej strefie!", "error")
            return False

        targets = []
        for zone in [Zone.BACK, Zone.SECOND, Zone.FRONT]:
            if zone == found_zone:
                continue
            cost_logistics = self._get_move_logistics_cost(found_zone, zone)
            if player.logistics >= cost_logistics and player.initiative >= 1:
                targets.append(zone)
        if not targets:
            self.add_message("Brak dostępnych stref docelowych (za mało logistyki lub inicjatywy)", "error")
            return False

        self.selected_soldier = card
        self.move_mode = True
        self.move_targets = targets
        self.selected_card = None
        self.allowed_zones = []
        self.attachment_targets = []
        return True

    def move_soldier_to_zone(self, zone: Zone) -> bool:
        if not self.move_mode or self.selected_soldier is None:
            self.add_message("Nie wybrano żołnierza do przeniesienia", "error")
            return False
        if zone not in self.move_targets:
            self.add_message("Ta strefa nie jest dostępna", "error")
            return False

        player = self.current_player
        from_zone = None
        for z, cards in player.zones.items():
            if self.selected_soldier in cards:
                from_zone = z
                break
        if from_zone is None:
            self.add_message("Żołnierz nie znajduje się w żadnej strefie", "error")
            return False

        cost_log = self._get_move_logistics_cost(from_zone, zone)
        if player.logistics < cost_log:
            self.add_message(f"Za mało logistyki! Potrzeba: {cost_log}", "error")
            return False
        if player.initiative < 1:
            self.add_message("Za mało inicjatywy! Potrzeba: 1", "error")
            return False

        player.zones[from_zone].remove(self.selected_soldier)
        player.zones[zone].append(self.selected_soldier)
        player.logistics -= cost_log
        player.initiative -= 1

        self.selected_soldier = None
        self.move_mode = False
        self.move_targets = []
        self.add_message(f"Przeniesiono żołnierza do {zone.value}", "success")
        return True

    def _get_move_logistics_cost(self, from_zone: Zone, to_zone: Zone) -> int:
        if from_zone == Zone.BACK and to_zone == Zone.SECOND:
            return 1
        if from_zone == Zone.BACK and to_zone == Zone.FRONT:
            return 2
        if from_zone == Zone.SECOND and to_zone == Zone.FRONT:
            return 1
        if from_zone == Zone.FRONT and to_zone == Zone.SECOND:
            return -1
        if from_zone == Zone.FRONT and to_zone == Zone.BACK:
            return -2
        if from_zone == Zone.SECOND and to_zone == Zone.BACK:
            return -1

    def get_attack_cost(self, num_attackers: int) -> int:
        """Zwraca koszt inicjatywy za atak N jednostkami.

        Wzór:
            base_cost + cost_per_unit * num_attackers
                      - next_attack_cost_decrease * (liczba ataków już wykonanych)
        ale nigdy mniej niż min_initiative_cost.
        """
        cfg = self.game_config.get("atack", {}) or {}
        base = int(cfg.get("base_cost", 10))
        per = int(cfg.get("cost_per_unit", 3))
        dec = int(cfg.get("next_attack_cost_decrease", 5))
        min_c = int(cfg.get("min_initiative_cost", 5))

        raw = base + per * num_attackers - dec * self.attack_count_this_turn
        return max(min_c, raw)

    # ---------- DOŁĄCZANIE (bez zmian) ----------
    def can_attach_to_card(self, attached_card: Card, target_card: Card) -> bool:
        if not attached_card.can_attach_to(target_card):
            return False

        player = self.current_player
        if attached_card.cost_production > 0 and player.production < attached_card.cost_production:
            return False
        
        if attached_card.food_consumption > 0 and player.food_production < attached_card.food_consumption:
            if not (attached_card.card_type == CardType.WORKER and target_card.food_production > 0):
                return False

        if attached_card.fuel_consumption > 0 and player.fuel_production < attached_card.fuel_consumption:
            return False
            
        if attached_card.cost_initiative > player.initiative:
            return False

        if target_card.max_workers > 0:
            worker_count = sum(1 for c in target_card.attached_cards if c.card_type == CardType.WORKER)
            if worker_count >= target_card.max_workers:
                return False
        
        if target_card.card_type == CardType.SOLDIER:
            if len(target_card.attached_cards) >= 1:
                return False
        
        return True
    
    def select_card(self, card: Card) -> bool:
        if card not in self.current_player.hand:
            return False
        self.selected_card = card
        self.allowed_zones = []
        self.attachment_targets = []

        for zone in Zone:
            if card.can_be_played_in_zone(zone):
                self.allowed_zones.append(zone)

        player = self.current_player
        for zone in Zone:
            for target_card in player.zones.get(zone, []):
                if self.can_attach_to_card(card, target_card):
                    self.attachment_targets.append((target_card, zone))
        return True

    def attach_card_to_target(self, target_card: Card) -> bool:
        if self.selected_card is None:
            return False
        if not self.can_attach_to_card(self.selected_card, target_card):
            return False
        if not any(t == target_card for t, _ in self.attachment_targets):
            return False

        player = self.current_player
        if self.selected_card.cost_initiative > player.initiative:
            return False

        if player.attach_card_to_target(self.selected_card, target_card):
            self.update_player_food_production(player)
            if self.selected_card.card_type == CardType.WORKER:
                self.add_message(f"Dołączam kartę: {CardType.WORKER} i zwiększam produkcję z karty: {target_card.card_type.name}", "info")
                if target_card.production > 0:
                    player.production += target_card.production
                if target_card.fuel_production > 0 and player.oil_production > 0:
                    player.fuel_production += min(target_card.fuel_production, player.oil_production)
                    player.oil_production -= min(target_card.fuel_production, player.oil_production)
                if target_card.oil_production > 0:
                    player.oil_production, player.fuel_production = self.get_oil_to_fuel_balance(player)
                if target_card.iron_ore_production > 0:
                    player.iron_production += target_card.iron_ore_production
                if target_card.steal_production > 0 and player.iron_production > 0:
                    player.steal += min(target_card.steal_production, player.iron_production)
                    player.iron_production -= min(target_card.steal_production, player.iron_production)
    
            if self.selected_card.fuel_consumption > 0:
                player.fuel_production -= self.selected_card.fuel_consumption 
            
            if self.selected_card.cost_production > 0:
                player.production -= self.selected_card.cost_production
            player.initiative -= self.selected_card.cost_initiative
            self.add_message(f"Dołączono kartę typu: {self.selected_card.card_type.name} do karty typu {target_card.card_type.name}", "success")
            self.deselect_card()
            return True
        return False

    def add_message(self, text: str, msg_type: str = "info"):
        if self.view:
            self.view.add_message(text, msg_type)

    def get_attachment_targets(self) -> List[Tuple[Card, Zone]]:
        return self.attachment_targets

    def deselect_card(self):
        self.selected_card = None
        self.allowed_zones = []
        self.attachment_targets = []
        self.selected_soldier = None
        self.move_mode = False
        self.move_targets = []
        self.attack_mode = False
        self.attack_range = 0
        self.attack_zones = {}
        self.attack_source_zone = None

    def get_move_targets(self) -> List[Zone]:
        return self.move_targets if self.move_mode else []

    def is_move_mode(self) -> bool:
        return self.move_mode
    
    # ---------- ZAGRANIE KARTY ----------
    def play_card_to_zone(self, zone: Zone) -> bool:
        if self.selected_card is None:
            return False
        if zone not in self.allowed_zones:
            return False
        
        player = self.current_player
        card = self.selected_card

        if card.cost_initiative > player.initiative:
            self.add_message(f"Za mało inicjatywy: {card.cost_initiative}", "error")
            return False
        if card.food_consumption > player.food_production:
            self.add_message(f"Za mało żywności: {card.food_production}", "error")
            return False
        if card.fuel_consumption > player.fuel_production:
            self.add_message(f"Za mało paliwa: {card.fuel_consumption}", "error")
            return False
        if not self.check_requirements(card, player):
            return False
        if card.cost_production > 0:
            if player.production < card.cost_production:
                self.add_message(f"Za mało produkcji: {card.cost_production}", "error")
                return False
        
        if player.play_card_to_zone(card, zone):
            self.update_player_food_production(player)
            player.initiative -= card.cost_initiative
            player.production -= card.cost_production
            self.add_message(f"Zagrano kartę typu {self.selected_card.card_type.name} do strefy {zone.name}", "success")
            self.add_message(f"Koszt inicjatywy: {card.cost_initiative}", "info")
            if card.logistics > 0:
                player.logistics += card.logistics
                self.add_message(f"Zwiększono logistykę +{card.logistics}", "info")
            if card.fuel_consumption > 0:
                player.fuel_production -= card.fuel_consumption
                self.add_message(f"Zwiększono zużycie paliwa +{card.fuel_consumption}", "info")
            self.deselect_card()
            return True
        return False
    
    def draw_card(self) -> bool:
        player = self.current_player
        cost = player.get_draw_cost()
        if player.initiative < cost:
            self.add_message(f"Za mało inicjatywy: {cost}", "error")
            return False
        if len(player.hand) >= player.max_hand_size:
            self.add_message(f"Za dużo kart na ręce: {player.max_hand_size}", "error")
            return False
        if not player.deck:
            self.add_message("Brak kart do dobrania", "error")
            return False
        player.initiative -= cost
        self.add_message(f"Dobrano kartę koszt inicjatywy {cost}", "success")
        card = player.draw_card()
        return card is not None
    
    def next_turn(self):
        self.deselect_card()
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        if self.current_player_index == 0:
            self.turn += 1
        self.start_turn(self.current_player)

    # ---------- TURA ----------
    def start_turn(self, player: Player):
        self.attack_count_this_turn = 0
        self.current_attack_cost = 0

        self.update_player_production(player, add=True)
        iron, steel = self.calculate_resurects_production(player)
        player.iron_production = iron
        player.steal += steel
        self.update_player_food_production(player)
        player.initiative += self.add_player_initiative(player)
        player.initiative = min(player.initiative, player.max_initiative)

    def add_player_initiative(self, player: Player):
        initiative = 0
        for zone in [Zone.STATE, Zone.BACK, Zone.SECOND, Zone.FRONT]:
            for card in player.zones.get(zone, []):
                initiative += card.initiative
                for attached_card in card.attached_cards:
                    initiative += attached_card.initiative
        return initiative
    
    def get_allowed_zones(self) -> List[Zone]:
        if self.selected_card is None:
            return []
        return self.selected_card.allowed_zones

    # ---------- STATYSTYKI I BILANS (bez zmian) ----------
    def count_cards_in_zone(self, player: Player, zone: Zone, card_type: CardType, include_attached: bool = True) -> int:
        count = 0
        for card in player.zones.get(zone, []):
            if card.card_type == card_type:
                count += 1
            if include_attached:
                for attached in card.attached_cards:
                    if attached.card_type == card_type:
                        count += 1
        return count

    def check_requirements(self, card: Card, player: Player) -> bool:
        if not card.requirements:
            return True
        for zone, req_type, req_count in card.requirements:
            count = self.count_cards_in_zone(player, zone, req_type)
            if count < req_count:
                return False
        return True

    def get_requirements_status(self, card: Card, player: Player) -> List[Tuple[bool, str]]:
        result = []
        if not card.requirements:
            return result
        for zone, req_type, req_count in card.requirements:
            count = self.count_cards_in_zone(player, zone, req_type)
            satisfied = count >= req_count
            zone_name = self.localization.get(f"zone_{zone.value}", zone.value)
            type_name = self.localization.get_card_type_name(req_type)
            desc = f"{count}/{req_count} {type_name} w {zone_name}"
            result.append((satisfied, desc))
        return result

    def get_oil_to_fuel_balance(self, player: Player):
        oil = 0
        fuel = 0
        for card in player.zones.get(Zone.STATE, []):
            if card.oil_production > 0:
                workers_attached = sum(1 for c in card.attached_cards if c.card_type == CardType.WORKER)
                oil += card.oil_production * workers_attached
        for card in player.zones.get(Zone.STATE, []):
            if card.fuel_production > 0:
                workers_attached = sum(1 for c in card.attached_cards if c.card_type == CardType.WORKER)
                fuel += card.fuel_production * workers_attached
        fuel_production = min(oil, fuel)
        oil -= fuel_production
        fuel = fuel_production
        return oil, fuel

    def calculate_resurects_production(self, player: Player):
        iron = 0
        steel = 0
        for card in player.zones.get(Zone.STATE, []):
            if card.iron_ore_production > 0:
                workers_attached = sum(1 for c in card.attached_cards if c.card_type == CardType.WORKER)
                iron += card.iron_ore_production * workers_attached
        for card in player.zones.get(Zone.STATE, []):
            if card.steal_production > 0:
                workers_attached = sum(1 for c in card.attached_cards if c.card_type == CardType.WORKER)
                steel += card.steal_production * workers_attached
        steel_production = min(iron, steel)
        iron -= steel_production
        steel = steel_production
        return iron, steel

    def calculate_food_balance(self, player: Player) -> int:
        total_food = player.initial_food_production
        for card in player.zones.get(Zone.STATE, []):
            if card.food_production > 0:
                workers_attached = sum(1 for c in card.attached_cards if c.card_type == CardType.WORKER)
                total_food += card.food_production * workers_attached
        total_consumption = 0
        for zone_cards in player.zones.values():
            for card in zone_cards:
                total_consumption += card.food_consumption
                for attached in card.attached_cards:
                    total_consumption += attached.food_consumption
        return total_food - total_consumption

    def update_player_food_production(self, player: Player):
        player.food_production = self.calculate_food_balance(player)

    def calculate_production_balance(self, player: Player) -> int:
        total_production = player.initial_production
        for card in player.zones.get(Zone.STATE, []):
            if card.production > 0:
                workers_attached = sum(1 for c in card.attached_cards if c.card_type == CardType.WORKER)
                if workers_attached > 0:
                    total_production += card.production * workers_attached
        return total_production

    def update_player_production(self, player: Player, add=False):
        balance = self.calculate_production_balance(player)
        if add:
            player.production += balance
            self.add_message(f"Dodano produkcję: {balance}", "info")

    def discard_selected_card(self) -> bool:
        if self.selected_card is None:
            self.add_message("Nie wybrano karty do odrzucenia!", "error")
            return False
        player = self.current_player
        if player.initiative < 1:
            self.add_message("Za mało inicjatywy (potrzeba 1)!", "error")
            return False
        if self.selected_card not in player.hand:
            self.add_message("Karta nie znajduje się w ręce!", "error")
            return False
        player.hand.remove(self.selected_card)
        player.discard.append(self.selected_card)
        player.initiative -= 1
        self.deselect_card()
        self.add_message("Odrzucono kartę!", "success")
        return True

    def draw_from_discard(self) -> bool:
        player = self.current_player
        if not player.discard:
            self.add_message("Stos odrzuconych jest pusty!", "error")
            return False
        if player.initiative < 5:
            self.add_message("Za mało inicjatywy (potrzeba 5)!", "error")
            return False
        if len(player.hand) >= player.max_hand_size:
            self.add_message("Masz za dużo kart na ręce!", "error")
            return False
        card = player.discard.pop()
        player.hand.append(card)
        player.initiative -= 5
        self.add_message("Wzięto kartę ze stosu odrzuconych!", "success")
        return True

    # ---------- NOWY SYSTEM ATAKU (tylko przyciski) ----------
    def get_attackers(self, attack_range: Optional[int] = None) -> List[Card]:
        """
        Zwraca listę żołnierzy na froncie, którzy mają ekwipunek o zasięgu >= attack_range.
        Jeśli attack_range to None, zwraca wszystkich z jakąkolwiek bronią (zasięg > 0).
        """
        player = self.current_player
        attackers = []
        for card in player.zones.get(Zone.FRONT, []):
            if card.card_type != CardType.SOLDIER:
                continue
            has_weapon = False
            for attached in card.attached_cards:
                if attached.attack_range > 0:
                    if attack_range is None or attached.attack_range >= attack_range:
                        has_weapon = True
                        break
            if has_weapon:
                attackers.append(card)
        return attackers

    def get_defenders(self, target_player: Player) -> List[Card]:
        """Zwraca listę kart przeciwnika w kolejności priorytetu: FRONT, SECOND, BACK, STATE (tereny)."""
        zones_order = [Zone.FRONT, Zone.SECOND, Zone.BACK]
        defenders = []
        for zone in zones_order:
            for card in target_player.zones.get(zone, []):
                if card.card_type == CardType.SOLDIER:
                    defenders.append(card)
            if defenders:
                return defenders
        # Jeśli brak żołnierzy, zwracamy tereny z STATE
        for card in target_player.zones.get(Zone.STATE, []):
            if card.card_type == CardType.TERRAIN:
                defenders.append(card)
        return defenders

    def get_attack_summary(self, zone: Zone) -> Dict[int, Dict[str, float]]:
        """
        Oblicza skumulowaną sumę ataku (wartości oczekiwane) dla każdego zasięgu (1, 2, 3).
        """
        min_range = {Zone.FRONT: 1, Zone.SECOND: 2, Zone.BACK: 3}.get(zone, 1)
        summary = {
            1: {"soft": 0.0, "hard": 0.0, "air": 0.0},
            2: {"soft": 0.0, "hard": 0.0, "air": 0.0},
            3: {"soft": 0.0, "hard": 0.0, "air": 0.0},
        }
        player = self.current_player
        for card in player.zones.get(zone, []):
            if card.card_type != CardType.SOLDIER:
                continue
            for attached in card.attached_cards:
                attack_range = attached.attack_range
                if attack_range < min_range or attack_range > 3:
                    continue
                for r in range(min_range, attack_range + 1):
                    for target_type, value in attached.attack.items():
                        if target_type in summary[r]:
                            summary[r][target_type] += self._value_to_number(value)
        return summary

    def get_attack_zones_for_range(self, attack_range: int, source_zone: Zone) -> Dict[Player, List[Zone]]:
        """
        Zwraca słownik: dla każdego przeciwnika listę stref, które mogą być zaatakowane.
        Uwzględnia priorytet: FRONT → SECOND → BACK → STATE (tylko tereny, jeśli brak żołnierzy).
        Maksymalna liczba stref zależy od źródła:
        - FRONT: attack_range stref
        - SECOND: attack_range - 1 stref
        - BACK: attack_range - 2 stref (minimum 0)
        """
        result = {}
        opponents = [p for p in self.players if p != self.current_player]
        # indeks źródła: FRONT=1, SECOND=2, BACK=3
        source_index = {Zone.FRONT: 1, Zone.SECOND: 2, Zone.BACK: 3}.get(source_zone, 1)
        max_targets = attack_range - (source_index - 1)
        if max_targets <= 0:
            return result  # brak celów

        for target_player in opponents:
            zone_order = [Zone.FRONT, Zone.SECOND, Zone.BACK]
            available_zones = []
            for zone in zone_order:
                defenders = [card for card in target_player.zones.get(zone, []) if card.card_type == CardType.SOLDIER]
                if defenders:
                    available_zones.append(zone)
            if not available_zones:
                # jeśli brak żołnierzy, sprawdź tereny w STATE
                for card in target_player.zones.get(Zone.STATE, []):
                    if card.card_type == CardType.TERRAIN or card.card_type == CardType.BUILDING or card.card_type == CardType.CITY:
                        available_zones.append(Zone.STATE)
                        break
            # wybierz pierwsze max_targets stref
            selected_zones = available_zones[:max_targets]
            if selected_zones:
                result[target_player] = selected_zones
        return result

    def start_attack_with_range(self, attack_range: int, zone: Zone) -> bool:
        """Rozpoczyna tryb ataku z zadanym zasięgiem i ze wskazanej strefy."""
        min_turns = int(self.game_config.get("min_turns", 10))
        if self.turn < min_turns:
            self.add_message(
                f"Ataki dostępne dopiero od tury {min_turns} (obecnie: {self.turn})",
                "error",
            )
            return False
        
        attackers = self.get_attackers_from_zone(attack_range, zone)
        if not attackers:
            self.add_message(f"Brak jednostek z bronią o zasięgu >= {attack_range} w strefie {zone.value}!", "error")
            return False

        cost = self.get_attack_cost(len(attackers))
        if self.current_player.initiative < cost:
            self.add_message(
                f"Za mało inicjatywy na atak: potrzeba {cost}, masz {self.current_player.initiative}",
                "error",
            )
            return False

        targets = self.get_attack_zones_for_range(attack_range, zone)
        has_targets = any(zones for zones in targets.values() if zones)
        if not has_targets:
            self.add_message(f"Brak celów w zasięgu {attack_range} z tej strefy!", "error")
            return False

        self.attack_mode = True
        self.attack_range = attack_range
        self.attack_zones = targets
        self.attack_source_zone = zone
        self.current_attack_cost = cost           # <-- ZAPAMIĘTUJEMY
        self.add_message(f"Atak: koszt {cost} inicjatywy. Wybierz strefę docelową.", "info")
        return True

    def get_attackers_from_zone(self, attack_range: int, zone: Zone) -> List[Card]:
        """Zwraca żołnierzy w danej strefie z bronią o zasięgu >= attack_range."""
        attackers = []
        player = self.current_player
        for card in player.zones.get(zone, []):
            if card.card_type != CardType.SOLDIER:
                continue
            has_weapon = any(a.attack_range >= attack_range for a in card.attached_cards if a.attack_range > 0)
            if has_weapon:
                attackers.append(card)
        return attackers

    def get_attack_zones(self) -> Dict[Player, List[Zone]]:
        return self.attack_zones if self.attack_mode else {}

    def is_attack_mode(self) -> bool:
        return self.attack_mode

    def cancel_attack(self):
        self.attack_mode = False
        self.attack_range = 0
        self.attack_zones = {}
        self.attack_source_zone = None
        self.current_attack_cost = 0

    def perform_attack_on_zone(self, target_player: Player, zone: Zone) -> bool:
        """Wykonuje atak na konkretną strefę przeciwnika."""
        if not self.attack_mode:
            return False
        allowed_zones = self.attack_zones.get(target_player, [])
        if zone not in allowed_zones:
            self.add_message("Ta strefa nie jest dostępna!", "error")
            return False

        defenders = []
        if zone == Zone.STATE:
            for card in target_player.zones.get(Zone.STATE, []):
                if card.card_type in (CardType.TERRAIN, CardType.CITY, CardType.BUILDING):
                    defenders.append(card)
        else:
            for card in target_player.zones.get(zone, []):
                if card.card_type == CardType.SOLDIER:
                    defenders.append(card)

        if not defenders:
            self.add_message("Brak celów w tej strefie!", "error")
            return False

        target = defenders[0]
        if target.card_type == CardType.TERRAIN:
            target_player.zones[Zone.STATE].remove(target)
            self.current_player.zones[Zone.STATE].append(target)
            self.add_message(f"Zdobyto teren: {target.name}!", "success")
            self.cancel_attack()
            return True
        else:
            for z in [Zone.FRONT, Zone.SECOND, Zone.BACK]:
                if target in target_player.zones[z]:
                    target_player.zones[z].remove(target)
                    break
            self.add_message(f"Zabito żołnierza {target.name}!", "success")
            self.cancel_attack()
            return True

    def get_zone_of_card(self, card: Card) -> Optional[Zone]:
        player = self.current_player
        for zone, cards in player.zones.items():
            if card in cards:
                return zone
        return None

    def prepare_attack_preview(self, target_player: Player, target_zone: Zone) -> bool:
        if not self.attack_mode:
            return False
        allowed_zones = self.attack_zones.get(target_player, [])
        if target_zone not in allowed_zones:
            return False

        defenders = []
        if target_zone == Zone.STATE:
            for card in target_player.zones.get(Zone.STATE, []):
                if card.card_type in (CardType.TERRAIN, CardType.CITY, CardType.BUILDING):
                    defenders.append(card)
        else:
            for card in target_player.zones.get(target_zone, []):
                if card.card_type == CardType.SOLDIER:
                    defenders.append(card)

        if not defenders:
            self.add_message("Brak celów w tej strefie!", "error")
            return False

        # Używamy zapamiętanej strefy źródłowej
        attackers = self.get_attackers_from_zone(self.attack_range, self.attack_source_zone)
        if not attackers:
            self.add_message("Brak jednostek zdolnych do ataku!", "error")
            return False

        self.attack_preview_data = {
            "target_player": target_player,
            "target_zone": target_zone,
            "defenders": defenders,
            "attackers": attackers,
            "source_zone": self.attack_source_zone,
            "selected_index": 0,
        }
        return True

    def set_selected_defender(self, index: int):
        """Ustawia indeks wybranego obrońcy."""
        if self.attack_preview_data and 0 <= index < len(self.attack_preview_data["defenders"]):
            self.attack_preview_data["selected_index"] = index

    def get_selected_defender(self) -> Optional[Card]:
        """Zwraca aktualnie wybranego obrońcę."""
        if self.attack_preview_data:
            defenders = self.attack_preview_data["defenders"]
            idx = self.attack_preview_data.get("selected_index", 0)
            if 0 <= idx < len(defenders):
                return defenders[idx]
        return None

    def get_attack_preview_data(self) -> Optional[Dict]:
        return self.attack_preview_data

    # ---------- ROZSTRZYGNIĘCIE WALKI (rzuty) ----------
    def _roll_value(self, value) -> List[Tuple[str, int]]:
        """Rzuca kości dla wartości (int/dict) i zwraca listę (dice_key, wynik)."""
        from dice import roll_each
        if not isinstance(value, dict):
            return []
        dice_key = value.get("dice")
        if not dice_key:
            return []
        count = int(value.get("count", 1))
        faces = roll_each(dice_key, count)
        return [(dice_key, v) for v in faces]

    def _roll_combat(self) -> Optional[Dict]:
        """Wykonuje rzuty kostkami dla aktualnego podglądu ataku."""
        if not self.attack_preview_data:
            return None

        attackers = self.attack_preview_data["attackers"]
        defenders = self.attack_preview_data["defenders"]
        idx = self.attack_preview_data.get("selected_index", 0)
        if not defenders or not (0 <= idx < len(defenders)):
            return None
        defender = defenders[idx]

        # Typ obrońcy
        defender_type = "SOFT"
        for attached in defender.attached_cards:
            if attached.target_type:
                defender_type = attached.target_type.value.upper()
                break
        if defender.target_type:
            defender_type = defender.target_type.value.upper()

        # ---- Rzuty atakujących ----
        attacker_results = []
        for atk in attackers:
            rolls: List[Tuple[str, int]] = []
            for attached in atk.attached_cards:
                val = attached.attack.get(defender_type.lower(), 0) if attached.attack else 0
                rolls.extend(self._roll_value(val))
            total = sum(v for _, v in rolls)
            atk_name = (self.localization.get_card_name(atk.name_key)
                        if atk.name_key else atk.name) or "?"
            attacker_results.append({
                "card": atk, "name": atk_name,
                "rolls": rolls, "total": total,
            })
        total_attack = sum(r["total"] for r in attacker_results)

        # ---- Obrona obrońcy ----
        defender_rolls: List[Tuple[str, int]] = []
        for attached in defender.attached_cards:
            defender_rolls.extend(self._roll_value(attached.defense))
        total_defense = sum(v for _, v in defender_rolls)

        defender_name = (self.localization.get_card_name(defender.name_key)
                        if defender.name_key else defender.name) or "?"
        defender_dies = total_attack > total_defense

        # ---- Kontrataki (obrońca atakuje każdego atakującego) ----
        counter_results = []
        for atk in attackers:
            atk_type = "SOFT"
            for attached in atk.attached_cards:
                if attached.target_type:
                    atk_type = attached.target_type.value.upper()
                    break

            # Atak obrońcy vs obrona atakującego
            def_atk_rolls: List[Tuple[str, int]] = []
            for attached in defender.attached_cards:
                val = attached.attack.get(atk_type.lower(), 0) if attached.attack else 0
                def_atk_rolls.extend(self._roll_value(val))
            def_atk_total = sum(v for _, v in def_atk_rolls)

            # Obrona atakującego
            atk_def_rolls: List[Tuple[str, int]] = []
            for attached in atk.attached_cards:
                atk_def_rolls.extend(self._roll_value(attached.defense))
            atk_def_total = sum(v for _, v in atk_def_rolls)

            is_ranged = any(a.is_ranged_attack for a in atk.attached_cards)
            hit = (not is_ranged) and (def_atk_total > atk_def_total)

            atk_name = (self.localization.get_card_name(atk.name_key)
                        if atk.name_key else atk.name) or "?"
            counter_results.append({
                "attacker": atk,
                "attacker_name": atk_name,
                "defender_attack_rolls": def_atk_rolls,
                "defender_attack_total": def_atk_total,
                "attacker_defense_rolls": atk_def_rolls,
                "attacker_defense_total": atk_def_total,
                "hit": hit,
                "is_ranged": is_ranged,
            })

        return {
            "attacker_results": attacker_results,
            "total_attack": total_attack,
            "defender": defender,
            "defender_name": defender_name,
            "defender_rolls": defender_rolls,
            "total_defense": total_defense,
            "defender_dies": defender_dies,
            "counter_results": counter_results,
            "defender_type": defender_type,
            "target_player": self.attack_preview_data["target_player"],
            "target_zone": self.attack_preview_data["target_zone"],
        }

    def confirm_attack(self) -> bool:
        """Potwierdza atak – wykonuje rzuty i czeka na kliknięcie, by zastosować."""
        if not self.attack_preview_data:
            return False
        result = self._roll_combat()
        if result is None:
            return False
        self.combat_result = result
        return True

    def get_combat_result(self) -> Optional[Dict]:
        return self.combat_result

    def is_combat_result_pending(self) -> bool:
        return self.combat_result is not None

    def _remove_defender_from_owner(self, defender: Card, owner: Player) -> Optional[Zone]:
        """Usuwa obrońcę ze wszystkich stref właściciela. Zwraca strefę lub None."""
        for z in (Zone.FRONT, Zone.SECOND, Zone.BACK, Zone.STATE):
            zone_list = owner.zones.get(z, [])
            if defender in zone_list:
                zone_list.remove(defender)
                return z
        return None

    def apply_combat_result(self) -> bool:
        """Zastosowuje wynik walki (wywoływane po zamknięciu ekranu rzutów)."""
        if not self.combat_result:
            return False
        result = self.combat_result
        self.combat_result = None

        attack_cost = self.current_attack_cost
        print(f"[DEBUG apply] attack_cost={attack_cost}")

        target_player = result["target_player"]
        defender = result["defender"]

        # 1) Kontrataki – giną atakujący trafieni
        for ca in result["counter_results"]:
            if not ca["hit"]:
                continue
            atk = ca["attacker"]
            for z in (Zone.FRONT, Zone.SECOND, Zone.BACK, Zone.STATE):
                if atk in self.current_player.zones.get(z, []):
                    self.current_player.zones[z].remove(atk)
                    break
            self.add_message(f"{ca['attacker_name']} zginął od kontrataku!", "error")

        # 2) Wynik ataku na obrońcę
        if result["defender_dies"]:
            # Karty dołączone do obrońcy → discard właściciela (zawsze)
            attached_cards = list(defender.attached_cards)
            defender.attached_cards.clear()

            if defender.card_type in (CardType.TERRAIN, CardType.CITY):
                # --- PRZEJĘCIE: teren / miasto idzie do atakującego (bez załączników) ---
                self._remove_defender_from_owner(defender, target_player)
                for att in attached_cards:
                    target_player.discard.append(att)
                self.current_player.zones[Zone.STATE].append(defender)
                self.add_message(
                    f"Zdobyto: {result['defender_name']}!", "success"
                )

            elif defender.card_type == CardType.BUILDING:
                # --- ZNISZCZENIE: budynek i jego załączniki do discardu właściciela ---
                self._remove_defender_from_owner(defender, target_player)
                for att in attached_cards:
                    target_player.discard.append(att)
                target_player.discard.append(defender)
                self.add_message(
                    f"Zniszczono budynek: {result['defender_name']}!", "success"
                )

            else:
                # --- ŻOŁNIERZ: znika z gry, jego ekwipunek do discardu ---
                self._remove_defender_from_owner(defender, target_player)
                for att in attached_cards:
                    target_player.discard.append(att)
                self.add_message(f"Zabito {result['defender_name']}!", "success")
        else:
            self.add_message(
                f"Atak nieudany – {result['defender_name']} przetrwał!", "error"
            )

        self.cancel_attack()
        self.cancel_attack_preview()

        # --- pobierz koszt inicjatywy za atak ---
        if attack_cost > 0:
            self.current_player.initiative -= attack_cost
            self.attack_count_this_turn += 1
            self.add_message(
                f"Zapłacono {attack_cost} inicjatywy za atak "
                f"(ataków w turze: {self.attack_count_this_turn})",
                "info",
            )
            self.current_attack_cost = 0

        # 5) Przelicz bilanse po zmianach własności kart
        self.update_player_food_production(target_player)
        self.update_player_food_production(self.current_player)
        # produkcja/iron/steel też mogą się zmienić – przeliczamy
        target_player.production = self.calculate_production_balance(target_player)
        self.current_player.production = self.calculate_production_balance(self.current_player)

        return True

    def cancel_attack_preview(self):
        """Anuluje podgląd ataku."""
        self.current_attack_cost = 0
        self.attack_preview_data = None

    def is_attack_preview_mode(self) -> bool:
        return self.attack_preview_data is not None

    def get_defense_type(self, card: Card) -> Optional[Tuple[str, float]]:
        """Zwraca (target_type, obrona_średnia) lub None."""
        for attached in card.attached_cards:
            defense_val = self._value_to_number(attached.defense)
            if defense_val > 0 and attached.target_type:
                return attached.target_type.value.upper(), defense_val
        return None

    def get_card_attack(self, card: Card) -> Dict[str, float]:
        """
        Zwraca sumaryczny atak karty (z dołączonych broni), jako wartości liczbowe
        (wartości oczekiwane z kości). Używane do wyświetlania 'Atak: SOFT(x) ...'.
        """
        result: Dict[str, float] = {}
        for attached in card.attached_cards:
            if attached.attack:
                for target_type, value in attached.attack.items():
                    v = self._value_to_number(value)
                    if v > 0:
                        result[target_type] = result.get(target_type, 0.0) + v
        return result

    def _value_to_number(self, value) -> float:
        """Zamienia wartość ataku/obrony (int lub dict{dice,count}) na wartość oczekiwaną."""
        if value is None:
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, dict):
            dice_key = value.get("dice")
            count = int(value.get("count", 1))
            if dice_key:
                from dice import expected_value
                return expected_value(dice_key, count)
        return 0.0

    def _dice_value_to_distribution(self, value) -> Dict[int, float]:
        """Zamienia wartość ataku/obrony (int lub dict{dice,count}) na rozkład."""
        from dice import dice_distribution, static_distribution

        if value is None:
            return {0: 1.0}
        if isinstance(value, (int, float)):
            return static_distribution(int(value))
        if isinstance(value, dict):
            dice_key = value.get("dice")
            count = int(value.get("count", 1))
            if dice_key:
                return dice_distribution(dice_key, count)
        return {0: 1.0}

    def _attack_distribution_for_card(self, card: Card, target_type: str) -> Dict[int, float]:
        """Rozkład ataku karty przeciwko danemu typowi celu (z dołączonych broni)."""
        from dice import combined_distribution

        dists = []
        for attached in card.attached_cards:
            val = attached.attack.get(target_type.lower(), 0) if attached.attack else 0
            dists.append(self._dice_value_to_distribution(val))
        if not dists:
            return {0: 1.0}
        return combined_distribution(dists)

    def _defense_distribution(self, card: Card) -> Dict[int, float]:
        """Rozkład obrony karty (z dołączonych broni)."""
        from dice import combined_distribution

        dists = []
        for attached in card.attached_cards:
            dists.append(self._dice_value_to_distribution(attached.defense))
        if not dists:
            return {0: 1.0}
        return combined_distribution(dists)

    def calculate_attack_simulation(self, attackers: List[Card], defender: Card) -> Dict:
        """
        Symultaniczna runda:
        - Suma ataków vs suma obrony → czy obrońca ginie
        - Każdy atakujący niezależnie kontratakowany przez obrońcę
        """
        from dice import (
            combined_distribution, probability_greater, distribution_average
        )

        # Typ obrońcy
        defender_type = "SOFT"
        for attached in defender.attached_cards:
            if attached.target_type:
                defender_type = attached.target_type.value.upper()
                break
        if defender.target_type:
            defender_type = defender.target_type.value.upper()

        # Rozkład ataku (suma)
        attack_dists = []
        attacker_avgs = []
        for atk in attackers:
            dist = self._attack_distribution_for_card(atk, defender_type)
            attack_dists.append(dist)
            attacker_avgs.append(distribution_average(dist))
        attack_dist = combined_distribution(attack_dists)

        # Rozkład obrony
        defense_dist = self._defense_distribution(defender)

        # P(obrońca ginie)
        success_chance = probability_greater(attack_dist, defense_dist)
        attack_avg = distribution_average(attack_dist)
        defense_avg = distribution_average(defense_dist)

        # Kontrataki — ZAWSZE, dla każdego atakującego
        counter_attacks = []
        for atk in attackers:
            atk_type = "SOFT"
            for attached in atk.attached_cards:
                if attached.target_type:
                    atk_type = attached.target_type.value.upper()
                    break

            # Atak obrońcy vs obrona atakującego
            def_attack_dists = []
            for attached in defender.attached_cards:
                val = attached.attack.get(atk_type.lower(), 0) if attached.attack else 0
                dist = self._dice_value_to_distribution(val)
                def_attack_dists.append(dist)
            def_attack_dist = (combined_distribution(def_attack_dists)
                            if def_attack_dists else {0: 1.0})

            atk_defense_dist = self._defense_distribution(atk)

            hit_chance = probability_greater(def_attack_dist, atk_defense_dist)
            is_ranged = any(a.is_ranged_attack for a in atk.attached_cards)
            total_hit_chance = 0.0 if is_ranged else hit_chance  # ZAWSZE, bez warunkowania

            atk_name = self.localization.get_card_name(atk.name_key) if atk.name_key else atk.name

            counter_attacks.append({
                "attacker_name": atk_name,
                "attacker_type": atk_type,
                "counter_chance": 1.0,           # kontratak zawsze następuje
                "hit_chance": hit_chance,         # P(trafienie)
                "total_hit_chance": total_hit_chance,
                "is_ranged": is_ranged,
                "attacker_defense_avg": distribution_average(atk_defense_dist),
                "counter_attack_avg": distribution_average(def_attack_dist),
            })

        return {
            "success_chance": success_chance,
            "attack_avg": attack_avg,
            "defense_avg": defense_avg,
            "attacker_avgs": attacker_avgs,
            "defender_type": defender_type,
            "counter_attacks": counter_attacks,
        }

    def load_game_config(self) -> dict:
        """Wczytuje defines/game.lua.

        Plik zwraca kolejno:
            game_start, atack, discard_card, card_value, victory, min_turns, max_turns
        """
        try:
            import lupa
            from lupa import LuaRuntime
            lua = LuaRuntime(unpack_returned_tuples=True)
            with open("defines/game.lua", "r", encoding="utf-8") as f:
                result = lua.execute(f.read())

            values = list(result) if isinstance(result, tuple) else [result]
            # dopełnij do 7 pustymi wartościami
            while len(values) < 7:
                values.append({})
            game_start, atack, discard_card, card_value, victory, min_turns, max_turns = values[:7]

            flat = {}
            for k, v in dict(game_start or {}).items():
                flat[str(k)] = v
            flat["atack"] = dict(atack or {})
            flat["discard_card"] = dict(discard_card or {})
            flat["card_value"] = dict(card_value or {})
            flat["victory"] = dict(victory or {})
            flat["min_turns"] = int(min_turns) if not isinstance(min_turns, dict) else 10
            flat["max_turns"] = int(max_turns) if not isinstance(max_turns, dict) else 50
            return flat

        except Exception as e:
            print(f"Nie udało się wczytać defines/game.lua: {e}, używam domyślnych.")
            import traceback
            traceback.print_exc()
            return {
                "atack": {
                    "base_cost": 10, "cost_per_unit": 3,
                    "next_attack_cost_decrease": 5, "min_initiative_cost": 5,
                },
                "discard_card": {"initiative_cost": 1},
                "card_value": {
                    "TERRAIN": 1, "WORKER": 1, "SOLDIER": 2,
                    "WEAPON": 3, "BUILDING": 3, "CITY": 3,
                    "TANK": 5, "PLANE": 5, "ARTILLERY": 5,
                    "VEHICLE": 3, "CAR": 2,
                },
                "victory": {"advantage_threshold": 0.75},
                "min_turns": 10,
                "max_turns": 50,
            }

    def set_view(self, view):
        self.view = view

    # ---------- WARTOŚĆ KART I PRZEWAGA ----------
    # Domyślne wagi – używane gdy typ nie ma wpisu w Lua
    _CARD_VALUE_DEFAULTS = {
        "TERRAIN": 1, "WORKER": 1,
        "SOLDIER": 2, "CAR": 2,
        "WEAPON": 3, "BUILDING": 3, "CITY": 3, "VEHICLE": 3,
        "TANK": 5, "PLANE": 5, "ARTILLERY": 5,
    }

    def get_card_value(self, card: Card) -> int:
        """Wartość pojedynczej karty (na podstawie typu)."""
        cfg = self.game_config.get("card_value", {}) or {}
        key = card.card_type.value
        if key in cfg:
            return int(cfg[key])
        return int(self._CARD_VALUE_DEFAULTS.get(key, 1))

    def get_player_strength(self, player: Player) -> int:
        """Suma wartości wszystkich kart gracza na planszy (w strefach) + załączniki."""
        total = 0
        for zone_cards in player.zones.values():
            for card in zone_cards:
                total += self.get_card_value(card)
                for att in card.attached_cards:
                    total += self.get_card_value(att)
        return total

    def get_all_strengths(self) -> Dict[Player, int]:
        """Słownik {Player: suma_wartości}."""
        return {p: self.get_player_strength(p) for p in self.players}

    def check_victory(self) -> Optional[Player]:
        """Sprawdza warunki zwycięstwa.

        1) Przed `min_turns` – zwycięstwo nie jest sprawdzane.
        2) Po `max_turns` – koniec gry: wygrywa gracz z największą liczbą punktów.
        3) W międzyczasie – zwycięstwo przez przewagę > threshold.
        """
        if self.victor:
            return self.victor

        min_turns = int(self.game_config.get("min_turns", 10))
        max_turns = int(self.game_config.get("max_turns", 50))

        # 2) Twardy limit tur
        if self.turn >= max_turns:
            strengths = self.get_all_strengths()
            if strengths:
                best = max(strengths, key=lambda p: strengths[p])
                self.victor = best
                self.add_message(
                    f"Koniec gry (tura {self.turn}). "
                    f"Zwycięstwo: {best.name} ({strengths[best]} pkt)",
                    "success",
                )
                return self.victor
            return None

        # 1) Za wcześnie
        if self.turn < min_turns:
            return None

        # 3) Zwycięstwo przez przewagę
        strengths = self.get_all_strengths()
        total = sum(strengths.values())
        if total <= 0:
            return None
        threshold = float(
            (self.game_config.get("victory", {}) or {}).get(
                "advantage_threshold", 0.75
            )
        )
        for p, s in strengths.items():
            share = s / total
            if share > threshold:
                self.victor = p
                self.add_message(
                    f"ZWYCIĘSTWO: {p.name}! Przewaga {share*100:.1f}%",
                    "success",
                )
                return p
        return None