# game_ai/base.py
"""Abstrakcyjny interfejs AI.

Kluczowa zasada: AI rozmawia TYLKO z GameLogic.
Nigdy nie dotyka pygame, ekranu ani view.
Dzięki temu ten sam AI działa headless (trening) i w oknie (gra).

Klasa BaseAI zapewnia:
  * enumerację legalnych akcji (na podstawie stanu GameLogic),
  * wykonanie wybranej akcji (przez publiczne metody GameLogic),
  * snapshot stanu (dict) – na potrzeby logów i przyszłej sieci neuronowej,
  * pętlę tury (take_turn), która woła pick_action() w podklasach.

Podklasa musi zaimplementować tylko pick_action(actions, state).
"""
from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any


class BaseAI(ABC):
    name: str = "base"
    version: str = "0.0"

    def __init__(self, logic, **kwargs):
        self.logic = logic
        # Bufor decyzji bieżącej tury – GameLogger go opróżnia.
        self.decision_buffer: List[Dict[str, Any]] = []
        # Wyniki ostatniej decyzji – wypełniane w pick_action().
        self.last_scores: Dict[str, float] = {}
        self.last_reason: str = ""

    # ------------------------------------------------------------------
    # GŁÓWNA METODA – do nadpisania w podklasach
    # ------------------------------------------------------------------
    @abstractmethod
    def pick_action(self, actions: List[Tuple], state: Dict) -> Tuple:
        """Zwraca wybraną akcję. Powinno ustawić self.last_scores."""
        ...

    # ------------------------------------------------------------------
    # PĘTLA TURY – wspólna dla wszystkich AI
    # ------------------------------------------------------------------
    def take_turn(self, max_actions: int = 40, on_action=None):
        """Wykonuje akcje, dopóki nie skończy się inicjatywa lub limit.

        on_action(action) – opcjonalny callback wołany po każdej akcji
        (używany przez widok, żeby narysować klatkę i zrobić pauzę).
        """
        for step in range(max_actions):
            actions = self.enumerate_actions()
            if not actions:
                break
            state = self.encode_state()
            chosen = self.pick_action(actions, state)

            self.decision_buffer.append({
                "step": step,
                "state": state,
                "legal_actions": [self.action_to_str(a) for a in actions],
                "chosen": self.action_to_str(chosen),
                "scores": dict(self.last_scores),
                "reason": self.last_reason,
            })

            self.execute(chosen)
            if on_action:
                on_action(chosen)
            if chosen[0] == "end_turn":
                break

    # ------------------------------------------------------------------
    # ENUMERACJA LEGALNYCH AKCJI
    # ------------------------------------------------------------------
    def enumerate_actions(self) -> List[Tuple]:
        """Zbiera wszystkie legalne akcje z GameLogic.

        Zwraca listę krotek, gdzie pierwszy element to typ akcji:
            ("play",   card, zone)
            ("attach", card, target)
            ("move",   soldier, dst_zone)
            ("attack", range, src_zone, enemy_player, dst_zone)
            ("draw",)
            ("end_turn",)
        """
        from card import Zone, CardType
        logic = self.logic
        p = logic.current_player
        actions: List[Tuple] = []

        # 1) zagranie karty z ręki
        for card in list(p.hand):
            if not card.allowed_zones:
                continue
            if card.cost_initiative > p.initiative:
                continue
            # nowe: koszty zasobowe – dokładnie te same warunki co w play_card_to_zone
            if card.food_consumption > p.food_production:
                continue
            if card.fuel_consumption > p.fuel_production:
                continue
            if card.cost_production > 0 and p.production < card.cost_production:
                continue
            if not logic.check_requirements(card, p):
                continue
            for zone in card.allowed_zones:
                actions.append(("play", card, zone))

        # 2) dołączenie karty z ręki do celu w strefie
        for card in list(p.hand):
            for zone in (Zone.FRONT, Zone.SECOND, Zone.BACK, Zone.STATE):
                for target in p.zones.get(zone, []):
                    if logic.can_attach_to_card(card, target):
                        actions.append(("attach", card, target))

        # 3) ruch żołnierza (tylko zmiana strefy)
        for zone in (Zone.BACK, Zone.SECOND, Zone.FRONT):
            for soldier in p.zones.get(zone, []):
                if soldier.card_type != CardType.SOLDIER:
                    continue
                for dst in (Zone.BACK, Zone.SECOND, Zone.FRONT):
                    if dst == zone:
                        continue
                    cost = logic._get_move_logistics_cost(zone, dst)
                    if p.logistics >= cost and p.initiative >= 1:
                        actions.append(("move", soldier, dst))

        # 4) ataki – dla każdego zasięgu i strefy źródłowej
        for atk_range in (1, 2, 3):
            for src_zone in (Zone.FRONT, Zone.SECOND, Zone.BACK):
                attackers = logic.get_attackers_from_zone(atk_range, src_zone)
                if not attackers:
                    continue
                cost = logic.get_attack_cost(len(attackers))
                if p.initiative < cost:
                    continue
                targets = logic.get_attack_zones_for_range(atk_range, src_zone)
                for enemy, zones in targets.items():
                    for z in zones:
                        actions.append(("attack", atk_range, src_zone, enemy, z))

        # 5) dobranie karty
        if (len(p.hand) < p.max_hand_size
                and p.deck
                and p.initiative >= p.get_draw_cost()):
            actions.append(("draw",))

        # 6) koniec tury – zawsze dostępny
        actions.append(("end_turn",))
        return actions

    # ------------------------------------------------------------------
    # WYKONANIE AKCJI – mostek do GameLogic
    # ------------------------------------------------------------------
    def execute(self, action: Tuple):
        kind = action[0]
        logic = self.logic

        if kind == "play":
            _, card, target_zone = action
            logic.select_card(card)
            if not logic.play_card_to_zone(target_zone):
                print(f"[AI] play_card_to_zone NIE powiodło się: {self.action_to_str(action)}")

        elif kind == "attach":
            _, card, target = action
            logic.select_card(card)
            logic.attach_card_to_target(target)

        elif kind == "move":
            _, soldier, dst = action
            logic.select_soldier_for_move(soldier)
            logic.move_soldier_to_zone(dst)

        elif kind == "attack":
            _, rng, src_zone, enemy, zone = action
            logic.start_attack_with_range(rng, src_zone)
            if logic.prepare_attack_preview(enemy, zone):
                logic.confirm_attack()
                logic.apply_combat_result()

        elif kind == "draw":
            logic.draw_card()

        elif kind == "end_turn":
            logic.deselect_card()

    # ------------------------------------------------------------------
    # SNAPSHOT STANU (dict) – na potrzeby logów i przyszłej sieci
    # ------------------------------------------------------------------
    def encode_state(self) -> Dict:
        from card import Zone
        p = self.logic.current_player
        return {
            "turn": self.logic.turn,
            "player": p.name,
            "initiative": p.initiative,
            "max_initiative": p.max_initiative,
            "food": p.food_production,
            "production": p.production,
            "logistics": p.logistics,
            "steal": p.steal,
            "oil": p.oil_production,
            "iron": p.iron_production,
            "fuel": p.fuel_production,
            "hand_size": len(p.hand),
            "deck_size": len(p.deck),
            "zones": {z.value: len(p.zones.get(z, [])) for z in Zone},
        }

    # ------------------------------------------------------------------
    # POMOCNICZE
    # ------------------------------------------------------------------
    @staticmethod
    def action_to_str(action: Tuple) -> str:
        """Serializuje akcję do stringa – na potrzeby logów i porównań.

        Przykłady:
            ("play", Card(card_13_name), Zone.STATE) → "play|card_13_name|state"
            ("draw",)                                → "draw"
            ("end_turn",)                            → "end_turn"
        """
        parts = [action[0]]
        for x in action[1:]:
            if hasattr(x, "name_key") and x.name_key:
                parts.append(x.name_key)
            elif hasattr(x, "value"):           # Enum (Zone, CardType)
                parts.append(str(x.value))
            elif hasattr(x, "name"):            # Player
                parts.append(str(x.name))
            else:
                parts.append(str(x))
        return "|".join(parts)