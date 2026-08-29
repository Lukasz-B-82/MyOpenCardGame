-- defines/game.lua
local game_start = {
    initiative = 45,
    max_hand_size = 10,
    initial_hand = 7,
    max_initiative = 50,
    food_production = 10,
    production = 0,
    steal = 0,
    logistics = 0,
    oil_production = 0,
    iron_production = 0,
    fuel_production = 0,
}

local discard_card = {
    initiative_cost = 1,
    move_from_discard_to_deck_all_initiative_cost = 15,
    move_from_discard_to_deck_first_initiative_cost = 5,
}

return game_start