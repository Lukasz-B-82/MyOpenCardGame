# game_view.py
import pygame
import time
from constants import *
from card_view import CardView
from card_renderer import draw_card
from fonts import fonts
from card import Zone

class GameView:
    def __init__(self, screen, logic, localization, card_back_image, background_image):
        self.screen = screen
        self.logic = logic
        self.localization = localization
        self.card_back_image = card_back_image
        self.background_image = background_image
        self.screen_width, self.screen_height = screen.get_size()
        self.zone_rects = {}
        self.card_views = []
        self.hovered_card_view = None
        self.preview_view = None
        self.preview_visible = False
        self.preview_width = 512
        self.preview_height = 768

        # Stałe dla stref
        self.zone_order = [Zone.FRONT, Zone.SECOND, Zone.BACK, Zone.STATE]
        self.zone_names = {
            Zone.FRONT: "Front",
            Zone.SECOND: "Druga linia",
            Zone.BACK: "Zaplecze",
            Zone.STATE: "Państwo"
        }
        self.zone_width = 375
        self.zone_spacing = 10
        self.zone_min_height = 150
        self.zone_max_height = 350
        self.zone_start_y = 0

        # Kolory dla zasobów
        self.resource_colors = {
            "food_production": (0, 200, 0),
            "production": (50, 100, 250),
            "steal": (180, 180, 200),
            "logistics": (200, 200, 100),
            "oil_production": (50, 50, 50),
            "iron_production": (200, 150, 100),
            "fuel_production": (75, 75, 75),
        }

        self.end_turn_button_rect = pygame.Rect(0, 0, 200, 50)

        # ---------- SYSTEM KOMUNIKATÓW ----------
        self.messages = []  # lista (tekst, kolor, czas_pojawienia)
        self.message_duration = 5.0  # sekundy
        self.message_font_size = 28
        self.message_padding = 15

    def add_message(self, text: str, msg_type: str = "info"):
        """
        Dodaje komunikat do wyświetlenia.
        msg_type: "info" (niebieski), "error" (czerwony), "success" (zielony)
        """
        colors = {
            "info": (100, 150, 255),
            "error": (255, 80, 80),
            "success": (80, 255, 80),
        }
        color = colors.get(msg_type, (255, 255, 255))
        self.messages.append((text, color, time.time()))

    def draw_messages(self):
        """Rysuje wszystkie aktywne komunikaty w górnej części ekranu."""
        now = time.time()
        # Usuń stare komunikaty
        self.messages = [m for m in self.messages if now - m[2] < self.message_duration]

        if not self.messages:
            return

        font = pygame.font.Font(None, self.message_font_size)
        line_height = font.get_height() + self.message_padding

        # Oblicz wysokość wszystkich komunikatów
        total_height = len(self.messages) * line_height + self.message_padding * 2
        start_y = 80  # pod paskiem informacyjnym

        for i, (text, color, timestamp) in enumerate(self.messages):
            # Tło dla każdego komunikatu
            text_surf = font.render(text, True, color)
            text_rect = text_surf.get_rect()
            
            # Szerokość tła = szerokość tekstu + padding
            bg_width = text_rect.width + self.message_padding * 4
            bg_height = text_rect.height + self.message_padding * 2
            bg_x = (self.screen_width - bg_width) // 2
            bg_y = start_y + i * line_height

            # Półprzezroczyste tło
            bg = pygame.Surface((bg_width, bg_height), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 200))
            self.screen.blit(bg, (bg_x, bg_y))
            
            # Ramka w kolorze komunikatu
            pygame.draw.rect(self.screen, color, (bg_x, bg_y, bg_width, bg_height), 2)

            # Tekst
            text_x = bg_x + self.message_padding * 2
            text_y = bg_y + self.message_padding
            self.screen.blit(text_surf, (text_x, text_y))

    def update_size(self, width, height):
        self.screen_width = width
        self.screen_height = height

    def draw(self):
        self.card_views.clear()
        self.screen.blit(self.background_image, (0, 0))
        
        self.draw_info()
        self.draw_opponents()
        self.draw_zones()
        self.draw_deck()
        self.draw_discard()
        self.draw_hand()
        self.draw_initiative_bar()
        self.draw_resources()
        self.draw_tooltip()
        self.draw_preview()
        self.draw_end_turn()
        self.draw_messages()

    def calculate_zone_heights(self, counts):
        total_cards = sum(counts)
        num_zones = len(self.zone_order)
        min_height = self.zone_min_height
        max_height = self.zone_max_height
        available_height = max_height - min_height

        if total_cards == 0:
            return [min_height + available_height // num_zones] * num_zones

        percentages = []
        for count in counts:
            if count == 0:
                percentages.append(0.05)
            else:
                percentages.append(count / total_cards)

        total_pct = sum(percentages)
        percentages = [p / total_pct for p in percentages]

        heights = []
        for p in percentages:
            h = min_height + p * available_height
            heights.append(int(h))
        return heights

    def draw_zones(self):
        player = self.logic.current_player
        allowed_zones = self.logic.get_allowed_zones()

        zone_height = 200
        margin = 50
        inner_margin = 10
        available_width = self.screen_width - (2 * margin) - (3 * inner_margin)

        counts = [len(player.zones.get(zone, [])) for zone in self.zone_order]
        total_cards = sum(counts)

        if total_cards == 0:
            widths = [available_width / len(self.zone_order)] * len(self.zone_order)
        else:
            min_pct = 0.15
            pcts = []
            for count in counts:
                if count == 0:
                    pcts.append(min_pct)
                else:
                    pcts.append(count / total_cards)
            total_pct = sum(pcts)
            pcts = [p / total_pct for p in pcts]
            widths = [available_width * p for p in pcts]

        widths = [int(w) for w in widths]
        diff = available_width - sum(widths)
        if diff != 0:
            widths[-1] += diff

        bottom_start = int(self.screen_height * 0.6)
        zones_y = bottom_start

        self.zone_rects.clear()
        x = margin
        y = zones_y

        for i, zone in enumerate(self.zone_order):
            if i > 0:
                x += inner_margin
            width = widths[i]
            rect = pygame.Rect(x, y, width, zone_height)
            self.zone_rects[zone] = rect

            # Tło
            is_allowed = (
                zone in allowed_zones and
                self.logic.check_requirements(self.logic.selected_card, player)
            )
            bg_color = (60, 200, 60, 80) if is_allowed else (60, 60, 80, 75)
            bg = pygame.Surface((width, zone_height), pygame.SRCALPHA)
            bg.fill(bg_color)
            self.screen.blit(bg, (x, y))
            border_color = (0, 255, 0, 200) if is_allowed else (200, 200, 200, 50)
            pygame.draw.rect(self.screen, border_color, rect, 2 if not is_allowed else 4)

            # Nazwa z licznikiem
            cards_in_zone = player.zones.get(zone, [])
            count = len(cards_in_zone)
            display_name = f"{self.zone_names[zone]} ({count})"
            name_surf, _ = fonts.render_text(
                display_name,
                size_key="StoryScript XS",
                color=WHITE,
                center=(rect.centerx, rect.y + 15)
            )
            self.screen.blit(name_surf, name_surf.get_rect(center=(rect.centerx, rect.y + 12)))

            # Karty w strefie
            if cards_in_zone:
                card_spacing = 5
                max_card_width = 100
                total_needed = len(cards_in_zone) * (max_card_width + card_spacing) - card_spacing
                if total_needed <= width - 20:
                    card_width = max_card_width
                else:
                    available_card_width = width - 20
                    card_width = (available_card_width + card_spacing) / len(cards_in_zone) - card_spacing
                    card_width = max(30, int(card_width))

                card_height = int(card_width * 1.4)
                total_cards_width = len(cards_in_zone) * (card_width + card_spacing) - card_spacing
                start_x_cards = rect.centerx - total_cards_width // 2
                card_y = rect.centery - card_height // 2 - 5

                for j, card in enumerate(cards_in_zone):
                    cx = start_x_cards + j * (card_width + card_spacing)
                    view = CardView(card, self.localization)
                    view.update_rect(cx, card_y, card_width, card_height)
                    view.draw(self.screen, cx, card_y, card_width, card_height, language=self.logic.language)
                    self.card_views.append(view)

                    # Rysuj załączniki
                    if card.attached_cards:
                        attach_offset_x = 15
                        attach_offset_y = 15
                        attach_scale = 1
                        attach_width = int(card_width * attach_scale)
                        attach_height = int(card_height * attach_scale)
                        for attach_card in card.attached_cards:
                            ax = cx + attach_offset_x
                            ay = card_y + attach_offset_y
                            attach_view = CardView(attach_card, self.localization)
                            attach_view.update_rect(ax, ay, attach_width, attach_height)
                            attach_view.draw(self.screen, ax, ay, attach_width, attach_height, language=self.logic.language)
                            self.card_views.append(attach_view)
                            attach_offset_x += 10
                            attach_offset_y += 10

                    if self.logic.selected_card is not None and self.logic.can_attach_to_card(self.logic.selected_card, card):
                        pygame.draw.rect(self.screen, (0, 255, 0), view.rect, 2)

            else:
                empty_surf, _ = fonts.render_text(
                    "pusta",
                    size_key="StoryScript S",
                    color=(150, 150, 150),
                    center=(rect.centerx, rect.centery + 10)
                )
                self.screen.blit(empty_surf, empty_surf.get_rect(center=(rect.centerx, rect.centery + 10)))

            x += width

    def draw_info(self):
        info_height = int(self.screen_height * 0.1)
        bg = pygame.Surface((self.screen_width, info_height), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 100))
        self.screen.blit(bg, (0, 0))
        info = f"Tura {self.logic.turn} | Gracz: {self.logic.current_player.name}"
        surf, rect = fonts.render_text(info, size_key="StoryScript L", color=WHITE, center=(self.screen_width//2, info_height//2))
        self.screen.blit(surf, rect)

    def draw_deck(self):
        player = self.logic.current_player
        deck_x = 20
        deck_y = self.screen_height - 180
        deck_width = 100
        deck_height = 140
        for i in range(min(len(player.deck), 12)):
            offset = i * 2
            self.screen.blit(self.card_back_image, (deck_x + offset, deck_y - offset))
        count_text = str(len(player.deck))
        surf, _ = fonts.render_text(count_text, size_key="StoryScript XS", color=WHITE)
        self.screen.blit(surf, (deck_x + deck_width//2 - surf.get_width()//2, deck_y + deck_height + 5))

    def draw_discard(self):
        player = self.logic.current_player
        discard_x = self.screen_width - 120
        discard_y = self.screen_height - 180
        discard_width = 100
        discard_height = 140
        for i in range(min(len(player.discard), 12)):
            offset = i * 2
            self.screen.blit(self.card_back_image, (discard_x + offset, discard_y - offset))
        count_text = str(len(player.discard))
        surf, _ = fonts.render_text(count_text, size_key="StoryScript M", color=WHITE)
        self.screen.blit(surf, (discard_x + discard_width//2 - surf.get_width()//2, discard_y + discard_height + 5))

    def draw_hand(self):
        player = self.logic.current_player
        
        bottom_start = int(self.screen_height * 0.6)
        bottom_height = int(self.screen_height * 0.4)
        hand_height = bottom_height // 2.5
        hand_y = bottom_start + hand_height + 50
        hand_width = self.screen_width - 500
        hand_x = 150

        panel = pygame.Surface((hand_width, hand_height), pygame.SRCALPHA)
        panel.fill((150, 150, 150, 80))
        pygame.draw.rect(panel, (100, 100, 150, 255), panel.get_rect(), 2)
        self.screen.blit(panel, (hand_x, hand_y))

        hand = player.hand
        if hand:
            card_width = 100
            card_height = 140
            spacing = 10
            total_width = len(hand) * (card_width + spacing) - spacing
            start_x = hand_x + (hand_width - total_width) // 2
            card_y = hand_y + (hand_height - card_height) // 2
            for i, card in enumerate(hand):
                x = start_x + i * (card_width + spacing)
                rect = pygame.Rect(x, card_y, card_width, card_height)
                view = CardView(card, self.localization)
                view.update_rect(x, card_y, card_width, card_height)
                view.draw(self.screen, x, card_y, card_width, card_height, language=self.logic.language)
                if self.logic.selected_card == card:
                    view.draw_selected_effect(self.screen)
                self.card_views.append(view)

    def draw_initiative_bar(self):
        player = self.logic.current_player
        
        bottom_start = int(self.screen_height * 0.6)
        bottom_height = int(self.screen_height * 0.4)
        hand_height = bottom_height // 2.5
        hand_y = bottom_start + hand_height + 50
        hand_width = self.screen_width - 500
        hand_x = 150

        init_x = hand_x + hand_width + 20
        init_y = hand_y + 10
        init_width = 20
        init_height = hand_height - 20

        pygame.draw.rect(self.screen, (60, 60, 60), (init_x, init_y, init_width, init_height))
        ratio = player.initiative / player.max_initiative
        fill_height = int(init_height * ratio)
        if ratio > 0.5:
            color = (0, 255, 0)
        elif ratio > 0.25:
            color = (255, 255, 0)
        else:
            color = (255, 0, 0)
        pygame.draw.rect(self.screen, color, (init_x, init_y + init_height - fill_height, init_width, fill_height))
        pygame.draw.rect(self.screen, (200, 200, 200), (init_x, init_y, init_width, init_height), 2)
        init_text = f"{player.initiative}/{player.max_initiative}"
        surf, _ = fonts.render_text(init_text, size_key="StoryScript XS", color=WHITE)
        self.screen.blit(surf, (init_x + init_width//2 - surf.get_width()//2, init_y + init_height + 5))

    def draw_resources(self):
        player = self.logic.current_player
        
        bottom_start = int(self.screen_height * 0.6)
        bottom_height = int(self.screen_height * 0.4)
        hand_height = bottom_height // 2.5
        hand_y = bottom_start + hand_height + 50
        hand_width = self.screen_width - 500
        hand_x = 150
        init_x = hand_x + hand_width + 60
        init_y = hand_y - 165
        init_height = hand_height - 20

        res_x = init_x
        res_y = init_y + init_height + 15
        font_key = "StoryScript XS"
        line_height = 24

        resource_keys = [
            ("food_production", "Żywność", player.food_production),  # dynamiczne
            ("production", "Produkcja", player.production),  # dynamiczne
            ("logistics", "Logistyka", player.logistics),
            ("oil_production", "Ropa", player.oil_production),
            ("fuel_production", "Paliwo", player.fuel_production),
            ("iron_production", "Ruda", player.iron_production),
            ("steal", "Stal", player.steal),
        ]

        for key, label, value in resource_keys:
            value = getattr(player, key, 0)
            color = self.resource_colors.get(key, (255, 255, 255))
            text = f"{label}: {value}"
            surf, _ = fonts.render_text(text, size_key=font_key, color=color, topleft=(res_x, res_y))
            self.screen.blit(surf, (res_x, res_y))
            res_y += line_height

    def draw_tooltip(self):
        if self.hovered_card_view:
            font_small = pygame.font.Font(None, 16)
            font_medium = pygame.font.Font(None, 20)
            self.hovered_card_view.draw_tooltip(
                self.screen,
                font_small=font_small,
                font_medium=font_medium,
                game_logic=self.logic,
                padding=10, x=100, y=100
            )

    def draw_end_turn(self):
        # ---- Przycisk "Koniec tury" ----
        button_x = self.screen_width - 220
        button_y = self.screen_height - 70
        self.end_turn_button_rect = pygame.Rect(button_x, button_y, 200, 50)
        pygame.draw.rect(self.screen, (80, 80, 120), self.end_turn_button_rect)
        pygame.draw.rect(self.screen, (200, 200, 200), self.end_turn_button_rect, 2)
        text = self.localization.get("end_turn", "Koniec tury")
        surf, _ = fonts.render_text(text, size_key="StoryScript M", color=WHITE, center=self.end_turn_button_rect.center)
        self.screen.blit(surf, surf.get_rect(center=self.end_turn_button_rect.center))

    def draw_preview(self):
        if self.preview_visible and self.preview_view:
            x = (self.screen_width - self.preview_width) // 2
            y = (self.screen_height - self.preview_height) // 2
            self.preview_view.draw_preview(
                self.screen,
                x, y,
                self.preview_width, self.preview_height,
                language=self.logic.language,
                show_attachments=True
            )

    # ---------- OBSŁUGA MYSZY ----------
    def handle_mouse_motion(self, pos):
        self.hovered_card_view = None
        for view in self.card_views:
            if view.rect and view.rect.collidepoint(pos):
                self.hovered_card_view = view
                view.hovered = True
            else:
                view.hovered = False

    def handle_click(self, pos, button):
        if button == 1:
            if self.end_turn_button_rect.collidepoint(pos):
                return "end_turn"
            deck_rect = pygame.Rect(50, self.screen_height - 220, 100, 140)
            if deck_rect.collidepoint(pos):
                return "draw"
            
            for view in self.card_views:
                if view.rect and view.rect.collidepoint(pos):
                    if self.logic.selected_card is not None and view.card != self.logic.selected_card:
                        if self.logic.can_attach_to_card(self.logic.selected_card, view.card):
                            player = self.logic.current_player
                            for zone_cards in player.zones.values():
                                if view.card in zone_cards:
                                    return ("attach", view.card)
                    if self.logic.selected_card == view.card:
                        return ("deselect", None)
                    else:
                        return ("select", view.card)
            
            for zone, rect in self.zone_rects.items():
                if rect.collidepoint(pos):
                    if self.logic.selected_card is not None:
                        return ("play", zone)
                    else:
                        return None
            
            return ("deselect", None)
        elif button == 3:
            for view in self.card_views:
                if view.rect and view.rect.collidepoint(pos):
                    self.preview_view = view
                    self.preview_visible = True
                    return None
            self.preview_visible = False
            self.preview_view = None
            return None
        return None

    def draw_opponents(self):
        """Rysuje strefy wszystkich przeciwników."""
        opponents = [p for i, p in enumerate(self.logic.players) if i != self.logic.current_player_index]
        if not opponents:
            return
        
        # Obszar dla przeciwników: górna część ekranu, pod paskiem info
        top_margin = 80  # po pasku info
        bottom_margin = (self.screen_height * 0.60) - 15  # do stref aktywnego gracza
        available_height = bottom_margin - top_margin
        available_width = self.screen_width - 20  # marginesy
        
        # Podziel dostępną przestrzeń na tyle samo kolumn ilu przeciwników
        num_opponents = len(opponents)
        panel_width = min(1000, available_width // num_opponents - 10)
        spacing = (available_width - panel_width * num_opponents) // (num_opponents + 1)
        x_start = spacing + 10
        
        for idx, opponent in enumerate(opponents):
            x = x_start + idx * (panel_width + spacing)
            y = top_margin
            rect = pygame.Rect(x, y, panel_width, available_height)
            self._draw_opponent_panel(opponent, rect)

    def _draw_opponent_panel(self, opponent, rect):
        bg = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        bg.fill((50, 50, 50, 50))
        self.screen.blit(bg, rect)
        pygame.draw.rect(self.screen, (200, 200, 200), rect, 2)
        name_surf, _ = fonts.render_text(
            opponent.name,
            size_key="StoryScript M",
            color=WHITE,
            center=(rect.centerx, rect.y + 25)
        )
        self.screen.blit(name_surf, name_surf.get_rect(center=(rect.centerx, rect.y + 25)))
        
        zone_order = [Zone.STATE, Zone.BACK, Zone.SECOND, Zone.FRONT]
        zone_names = {
            Zone.STATE: "Państwo",
            Zone.BACK: "Zaplecze",
            Zone.SECOND: "Druga linia",
            Zone.FRONT: "Front"
        }
        y_offset = 60
        line_height = (rect.height - y_offset) // len(zone_order)
        font = pygame.font.Font(None, 16)
        
        for zone in zone_order:
            cards = opponent.zones.get(zone, [])
            count = len(cards)
            text = f"{zone_names[zone]}: {count}"
            surf = font.render(text, True, (200, 200, 200))
            self.screen.blit(surf, (rect.x + 10, rect.y + y_offset))
            
            # Rysuj karty w strefie (małe)
            if cards:
                card_width = 30
                card_height = 42
                spacing = 4
                max_per_row = (rect.width - 20) // (card_width + spacing)
                row = 0
                col = 0
                for card in cards[:12]:  # ogranicz do 12 kart, żeby nie przepełnić
                    cx = rect.x + 10 + col * (card_width + spacing)
                    cy = rect.y + y_offset + 20 + row * (card_height + spacing)
                    if cy + card_height > rect.y + y_offset + line_height - 10:
                        break
                    view = CardView(card, self.localization)
                    view.update_rect(cx, cy, card_width, card_height)
                    view.draw(self.screen, cx, cy, card_width, card_height, language=self.logic.language)
                    self.card_views.append(view)
                    # Dołączone karty (małe przesunięcie)
                    if card.attached_cards:
                        attach_offset_x = 6
                        attach_offset_y = 6
                        attach_width = card_width - 4
                        attach_height = card_height - 4
                        for i, attach in enumerate(card.attached_cards[:3]):
                            ax = cx + attach_offset_x * (i + 1)
                            ay = cy + attach_offset_y * (i + 1)
                            attach_view = CardView(attach, self.localization)
                            attach_view.update_rect(ax, ay, attach_width, attach_height)
                            attach_view.draw(self.screen, ax, ay, attach_width, attach_height, language=self.logic.language)
                    col += 1
                    if col >= max_per_row:
                        col = 0
                        row += 1
            y_offset += line_height

    def close_preview(self):
        self.preview_visible = False
        self.preview_view = None