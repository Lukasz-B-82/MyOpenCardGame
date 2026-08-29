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
            player.shuffle_deck()
            player.draw_initial_hand(self.game_config.get("initial_hand", 5))
            self.players.append(player)
        
        self.current_player_index = 0
        self.turn = 1
        
        # Stan gry
        self.selected_card: Optional[Card] = None
        self.allowed_zones: List[Zone] = []
        self.attachment_targets: List[Tuple[Card, Zone]] = []
        self.move_mode: bool = False          # czy jesteśmy w trybie przenoszenia
        self.move_targets: List[Zone] = []    # dozwolone strefy do przeniesienia
        self.selected_soldier: Optional[Card] = None  # żołnierz do przeniesienia

        self.view = None  # referencja do widoku
        
    @property
    def current_player(self) -> Player:
        return self.players[self.current_player_index]

    def select_soldier_for_move(self, card: Card):
        """Rozpoczyna tryb przenoszenia żołnierza."""
        if card.card_type != CardType.SOLDIER:
            self.add_message("Tylko żołnierze mogą być przenoszeni!", "error")
            return False
        # Sprawdź, czy żołnierz jest w którejś strefie
        player = self.current_player
        found_zone = None
        for zone, cards in player.zones.items():
            if card in cards:
                found_zone = zone
                break
        if found_zone is None:
            self.add_message("Żołnierz nie znajduje się w żadnej strefie!", "error")
            return False

        # Oblicz dostępne strefy docelowe
        targets = []
        for zone in [Zone.BACK, Zone.SECOND, Zone.FRONT]:
            if zone == found_zone:
                continue
            # Koszt logistyki: BACK→SECOND = 1, BACK→FRONT = 2, SECOND→FRONT = 1
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
        """Przenosi zaznaczonego żołnierza do strefy docelowej."""
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

        # Koszt logistyki
        cost_log = self._get_move_logistics_cost(from_zone, zone)
        if player.logistics < cost_log:
            self.add_message(f"Za mało logistyki! Potrzeba: {cost_log}", "error")
            return False
        if player.initiative < 1:
            self.add_message("Za mało inicjatywy! Potrzeba: 1", "error")
            return False

        # Przenieś żołnierza wraz z dołączonymi kartami
        player.zones[from_zone].remove(self.selected_soldier)
        player.zones[zone].append(self.selected_soldier)
        player.logistics -= cost_log
        player.initiative -= 1

        # Wyczyść tryb przenoszenia
        self.selected_soldier = None
        self.move_mode = False
        self.move_targets = []
        self.add_message(f"Przeniesiono żołnierza do {zone.value}", "success")
        return True

    def _get_move_logistics_cost(self, from_zone: Zone, to_zone: Zone) -> int:
        """Zwraca koszt logistyki przeniesienia żołnierza między strefami."""
        # BACK → SECOND = 1, BACK → FRONT = 2, SECOND → FRONT = 1
        if from_zone == Zone.BACK and to_zone == Zone.SECOND:
            return 1
        if from_zone == Zone.BACK and to_zone == Zone.FRONT:
            return 2
        if from_zone == Zone.SECOND and to_zone == Zone.FRONT:
            return 1
        # Przenoszenie w drugą stronę (cofanie) – można dodać później
        return 999  # na razie zabraniamy cofania
    
    def can_attach_to_card(self, attached_card: Card, target_card: Card) -> bool:
        """
        Sprawdza, czy attached_card może być dołączona do target_card,
        uwzględniając limity:
        - max_workers (dla terenów, miast, budynków)
        - unikalność typów dla żołnierzy (tylko jedna karta z danego typu)
        """
        # 1. Sprawdź podstawową możliwość dołączenia
        if not attached_card.can_attach_to(target_card):
            return False

        player = self.current_player
        if (attached_card.cost_production > 0 and player.production < attached_card.cost_production):
            return False
        
        if (attached_card.food_consumption > 0 
            and player.food_production < attached_card.food_consumption 
            and not (attached_card.card_type == CardType.WORKER and target_card.food_production > 0)):
            return False

        if (attached_card.cost_initiative > player.initiative):
            return False

        if target_card.max_workers > 0:
            worker_count = sum(1 for c in target_card.attached_cards if c.card_type == CardType.WORKER)
            if worker_count >= target_card.max_workers:
                return False
        
        # 3. Limit dla żołnierzy – tylko jedna karta z danego typu
        if target_card.card_type == CardType.SOLDIER:
            has_same_type = any(c.card_type == attached_card.card_type for c in target_card.attached_cards)
            if has_same_type:
                return False
        
        # Wszystkie warunki spełnione
        return True
    
    def select_card(self, card: Card) -> bool:
        if card not in self.current_player.hand:
            return False
        self.selected_card = card
        self.allowed_zones = []
        self.attachment_targets = []

        # Sprawdź strefy do zagrania
        for zone in Zone:
            if card.can_be_played_in_zone(zone):
                self.allowed_zones.append(zone)

        # Sprawdź cele do dołączenia (używając metody can_attach_to_card)
        player = self.current_player
        for zone in Zone:
            for target_card in player.zones.get(zone, []):
                if self.can_attach_to_card(card, target_card):
                    self.attachment_targets.append((target_card, zone))

        return True

    def attach_card_to_target(self, target_card: Card) -> bool:
        if self.selected_card is None:
            return False
        
        # Ponownie sprawdź, czy dołączenie jest możliwe (na wypadek zmian)
        if not self.can_attach_to_card(self.selected_card, target_card):
            return False
        
        # Sprawdź, czy target_card jest w attachment_targets (dodatkowe zabezpieczenie)
        if not any(t == target_card for t, _ in self.attachment_targets):
            return False

        player = self.current_player

        if (self.selected_card.cost_initiative > player.initiative):
            return False

        if player.attach_card_to_target(self.selected_card, target_card):
            self.update_player_food_production(player)
            #player.oil_production, player.fuel_production, player.iron_production, player.steal, player.logistics = self.calculate_resurects_balance(player)
            if self.selected_card.card_type == CardType.WORKER:
                self.add_message(f"Dołączam kartę: {CardType.WORKER} i zwiększam produkcję z karty: {target_card.card_type.name}", "info")
                if (target_card.production > 0):
                    player.production += target_card.production
                if (target_card.fuel_production > 0 and player.oil_production > 0):
                    player.fuel_production += min(target_card.fuel_production, player.oil_production)
                    player.oil_production -= min(target_card.fuel_production, player.oil_production)
                if (target_card.oil_production > 0):
                    player.oil_production += target_card.oil_production
                if (target_card.iron_ore_production > 0):
                    player.iron_production += target_card.iron_ore_production
                if (target_card.steal_production > 0 and player.iron_production > 0):
                    player.steal += min(target_card.steal_production, player.iron_production)
                    player.iron_production -= min(target_card.steal_production, player.iron_production)
                if (self.selected_card.fuel_consumption > 0):
                    player.fuel_production -= self.selected_card.fuel_consumption 
            
            if (self.selected_card.cost_production > 0):
                player.production -= self.selected_card.cost_production
            player.initiative -= self.selected_card.cost_initiative
            self.add_message(
                f"Dołączono kartę typu: {self.selected_card.card_type.name} do karty typu {target_card.card_type.name}", "success")
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
        # Wyczyść również tryb przenoszenia
        self.selected_soldier = None
        self.move_mode = False
        self.move_targets = []

    def get_move_targets(self) -> List[Zone]:
        return self.move_targets if self.move_mode else []

    def is_move_mode(self) -> bool:
        return self.move_mode
    
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

        if (card.fuel_consumption > player.fuel_production):
            self.add_message(f"Za mało paliwa: {card.fuel_consumption}", "error")
            return False
        
        # Sprawdź wymagania
        if not self.check_requirements(card, player):
            return False

         # Sprawdź koszt produkcji
        if card.cost_production > 0:
            if player.production < card.cost_production:
                self.add_message(f"Za mało produkcji: {card.cost_production}", "error")
                return False  # brak produkcji
            
        
        if player.play_card_to_zone(card, zone):
            self.update_player_food_production(player)
            player.initiative -= card.cost_initiative
            player.production -= card.cost_production
            self.add_message(f"Zagrano kartę typu {self.selected_card.card_type.name} do strefy {zone.name}", "success")
            self.add_message(f"Koszt inicjatywy: {card.cost_initiative}", "info")
            if (card.logistics > 0):
                player.logistics += card.logistics
                self.add_message(f"Zwiększono logistykę +{card.logistics}", "info")
            if (card.fuel_consumption > 0):
                player.fuel_production -= card.fuel_consumption
                self.add_message(f"Zwiększono zużycie paliwa +{card.fuel_consumption}", "info")
            self.deselect_card()
            return True
        return False
    
    def draw_card(self) -> bool:
        player = self.current_player
        cost = player.get_draw_cost()
        if player.initiative < cost:
            self.add_message(f"Za mało inicjatyey: {cost}", "error")
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

    def start_turn(self, player: Player):
        """Wykonuje czynności na początku tury gracza."""
        # 1. Zbierz produkcję (kumulacja)
        self.update_player_production(player, add=True)
        iron, steel = self.calculate_resurects_production(player)
        player.iron_production = iron
        player.steal += steel
        # 2. Zbierz żywność (tylko wyświetl, nie kumuluj)
        self.update_player_food_production(player)
        player.initiative += self.add_player_initiative(player)
        player.initiative = min(player.initiative, player.max_initiative)

    def add_player_initiative(self, player: Player):
        initiative = 0
        for card in player.zones.get(Zone.STATE, []):
            initiative += card.initiative
            for attached_card in card.attached_cards:
                initiative += attached_card.initiative

        for card in player.zones.get(Zone.BACK, []):
            initiative += card.initiative
            for attached_card in card.attached_cards:
                initiative += attached_card.initiative

        for card in player.zones.get(Zone.SECOND, []):
            initiative += card.initiative
            for attached_card in card.attached_cards:
                initiative += attached_card.initiative

        for card in player.zones.get(Zone.FRONT, []):
            initiative += card.initiative
            for attached_card in card.attached_cards:
                initiative += attached_card.initiative

        print(f"add_player_initiative: {initiative}")
        return initiative
    
    def get_allowed_zones(self) -> List[Zone]:
        if self.selected_card is None:
            return []
        return self.selected_card.allowed_zones

    def count_cards_in_zone(self, player: Player, zone: Zone, card_type: CardType, include_attached: bool = True) -> int:
        """Liczy karty danego typu w strefie (uwzględniając załączniki, jeśli include_attached=True)."""
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
        """Sprawdza, czy wszystkie wymagania karty są spełnione."""
        if not card.requirements:
            return True
        for zone, req_type, req_count in card.requirements:
            count = self.count_cards_in_zone(player, zone, req_type)
            if count < req_count:
                return False
        return True

    def get_requirements_status(self, card: Card, player: Player) -> List[Tuple[bool, str]]:
        """
        Zwraca listę krotek (spełnione: bool, opis: str) dla każdego wymagania.
        """
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

    def calculate_resurects_balance(self, player: Player):
        oil = 0
        iron = 0
        fuel = 0
        steel = 0
        logistics = 0

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

        for card in player.zones.get(Zone.STATE, []):
            if card.logistics > 0:
                logistics += card.logistics

        for card in player.get_all_cards(include_attached=True):
            if card.fuel_consumption > 0:
                fuel -= card.fuel_consumption

        return oil, fuel, iron, steel, logistics

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
        """
        Oblicza bilans żywności dla gracza.
        Wzór: startowa_produkcja + suma(food_production * liczba_robotników_na_karcie) - suma(food_consumption)
        """
        # 1. Startowa produkcja (z configu)
        total_food = player.initial_food_production
        
        # 2. Produkcja z kart w strefie STATE (tereny, miasta, budynki)
        for card in player.zones.get(Zone.STATE, []):
            # Każda karta ma food_production (np. TERRAIN ma 4)
            if card.food_production > 0:
                # Liczymy robotników dołączonych do tej karty
                workers_attached = sum(1 for c in card.attached_cards if c.card_type == CardType.WORKER)
                total_food += card.food_production * workers_attached
        
        # 3. Konsumpcja żywności (wszystkie karty gracza we wszystkich strefach)
        total_consumption = 0
        for zone_cards in player.zones.values():
            for card in zone_cards:
                # Każda karta ma food_consumption (np. SOLDIER, WORKER)
                total_consumption += card.food_consumption
                # Załączniki też mogą mieć konsumpcję
                for attached in card.attached_cards:
                    total_consumption += attached.food_consumption
        
        # 4. Bilans
        return total_food - total_consumption

    def update_player_food_production(self, player: Player):
        """Aktualizuje pole food_production gracza na podstawie bilansu."""
        player.food_production = self.calculate_food_balance(player)

    def calculate_production_balance(self, player: Player) -> int:
        """
        Oblicza bilans produkcji dla gracza.
        Wzór: initial_production + suma(production * liczba_robotników_na_karcie) - suma(cost_production)
        """
        # 1. Startowa produkcja (z configu, domyślnie 0)
        total_production = player.initial_production
        
        # 2. Produkcja z kart w strefie STATE (fabryki, budynki)
        for card in player.zones.get(Zone.STATE, []):
            if card.production > 0:
                # Liczymy robotników dołączonych do tej karty
                workers_attached = sum(1 for c in card.attached_cards if c.card_type == CardType.WORKER)
                # Tylko jeśli są robotnicy, karta produkuje
                if workers_attached > 0:
                    total_production += card.production * workers_attached
        
        return total_production 

    def update_player_production(self, player: Player, add=False):
        """Aktualizuje pole production gracza (kumulacja)."""
        balance = self.calculate_production_balance(player)
        if add:
            player.production += balance
            self.add_message(f"Dodano produkcję: {balance}", "info")

        print(f"update_player_production(add={add}) {player.production}")

    def load_game_config(self) -> dict:
        try:
            import lupa
            from lupa import LuaRuntime
            lua = LuaRuntime(unpack_returned_tuples=True)
            with open("defines/game.lua", "r", encoding="utf-8") as f:
                result = lua.execute(f.read())
            if result is not None:
                # result to tabela Lua – konwertujemy na dict
                return dict(result)
            else:
                return {}
        except Exception as e:
            print(f"Nie udało się wczytać defines/game.lua: {e}, używam domyślnych wartości.")
            return {}

    def set_view(self, view):
        self.view = view