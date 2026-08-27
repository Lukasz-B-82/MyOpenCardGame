# game.py
import pygame
import sys
import os
import random
from typing import List, Optional
from PIL import Image
from constants import *
from localization import Localization
from fonts import fonts
from card import Card, CardType, Zone
from card_renderer import draw_card, draw_tooltip
from player import Player
from deck_editor import ALL_CARDS
from game_logic import GameLogic
from card_view import CardView
from game_view import GameView


class Game:
    def __init__(self, screen, clock, players_config, language="pl"):
        self.screen = screen
        self.clock = clock
        self.running = True
        self.language = language
        self.localization = Localization(language)
        self.screen_width, self.screen_height = screen.get_size()
        
        self.logic = GameLogic(players_config, self.create_deck, language)
        self.logic.start_turn(self.logic.current_player)

        self.background_image = None
        self.load_background()
        self.card_back_image = self.load_card_back_image()

        # Tworzymy GameView
        self.view = GameView(
            screen, self.logic, self.localization,
            self.card_back_image, self.background_image
        )
        print("set_view")
        self.logic.set_view(self.view)
                
        # Lista wszystkich widocznych kart (do tooltipów i podglądu)
        self.card_views = []  # wszystkie CardView w grze (ręka + strefy)
        self.hovered_card_view = None  # aktualnie najechany
        self.preview_view = None
        self.preview_visible = False
        self.preview_width = 512
        self.preview_height = 768
        
        self.zone_rects = {}

    def create_deck(self, deck_name: str) -> List[Card]:
        import json
        deck_path = os.path.join("decks", f"{deck_name}.json")
        cards = []
        try:
            with open(deck_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for card_key in data.get("cards", []):
                    for c in ALL_CARDS:
                        if c.name_key == card_key:
                            cards.append(c.copy())
                            break
        except:
            print(f"Nie znaleziono talii {deck_name}, używam przykładowej.")
            for c in ALL_CARDS[:30]:
                cards.append(c.copy())
        return cards

    def load_background(self):
        path = "images/board"
        if not os.path.exists(path):
            self.create_dummy_background()
            return
        files = [f for f in os.listdir(path) if f.lower().endswith(('.jfif', '.jpg', '.png'))]
        if files:
            file = random.choice(files)
            full_path = os.path.join(path, file)
            try:
                pil_image = Image.open(full_path)
                pil_image = pil_image.convert('RGB')
                pil_image = pil_image.resize((self.screen_width, self.screen_height), Image.Resampling.LANCZOS)
                mode = pil_image.mode
                size = pil_image.size
                data = pil_image.tobytes()
                self.background_image = pygame.image.fromstring(data, size, mode)
            except Exception as e:
                print(f"Błąd wczytywania tła: {e}")
                self.create_dummy_background()
        else:
            self.create_dummy_background()

    def create_dummy_background(self):
        self.background_image = pygame.Surface((self.screen_width, self.screen_height))
        self.background_image.fill((40, 40, 80))

    def load_card_back_image(self):
        back_dir = "images/cards/backs"
        if not os.path.exists(back_dir):
            print(f"Katalog {back_dir} nie istnieje, tworzę domyślny rewers.")
            dummy = pygame.Surface((100, 140))
            dummy.fill((50, 50, 80))
            pygame.draw.rect(dummy, (100, 100, 150), dummy.get_rect(), 2)
            return dummy
        files = [f for f in os.listdir(back_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.jfif'))]
        if not files:
            print(f"Brak plików w {back_dir}, używam domyślnego rewersu.")
            dummy = pygame.Surface((100, 140))
            dummy.fill((50, 50, 80))
            pygame.draw.rect(dummy, (100, 100, 150), dummy.get_rect(), 2)
            return dummy
        chosen = random.choice(files)
        path = os.path.join(back_dir, chosen)
        try:
            img = pygame.image.load(path).convert_alpha()
            img = pygame.transform.smoothscale(img, (100, 140))
            return img
        except Exception as e:
            print(f"Błąd wczytywania rewersu {path}: {e}")
            dummy = pygame.Surface((100, 140))
            dummy.fill((50, 50, 80))
            pygame.draw.rect(dummy, (100, 100, 150), dummy.get_rect(), 2)
            return dummy

    @property
    def current_player(self) -> Player:
        return self.logic.current_player

    def draw_zones(self):
        player = self.current_player
        allowed_zones = self.logic.get_allowed_zones()  # <-- pobieramy dozwolone strefy
        
        zone_names = {
            Zone.FRONT: "Front",
            Zone.SECOND: "Druga linia",
            Zone.BACK: "Zaplecze",
            Zone.STATE: "Państwo"
        }
        zone_width = 375
        zone_height = 200
        spacing = 10
        start_y = self.screen_height - 420
        start_x = (self.screen_width - (4 * zone_width + 3 * spacing)) // 2

        self.zone_rects.clear()
        for i, zone in enumerate([Zone.FRONT, Zone.SECOND, Zone.BACK, Zone.STATE]):
            x = start_x + i * (zone_width + spacing)
            y = start_y
            rect = pygame.Rect(x, y, zone_width, zone_height)
            self.zone_rects[zone] = rect

            # Sprawdź, czy strefa jest dozwolona
            is_allowed = self.logic.selected_card is not None and zone in allowed_zones

            # Tło zależne od dozwolenia
            if is_allowed:
                bg_color = (60, 200, 60, 80)  # zielone przezroczyste tło
            else:
                bg_color = (60, 60, 80, 75)   # standardowe
            bg_surface = pygame.Surface((zone_width, zone_height), pygame.SRCALPHA)
            bg_surface.fill(bg_color)
            self.screen.blit(bg_surface, (x, y))

            # Ramka – zielona jeśli dozwolona
            border_color = (0, 255, 0, 200) if is_allowed else (200, 200, 200, 50)
            pygame.draw.rect(self.screen, border_color, rect, 2 if not is_allowed else 4)

            # Nazwa z licznikiem
            cards_in_zone = player.zones.get(zone, [])
            count = len(cards_in_zone)
            display_name = f"{zone_names[zone]} ({count})"
            name_surf, _ = fonts.render_text(
                display_name,
                size_key="StoryScript XS",
                color=WHITE,
                center=(rect.centerx, rect.y + 15)
            )
            self.screen.blit(name_surf, name_surf.get_rect(center=(rect.centerx, rect.y + 12)))

            # Karty w strefie (używamy CardView)
            if cards_in_zone:
                max_visible = 3
                visible_cards = cards_in_zone[:max_visible]
                card_width = 80
                card_height = 112
                card_spacing = 10
                total_cards_width = len(visible_cards) * (card_width + card_spacing) - card_spacing
                start_x_cards = rect.centerx - total_cards_width // 2
                card_y = rect.centery - card_height // 2 + 10

                for j, card in enumerate(visible_cards):
                    cx = start_x_cards + j * (card_width + card_spacing)
                    view = CardView(card, self.localization)
                    view.update_rect(cx, card_y, card_width, card_height)
                    view.draw(self.screen, cx, card_y, card_width, card_height, language=self.language)
                    self.card_views.append(view)

                if count > max_visible:
                    more_text = f"+{count - max_visible}"
                    more_surf, _ = fonts.render_text(
                        more_text,
                        size_key="StoryScript S",
                        color=(255, 255, 0),
                        center=(rect.right - 25, rect.bottom - 20)
                    )
                    self.screen.blit(more_surf, more_surf.get_rect(center=(rect.right - 25, rect.bottom - 20)))
            else:
                empty_surf, _ = fonts.render_text(
                    "pusta",
                    size_key="StoryScript S",
                    color=(150, 150, 150),
                    center=(rect.centerx, rect.centery + 10)
                )
                self.screen.blit(empty_surf, empty_surf.get_rect(center=(rect.centerx, rect.centery + 10)))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                self.running = False
                return
            if event.type == pygame.VIDEORESIZE:
                self.screen_width, self.screen_height = event.w, event.h
                self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                self.load_background()
                self.view.update_size(event.w, event.h)

            if event.type == pygame.MOUSEMOTION:
                self.view.handle_mouse_motion(event.pos)

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    action = self.view.handle_click(event.pos, 1)
                    if action == "end_turn":
                        self.logic.next_turn()
                        # Odśwież widok (automatycznie w następnej iteracji pętli)
                        continue
                    if action == "draw":
                        if self.logic.draw_card():
                            print("Dobrano kartę")
                        else:
                            print("Nie można dobrać karty")
                    elif isinstance(action, tuple):
                        if action[0] == "play":
                            zone = action[1]
                            if self.logic.play_card_to_zone(zone):
                                print(f"Zagrano kartę do strefy {zone.value}")
                            else:
                                print("Nie można zagrać karty w tej strefie!")
                        elif action[0] == "attach":
                            target_card = action[1]
                            if self.logic.attach_card_to_target(target_card):
                                print(f"Dołączono kartę do {target_card.name_key}")
                            else:
                                print("Nie można dołączyć tej karty!")
                        elif action[0] == "select":
                            card = action[1]
                            if self.logic.selected_card == card:
                                self.logic.deselect_card()
                            else:
                                self.logic.select_card(card)
                        elif action[0] == "deselect":
                            self.logic.deselect_card()

                elif event.button == 3:
                    self.view.handle_click(event.pos, 3)

                if event.button == 1 and self.view.preview_visible:
                    preview_rect = pygame.Rect(
                        (self.screen_width - self.view.preview_width) // 2,
                        (self.screen_height - self.view.preview_height) // 2,
                        self.view.preview_width, self.view.preview_height
                    )
                    if not preview_rect.collidepoint(event.pos):
                        self.view.close_preview()

    def draw(self):
        self.view.draw()

    def run(self):
        while self.running:
            self.handle_events()
            self.draw()
            pygame.display.flip()
            self.clock.tick(FPS)

def game_loop(screen, clock, players_config, language="pl"):
    game = Game(screen, clock, players_config, language)
    game.run()