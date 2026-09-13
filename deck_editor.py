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
from card_renderer import draw_card, draw_tooltip, get_card_color, load_svg_icon
from card_view import CardView
import random

# ---------- WCZYTYWANIE KART ----------
ALL_CARDS = []
CARDS_FILE = os.path.join("defines", "cards.lua")
DECKS_DIR = "decks"
ICON_FOLDER_PATH = os.path.join("images", "cards", "icons", "playing_cards.svg")
ICON_CHART_PATH  = os.path.join("images", "cards", "icons", "ssid_chart.svg")

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

class DeckEditorCardTypeIcon:
    """Klikalna ikona typu karty w nagłówku edytora talii.

    Trzyma swój stan (selected) i grafikę. Sam się rysuje i sam
    rozpoznaje kliknięcia. DeckEditor tylko dostarcza aktualną liczbę
    kart danego typu oraz pozycję do narysowania.
    """

    ICON_SIZE = 64
    GAP = 8                 # odstęp ikona ↔ liczba
    PAD_BETWEEN = 20        # odstęp między kolejnymi ikonami

    def __init__(self, card_type, icon_surface: pygame.Surface):
        self.card_type = card_type
        self.icon = icon_surface          # już przeskalowany do ICON_SIZE
        self.selected = True              # domyślnie włączony filtr
        self.rect = None                  # aktualny prostokąt (przy rysowaniu)
        self.hovered = False
        self.count = 0                    # aktualna liczba kart w talii

    # -------- geometria --------
    def width(self, count_font) -> int:
        """Szerokość elementu (ikona + odstęp + liczba) dla danej liczby."""
        txt = count_font.render(str(self.count), True, (0, 0, 0))
        return self.ICON_SIZE + self.GAP + txt.get_width()

    # -------- rysowanie --------
    def draw(self, surface, x: int, cy: int, count_font, mouse_pos) -> int:
        """Rysuje ikonę i liczbę. Zwraca x po prawej stronie elementu."""
        y = cy - self.ICON_SIZE // 2
        self.rect = pygame.Rect(x, y, self.ICON_SIZE, self.ICON_SIZE)
        self.hovered = self.rect.collidepoint(mouse_pos)

        if self.selected:
            surface.blit(self.icon, (x, y))
            if self.hovered:
                pygame.draw.rect(surface, (0, 200, 0), self.rect, 2)
        else:
            dark = self.icon.copy()
            dark.set_alpha(80)
            surface.blit(dark, (x, y))

            ov = pygame.Surface((self.ICON_SIZE, self.ICON_SIZE),
                                pygame.SRCALPHA)
            ov.fill((0, 0, 0, 140))
            surface.blit(ov, (x, y))

            border = (200, 60, 60) if self.hovered else (120, 60, 60)
            pygame.draw.rect(surface, border, self.rect, 2)

        color = (255, 255, 200) if self.selected else (120, 120, 120)
        txt = count_font.render(str(self.count), True, color)
        tx = x + self.ICON_SIZE + self.GAP
        ty = cy - txt.get_height() // 2
        surface.blit(txt, (tx, ty))

        return tx + txt.get_width()

    # -------- interakcja --------
    def handle_click(self, pos) -> bool:
        """Zwraca True, jeśli kliknięto w tę ikonę."""
        if self.rect and self.rect.collidepoint(pos):
            self.selected = not self.selected
            return True
        return False

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

        # ---------- IKONY PRZYCISKÓW (SVG) ----------
        self.icon_folder = load_svg_icon(ICON_FOLDER_PATH, 24)
        self.icon_chart  = load_svg_icon(ICON_CHART_PATH, 24)
        self.icon_folder_small = load_svg_icon(ICON_FOLDER_PATH, 20)

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

        # ---------- WYBIERAK TALII (modal) ----------
        self.deck_picker_visible = False
        self._picker_buttons = []      # [{"rect": Rect, "deck": str}]
        self._picker_bg_rect = None
        self._picker_close_rect = None

        # ---------- IKONY TYPÓW (cache) ----------
        self.type_icons_cache = {}   # (CardType, size) -> Surface | None

        # ---------- IKONY TYPÓW (obiekty) ----------
        self.type_icons = []
        self._build_type_icons()

        # ---------- MODAL STATYSTYK (wykres) ----------
        self.stats_visible = False
        self._stats_bg_rect = None
        self._stats_close_rect = None

    def _build_type_icons(self):
        """Buduje listę klikalnych ikon typów (raz na start / po resize)."""
        from card import CardType
        self.type_icons = []
        for ct in CardType:
            icon = self._get_type_icon(ct, DeckEditorCardTypeIcon.ICON_SIZE)
            if icon is None:
                continue
            self.type_icons.append(DeckEditorCardTypeIcon(ct, icon))

    # ---------- STATYSTYKI ----------
    def _open_stats(self):
        """Otwiera modal ze statystykami talii."""
        if self.deck_picker_visible:
            self._close_deck_picker()
        self._build_stats_layout()
        self.stats_visible = True

    def _close_stats(self):
        self.stats_visible = False
        self._stats_bg_rect = None
        self._stats_close_rect = None

    def _build_stats_layout(self):
        panel_w = min(1000, self.screen_width - 40)
        panel_h = min(700, self.screen_height - 40)
        px = (self.screen_width - panel_w) // 2
        py = (self.screen_height - panel_h) // 2
        self._stats_bg_rect = pygame.Rect(px, py, panel_w, panel_h)
        self._stats_close_rect = pygame.Rect(
            px + panel_w - 160, py + 15, 140, 35
        )

    def _handle_stats_click(self, pos):
        if self._stats_close_rect and self._stats_close_rect.collidepoint(pos):
            self._close_stats()
            return True
        if self._stats_bg_rect and not self._stats_bg_rect.collidepoint(pos):
            self._close_stats()
            return True
        return True

    def _compute_stats_data(self):
        """Zwraca (data, N).

        data: {CardType: [(x, y), ...]} – punkty linii każdego typu, gdzie
              x = pozycja karty w talii w ORYGINALNEJ kolejności (1..N),
              y = narastająca liczba kart danego typu do pozycji x.
        N:    całkowita liczba kart w talii.
        """
        N = len(self.deck)
        if N == 0:
            return {}, 0

        type_order = {ct: i for i, ct in enumerate(CardType)}

        # Zbiór typów obecnych w talii – w deterministycznej kolejności
        present_types = sorted(
            set(c.card_type for c in self.deck),
            key=lambda ct: type_order.get(ct, 99),
        )

        counters = {ct: 0 for ct in present_types}
        data = {ct: [] for ct in present_types}

        # Iterujemy po oryginalnej kolejności talii (self.deck)
        for i, card in enumerate(self.deck, start=1):
            counters[card.card_type] += 1
            for ct in present_types:
                data[ct].append((i, counters[ct]))

        return data, N

    def _draw_stats_modal(self):
        if not self.stats_visible or not self._stats_bg_rect:
            return

        # overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))

        bg = self._stats_bg_rect
        pygame.draw.rect(self.screen, (35, 35, 50), bg)
        pygame.draw.rect(self.screen, (200, 200, 220), bg, 2)

        # tytuł
        title = f"Statystyki talii: {self.current_deck_name}"
        ts, tr = fonts.render_text(title, size_key="StoryScript L", color=WHITE,
                                   center=(bg.centerx, bg.y + 35))
        self.screen.blit(ts, tr)

        # przycisk "Zamknij" w prawym górnym rogu
        rect = self._stats_close_rect
        mouse_pos = pygame.mouse.get_pos()
        hover = rect.collidepoint(mouse_pos)
        color = (180, 80, 80) if hover else (150, 60, 60)
        pygame.draw.rect(self.screen, color, rect)
        pygame.draw.rect(self.screen, BLACK, rect, 2)
        cs, cr = fonts.render_text("Zamknij", size_key="StoryScript S",
                                   color=WHITE, center=rect.center)
        self.screen.blit(cs, cr)

        data, N = self._compute_stats_data()
        if N == 0:
            msg, mr = fonts.render_text("Pusta talia", size_key="StoryScript M",
                                        color=(150, 150, 150),
                                        center=(bg.centerx, bg.centery))
            self.screen.blit(msg, mr)
            return

        # obszar wykresu
        chart_left = bg.x + 80
        chart_top = bg.y + 80
        chart_right = bg.right - 40
        chart_bottom = bg.bottom - 220
        chart_w = chart_right - chart_left
        chart_h = chart_bottom - chart_top

        pygame.draw.rect(self.screen, (20, 20, 30),
                         (chart_left, chart_top, chart_w, chart_h))
        pygame.draw.rect(self.screen, (100, 100, 120),
                         (chart_left, chart_top, chart_w, chart_h), 1)

        # max Y = największa liczba kart jednego typu
        max_y = 1
        for pts in data.values():
            for _, y in pts:
                if y > max_y:
                    max_y = y

        if max_y <= 5:
            step = 1
        elif max_y <= 10:
            step = 2
        elif max_y <= 20:
            step = 5
        elif max_y <= 100:
            step = 10
        else:
            step = max(1, max_y // 10)

        tick_vals = list(range(0, max_y + 1, step))
        if tick_vals[-1] != max_y:
            tick_vals.append(max_y)

        for val in tick_vals:
            py_line = chart_bottom - (val / max_y) * chart_h
            pygame.draw.line(self.screen, (60, 60, 80),
                             (chart_left, py_line), (chart_right, py_line), 1)
            lbl_s, lbl_r = fonts.render_text(str(val),
                                             size_key="StoryScript XXS",
                                             color=(200, 200, 200))
            lbl_r.midright = (chart_left - 8, py_line)
            self.screen.blit(lbl_s, lbl_r)

        # osie X – etykiety 1..N
        x_step = 1 if N <= 15 else max(1, N // 10)
        for x in range(1, N + 1, x_step):
            px_line = chart_left + (x - 1) / max(1, N - 1) * chart_w
            pygame.draw.line(self.screen, (60, 60, 80),
                             (px_line, chart_bottom), (px_line, chart_bottom + 4), 1)
            lbl_s, lbl_r = fonts.render_text(str(x),
                                             size_key="StoryScript XXS",
                                             color=(200, 200, 200))
            lbl_r.midtop = (px_line, chart_bottom + 6)
            self.screen.blit(lbl_s, lbl_r)

        # etykiety osi
        lbl_s, lbl_r = fonts.render_text("Liczba kart w talii",
                                         size_key="StoryScript XS",
                                         color=(220, 220, 220))
        lbl_r.midtop = (chart_left + chart_w // 2, chart_bottom + 30)
        self.screen.blit(lbl_s, lbl_r)

        # konwersja (x, y) -> piksele
        def to_px(x, y):
            px_p = chart_left + (x - 1) / max(1, N - 1) * chart_w
            py_p = chart_bottom - (y / max_y) * chart_h
            return px_p, py_p

        # linie
        for ct, pts in data.items():
            color = get_card_color(ct)
            px_pts = [to_px(x, y) for x, y in pts]
            if len(px_pts) >= 2:
                pygame.draw.lines(self.screen, color, False, px_pts, 2)
            for p in px_pts:
                pygame.draw.circle(self.screen, color,
                                   (int(p[0]), int(p[1])), 3)

        # legenda
        legend_x = bg.x + 40
        legend_y = chart_bottom + 60
        row_limit = bg.right - 40
        for ct in data.keys():
            count = data[ct][-1][1] if data[ct] else 0
            color = get_card_color(ct)
            pygame.draw.rect(self.screen, color, (legend_x, legend_y, 14, 14))
            pygame.draw.rect(self.screen, (0, 0, 0),
                             (legend_x, legend_y, 14, 14), 1)
            text = f"{ct.value} ({count})"
            t_s, t_r = fonts.render_text(text,
                                         size_key="StoryScript XXS",
                                         color=(220, 220, 220),
                                         topleft=(legend_x + 20, legend_y))
            self.screen.blit(t_s, t_r)
            legend_x += 20 + t_r.width + 25
            if legend_x > row_limit - 100:
                legend_x = bg.x + 40
                legend_y += 22

    # ---------- WYBIERAK TALII ----------
    def _open_deck_picker(self):
        """Otwiera modal z listą talii i buduje jego layout."""
        self._build_picker_layout()
        self.deck_picker_visible = True

    def _close_deck_picker(self):
        self.deck_picker_visible = False
        self._picker_buttons = []
        self._picker_bg_rect = None
        self._picker_close_rect = None

    def _build_picker_layout(self):
        """Liczy pozycje przycisków modala na podstawie rozmiaru ekranu."""
        decks = self.get_deck_list()
        n = len(decks)

        panel_w = 420
        padding = 20
        btn_h = 42
        btn_spacing = 6
        header_h = 50
        close_h = 42

        panel_h = (padding
                   + header_h
                   + n * (btn_h + btn_spacing)
                   + close_h
                   + padding + 10)

        px = (self.screen_width - panel_w) // 2
        py = (self.screen_height - panel_h) // 2
        self._picker_bg_rect = pygame.Rect(px, py, panel_w, panel_h)

        self._picker_buttons = []
        y = py + padding + header_h
        for name in decks:
            rect = pygame.Rect(px + padding, y, panel_w - 2 * padding, btn_h)
            self._picker_buttons.append({"rect": rect, "deck": name})
            y += btn_h + btn_spacing

        self._picker_close_rect = pygame.Rect(
            px + padding, y + 10, panel_w - 2 * padding, close_h
        )

    def _handle_picker_click(self, pos):
        """Obsługuje klik w modalu. Zwraca True, jeśli event został zjedzony."""
        # 1) kliknięcie w talię?
        for btn in self._picker_buttons:
            if btn["rect"].collidepoint(pos):
                self._switch_deck(btn["deck"])
                self._close_deck_picker()
                return True
        # 2) kliknięcie w "Zamknij"?
        if self._picker_close_rect and self._picker_close_rect.collidepoint(pos):
            self._close_deck_picker()
            return True
        # 3) kliknięcie poza modalem?
        if self._picker_bg_rect and not self._picker_bg_rect.collidepoint(pos):
            self._close_deck_picker()
            return True
        # 4) kliknięcie wewnątrz modala, ale poza przyciskami — zjadamy, nic nie robimy
        return True

    def _switch_deck(self, name: str):
        """Przełącza aktualnie edytowaną talię (zapis starej, wczytanie nowej)."""
        if name == self.current_deck_name:
            return
        self.save_deck(self.current_deck_name)
        self.load_deck(name)
        self.current_deck_name = name
        self.deck_list = self.get_deck_list()
        for btn in self.buttons:
            if btn["type"] == "deck_selector":
                btn["text"] = f"📂 {name}"
        print(f"Wczytano talię: {name}")

    def _draw_deck_picker(self):
        """Rysuje modal z listą talii."""
        if not self.deck_picker_visible or not self._picker_bg_rect:
            return

        # przyciemnij tło
        overlay = pygame.Surface((self.screen_width, self.screen_height),
                                 pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # panel
        bg = self._picker_bg_rect
        pygame.draw.rect(self.screen, (45, 45, 65), bg)
        pygame.draw.rect(self.screen, (200, 200, 220), bg, 2)

        # nagłówek
        title_surf, title_rect = fonts.render_text(
            "Wybierz talię",
            size_key="StoryScript M", color=WHITE,
            center=(bg.centerx, bg.y + 30),
        )
        self.screen.blit(title_surf, title_rect)

        # przyciski talii
        mouse_pos = pygame.mouse.get_pos()
        for btn in self._picker_buttons:
            rect = btn["rect"]
            is_current = (btn["deck"] == self.current_deck_name)
            hover = rect.collidepoint(mouse_pos)

            if is_current:
                color = (80, 140, 80)
            else:
                color = BUTTON_HOVER_COLOR if hover else BUTTON_COLOR

            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, BLACK, rect, 2)

            label = btn["deck"] + (" *" if is_current else "")
            self._draw_icon_text(
                label,
                self.icon_folder_small,
                center=rect.center,
                text_color=WHITE,
                size_key="StoryScript S",
            )

        # przycisk "Zamknij"
        if self._picker_close_rect:
            rect = self._picker_close_rect
            hover = rect.collidepoint(mouse_pos)
            color = (180, 80, 80) if hover else (150, 60, 60)
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, BLACK, rect, 2)
            c_surf, c_rect = fonts.render_text(
                "Zamknij", size_key="StoryScript S", color=WHITE,
                center=rect.center,
            )
            self.screen.blit(c_surf, c_rect)

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
            "rect": pygame.Rect(x, btn_y, 160, btn_height),
            "text": self.current_deck_name,
            "icon": self.icon_folder,
            "action": self.show_deck_selection,
            "type": "deck_selector"
        })

        x += 150

        self.buttons.append({
            "rect": pygame.Rect(x, btn_y, 170, btn_height),
            "text": "Statystyki",
            "icon": self.icon_chart,
            "action": self._open_stats,
            "type": "stats"
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
                    btn["text"] = name
        elif name in self.deck_list:
            print(f"Talia '{name}' już istnieje!")
        else:
            print("Anulowano.")

    def show_deck_selection(self):
        """Otwiera modal wyboru talii (zamiast terminala)."""
        self._open_deck_picker()

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

    def _draw_icon_text(self, text, icon, center,
                        text_color=(255, 255, 255),
                        size_key="StoryScript S", gap=8):
        """Rysuje ikonę + tekst wyśrodkowane w pionie wokół `center`."""
        t_surf, t_rect = fonts.render_text(
            text, size_key=size_key, color=text_color
        )
        icon_w = icon.get_width() if icon else 0
        icon_w_with_gap = icon_w + (gap if icon else 0)
        total_w = icon_w_with_gap + t_rect.width

        x0 = center[0] - total_w // 2
        cy = center[1]

        if icon:
            iy = cy - icon.get_height() // 2
            self.screen.blit(icon, (x0, iy))
            x0 += icon_w + gap

        self.screen.blit(t_surf, (x0, cy - t_surf.get_height() // 2))

    def _get_type_icon(self, card_type, size: int = 64):
        """Zwraca przeskalowaną ikonę typu karty (cache) lub None."""
        from card_renderer import load_image, ICONS_DIR, _icon_cache
        key = (card_type, size)
        if key in self.type_icons_cache:
            return self.type_icons_cache[key]
        filename = f"{card_type.value}.png"
        img = load_image(filename, _icon_cache, ICONS_DIR)
        if img is None:
            # Fallback – prostokąt z pierwszą literą typu
            surf = pygame.Surface((size, size), pygame.SRCALPHA)
            surf.fill((70, 70, 70, 180))
            pygame.draw.rect(surf, (120, 120, 120), surf.get_rect(), 2)
            font = fonts.get_font("StoryScript M")
            letter = card_type.value[0] if card_type.value else "?"
            text = font.render(letter, True, (200, 200, 200))
            surf.blit(text, text.get_rect(center=(size // 2, size // 2)))
            self.type_icons_cache[key] = surf
            return surf
        scaled = pygame.transform.smoothscale(img, (size, size))
        self.type_icons_cache[key] = scaled
        return scaled

    def _draw_deck_summary(self, right_rect):
        """Rysuje rząd klikalnych ikon typów + liczby kart danego typu.

        Kliknięcie ikony przełącza filtr (selected/not selected).
        Odznaczone typy są wyszarzone i wykluczone z prawego panelu.
        """
        if not self.type_icons:
            s, r = fonts.render_text(
                "Brak ikon typów", size_key="StoryScript M",
                color=(150, 150, 150),
                center=(right_rect.centerx, 75),
            )
            self.screen.blit(s, r)
            return

        # Zaktualizuj liczby
        counts = {}
        for c in self.deck:
            counts[c.card_type] = counts.get(c.card_type, 0) + 1
        for ic in self.type_icons:
            ic.count = counts.get(ic.card_type, 0)

        count_font = fonts.get_font("StoryScript S")
        pad_between = DeckEditorCardTypeIcon.PAD_BETWEEN

        # Całkowita szerokość rzędu
        total_w = sum(ic.width(count_font) for ic in self.type_icons)
        total_w += pad_between * (len(self.type_icons) - 1)

        x = right_rect.centerx - total_w // 2
        cy = 92
        mouse_pos = pygame.mouse.get_pos()

        for ic in self.type_icons:
            x = ic.draw(self.screen, x, cy, count_font, mouse_pos)
            x += pad_between

    def _is_type_visible(self, card_type) -> bool:
        """True, jeśli karty danego typu mają być widoczne w prawym panelu.

        Jeśli typ nie ma ikony (nie ma go w self.type_icons), traktujemy
        go jako zawsze widoczny.
        """
        for ic in self.type_icons:
            if ic.card_type == card_type:
                return ic.selected
        return True
            
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
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if self.stats_visible:
                    self._close_stats()
                    continue
                if self.deck_picker_visible:
                    self._close_deck_picker()
                    continue
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
                    # 1) Modal statystyk – zjada kliknięcia
                    if self.stats_visible:
                        self._handle_stats_click(event.pos)
                        return                    
                    # 2) Modal wyboru talii – zjada kliknięcia
                    if self.deck_picker_visible:
                        self._handle_picker_click(event.pos)
                        return

                    mouse_pos = event.pos

                    # 2) Klik w ikonę filtra typu
                    for ic in self.type_icons:
                        if ic.handle_click(mouse_pos):
                            return

                    # 3) Przyciski
                    for btn in self.buttons:
                        if btn["rect"].collidepoint(mouse_pos) and btn["action"] is not None:
                            btn["action"]()
                            return

                    # 4) Prawy panel – dodaj kopię
                    for rect, card in self.card_rects:
                        if rect.collidepoint(mouse_pos):
                            if self.deck_counts.get(card.name_key, 0) < getattr(card, 'max_in_deck', 6):
                                self.deck.append(card)
                                self.deck_counts[card.name_key] = self.deck_counts.get(card.name_key, 0) + 1
                            return

                    # 5) Lewy panel – usuń kopię
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

        self._draw_icon_text(
            self.current_deck_name,
            self.icon_folder_small,
            center=(left_width // 2, 115),
            text_color=(200, 200, 200),
            size_key="StoryScript S",
        )

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

        # Nagłówek = podsumowanie typów w talii (ikony + liczniki)
        header_h = 150
        header_rect = pygame.Rect(right_rect.x, right_rect.y, right_rect.width, header_h)
        pygame.draw.rect(self.screen, (30, 30, 30), header_rect)        
        self._draw_deck_summary(right_rect)

        # --- Karty: klipujemy do obszaru poniżej nagłówka ---
        old_clip = self.screen.get_clip()
        self.screen.set_clip(pygame.Rect(
            right_rect.x,
            right_rect.y + header_h,
            right_rect.width,
            right_rect.height - header_h,
        ))

        available_width = right_rect.width - 2 * self.padding
        self.cards_per_row = 5
        self.card_width = (available_width - (self.cards_per_row - 1) * self.padding) // self.cards_per_row
        self.card_height = int(self.card_width * 1.4)

        self.card_rects.clear()
        self.card_views.clear()
        x_start = right_rect.x + self.padding
        y_start = right_rect.y + 150 - self.scroll_offset

        visible_cards = [c for c in self.all_cards
                         if self._is_type_visible(c.card_type)]
        if not visible_cards:
            self.scroll_offset = 0

        for idx, card in enumerate(visible_cards):
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

        # --- Koniec klipowania ---
        self.screen.set_clip(old_clip)

        # ---------- PRZYCISKI ----------
        mouse_pos = pygame.mouse.get_pos()
        for btn in self.buttons:
            rect = btn["rect"]
            hover = rect.collidepoint(mouse_pos)
            color = BUTTON_HOVER_COLOR if hover else BUTTON_COLOR
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, BLACK, rect, 2)
            self._draw_icon_text(
                btn["text"],
                btn.get("icon"),
                center=rect.center,
                text_color=TEXT_COLOR,
                size_key="StoryScript S",
            )

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

        # ---------- WYBIERAK TALII (modal, na wierzchu) ----------
        self._draw_deck_picker()

        # ---------- STATYSTYKI (modal, na wierzchu) ----------
        self._draw_stats_modal()

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