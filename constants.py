# constants.py
import os

SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 1024
FPS = 60

MAX_PLAYERS = 8

# Kolory
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
BG_COLOR = (30, 30, 30)
BUTTON_COLOR = (100, 100, 150)
BUTTON_HOVER_COLOR = (150, 150, 200)
TEXT_COLOR = WHITE

FONTS_DIR = "fonts"
FONT_STORY_SCRIPT = os.path.join(FONTS_DIR, "StoryScript-Regular.ttf")
FONT_BIZUD_GOTHIC_BOLD = os.path.join(FONTS_DIR, "BIZUDGothic-Bold.ttf")
FONT_BIZUD_GOTHIC = os.path.join(FONTS_DIR, "BIZUDGothic-Regular.ttf")
