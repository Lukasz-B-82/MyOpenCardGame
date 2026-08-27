-- defines/frames.lua
local frames = {}

frames["01"] = {
    image = "01.png",
    offset_x = 10,
    offset_y = 2,
    text_color = {0, 0, 0},  -- czarny
    font = "StoryScript XS",
    title_offset_x = -135,
    title_offset_y = 15,
    icon_offset_x = -78,
    icon_offset_y = 280
}

frames["02"] = {
    image = "02.png",
    offset_x = -16,
    offset_y = 2,
    text_color = {255, 255, 255},  -- biały
    font = "StoryScript XS",
    title_offset_x = -35,
    title_offset_y = 43,
    icon_offset_x = -44,
    icon_offset_y = 260
}

frames["03"] = {
    image = "03.png",
    offset_x = -16,
    offset_y = 3,
    text_color = {0, 0, 0},  -- czarny
    font = "StoryScript XS",
    title_offset_x = -10,
    title_offset_y = 30,
    icon_offset_x = -42,
    icon_offset_y = 200
}

frames["04"] = {
    image = "04.png",
    offset_x = -10,
    offset_y = 3,
    text_color = {200, 200, 255}, -- jasnoniebieski
    font = "StoryScript XS",
    title_offset_x = -25,
    title_offset_y = 35,
    icon_offset_x = -53,
    icon_offset_y = 260
}

return frames