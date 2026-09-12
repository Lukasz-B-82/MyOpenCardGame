# game_ai/heuristic_ai.py
"""Heurystyczne AI – punkt wyjścia do dalszych eksperymentów.

Cała „inteligencja" sprowadza się do funkcji score_action(action, state).
Wagi trzymamy w słowniku, żeby można je było:
  - nadpisać przez konstruktor (testy, Optuna),
  - logować (widzimy, co AI rozważało),
  - w przyszłości modyfikować przez sieć neuronową lub loader Lua.

Kolejność oceniania: każda legalna akcja dostaje liczbę punktów.
Wygrywa akcja z najwyższą punktacją. Jeśli nawet najlepsza akcja ma
mniej niż `min_score`, AI woli zakończyć turę.
"""
from game_ai.base import BaseAI
from game_ai.registry import register
from card import Zone, CardType


# ----------------------------------------------------------------------
# WAGI DOMYŚLNE
# ----------------------------------------------------------------------
# Klucze są zgodne z tym, co zwróci loader Lua (defines/ai_heuristic.lua)
# po spłaszczeniu: sekcja_klucz, np. "play_base", "attach_worker_base".
# ----------------------------------------------------------------------
FALLBACK_WEIGHTS = {
    # progi globalne
    "min_score": 5.0,           # poniżej tego AI woli zakończyć turę
    "end_turn": 0.0,

    # meta (do logów)
    "meta_version": "1.0",
    "meta_description": "Punkt startowy dla HeuristicAI – wagi wbudowane.",

    # zagranie karty z ręki
    "play_base": 20.0,
    "play_bonus_state": 10.0,       # premia za STATE (ekonomia)
    "play_bonus_front": 8.0,        # premia za FRONT (militaria)
    "play_bonus_building": 15.0,    # premia za BUILDING (długoterminowa wartość)
    "play_w_food": 3.0,
    "play_w_prod": 2.0,
    "play_w_init": 2.0,
    "play_w_steal": 4.0,
    "play_w_oil": 3.0,
    "play_w_iron": 3.0,
    "play_w_fuel": 3.0,

    # dołączenie karty
    "attach_worker_base": 15.0,
    "attach_worker_per_food": 3.0,
    "attach_worker_per_iron": 3.0,
    "attach_worker_per_oil": 3.0,
    "attach_weapon_base": 20.0,
    "attach_weapon_per_range": 10.0,

    # ruch żołnierza
    "move_base": 5.0,
    "move_per_step_toward_front": 8.0,

    # atak
    "attack_base": 10.0,
    "attack_per_success_chance": 100.0,
    "attack_per_counter_risk": -50.0,
    "attack_per_initiative_cost": -1.0,

    # dobranie / koniec tury
    "draw_base": 8.0,
    "draw_when_full": -50.0,
}


@register("heuristic")
class HeuristicAI(BaseAI):
    version = "1.0"

    def __init__(self, logic, weights=None, **kwargs):
        super().__init__(logic)
        # Kopia, żeby modyfikacje w self.w nie psuły oryginału.
        self.w = dict(FALLBACK_WEIGHTS)
        if weights:
            self.w.update(weights)

    # ------------------------------------------------------------------
    # WYBÓR AKCJI
    # ------------------------------------------------------------------
    def pick_action(self, actions, state):
        # 1) Oceń każdą legalną akcję
        scored = []
        for a in actions:
            s = self.score_action(a, state)
            scored.append((a, s))

        # 2) Zapisz wyniki do logu
        self.last_scores = {
            self.action_to_str(a): float(s) for a, s in scored
        }

        # 3) Wybierz najlepszą
        best_action, best_score = max(scored, key=lambda kv: kv[1])

        # 4) Jeśli nawet najlepsza jest bez sensu – kończ turę
        if best_score < self.w["min_score"]:
            self.last_reason = (
                f"best={best_score:.1f} < min_score={self.w['min_score']}"
            )
            return ("end_turn",)

        self.last_reason = f"best={best_score:.1f}"
        return best_action

    # ------------------------------------------------------------------
    # OCENA POJEDYNCZEJ AKCJI
    # ------------------------------------------------------------------
    def score_action(self, action, state) -> float:
        w = self.w
        kind = action[0]
        p = self.logic.current_player

        # ---- ZAGRANIE KARTY ----
        if kind == "play":
            _, card, zone = action
            s = w["play_base"]
            s += card.food_production     * w["play_w_food"]
            s += card.production          * w["play_w_prod"]
            s += card.initiative          * w["play_w_init"]
            s += card.steal_production    * w["play_w_steal"]
            s += card.oil_production      * w["play_w_oil"]
            s += card.iron_ore_production * w["play_w_iron"]
            s += card.fuel_production     * w["play_w_fuel"]

            if zone == Zone.STATE:
                s += w["play_bonus_state"]
            elif zone == Zone.FRONT:
                s += w["play_bonus_front"]

            if card.card_type == CardType.BUILDING:
                s += w["play_bonus_building"]
            return s

        # ---- DOŁĄCZENIE KARTY ----
        if kind == "attach":
            _, card, target = action
            if card.card_type == CardType.WORKER:
                return (w["attach_worker_base"]
                        + w["attach_worker_per_food"] * target.food_production
                        + w["attach_worker_per_iron"] * target.iron_ore_production
                        + w["attach_worker_per_oil"]  * target.oil_production)
            if card.card_type == CardType.WEAPON:
                return (w["attach_weapon_base"]
                        + w["attach_weapon_per_range"] * card.attack_range)
            # inne typy załączników – na razie stała premia
            return w["attach_worker_base"]

        # ---- RUCH ŻOŁNIERZA ----
        if kind == "move":
            _, soldier, dst = action
            order = {Zone.BACK: 0, Zone.SECOND: 1, Zone.FRONT: 2}
            src = None
            for z in (Zone.FRONT, Zone.SECOND, Zone.BACK):
                if soldier in p.zones.get(z, []):
                    src = z
                    break
            if src is None:
                return 0.0
            return (w["move_base"]
                    + (order[dst] - order[src]) * w["move_per_step_toward_front"])

        # ---- ATAK ----
        if kind == "attack":
            _, rng, src_zone, enemy, zone = action
            attackers = self.logic.get_attackers_from_zone(rng, src_zone)
            defenders = [c for c in enemy.zones.get(zone, [])
                         if c.card_type == CardType.SOLDIER]
            if not attackers or not defenders:
                return 0.0
            # Korzystamy z gotowej symulacji w GameLogic
            sim = self.logic.calculate_attack_simulation(attackers, defenders[0])
            risk = sum(ca["hit_chance"] for ca in sim["counter_attacks"])
            cost = self.logic.get_attack_cost(len(attackers))
            return (w["attack_base"]
                    + w["attack_per_success_chance"] * sim["success_chance"]
                    + w["attack_per_counter_risk"] * risk
                    + w["attack_per_initiative_cost"] * cost) 

        # ---- DOBRANIE ----
        if kind == "draw":
            if len(p.hand) < p.max_hand_size - 1:
                return w["draw_base"]
            return w["draw_when_full"]

        # ---- KONIEC TURY ----
        if kind == "end_turn":
            return w["end_turn"]

        return 0.0