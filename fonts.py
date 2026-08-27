# fonts.py
import pygame
import os
from constants import FONT_STORY_SCRIPT, FONT_BIZUD_GOTHIC_BOLD, FONT_BIZUD_GOTHIC

class Fonts:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
            cls._instance.font_cache = {}
        return cls._instance

    def initialize(self):
        if self._initialized:
            return
        self._initialized = True
        self.load_fonts()

    def load_fonts(self):
        if os.path.exists(FONT_STORY_SCRIPT):
            self.font_cache["main"] = {
                "StoryScript XXS": pygame.font.Font(FONT_STORY_SCRIPT, 13),
                "StoryScript XS": pygame.font.Font(FONT_STORY_SCRIPT, 18),
                "StoryScript S": pygame.font.Font(FONT_STORY_SCRIPT, 24),
                "StoryScript M": pygame.font.Font(FONT_STORY_SCRIPT, 36),
                "StoryScript L": pygame.font.Font(FONT_STORY_SCRIPT, 48),
                "StoryScript XL": pygame.font.Font(FONT_STORY_SCRIPT, 72),
                
                "BIZUDGothic XS": pygame.font.Font(FONT_BIZUD_GOTHIC, 18),
                "BIZUDGothic S": pygame.font.Font(FONT_BIZUD_GOTHIC, 24),
                "BIZUDGothic M": pygame.font.Font(FONT_BIZUD_GOTHIC, 36),
                "BIZUDGothic L": pygame.font.Font(FONT_BIZUD_GOTHIC, 48),
                "BIZUDGothic XL": pygame.font.Font(FONT_BIZUD_GOTHIC, 72),
                
                "BIZUDGothic XS Bold": pygame.font.Font(FONT_BIZUD_GOTHIC_BOLD, 18),
                "BIZUDGothic S Bold": pygame.font.Font(FONT_BIZUD_GOTHIC_BOLD, 24),
                "BIZUDGothic M Bold": pygame.font.Font(FONT_BIZUD_GOTHIC_BOLD, 36),
                "BIZUDGothic L Bold": pygame.font.Font(FONT_BIZUD_GOTHIC_BOLD, 48),
                "BIZUDGothic XL Bold": pygame.font.Font(FONT_BIZUD_GOTHIC_BOLD, 72),
            }
        else:
            print(f"Ostrzeżenie: nie znaleziono fontu {FONT_MAIN}, używam domyślnej.")
            self.font_cache["main"] = {
                "StoryScript XXS": pygame.font.Font(None, 12),
                "StoryScript XS": pygame.font.Font(None, 18),
                "StoryScript S": pygame.font.Font(None, 24),
                "StoryScript M": pygame.font.Font(None, 36),
                "StoryScript L": pygame.font.Font(None, 48),
                "StoryScript XL": pygame.font.Font(None, 72),
                
                "BIZUDGothic XS": pygame.font.Font(None, 18),
                "BIZUDGothic S": pygame.font.Font(None, 24),
                "BIZUDGothic M": pygame.font.Font(None, 36),
                "BIZUDGothic L": pygame.font.Font(None, 48),
                "BIZUDGothic XL": pygame.font.Font(None, 72),
                
                "BIZUDGothic XS Bold": pygame.font.Font(None, 18),
                "BIZUDGothic S Bold": pygame.font.Font(None, 24),
                "BIZUDGothic M Bold": pygame.font.Font(None, 36),
                "BIZUDGothic L Bold": pygame.font.Font(None, 48),
                "BIZUDGothic XL Bold": pygame.font.Font(None, 72),
            }

    def get_font(self, size_key: str = "StoryScript M", style: str = "main"):
        if not self._initialized:
            self.initialize()
        return self.font_cache.get(style, {}).get(size_key, pygame.font.Font(None, 24))

    def render_text(self, text: str, size_key: str = "StoryScript M", color=(255,255,255), 
                    style: str = "main", center=None, topleft=None):
        """Renderuje tekst i zwraca powierzchnię oraz prostokąt.
           Jeśli podano center lub topleft, ustawia odpowiednią pozycję."""
        font = self.get_font(size_key, style)
        surface = font.render(text, True, color)
        rect = surface.get_rect()
        if center is not None:
            rect.center = center
        elif topleft is not None:
            rect.topleft = topleft
        return surface, rect

# Singleton
fonts = Fonts()