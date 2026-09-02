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

        self.view = None  # referencja do widoku
        
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

        if attached_card.cost_initiative > player.initiative:
            return False

        if target_card.max_workers > 0:
            worker_count = sum(1 for c in target_card.attached_cards if c.card_type == CardType.WORKER)
            if worker_count >= target_card.max_workers:
                return False
        
        if target_card.card_type == CardType.SOLDIER:
            has_same_type = any(c.card_type == attached_card.card_type for c in target_card.attached_cards)
            if has_same_type:
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

    def get_attack_summary(self) -> Dict[int, Dict[str, int]]:
        """Oblicza skumulowaną sumę ataku dla każdego zasięgu (1, 2, 3).
        Dla zasięgu 1: wszystkie bronie z range >= 1.
        Dla zasięgu 2: wszystkie bronie z range >= 2.
        Dla zasięgu 3: wszystkie bronie z range >= 3.
        """
        summary = {
            1: {"soft": 0, "hard": 0, "air": 0},
            2: {"soft": 0, "hard": 0, "air": 0},
            3: {"soft": 0, "hard": 0, "air": 0}
        }
        player = self.current_player
        for card in player.zones.get(Zone.FRONT, []):
            if card.card_type != CardType.SOLDIER:
                continue
            for attached in card.attached_cards:
                attack_range = attached.attack_range
                if attack_range <= 0 or attack_range > 3:
                    continue
                # Dla każdego zasięgu r, jeśli attack_range >= r, dodajemy wartość
                for r in range(1, attack_range + 1):
                    for target_type, value in attached.attack.items():
                        if target_type in summary[r]:
                            summary[r][target_type] += value
        return summary

    def get_attack_zones_for_range(self, attack_range: int) -> Dict[Player, List[Zone]]:
        """
        Zwraca słownik: dla każdego przeciwnika listę stref, które mogą być zaatakowane.
        Uwzględnia priorytet: FRONT → SECOND → BACK → STATE (tylko tereny, jeśli brak żołnierzy).
        attack_range określa liczbę najbliższych stref z żołnierzami (1, 2 lub 3).
        Jeśli attack_range=1, wybiera pierwszą niepustą strefę (FRONT, jeśli nie ma to SECOND, itd.).
        Jeśli attack_range=2, wybiera dwie pierwsze niepuste strefy.
        Jeśli attack_range>=3, wybiera wszystkie strefy (w tym STATE tereny, jeśli brak żołnierzy).
        """
        result = {}
        opponents = [p for p in self.players if p != self.current_player]
        for target_player in opponents:
            # Kolejność stref: od najbliższej do najdalszej
            zone_order = [Zone.FRONT, Zone.SECOND, Zone.BACK]
            # Zbierz strefy z żołnierzami (tylko te, które mają co najmniej jednego żołnierza)
            available_zones = []
            for zone in zone_order:
                defenders = [card for card in target_player.zones.get(zone, []) if card.card_type == CardType.SOLDIER]
                if defenders:
                    available_zones.append(zone)
            # Jeśli nie ma żołnierzy w żadnej strefie, weź STATE (tereny) jako ostatnią możliwość
            if not available_zones:
                # Sprawdź, czy są tereny w STATE
                for card in target_player.zones.get(Zone.STATE, []):
                    if card.card_type == CardType.TERRAIN:
                        available_zones.append(Zone.STATE)
                        break
            # Wybierz strefy w zależności od zasięgu
            if attack_range == 1:
                # Tylko pierwsza niepusta strefa
                selected_zones = available_zones[:1]
            elif attack_range == 2:
                # Dwie pierwsze niepuste strefy
                selected_zones = available_zones[:2]
            else:  # attack_range >= 3
                # Wszystkie dostępne strefy
                selected_zones = available_zones
            result[target_player] = selected_zones
        return result

    def start_attack_with_range(self, attack_range: int) -> bool:
        """Rozpoczyna tryb ataku z zadanym zasięgiem."""
        if not self.get_attackers(attack_range):
            self.add_message(f"Brak jednostek z bronią o zasięgu >= {attack_range}!", "error")
            return False
        targets = self.get_attack_zones_for_range(attack_range)
        has_targets = any(zones for zones in targets.values() if zones)
        if not has_targets:
            self.add_message(f"Brak celów w zasięgu {attack_range}!", "error")
            return False
        self.attack_mode = True
        self.attack_range = attack_range
        self.attack_zones = targets
        self.add_message("Wybierz strefę docelową (podświetlona)", "info")
        return True

    def get_attack_zones(self) -> Dict[Player, List[Zone]]:
        return self.attack_zones if self.attack_mode else {}

    def is_attack_mode(self) -> bool:
        return self.attack_mode

    def cancel_attack(self):
        self.attack_mode = False
        self.attack_range = 0
        self.attack_zones = {}

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
                if card.card_type == CardType.TERRAIN:
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
        """Przygotowuje dane do podglądu ataku."""
        if not self.attack_mode:
            return False
        allowed_zones = self.attack_zones.get(target_player, [])
        if target_zone not in allowed_zones:
            return False

        defenders = []
        if target_zone == Zone.STATE:
            for card in target_player.zones.get(Zone.STATE, []):
                if card.card_type == CardType.TERRAIN:
                    defenders.append(card)
        else:
            for card in target_player.zones.get(target_zone, []):
                if card.card_type == CardType.SOLDIER:
                    defenders.append(card)

        if not defenders:
            self.add_message("Brak celów w tej strefie!", "error")
            return False

        # Używamy zapamiętanego zasięgu do wyboru atakujących
        attackers = self.get_attackers(self.attack_range)
        if not attackers:
            self.add_message("Brak jednostek zdolnych do ataku!", "error")
            return False

        self.attack_preview_data = {
            "target_player": target_player,
            "target_zone": target_zone,
            "defenders": defenders,
            "attackers": attackers,
        }
        return True

    def get_attack_preview_data(self) -> Optional[Dict]:
        return self.attack_preview_data

    def confirm_attack(self) -> bool:
        """Potwierdza atak – wykonuje go na podstawie danych podglądu."""
        if not self.attack_preview_data:
            return False
        target_player = self.attack_preview_data["target_player"]
        target_zone = self.attack_preview_data["target_zone"]
        self.attack_preview_data = None
        return self.perform_attack_on_zone(target_player, target_zone)

    def cancel_attack_preview(self):
        """Anuluje podgląd ataku."""
        self.attack_preview_data = None

    def is_attack_preview_mode(self) -> bool:
        return self.attack_preview_data is not None

    def get_defense_type(self, card: Card) -> Optional[str]:
        """
        Zwraca typ obrony karty na podstawie jej dołączonych kart (bronie).
        Zwraca pierwszy target_type z karty, która ma defense > 0.
        """
        for attached in card.attached_cards:
            if attached.defense > 0 and attached.target_type and len(attached.target_type) > 0:
                return attached.target_type[0].upper(), attached.defense
        return None

    def get_card_attack(self, card: Card) -> Dict[str, int]:

        for attached in card.attached_cards:
            if attached.attack and len(attached.attack) > 0:
                return attached.attack
        return {}

    def load_game_config(self) -> dict:
        try:
            import lupa
            from lupa import LuaRuntime
            lua = LuaRuntime(unpack_returned_tuples=True)
            with open("defines/game.lua", "r", encoding="utf-8") as f:
                result = lua.execute(f.read())
            if result is not None:
                return dict(result)
            else:
                return {}
        except Exception as e:
            print(f"Nie udało się wczytać defines/game.lua: {e}, używam domyślnych wartości.")
            return {}

    def set_view(self, view):
        self.view = view