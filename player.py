# player.py
import random
from typing import List, Optional, Dict
from card import Card, Zone

class Player:
    def __init__(self, name: str, deck: List[Card] = None, config: dict = None):
        self.name = name
        self.hand: List[Card] = []
        self.deck: List[Card] = deck if deck is not None else []
        self.discard: List[Card] = []

        # Domyślne wartości (jeśli brak config)
        if config is None:
            config = {}
        
        self.initiative = config.get("initiative", 25)
        self.max_hand_size = config.get("max_hand_size", 7)
        self.max_initiative = config.get("max_initiative", 30)
        
        # Zasoby
        self.initial_food_production = config.get("food_production", 10)
        self.initial_production = config.get("production", 0)
        self.food_production = 0
        self.production = 0
        self.steal = config.get("steal", 0)
        self.logistics = config.get("logistics", 0)
        self.oil_production = config.get("oil_production", 0)
        self.iron_production = config.get("iron_production", 0)
        self.fuel_production = config.get("fuel_production", 0)
        
        self.zones: Dict[Zone, List[Card]] = {
            Zone.FRONT: [],
            Zone.SECOND: [],
            Zone.BACK: [],
            Zone.STATE: []
        }

    def play_card_to_zone(self, card: Card, zone: Zone) -> bool:
        if card not in self.hand:
            return False
        if zone not in self.zones:
            return False
        if not card.can_be_played_in_zone(zone):
            return False
        self.hand.remove(card)
        self.zones[zone].append(card)
        return True

    def draw_card(self) -> Optional[Card]:
        """Dobiera jedną kartę z talii do ręki."""
        if not self.deck:
            return None
        if len(self.hand) >= self.max_hand_size:
            return None
        card = self.deck.pop()
        self.hand.append(card)
        return card
    
    def draw_initial_hand(self, count: int = 5):
        """Dobiera początkowe karty."""
        for _ in range(min(count, self.max_hand_size)):
            if not self.deck:
                break
            self.draw_card()
    
    def get_draw_cost(self) -> int:
        """Zwraca koszt dobrania karty (1 + liczba kart powyżej 5 w ręce)."""
        return 1 + max(0, len(self.hand) - 5)

    def discard_card(self, card: Card):
        """Odrzuca kartę z ręki na stos odrzuconych."""
        if card in self.hand:
            self.hand.remove(card)
            self.discard.append(card)

    def attach_card_to_target(self, card_from_hand: Card, target_card: Card) -> bool:
        """Dołącza kartę z ręki do target_card (która musi być w strefie)."""
        if card_from_hand not in self.hand:
            return False
        # Sprawdź, czy target_card jest w którejś strefie
        found = False
        for zone_cards in self.zones.values():
            if target_card in zone_cards:
                found = True
                break
        if not found:
            return False
        if not card_from_hand.can_attach_to(target_card):
            return False
        self.hand.remove(card_from_hand)
        target_card.attach(card_from_hand)
        return True

    def get_all_cards(self, include_attached: bool = True) -> List[Card]:
        """
        Zwraca wszystkie karty gracza we wszystkich strefach.
        Jeśli include_attached=True, zwraca również karty dołączone do innych kart.
        """
        result = []
        for zone_cards in self.zones.values():
            for card in zone_cards:
                result.append(card)
                if include_attached:
                    result.extend(card.attached_cards)
        return result
    
    def shuffle_deck(self):
        """Tasuje talię."""
        random.shuffle(self.deck)