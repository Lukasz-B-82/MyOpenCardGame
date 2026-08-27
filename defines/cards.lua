-- cards.lua
-- Definicje kart – każda karta ma unikalny klucz card_<numer>
-- name_key wskazuje na klucz w tłumaczeniach (np. "card_0_name")

local CardType = {
    SOLDIER = "SOLDIER",
    WORKER = "WORKER",
    VEHICLE = "VEHICLE",
    TANK = "TANK",
    CAR = "CAR",
    PLANE = "PLANE",
    WEAPON = "WEAPON",
    TERRAIN = "TERRAIN",
    CITY = "CITY",
    BUILDING = "BUILDING",
    ARTILLERY = "ARTILLERY"
}

local Faction = {
    NEUTRAL = "NEUTRAL",
    RED = "RED",
    BLUE = "BLUE",
    GREEN = "GREEN",
    WHITE = "WHITE",
    BLACK = "BLACK"
}

local Zone = {
    FRONT = "front",
    SECOND = "second",
    BACK = "back",
    STATE = "state"
}

cards = {}

-- ==================== 0-7: Rekruci ====================
cards["card_0"] = {
    name_key = "card_0_name",
    type = CardType.SOLDIER,
    faction = Faction.NEUTRAL,
    cost_initiative = 5,
    initiative = 2,
    food_consumption = 1,
    allowed_zones = { Zone.BACK },
    allowed_attachments = { CardType.WEAPON, CardType.TANK, CardType.PLANE, CardType.ARTILLERY },
    image = "0.png",
    frame_key = "01"
}
cards["card_1"] = {
    name_key = "card_1_name",
    type = CardType.SOLDIER,
    faction = Faction.NEUTRAL,
    cost_initiative = 5,
    initiative = 2,
    food_consumption = 1,
    allowed_zones = { Zone.BACK },
    allowed_attachments = { CardType.WEAPON, CardType.TANK, CardType.PLANE, CardType.ARTILLERY },
    image = "1.png",
    frame_key = "01"
}
cards["card_2"] = {
    name_key = "card_2_name",
    type = CardType.SOLDIER,
    faction = Faction.NEUTRAL,
    cost_initiative = 5,
    initiative = 2,
    food_consumption = 1,
    allowed_zones = { Zone.BACK },
    allowed_attachments = { CardType.WEAPON, CardType.TANK, CardType.PLANE, CardType.ARTILLERY },
    image = "2.png",
    frame_key = "01"
}
cards["card_3"] = {
    name_key = "card_3_name",
    type = CardType.SOLDIER,
    faction = Faction.NEUTRAL,
    cost_initiative = 5,
    initiative = 2,
    food_consumption = 1,
    allowed_zones = { Zone.BACK },
    allowed_attachments = { CardType.WEAPON, CardType.TANK, CardType.PLANE, CardType.ARTILLERY },
    image = "3.png",
    frame_key = "01"
}
cards["card_4"] = {
    name_key = "card_4_name",
    type = CardType.SOLDIER,
    faction = Faction.NEUTRAL,
    cost_initiative = 5,
    initiative = 2,
    food_consumption = 1,
    allowed_zones = { Zone.BACK },
    allowed_attachments = { CardType.WEAPON, CardType.TANK, CardType.PLANE, CardType.ARTILLERY },
    image = "4.png",
    frame_key = "01"
}
cards["card_5"] = {
    name_key = "card_5_name",
    type = CardType.SOLDIER,
    faction = Faction.NEUTRAL,
    cost_initiative = 5,
    initiative = 2,
    food_consumption = 1,
    allowed_zones = { Zone.BACK },
    allowed_attachments = { CardType.WEAPON, CardType.TANK, CardType.PLANE, CardType.ARTILLERY },
    image = "5.png",
    frame_key = "01"
}
cards["card_6"] = {
    name_key = "card_6_name",
    type = CardType.SOLDIER,
    faction = Faction.NEUTRAL,
    cost_initiative = 5,
    initiative = 2,
    food_consumption = 1,
    allowed_zones = { Zone.BACK },
    allowed_attachments = { CardType.WEAPON, CardType.TANK, CardType.PLANE, CardType.ARTILLERY },
    image = "6.png",
    frame_key = "01"
}
cards["card_7"] = {
    name_key = "card_7_name",
    type = CardType.SOLDIER,
    faction = Faction.NEUTRAL,
    cost_initiative = 5,
    initiative = 2,
    food_consumption = 1,
    allowed_zones = { Zone.BACK },
    allowed_attachments = { CardType.WEAPON, CardType.TANK, CardType.PLANE, CardType.ARTILLERY },
    image = "7.png",
    frame_key = "01"
}

-- ==================== 8-10: Robotnicy (I) ====================
cards["card_8"] = {
    name_key = "card_8_name",
    type = CardType.WORKER,
    faction = Faction.NEUTRAL,
    cost_initiative = 3,
    initiative = 1,
    food_consumption = 1,
    allowed_zones = {},
    allowed_attachments = {},
    image = "8.png",
    frame_key = "01"
}
cards["card_9"] = {
    name_key = "card_9_name",
    type = CardType.WORKER,
    faction = Faction.NEUTRAL,
    cost_initiative = 3,
    initiative = 1,
    food_consumption = 1,
    allowed_zones = {},
    allowed_attachments = {},
    image = "9.png",
    frame_key = "01"
}
cards["card_10"] = {
    name_key = "card_10_name",
    type = CardType.WORKER,
    faction = Faction.NEUTRAL,
    cost_initiative = 3,
    initiative = 1,
    food_consumption = 1,
    allowed_zones = {},
    allowed_attachments = {},
    image = "10.png",
    frame_key = "01"
}

-- ==================== 11-12: Czołgi lekkie ====================
cards["card_11"] = {
    name_key = "card_11_name",
    type = CardType.TANK,
    faction = Faction.NEUTRAL,
    cost_initiative = 6,
    cost_production = 6,
    fuel_consumption = 2,
    cost_steal = 10,
    allowed_zones = {},
    allowed_attachments = {},
    image = "11.png",
    frame_key = "04"
}
cards["card_12"] = {
    name_key = "card_12_name",
    type = CardType.TANK,
    faction = Faction.NEUTRAL,
    cost_initiative = 6,
    cost_production = 6,
    fuel_consumption = 2,
    cost_steal = 10,
    allowed_zones = {},
    allowed_attachments = {},
    image = "12.png",
    frame_key = "04"
}

-- ==================== 13-18: Równiny ====================
cards["card_13"] = {
    name_key = "card_13_name",
    type = CardType.TERRAIN,
    faction = Faction.NEUTRAL,
    cost_initiative = 1,
    initiative = 1,
    max_workers = 2,
    food_production = 4,
    allowed_zones = { Zone.STATE },
    allowed_attachments = { CardType.WORKER },
    image = "13.png",
    frame_key = "01"
}
cards["card_14"] = {
    name_key = "card_14_name",
    type = CardType.TERRAIN,
    faction = Faction.NEUTRAL,
    cost_initiative = 1,
    initiative = 1,
    max_workers = 2,
    food_production = 4,
    allowed_zones = { Zone.STATE },
    allowed_attachments = { CardType.WORKER },
    image = "14.png",
    frame_key = "01"
}
cards["card_15"] = {
    name_key = "card_15_name",
    type = CardType.TERRAIN,
    faction = Faction.NEUTRAL,
    cost_initiative = 1,
    initiative = 1,
    max_workers = 2,
    food_production = 4,
    allowed_zones = { Zone.STATE },
    allowed_attachments = { CardType.WORKER },
    image = "15.png",
    frame_key = "01"
}
cards["card_16"] = {
    name_key = "card_16_name",
    type = CardType.TERRAIN,
    faction = Faction.NEUTRAL,
    cost_initiative = 1,
    initiative = 1,
    max_workers = 2,
    food_production = 4,
    allowed_zones = { Zone.STATE },
    allowed_attachments = { CardType.WORKER },
    image = "16.png",
    frame_key = "01"
}
cards["card_17"] = {
    name_key = "card_17_name",
    type = CardType.TERRAIN,
    faction = Faction.NEUTRAL,
    cost_initiative = 1,
    initiative = 1,
    max_workers = 2,
    food_production = 4,
    allowed_zones = { Zone.STATE },
    allowed_attachments = { CardType.WORKER },
    image = "17.png",
    frame_key = "01"
}
cards["card_18"] = {
    name_key = "card_18_name",
    type = CardType.TERRAIN,
    faction = Faction.NEUTRAL,
    cost_initiative = 1,
    initiative = 1,
    max_workers = 2,
    food_production = 4,
    allowed_zones = { Zone.STATE },
    allowed_attachments = { CardType.WORKER },
    image = "18.png",
    frame_key = "01"
}

-- ==================== 19-21: Wzgórza ====================
cards["card_19"] = {
    name_key = "card_19_name",
    type = CardType.TERRAIN,
    faction = Faction.NEUTRAL,
    cost_initiative = 1,
    initiative = 1,
    max_workers = 2,
    food_production = 2,
    iron_ore_production = 1,
    allowed_zones = { Zone.STATE },
    allowed_attachments = { CardType.WORKER },
    image = "19.png",
    frame_key = "01"
}
cards["card_20"] = {
    name_key = "card_20_name",
    type = CardType.TERRAIN,
    faction = Faction.NEUTRAL,
    cost_initiative = 1,
    initiative = 1,
    max_workers = 2,
    food_production = 2,
    iron_ore_production = 1,
    allowed_zones = { Zone.STATE },
    allowed_attachments = { CardType.WORKER },
    image = "20.png",
    frame_key = "01"
}
cards["card_21"] = {
    name_key = "card_21_name",
    type = CardType.TERRAIN,
    faction = Faction.NEUTRAL,
    cost_initiative = 1,
    initiative = 1,
    max_workers = 2,
    food_production = 2,
    iron_ore_production = 1,
    allowed_zones = { Zone.STATE },
    allowed_attachments = { CardType.WORKER },
    image = "21.png",
    frame_key = "01"
}

-- ==================== 22-23: Góry ====================
cards["card_22"] = {
    name_key = "card_22_name",
    type = CardType.TERRAIN,
    faction = Faction.NEUTRAL,
    cost_initiative = 5,
    initiative = 1,
    max_workers = 3,
    iron_ore_production = 2,
    allowed_zones = { Zone.STATE },
    allowed_attachments = { CardType.WORKER },
    image = "22.png",
    frame_key = "01"
}
cards["card_23"] = {
    name_key = "card_23_name",
    type = CardType.TERRAIN,
    faction = Faction.NEUTRAL,
    cost_initiative = 5,
    initiative = 1,
    max_workers = 3,
    iron_ore_production = 2,
    allowed_zones = { Zone.STATE },
    allowed_attachments = { CardType.WORKER },
    image = "23.png",
    frame_key = "01"
}

-- ==================== 24-27: Karabiny (I) ====================
cards["card_24"] = {
    name_key = "card_24_name",
    type = CardType.WEAPON,
    faction = Faction.NEUTRAL,
    cost_initiative = 2,
    cost_production = 2,
    allowed_zones = {},
    allowed_attachments = {},
    image = "24.png",
    frame_key = "01"
}
cards["card_25"] = {
    name_key = "card_25_name",
    type = CardType.WEAPON,
    faction = Faction.NEUTRAL,
    cost_initiative = 2,
    cost_production = 2,
    allowed_zones = {},
    allowed_attachments = {},
    image = "25.png",
    frame_key = "01"
}
cards["card_26"] = {
    name_key = "card_26_name",
    type = CardType.WEAPON,
    faction = Faction.NEUTRAL,
    cost_initiative = 2,
    cost_production = 2,
    allowed_zones = {},
    allowed_attachments = {},
    image = "26.png",
    frame_key = "01"
}
cards["card_27"] = {
    name_key = "card_27_name",
    type = CardType.WEAPON,
    faction = Faction.NEUTRAL,
    cost_initiative = 2,
    cost_production = 2,
    allowed_zones = {},
    allowed_attachments = {},
    image = "27.png",
    frame_key = "01"
}

-- ==================== 28-29: Pistolety ====================
cards["card_28"] = {
    name_key = "card_28_name",
    type = CardType.WEAPON,
    faction = Faction.NEUTRAL,
    cost_initiative = 1,
    cost_production = 1,
    allowed_zones = {},
    allowed_attachments = {},
    image = "28.png",
    frame_key = "01"
}
cards["card_29"] = {
    name_key = "card_29_name",
    type = CardType.WEAPON,
    faction = Faction.NEUTRAL,
    cost_initiative = 1,
    cost_production = 1,
    allowed_zones = {},
    allowed_attachments = {},
    image = "29.png",
    frame_key = "01"
}

-- ==================== 30: Pustynia ====================
cards["card_30"] = {
    name_key = "card_30_name",
    type = CardType.TERRAIN,
    faction = Faction.NEUTRAL,
    cost_initiative = 5,
    max_workers = 3,
    oil_production = 5,
    allowed_zones = { Zone.STATE },
    allowed_attachments = { CardType.WORKER },
    image = "30.png",
    frame_key = "01"
}

-- ==================== 31: Fabryka (I) ====================
cards["card_31"] = {
    name_key = "card_31_name",
    type = CardType.BUILDING,
    faction = Faction.NEUTRAL,
    cost_initiative = 8,
    production = 2,
    max_workers = 4,
    requirements = {
        { zone = Zone.STATE, type = CardType.CITY, count = 1 },
        { zone = Zone.STATE, type = CardType.TERRAIN, count = 3 },
        { zone = Zone.STATE, type = CardType.WORKER, count = 3 }
    },
    allowed_zones = { Zone.STATE },
    allowed_attachments = { CardType.WORKER },
    image = "31.png",
    frame_key = "03"
}

-- ==================== 32-34: Robotnicy (II) ====================
cards["card_32"] = {
    name_key = "card_32_name",
    type = CardType.WORKER,
    faction = Faction.NEUTRAL,
    cost_initiative = 3,
    initiative = 1,
    food_consumption = 1,
    allowed_zones = {},
    allowed_attachments = {},
    image = "32.png",
    frame_key = "01"
}
cards["card_33"] = {
    name_key = "card_33_name",
    type = CardType.WORKER,
    faction = Faction.NEUTRAL,
    cost_initiative = 3,
    initiative = 1,
    food_consumption = 1,
    allowed_zones = { },
    allowed_attachments = {},
    image = "33.png",
    frame_key = "01"
}
cards["card_34"] = {
    name_key = "card_34_name",
    type = CardType.WORKER,
    faction = Faction.NEUTRAL,
    cost_initiative = 3,
    initiative = 1,
    food_consumption = 1,
    allowed_zones = {},
    allowed_attachments = {},
    image = "34.png",
    frame_key = "01"
}

-- ==================== 35-36: Karabiny (II) ====================
cards["card_35"] = {
    name_key = "card_35_name",
    type = CardType.WEAPON,
    faction = Faction.NEUTRAL,
    cost_initiative = 2,
    cost_production = 2,
    allowed_zones = {},
    allowed_attachments = {},
    image = "35.png",
    frame_key = "01"
}
cards["card_36"] = {
    name_key = "card_36_name",
    type = CardType.WEAPON,
    faction = Faction.NEUTRAL,
    cost_initiative = 2,
    cost_production = 2,
    allowed_zones = {},
    allowed_attachments = {},
    image = "36.png",
    frame_key = "01"
}

-- ==================== 37: Czołg lekki (II) ====================
cards["card_37"] = {
    name_key = "card_37_name",
    type = CardType.TANK,
    faction = Faction.NEUTRAL,
    cost_initiative = 6,
    cost_production = 6,
    fuel_consumption = 2,
    cost_steal = 10,
    allowed_zones = {},
    allowed_attachments = {},
    image = "37.png",
    frame_key = "01"
}

-- ==================== 38-40: Robotnicy (III) ====================
cards["card_38"] = {
    name_key = "card_38_name",
    type = CardType.WORKER,
    faction = Faction.NEUTRAL,
    cost_initiative = 3,
    initiative = 1,
    food_consumption = 1,
    allowed_zones = {},
    allowed_attachments = {},
    image = "38.png",
    frame_key = "01"
}
cards["card_39"] = {
    name_key = "card_39_name",
    type = CardType.WORKER,
    faction = Faction.NEUTRAL,
    cost_initiative = 3,
    initiative = 1,
    food_consumption = 1,
    allowed_zones = {},
    allowed_attachments = {},
    image = "39.png",
    frame_key = "01"
}
cards["card_40"] = {
    name_key = "card_40_name",
    type = CardType.WORKER,
    faction = Faction.NEUTRAL,
    cost_initiative = 3,
    initiative = 1,
    food_consumption = 1,
    allowed_zones = {},
    allowed_attachments = {},
    image = "40.png",
    frame_key = "01"
}

-- ==================== 41-42: Fabryki (II) ====================
cards["card_41"] = {
    name_key = "card_41_name",
    type = CardType.BUILDING,
    faction = Faction.NEUTRAL,
    cost_initiative = 8,
    production = 2,
    max_workers = 4,
    requirements = {
        { zone = Zone.STATE, type = CardType.CITY, count = 1 },
        { zone = Zone.STATE, type = CardType.TERRAIN, count = 3 },
        { zone = Zone.STATE, type = CardType.WORKER, count = 3 }
    },
    allowed_zones = { Zone.STATE },
    allowed_attachments = { CardType.WORKER },
    image = "41.png",
    frame_key = "01"
}
cards["card_42"] = {
    name_key = "card_42_name",
    type = CardType.BUILDING,
    faction = Faction.NEUTRAL,
    cost_initiative = 8,
    production = 2,
    max_workers = 4,
    requirements = {
        { zone = Zone.STATE, type = CardType.CITY, count = 1 },
        { zone = Zone.STATE, type = CardType.TERRAIN, count = 3 },
        { zone = Zone.STATE, type = CardType.WORKER, count = 3 }
    },
    allowed_zones = { Zone.STATE },
    allowed_attachments = { CardType.WORKER },
    image = "42.png",
    frame_key = "01"
}

-- ==================== 43-46: Równiny (II) ====================
cards["card_43"] = {
    name_key = "card_43_name",
    type = CardType.TERRAIN,
    faction = Faction.NEUTRAL,
    cost_initiative = 1,
    initiative = 1,
    max_workers = 2,
    food_production = 4,
    allowed_zones = { Zone.STATE },
    allowed_attachments = { CardType.WORKER },
    image = "43.png",
    frame_key = "01"
}
cards["card_44"] = {
    name_key = "card_44_name",
    type = CardType.TERRAIN,
    faction = Faction.NEUTRAL,
    cost_initiative = 1,
    initiative = 1,
    max_workers = 2,
    food_production = 4,
    allowed_zones = { Zone.STATE },
    allowed_attachments = { CardType.WORKER },
    image = "44.png",
    frame_key = "01"
}
cards["card_45"] = {
    name_key = "card_45_name",
    type = CardType.TERRAIN,
    faction = Faction.NEUTRAL,
    cost_initiative = 1,
    initiative = 1,
    max_workers = 2,
    food_production = 4,
    allowed_zones = { Zone.STATE },
    allowed_attachments = { CardType.WORKER },
    image = "45.png",
    frame_key = "01"
}
cards["card_46"] = {
    name_key = "card_46_name",
    type = CardType.TERRAIN,
    faction = Faction.NEUTRAL,
    cost_initiative = 1,
    initiative = 1,
    max_workers = 2,
    food_production = 4,
    allowed_zones = { Zone.STATE },
    allowed_attachments = { CardType.WORKER },
    image = "46.png",
    frame_key = "01"
}

-- ==================== 47-52: Miasta ====================
cards["card_47"] = {
    name_key = "card_47_name",
    type = CardType.CITY,
    faction = Faction.GREEN,
    cost_initiative = 10,
    initiative = 2,
    food_consumption = 5,
    allowed_zones = { Zone.STATE },
    allowed_attachments = {},
    image = "47.png",
    frame_key = "01"
}
cards["card_48"] = {
    name_key = "card_48_name",
    type = CardType.CITY,
    faction = Faction.NEUTRAL,
    cost_initiative = 10,
    initiative = 2,
    food_consumption = 5,
    allowed_zones = { Zone.STATE },
    allowed_attachments = {},
    image = "48.png",
    frame_key = "01"
}
cards["card_49"] = {
    name_key = "card_49_name",
    type = CardType.CITY,
    faction = Faction.RED,
    cost_initiative = 10,
    initiative = 2,
    food_consumption = 5,
    allowed_zones = { Zone.STATE },
    allowed_attachments = {},
    image = "49.png",
    frame_key = "01"
}
cards["card_50"] = {
    name_key = "card_50_name",
    type = CardType.CITY,
    faction = Faction.BLUE,
    cost_initiative = 10,
    initiative = 2,
    food_consumption = 5,
    allowed_zones = { Zone.STATE },
    allowed_attachments = {},
    image = "50.png",
    frame_key = "01"
}
cards["card_51"] = {
    name_key = "card_51_name",
    type = CardType.CITY,
    faction = Faction.WHITE,
    cost_initiative = 15,
    initiative = 3,
    food_consumption = 5,
    allowed_zones = { Zone.STATE },
    allowed_attachments = {},
    image = "51.png",
    frame_key = "01"
}
cards["card_52"] = {
    name_key = "card_52_name",
    type = CardType.CITY,
    faction = Faction.WHITE,
    cost_initiative = 15,
    initiative = 3,
    food_consumption = 5,
    allowed_zones = { Zone.STATE },
    allowed_attachments = {},
    image = "52.png",
    frame_key = "02"
}

-- ==================== 53-56: Huty stali ====================
cards["card_53"] = {
    name_key = "card_53_name",
    type = CardType.BUILDING,
    faction = Faction.NEUTRAL,
    cost_initiative = 10,
    max_workers = 4,
    steal_production = 1,
    requirements = {
        { zone = Zone.STATE, type = CardType.CITY, count = 1 },
        { zone = Zone.STATE, type = CardType.TERRAIN, count = 5 },
        { zone = Zone.STATE, type = CardType.WORKER, count = 5 }
    },
    allowed_zones = { Zone.STATE },
    allowed_attachments = { CardType.WORKER },
    image = "53.png",
    frame_key = "01"
}
cards["card_54"] = {
    name_key = "card_54_name",
    type = CardType.BUILDING,
    faction = Faction.NEUTRAL,
    cost_initiative = 10,
    max_workers = 4,
    steal_production = 1,
    requirements = {
        { zone = Zone.STATE, type = CardType.CITY, count = 1 },
        { zone = Zone.STATE, type = CardType.TERRAIN, count = 5 },
        { zone = Zone.STATE, type = CardType.WORKER, count = 5 }
    },
    allowed_zones = { Zone.STATE },
    allowed_attachments = { CardType.WORKER },
    image = "54.png",
    frame_key = "01"
}
cards["card_55"] = {
    name_key = "card_55_name",
    type = CardType.BUILDING,
    faction = Faction.NEUTRAL,
    cost_initiative = 10,
    max_workers = 4,
    steal_production = 1,
    requirements = {
        { zone = Zone.STATE, type = CardType.CITY, count = 1 },
        { zone = Zone.STATE, type = CardType.TERRAIN, count = 5 },
        { zone = Zone.STATE, type = CardType.WORKER, count = 5 }
    },
    allowed_zones = { Zone.STATE },
    allowed_attachments = { CardType.WORKER },
    image = "55.png",
    frame_key = "01"
}
cards["card_56"] = {
    name_key = "card_56_name",
    type = CardType.BUILDING,
    faction = Faction.NEUTRAL,
    cost_initiative = 10,
    max_workers = 4,
    steal_production = 1,
    requirements = {
        { zone = Zone.STATE, type = CardType.CITY, count = 1 },
        { zone = Zone.STATE, type = CardType.TERRAIN, count = 5 },
        { zone = Zone.STATE, type = CardType.WORKER, count = 5 }
    },
    allowed_zones = { Zone.STATE },
    allowed_attachments = { CardType.WORKER },
    image = "56.png",
    frame_key = "01"
}

-- ==================== 57-61: Rafinerie ====================
cards["card_57"] = {
    name_key = "card_57_name",
    type = CardType.BUILDING,
    faction = Faction.NEUTRAL,
    cost_initiative = 15,
    max_workers = 4,
    fuel_production = 1,
    requirements = {
        { zone = Zone.STATE, type = CardType.CITY, count = 1 },
        { zone = Zone.STATE, type = CardType.TERRAIN, count = 5 },
        { zone = Zone.STATE, type = CardType.WORKER, count = 5 }
    },
    allowed_zones = { Zone.STATE },
    allowed_attachments = { CardType.WORKER },
    image = "57.png",
    frame_key = "01"
}
cards["card_58"] = {
    name_key = "card_58_name",
    type = CardType.BUILDING,
    faction = Faction.NEUTRAL,
    cost_initiative = 15,
    max_workers = 4,
    fuel_production = 1,
    requirements = {
        { zone = Zone.STATE, type = CardType.CITY, count = 1 },
        { zone = Zone.STATE, type = CardType.TERRAIN, count = 5 },
        { zone = Zone.STATE, type = CardType.WORKER, count = 5 }
    },
    allowed_zones = { Zone.STATE },
    allowed_attachments = { CardType.WORKER },
    image = "58.png",
    frame_key = "01"
}
cards["card_59"] = {
    name_key = "card_59_name",
    type = CardType.BUILDING,
    faction = Faction.NEUTRAL,
    cost_initiative = 15,
    max_workers = 4,
    fuel_production = 1,
    requirements = {
        { zone = Zone.STATE, type = CardType.CITY, count = 1 },
        { zone = Zone.STATE, type = CardType.TERRAIN, count = 5 },
        { zone = Zone.STATE, type = CardType.WORKER, count = 5 }
    },
    allowed_zones = { Zone.STATE },
    allowed_attachments = { CardType.WORKER },
    image = "59.png",
    frame_key = "01"
}
cards["card_60"] = {
    name_key = "card_60_name",
    type = CardType.BUILDING,
    faction = Faction.NEUTRAL,
    cost_initiative = 15,
    max_workers = 4,
    fuel_production = 1,
    requirements = {
        { zone = Zone.STATE, type = CardType.CITY, count = 1 },
        { zone = Zone.STATE, type = CardType.TERRAIN, count = 5 },
        { zone = Zone.STATE, type = CardType.WORKER, count = 5 }
    },
    allowed_zones = { Zone.STATE },
    allowed_attachments = { CardType.WORKER },
    image = "60.png",
    frame_key = "01"
}
cards["card_61"] = {
    name_key = "card_61_name",
    type = CardType.BUILDING,
    faction = Faction.NEUTRAL,
    cost_initiative = 15,
    max_workers = 4,
    fuel_production = 1,
    requirements = {
        { zone = Zone.STATE, type = CardType.CITY, count = 1 },
        { zone = Zone.STATE, type = CardType.TERRAIN, count = 5 },
        { zone = Zone.STATE, type = CardType.WORKER, count = 5 }
    },
    allowed_zones = { Zone.STATE },
    allowed_attachments = { CardType.WORKER },
    image = "61.png",
    frame_key = "01"
}
cards["card_62"] = {
    name_key = "card_62_name",
    type = CardType.BUILDING,
    faction = Faction.NEUTRAL,
    cost_initiative = 15,
    max_workers = 4,
    fuel_production = 1,
    requirements = {
        { zone = Zone.STATE, type = CardType.CITY, count = 1 },
        { zone = Zone.STATE, type = CardType.TERRAIN, count = 5 },
        { zone = Zone.STATE, type = CardType.WORKER, count = 5 }
    },
    allowed_zones = { Zone.STATE },
    allowed_attachments = { CardType.WORKER },
    image = "lucid-origin_A_sprawling_industrial_refinery_complex_a_fusion_of_steampunk_cyberpunk_and_goth-0.jpg",
    frame_key = "03",
    img_author = "leonardo.ai"
}

-- ==================== 63: Czołgi lekkie ====================
cards["card_63"] = {
    name_key = "card_63_name",
    type = CardType.TANK,
    faction = Faction.NEUTRAL,
    cost_initiative = 6,
    cost_production = 6,
    fuel_consumption = 2,
    cost_steal = 10,
    allowed_zones = {},
    allowed_attachments = {},
    image = "63.png",
    frame_key = "02"
}

-- ==================== 64-70: Samochody ====================
cards["card_64"] = {
    name_key = "card_63_name",
    type = CardType.CAR,
    faction = Faction.NEUTRAL,
    cost_initiative = 3,
    cost_production = 4,
    fuel_consumption = 1,
    logistics = 1,
    cost_steal = 2,
    allowed_zones = { Zone.STATE },
    allowed_attachments = {},
    image = "64.jfif",
    frame_key = "01"
}
cards["card_65"] = {
    name_key = "card_65_name",
    type = CardType.CAR,
    faction = Faction.NEUTRAL,
    cost_initiative = 3,
    cost_production = 4,
    fuel_consumption = 1,
    logistics = 1,
    cost_steal = 2,
    allowed_zones = { Zone.STATE },
    allowed_attachments = {},
    image = "65.jfif",
    frame_key = "01"
}
cards["card_66"] = {
    name_key = "card_66_name",
    type = CardType.CAR,
    faction = Faction.NEUTRAL,
    cost_initiative = 3,
    cost_production = 4,
    fuel_consumption = 1,
    logistics = 1,
    cost_steal = 2,
    allowed_zones = { Zone.STATE },
    allowed_attachments = {},
    image = "66.jfif",
    frame_key = "01"
}
cards["card_67"] = {
    name_key = "card_67_name",
    type = CardType.CAR,
    faction = Faction.NEUTRAL,
    cost_initiative = 3,
    cost_production = 4,
    fuel_consumption = 1,
    logistics = 1,
    cost_steal = 2,
    allowed_zones = { Zone.STATE },
    allowed_attachments = {},
    image = "67.jfif",
    frame_key = "01"
}
cards["card_68"] = {
    name_key = "card_68_name",
    type = CardType.CAR,
    faction = Faction.NEUTRAL,
    cost_initiative = 3,
    cost_production = 4,
    fuel_consumption = 1,
    logistics = 1,
    cost_steal = 2,
    allowed_zones = { Zone.STATE },
    allowed_attachments = {},
    image = "68.jfif",
    frame_key = "01"
}
cards["card_69"] = {
    name_key = "card_69_name",
    type = CardType.CAR,
    faction = Faction.NEUTRAL,
    cost_initiative = 3,
    cost_production = 4,
    fuel_consumption = 1,
    logistics = 1,
    cost_steal = 2,
    allowed_zones = { Zone.STATE },
    allowed_attachments = {},
    image = "69.jfif",
    frame_key = "01"
}
cards["card_70"] = {
    name_key = "card_70_name",
    type = CardType.CAR,
    faction = Faction.NEUTRAL,
    cost_initiative = 3,
    cost_production = 4,
    fuel_consumption = 1,
    logistics = 1,
    cost_steal = 2,
    allowed_zones = { Zone.STATE },
    allowed_attachments = {},
    image = "70.jfif",
    frame_key = "01"
}
return cards