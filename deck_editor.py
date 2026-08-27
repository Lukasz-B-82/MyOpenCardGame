# deck_editor.py
import pygame
import sys
import os
import json
import glob
from PIL import Image
from constants import *
from localization import Localization
from fonts import fonts
from card import Card, CardType, Faction, Zone, create_card_from_lua
from card_renderer import draw_card, draw_tooltip
from card_view import CardView  # <-- DODANE
import random

# ---------- WCZYTYWANIE KART ----------
ALL_CARDS = []
CARDS_FILE = os.path.join("defines", "cards.lua")
DECKS_DIR = "decks"

def load_cards():
    global ALL_CARDS
    ALL_CARDS = []
    try:
        import lupa
        from lupa import LuaRuntime
        lua = LuaRuntime(unpack_returned_tuples=True)
        with open(CARDS_FILE, "r", encoding="utf-8") as f:
            result = lua.execute(f.read())
        if result is not None:
            cards_table = result
        else:
            cards_table = lua.globals().get("cards")
            if cards_table is None:
                raise ValueError("Nie znaleziono tabeli 'cards' w pliku Lua")
        
        for key, defn in cards_table.items():
            card = create_card_from_lua(defn, key)
            if not hasattr(card, 'max_in_deck') or card.max_in_deck == 0:
                card.max_in_deck = 6
            ALL_CARDS.append(card)
        print(f"Wczytano {len(ALL_CARDS)} kart z {CARDS_FILE}")
    except Exception as e:
        print(f"Nie udało się wczytać {CARDS_FILE}: {e}, używam przykładowych kart.")
        import traceback
        traceback.print_exc()
        for i in range(20):
            card = Card(
                name=f"Karta {i+1}",
                card_type=CardType.SOLDIER if i%3==0 else CardType.TERRAIN if i%1==0 else CardType.WEAPON,
                faction=Faction.NEUTRAL,
                cost_initiative=random.randint(1, 5),
                initiative=random.randint(0, 3),
                max_in_deck=6
            )
            ALL_CARDS.append(card)

load_cards()

class DeckEditor:
    def __init__(self, screen, clock, language="pl", deck_name="default"):
        self.screen = screen
        self.clock = clock
        self.running = True
        self.language = language
        self.localization = Localization(language)
        self.fullscreen = False
        self.hovered_card = None
        self.preview_card = None
        self.preview_visible = False
        self.preview_x = 0
        self.preview_y = 0
        self.preview_width = 512
        self.preview_height = 768

        self.screen_width, self.screen_height = screen.get_size()

        # ---------- ZARZĄDZANIE TALIAMI ----------
        self.current_deck_name = deck_name
        self.deck_list = self.get_deck_list()
        self.selected_deck_index = 0

        # Talia
        self.deck = []
        self.deck_counts = {}
        self.load_deck(deck_name)

        # Wszystkie karty – posortuj po nazwie z tłumaczeń
        self.all_cards = sorted(ALL_CARDS, key=lambda c: self.localization.get_card_name(c.name_key) if c.name_key else c.name)

        # Przyciski
        self.buttons = []
        self.create_buttons()

        # Scroll dla prawego panelu
        self.scroll_offset = 0
        # Scroll dla lewego panelu
        self.left_scroll_offset = 0

        self.card_width = 0
        self.card_height = 0
        self.cards_per_row = 5
        self.padding = 10

        # Przechowujemy CardView dla wszystkich wyświetlanych kart
        self.card_views = []  # lista CardView dla kart w prawym panelu
        self.deck_card_views = []  # lista CardView dla kart w lewym panelu
        self.card_rects = []  # (rect, card) dla prawego panelu (do kliknięć)
        self.deck_card_rects = []  # (rect, card) dla lewego panelu (do kliknięć)

    def get_deck_list(self):
        if not os.path.exists(DECKS_DIR):
            os.makedirs(DECKS_DIR)
        files = glob.glob(os.path.join(DECKS_DIR, "*.json"))
        names = [os.path.splitext(os.path.basename(f))[0] for f in files]
        if not names:
            self.create_default_deck()
            names = ["default"]
        return sorted(names)

    def create_default_deck(self):
        if not os.path.exists(DECKS_DIR):
            os.makedirs(DECKS_DIR)
        default_deck = []
        for i, card in enumerate(ALL_CARDS[:30]):
            default_deck.append(card.name_key)
        with open(os.path.join(DECKS_DIR, "default.json"), "w", encoding="utf-8") as f:
            json.dump({"cards": default_deck}, f, indent=2, ensure_ascii=False)

    def load_deck(self, deck_name):
        self.deck = []
        self.deck_counts = {}
        path = os.path.join(DECKS_DIR, f"{deck_name}.json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for card_key in data.get("cards", []):
                    for c in ALL_CARDS:
                        if c.name_key == card_key:
                            self.deck.append(c)
                            self.deck_counts[card_key] = self.deck_counts.get(card_key, 0) + 1
                            break
        except:
            self.deck = []
        for c in ALL_CARDS:
            if c.name_key not in self.deck_counts:
                self.deck_counts[c.name_key] = 0

    def save_deck(self, deck_name=None):
        if deck_name is None:
            deck_name = self.current_deck_name
        path = os.path.join(DECKS_DIR, f"{deck_name}.json")
        data = {"cards": [c.name_key for c in self.deck]}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        self.deck_list = self.get_deck_list()
        print(f"Zapisano talię: {deck_name}")

    def delete_deck(self, deck_name):
        path = os.path.join(DECKS_DIR, f"{deck_name}.json")
        if os.path.exists(path) and deck_name != "default":
            os.remove(path)
            self.deck_list = self.get_deck_list()
            if self.current_deck_name == deck_name:
                self.load_deck("default")
                self.current_deck_name = "default"
            print(f"Usunięto talię: {deck_name}")

    def create_buttons(self):
        self.buttons.clear()
        left_width = int(self.screen_width * 0.2)
        btn_height = 35
        btn_y = 20
        
        x = left_width + 20
        btn_width = 120
        
        self.buttons.append({
            "rect": pygame.Rect(x, btn_y, btn_width, btn_height),
            "text": self.localization.get("save_deck"),
            "action": lambda: self.save_deck(self.current_deck_name),
            "type": "save"
        })
        x += btn_width + 10
        
        self.buttons.append({
            "rect": pygame.Rect(x, btn_y, btn_width, btn_height),
            "text": self.localization.get("save_as"),
            "action": self.save_as_dialog,
            "type": "save_as"
        })
        x += btn_width + 10
        
        self.buttons.append({
            "rect": pygame.Rect(x, btn_y, btn_width, btn_height),
            "text": self.localization.get("delete_deck"),
            "action": lambda: self.delete_deck(self.current_deck_name) if self.current_deck_name != "default" else None,
            "type": "delete"
        })
        x += btn_width + 10
        
        self.buttons.append({
            "rect": pygame.Rect(x, btn_y, 140, btn_height),
            "text": f"📂 {self.current_deck_name}",
            "action": self.show_deck_selection,
            "type": "deck_selector"
        })
        
        x = self.screen_width - 150
        self.buttons.append({
            "rect": pygame.Rect(x, btn_y, 130, btn_height),
            "text": self.localization.get("fullscreen"),
            "action": self.toggle_fullscreen,
            "type": "fullscreen"
        })
        x = self.screen_width - 150
        self.buttons.append({
            "rect": pygame.Rect(x, btn_y + btn_height + 5, 130, btn_height),
            "text": self.localization.get("back"),
            "action": self.back_to_menu,
            "type": "back"
        })

    def save_as_dialog(self):
        print("=== ZAPISZ TALIĘ JAKO ===")
        name = input("Podaj nazwę nowej talii: ").strip()
        if name and name not in self.deck_list:
            self.save_deck(name)
            self.current_deck_name = name
            self.deck_list = self.get_deck_list()
            for btn in self.buttons:
                if btn["type"] == "deck_selector":
                    btn["text"] = f"📂 {name}"
        elif name in self.deck_list:
            print(f"Talia '{name}' już istnieje!")
        else:
            print("Anulowano.")

    def show_deck_selection(self):
        print("=== WYBÓR TALII ===")
        for i, name in enumerate(self.deck_list):
            print(f"{i+1}. {name}" + (" *" if name == self.current_deck_name else ""))
        try:
            choice = int(input("Wybierz numer: ")) - 1
            if 0 <= choice < len(self.deck_list):
                selected = self.deck_list[choice]
                if selected != self.current_deck_name:
                    self.save_deck(self.current_deck_name)
                    self.load_deck(selected)
                    self.current_deck_name = selected
                    for btn in self.buttons:
                        if btn["type"] == "deck_selector":
                            btn["text"] = f"📂 {selected}"
                    print(f"Wczytano talię: {selected}")
        except:
            print("Anulowano.")

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
        self.screen = pygame.display.get_surface()
        self.screen_width, self.screen_height = self.screen.get_size()

    def back_to_menu(self):
        self.save_deck(self.current_deck_name)
        self.running = False

    def draw_card_counter(self, view, x, y, width, height):
        """Rysuje licznik kopii na karcie."""
        count = self.deck_counts.get(view.card.name_key, 0)
        max_count = getattr(view.card, 'max_in_deck', 6)
        if max_count == 0:
            return
        text = f"{count}/{max_count}"
        font_size = max(10, int(width * 0.08))
        font = pygame.font.Font(None, font_size)
        color = (255, 255, 255)
        text_surf = font.render(text, True, color)
        text_rect = text_surf.get_rect(topright=(x + width - 8, y + 8))
        bg_rect = text_rect.inflate(12, 6)
        bg = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
        bg.fill((0, 0, 0, 200))
        self.screen.blit(bg, bg_rect.topleft)
        self.screen.blit(text_surf, text_rect)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                pygame.quit()
                sys.exit()
            if event.type == pygame.VIDEORESIZE:
                if not self.fullscreen:
                    self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                    self.screen_width, self.screen_height = self.screen.get_size()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:  # scroll w górę
                    mouse_pos = pygame.mouse.get_pos()
                    left_width = int(self.screen_width * 0.2)
                    if mouse_pos[0] < left_width:
                        self.left_scroll_offset = max(0, self.left_scroll_offset - 30)
                    else:
                        self.scroll_offset = max(0, self.scroll_offset - 30)
                elif event.button == 5:  # scroll w dół
                    mouse_pos = pygame.mouse.get_pos()
                    left_width = int(self.screen_width * 0.2)
                    if mouse_pos[0] < left_width:
                        self.left_scroll_offset += 30
                    else:
                        self.scroll_offset += 30
                elif event.button == 1:
                    mouse_pos = event.pos
                    for btn in self.buttons:
                        if btn["rect"].collidepoint(mouse_pos) and btn["action"] is not None:
                            btn["action"]()
                            return
                    # Kliknięcie w prawym panelu – dodaj kopię
                    for rect, card in self.card_rects:
                        if rect.collidepoint(mouse_pos):
                            if self.deck_counts.get(card.name_key, 0) < getattr(card, 'max_in_deck', 6):
                                self.deck.append(card)
                                self.deck_counts[card.name_key] = self.deck_counts.get(card.name_key, 0) + 1
                            return
                    # Kliknięcie w lewym panelu – usuń kopię
                    for rect, card in self.deck_card_rects:
                        if rect.collidepoint(mouse_pos):
                            if card in self.deck:
                                self.deck.remove(card)
                                self.deck_counts[card.name_key] -= 1
                            return
            if event.type == pygame.MOUSEMOTION:
                self.hovered_card = None
                for view in self.card_views:
                    if view.rect and view.rect.collidepoint(event.pos):
                        self.hovered_card = view.card
                        break
                if not self.hovered_card:
                    for view in self.deck_card_views:
                        if view.rect and view.rect.collidepoint(event.pos):
                            self.hovered_card = view.card
                            break
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 3:
                    clicked_view = None
                    for view in self.card_views:
                        if view.rect and view.rect.collidepoint(event.pos):
                            clicked_view = view
                            break
                    if not clicked_view:
                        for view in self.deck_card_views:
                            if view.rect and view.rect.collidepoint(event.pos):
                                clicked_view = view
                                break
                    if clicked_view:
                        self.preview_card = clicked_view.card
                        self.preview_visible = True
                        self.preview_x = (self.screen_width - self.preview_width) // 2
                        self.preview_y = (self.screen_height - self.preview_height) // 2
                    else:
                        self.preview_visible = False
                        self.preview_card = None
                    return
                elif event.button == 1 and self.preview_visible:
                    preview_rect = pygame.Rect(self.preview_x, self.preview_y, self.preview_width, self.preview_height)
                    if not preview_rect.collidepoint(event.pos):
                        self.preview_visible = False
                        self.preview_card = None
                    return

    def draw(self):
        self.screen.fill(BG_COLOR)

        # ---------- LEWY PANEL ----------
        left_width = int(self.screen_width * 0.2)
        left_rect = pygame.Rect(0, 0, left_width, self.screen_height)
        pygame.draw.rect(self.screen, (50, 50, 50), left_rect)
        pygame.draw.rect(self.screen, BLACK, left_rect, 2)

        title_surf, title_rect = fonts.render_text(
            self.localization.get("deck_list"),
            size_key="StoryScript L",
            color=TEXT_COLOR,
            center=(left_width//2, 75)
        )
        self.screen.blit(title_surf, title_rect)

        deck_name_surf, _ = fonts.render_text(
            f"📂 {self.current_deck_name}",
            size_key="StoryScript S",
            color=(200, 200, 200),
            center=(left_width//2, 115)
        )
        self.screen.blit(deck_name_surf, deck_name_surf.get_rect(center=(left_width//2, 115)))

        # Karty w lewym panelu z przewijaniem
        y = 150 - self.left_scroll_offset
        self.deck_card_rects.clear()
        self.deck_card_views.clear()
        card_w = left_width - 20
        card_h = int(card_w * 1.4)
        for card in self.deck:
            rect = pygame.Rect(10, y, card_w, card_h)
            if rect.bottom > 150 and rect.top < self.screen_height:
                # Tworzymy CardView
                view = CardView(card, self.localization)
                view.update_rect(rect.x, rect.y, rect.width, rect.height)
                view.draw(self.screen, rect.x, rect.y, rect.width, rect.height, language=self.language)
                self.deck_card_views.append(view)
                self.deck_card_rects.append((rect, card))
            y += card_h - 330

        # ---------- PRAWY PANEL ----------
        right_rect = pygame.Rect(left_width, 0, self.screen_width - left_width, self.screen_height)
        pygame.draw.rect(self.screen, (30, 30, 30), right_rect)
        pygame.draw.rect(self.screen, BLACK, right_rect, 2)

        title_surf, title_rect = fonts.render_text(
            self.localization.get("all_cards"),
            size_key="StoryScript L",
            color=TEXT_COLOR,
            center=(right_rect.centerx, 75)
        )
        self.screen.blit(title_surf, title_rect)

        available_width = right_rect.width - 2 * self.padding
        self.cards_per_row = 5
        self.card_width = (available_width - (self.cards_per_row - 1) * self.padding) // self.cards_per_row
        self.card_height = int(self.card_width * 1.4)

        self.card_rects.clear()
        self.card_views.clear()
        x_start = right_rect.x + self.padding
        y_start = right_rect.y + 150 - self.scroll_offset

        for idx, card in enumerate(self.all_cards):
            row = idx // self.cards_per_row
            col = idx % self.cards_per_row
            x = x_start + col * (self.card_width + self.padding)
            y = y_start + row * (self.card_height + self.padding)
            rect = pygame.Rect(x, y, self.card_width, self.card_height)

            if rect.bottom < right_rect.y + 150 or rect.top > self.screen_height:
                continue

            # Tworzymy CardView
            view = CardView(card, self.localization)
            view.update_rect(rect.x, rect.y, rect.width, rect.height)
            view.draw(self.screen, rect.x, rect.y, rect.width, rect.height, language=self.language)
            self.card_views.append(view)

            # Licznik kopii
            self.draw_card_counter(view, rect.x, rect.y, rect.width, rect.height)

            # Zielona ramka, jeśli karta jest w talii
            if self.deck_counts.get(card.name_key, 0) > 0:
                pygame.draw.rect(self.screen, (0, 200, 0), rect, 4)
            else:
                pygame.draw.rect(self.screen, BLACK, rect, 2)

            self.card_rects.append((rect, card))

        # ---------- PRZYCISKI ----------
        mouse_pos = pygame.mouse.get_pos()
        for btn in self.buttons:
            rect = btn["rect"]
            hover = rect.collidepoint(mouse_pos)
            color = BUTTON_HOVER_COLOR if hover else BUTTON_COLOR
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, BLACK, rect, 2)
            text_surf, text_rect = fonts.render_text(
                btn["text"],
                size_key="StoryScript S",
                color=TEXT_COLOR,
                center=rect.center
            )
            self.screen.blit(text_surf, text_rect)

        # ---------- TOOLTIP (używamy CardView) ----------
        if self.hovered_card:
            # Znajdujemy odpowiedni CardView
            for view in self.card_views:
                if view.card == self.hovered_card:
                    font_small = pygame.font.Font(None, 16)
                    font_medium = pygame.font.Font(None, 20)
                    view.draw_tooltip(self.screen, font_small=font_small, font_medium=font_medium, game_logic=None)
                    break
            else:
                for view in self.deck_card_views:
                    if view.card == self.hovered_card:
                        font_small = pygame.font.Font(None, 16)
                        font_medium = pygame.font.Font(None, 20)
                        view.draw_tooltip(self.screen, font_small=font_small, font_medium=font_medium, game_logic=None)
                        break

        # ---------- PODGLĄD (używamy CardView) ----------
        if self.preview_visible and self.preview_card:
            overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))
            
            # Tworzymy CardView dla podglądu
            preview_view = CardView(self.preview_card, self.localization)
            preview_view.draw_preview(
                self.screen,
                self.preview_x, self.preview_y,
                self.preview_width, self.preview_height,
                language=self.language
            )

    def run(self):
        last_time = pygame.time.get_ticks()
        while self.running:
            dt = pygame.time.get_ticks() - last_time
            last_time = pygame.time.get_ticks()
            self.handle_events()
            self.draw()
            pygame.display.flip()
            self.clock.tick(FPS)

def deck_editor_loop(screen, clock, language="pl", deck_name="default"):
    editor = DeckEditor(screen, clock, language, deck_name)
    editor.run()