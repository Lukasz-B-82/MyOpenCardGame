-- defines/game.lua
local game_start = {
    initiative = 10,
    max_hand_size = 10,
    initial_hand = 7,
    max_initiative = 50,
    food_production = 0,
    production = 0,
    steal = 0,
    logistics = 0,
    oil_production = 0,
    iron_production = 0,
    fuel_production = 0,
}
local atack = {
    base_cost = 10,
    cost_per_unit = 2,
    next_attack_cost_decrease = 5,
    min_initiative_cost = 5,
}
local discard_card = {
    initiative_cost = 1,
--    move_from_discard_to_deck_all_initiative_cost = 15,
--    move_from_discard_to_deck_first_initiative_cost = 5,
}

-- =============================================================================
-- WARTOŚĆ KART (do liczenia przewagi)
-- =============================================================================
-- Klucze odpowiadają CardType.value z Python-a.
-- Jeśli karta ma typ nieobecny w tej tabeli, używamy domyślnej wagi z Pythona.
-- =============================================================================
local card_value = {
    TERRAIN   = 1,
    WORKER    = 1,

    SOLDIER   = 2,
    CAR       = 2,

    WEAPON    = 3,
    BUILDING  = 3,
    CITY      = 3,
    VEHICLE   = 3,

    TANK      = 5,
    PLANE     = 5,
    ARTILLERY = 5,
}

-- =============================================================================
-- WARUNKI ZWYCIĘSTWA
-- =============================================================================
-- advantage_threshold = 0.80 → gracz wygrywa, gdy jego suma wartości kart
-- na planszy przekroczy 80% sumy wartości wszystkich graczy.
-- =============================================================================
local victory = {
    advantage_threshold = 0.80,
}

local min_turns = 20
local max_turns = 60

return game_start, atack, discard_card, card_value, victory, min_turns, max_turns
