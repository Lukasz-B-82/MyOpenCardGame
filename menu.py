# menu.py
import pygame
import sys
import os
import glob
from PIL import Image
from constants import *
from localization import Localization
from fonts import fonts

class PlayerConfig:
    """Konfiguracja pojedynczego gracza."""
    def __init__(self, index):
        self.index = index
        self.active = True
        self.type = "human"  # "human" lub "ai"
        self.deck = "default"  # nazwa talii

class MainMenu:
    def __init__(self, screen, clock):
        self.screen = screen
        self.clock = clock
        self.running = True
        self.language = "pl"
        self.fullscreen = False
        self.localization = Localization(self.language)
        self.return_to_editor = False
        
        # Pobierz aktualne wymiary ekranu
        self.screen_width, self.screen_height = screen.get_size()

        # Konfiguracja graczy – domyślnie 2 aktywnych
        self.players = [PlayerConfig(i) for i in range(MAX_PLAYERS)]
        self.max_players = 2
        self.hovered_component = None

        # Tło
        self.background_images = []
        self.current_bg_index = 0
        self.bg_timer = 0
        self.bg_change_interval = 6500
        self.load_background_images()

        # Przyciski
        self.buttons = []
        self.components = []
        self.create_buttons()
        self.create_components()

    def load_background_images(self):
        """Wczytuje i skaluje obrazy tła do aktualnego rozmiaru okna."""
        path = "images/start_screen"
        self.background_images.clear()
        if not os.path.exists(path):
            self.create_dummy_background()
            return
        files = [f for f in os.listdir(path) if f.lower().endswith(('.jfif', '.jpg', '.png'))]
        files.sort()
        for file in files:
            full_path = os.path.join(path, file)
            try:
                pil_image = Image.open(full_path)
                pil_image = pil_image.convert('RGB')
                pil_image = pil_image.resize((self.screen_width, self.screen_height), Image.Resampling.LANCZOS)
                mode = pil_image.mode
                size = pil_image.size
                data = pil_image.tobytes()
                surface = pygame.image.fromstring(data, size, mode)
                self.background_images.append(surface)
            except Exception as e:
                print(f"Błąd wczytywania {full_path}: {e}")
        if not self.background_images:
            self.create_dummy_background()

    def create_dummy_background(self):
        dummy = pygame.Surface((self.screen_width, self.screen_height))
        dummy.fill(BG_COLOR)
        self.background_images.append(dummy)

    def create_buttons(self):
        """Tworzy przyciski główne – pozycje zależne od rozmiaru okna."""
        self.buttons.clear()
        # Przycisk zmiany języka (PL/EN)
        self.buttons.append({
            "rect": pygame.Rect(50, 50, 120, 50),
            "text": "PL/EN",
            "action": self.toggle_language,
            "type": "lang"
        })
        # Edytor
        self.buttons.append({
            "rect": pygame.Rect(self.screen_width - 250, 50, 200, 70),
            "text": self.localization.get("editor"),
            "action": self.open_deck_editor,
            "type": "editor"
        })
        # Fullscreen
        self.buttons.append({
            "rect": pygame.Rect(self.screen_width - 250, self.screen_height - 100, 200, 70),
            "text": self.localization.get("fullscreen"),
            "action": self.toggle_fullscreen,
            "type": "fullscreen"
        })
        # Start
        self.buttons.append({
            "rect": pygame.Rect(self.screen_width//2 - 200, self.screen_height - 100, 400, 70),
            "text": self.localization.get("start"),
            "action": self.start_game,
            "type": "start"
        })
        # Przegeneruj karty
        self.buttons.append({
            "rect": pygame.Rect(self.screen_width - 250, self.screen_height - 180, 200, 50),
            "text": self.localization.get("regenerate_cards"),
            "action": self.regenerate_cards,
            "type": "regenerate"
        })

    def regenerate_cards(self):
        from card_generator import regenerate_all_cards
        from deck_editor import ALL_CARDS
        languages = ["pl", "en"]
        regenerate_all_cards(ALL_CARDS, languages)
        print("Karty zostały przegenerowane.")

    def create_components(self):
        """Tworzy elementy konfiguracji graczy – pozycje zależne od rozmiaru okna."""
        self.components.clear()
        y_start = 300
        for idx, player in enumerate(self.players):
            y = y_start + idx * 75
            # Checkbox aktywności
            rect_check = pygame.Rect(self.screen_width//2 - 350, y - 10, 50, 50)
            self.components.append({
                "rect": rect_check,
                "type": "checkbox",
                "player": idx,
                "text": "",
                "action": lambda i=idx: self.toggle_active(i)
            })
            # Etykieta "Gracz X"
            rect_label = pygame.Rect(self.screen_width//2 - 250, y, 80, 30)
            self.components.append({
                "rect": rect_label,
                "type": "label",
                "player": idx,
                "text": f"Gracz {idx+1}",
                "action": None
            })
            # Przycisk typu (Człowiek / AI)
            rect_type = pygame.Rect(self.screen_width//2 - 50, y - 10, 120, 50)
            self.components.append({
                "rect": rect_type,
                "type": "type_button",
                "player": idx,
                "text": self.localization.get("human") if player.type == "human" else "AI",
                "action": lambda i=idx: self.toggle_type(i)
            })
            # Wybór talii – dynamiczna lista z katalogu decks/
            rect_deck = pygame.Rect(self.screen_width//2 + 150, y - 10, 180, 50)
            deck_names = self.get_deck_list()
            if player.deck not in deck_names:
                player.deck = deck_names[0] if deck_names else "default"
            self.components.append({
                "rect": rect_deck,
                "type": "deck_button",
                "player": idx,
                "text": player.deck,
                "action": lambda i=idx: self.cycle_deck(i)
            })

    def get_deck_list(self):
        """Zwraca listę dostępnych talii z katalogu decks/."""
        decks_dir = "decks"
        if not os.path.exists(decks_dir):
            os.makedirs(decks_dir)
        files = glob.glob(os.path.join(decks_dir, "*.json"))
        names = [os.path.splitext(os.path.basename(f))[0] for f in files]
        return sorted(names) if names else ["default"]

    def toggle_active(self, idx):
        self.players[idx].active = not self.players[idx].active

    def toggle_type(self, idx):
        p = self.players[idx]
        p.type = "ai" if p.type == "human" else "human"
        self.update_type_button_texts()

    def update_type_button_texts(self):
        """Odświeża teksty przycisków typu dla wszystkich graczy."""
        for comp in self.components:
            if comp["type"] == "type_button":
                idx = comp["player"]
                p = self.players[idx]
                comp["text"] = self.localization.get("human") if p.type == "human" else "AI"

    def cycle_deck(self, idx):
        decks = self.get_deck_list()
        p = self.players[idx]
        current = p.deck
        try:
            i = decks.index(current)
            i = (i + 1) % len(decks)
        except ValueError:
            i = 0
        p.deck = decks[i]
        for comp in self.components:
            if comp["type"] == "deck_button" and comp["player"] == idx:
                comp["text"] = p.deck
                break

    def toggle_language(self):
        self.language = "en" if self.language == "pl" else "pl"
        self.localization.set_language(self.language)
        # Odśwież teksty przycisków głównych
        for btn in self.buttons:
            if btn["type"] == "start":
                btn["text"] = self.localization.get("start")
            elif btn["type"] == "editor":
                btn["text"] = self.localization.get("editor")
            elif btn["type"] == "fullscreen":
                btn["text"] = self.localization.get("fullscreen")
            elif btn["type"] == "regenerate":
                btn["text"] = self.localization.get("regenerate_cards")
        # Odśwież teksty przycisków typu
        self.update_type_button_texts()

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
        self.screen = pygame.display.get_surface()
        # Odśwież wymiary
        self.screen_width, self.screen_height = self.screen.get_size()
        self.load_background_images()
        self.create_buttons()
        self.create_components()

    def open_deck_editor(self):
        self.running = False
        self.return_to_editor = True

    def start_game(self):
        self.running = False

    def draw(self):
        self.screen.fill(BG_COLOR)
        if self.background_images:
            self.screen.blit(self.background_images[self.current_bg_index], (0, 0))

        # Tytuł
        title_surf, title_rect = fonts.render_text(
            self.localization.get("title"),
            size_key="StoryScript XL",
            color=TEXT_COLOR,
            center=(self.screen_width//2, 100)
        )
        self.screen.blit(title_surf, title_rect)

        # Nagłówek konfiguracji
        header_surf, header_rect = fonts.render_text(
            self.localization.get("player_config"),
            size_key="StoryScript L",
            color=TEXT_COLOR,
            center=(self.screen_width//2, 200)
        )
        self.screen.blit(header_surf, header_rect)

        # Rysuj komponenty
        mouse_pos = pygame.mouse.get_pos()
        for comp in self.components:
            rect = comp["rect"]
            hover = rect.collidepoint(mouse_pos)
            color = BUTTON_HOVER_COLOR if hover else BUTTON_COLOR

            if comp["type"] == "checkbox":
                pygame.draw.rect(self.screen, GRAY if not self.players[comp["player"]].active else WHITE, rect)
                pygame.draw.rect(self.screen, BLACK, rect, 1)
                if self.players[comp["player"]].active:
                    check = fonts.get_font("BIZUDGothic M").render("✓", True, BLACK)
                    self.screen.blit(check, check.get_rect(center=rect.center))
            elif comp["type"] == "label":
                text_surf, text_rect = fonts.render_text(
                    comp["text"], size_key="StoryScript M", color=TEXT_COLOR, center=rect.center
                )
                self.screen.blit(text_surf, text_rect)
            elif comp["type"] == "type_button" or comp["type"] == "deck_button":
                pygame.draw.rect(self.screen, color, rect)
                pygame.draw.rect(self.screen, BLACK, rect, 2)
                text_surf, text_rect = fonts.render_text(
                    comp["text"], size_key="StoryScript S", color=TEXT_COLOR, center=rect.center
                )
                self.screen.blit(text_surf, text_rect)

        # Przyciski główne
        for btn in self.buttons:
            rect = btn["rect"]
            hover = rect.collidepoint(mouse_pos)
            color = BUTTON_HOVER_COLOR if hover else BUTTON_COLOR
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, BLACK, rect, 2)
            text_surf, text_rect = fonts.render_text(
                btn["text"], size_key="StoryScript M", color=TEXT_COLOR, center=rect.center
            )
            self.screen.blit(text_surf, text_rect)

    def update_background(self, dt):
        self.bg_timer += dt
        if self.bg_timer >= self.bg_change_interval and len(self.background_images) > 1:
            self.bg_timer = 0
            self.current_bg_index = (self.current_bg_index + 1) % len(self.background_images)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                pygame.quit()
                sys.exit()
            if event.type == pygame.VIDEORESIZE:
                if not self.fullscreen:
                    self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                    self.screen_width, self.screen_height = self.screen.get_size()
                    self.load_background_images()
                    self.create_buttons()
                    self.create_components()
                else:
                    self.screen_width, self.screen_height = self.screen.get_size()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = event.pos
                for comp in self.components:
                    if comp["rect"].collidepoint(mouse_pos) and comp.get("action") is not None:
                        comp["action"]()
                        break
                for btn in self.buttons:
                    if btn["rect"].collidepoint(mouse_pos) and btn["action"] is not None:
                        btn["action"]()
                        if btn["type"] == "regenerate":
                            # po regeneracji odśwież listę talii w komponentach
                            self.create_components()

    def run(self):
        last_time = pygame.time.get_ticks()
        while self.running:
            dt = pygame.time.get_ticks() - last_time
            last_time = pygame.time.get_ticks()
            self.handle_events()
            self.update_background(dt)
            self.draw()
            pygame.display.flip()
            self.clock.tick(FPS)

        # Zwróć konfigurację graczy
        players_config = []
        for p in self.players:
            if p.active:
                players_config.append({
                    "index": p.index,
                    "name": f"Gracz {p.index+1}",
                    "type": p.type,
                    "deck": p.deck
                })
        return self.language, players_config, getattr(self, 'return_to_editor', False)

def menu_loop(screen, clock):
    menu = MainMenu(screen, clock)
    return menu.run()