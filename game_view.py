# game_view.py
import pygame
import time
from constants import *
from card_view import CardView
from card_renderer import draw_card
from fonts import fonts
from card import Zone, CardType
from render_utils import draw_alpha_rect, draw_button, draw_text_bg

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
        self.opponent_rects = []
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
        self.discard_rect = pygame.Rect(0, 0, 100, 140)
        self.attack_buttons = {}

        self.attack_preview_rect = None
        self.confirm_button_rect = None
        self.cancel_button_rect = None

        # ---------- SYSTEM KOMUNIKATÓW ----------
        self.messages = []
        self.message_duration = 5.0
        self.message_font_size = 28
        self.message_padding = 15


    def draw_attack_preview(self):
        """Rysuje podgląd ataku jako nakładkę."""
        data = self.logic.get_attack_preview_data()
        if not data:
            return

        # Przyciemnij tło
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # Wymiary podglądu
        preview_width = int(self.screen_width * 0.75)
        preview_height = int(self.screen_height * 0.75)
        preview_x = (self.screen_width - preview_width) // 2
        preview_y = (self.screen_height - preview_height) // 2
        self.attack_preview_rect = pygame.Rect(preview_x, preview_y, preview_width, preview_height)

        # Tło podglądu
        draw_alpha_rect(
            self.screen,
            preview_x, preview_y, preview_width, preview_height,
            (40, 40, 60), 255,
            (200, 200, 200), 2
        )

        # Tytuł
        title = f"Podgląd ataku na {data['target_player'].name} (strefa: {data['target_zone'].value})"
        title_surf, _ = fonts.render_text(title, size_key="StoryScript M", color=WHITE, center=(self.screen_width//2, preview_y + 40))
        self.screen.blit(title_surf, title_surf.get_rect(center=(self.screen_width//2, preview_y + 40)))

        # Podziel na dwie części: górna – cele, dolna – atakujący
        half_height = (preview_height - 80) // 2
        # Cele (przeciwnik)
        defenders = data["defenders"]
        attackers = data["attackers"]

        # Rysuj etykiety
        label_y = preview_y + 70
        label_surf, _ = fonts.render_text("Cele przeciwnika:", size_key="StoryScript S", color=WHITE, topleft=(preview_x + 20, label_y))
        self.screen.blit(label_surf, (preview_x + 20, label_y))

        # Rysuj karty celów
        card_width = 100
        card_height = 140
        spacing = 25
        start_x = preview_x + 20
        card_y = label_y + 70
        for i, card in enumerate(defenders):
            x = start_x + i * (card_width + spacing)
            view = CardView(card, self.localization)
            view.update_rect(x, card_y, card_width, card_height)
            view.draw(self.screen, x, card_y, card_width, card_height, language=self.logic.language)
            self.card_views.append(view)

            # Etykieta obrony (używamy target_type)
            defense_type, defense_value = self.logic.get_defense_type(card)
            if defense_type:
                label = f"{defense_type} [Obrona: {defense_value}]"
                draw_text_bg(
                    self.screen, label,
                    fonts.get_font("StoryScript XXS"),
                    (200, 200, 255),
                    x, card_y - 35,
                    padding=8, bg_color=(20,20,20), bg_alpha=150
                )    

            # Kontratak (atak własny karty)
            card_attack = self.logic.get_card_attack(card)
            attack_parts = []
            for atype in ["soft", "hard", "air"]:
                value = card_attack.get(atype, 0)
                if value > 0:
                    attack_parts.append(f"{atype.upper()}({value})")
            if attack_parts:
                label = "Atak: " + ", ".join(attack_parts)
                draw_text_bg(
                    self.screen, label,
                    fonts.get_font("StoryScript XXS"),
                    (255, 200, 100),
                    x, card_y + card_height + 45,
                    padding=8, bg_color=(20,20,20), bg_alpha=180
                )        

            if card.attached_cards:
                attach_offset_x = 25
                attach_offset_y = 25
                attach_width = card_width
                attach_height = card_height
                for j, attach_card in enumerate(card.attached_cards):
                    ax = x + attach_offset_x * (j + 1)
                    ay = card_y + attach_offset_y * (j + 1)
                    attach_view = CardView(attach_card, self.localization)
                    attach_view.update_rect(ax, ay, attach_width, attach_height)
                    attach_view.draw(self.screen, ax, ay, attach_width, attach_height, language=self.logic.language)
                    self.card_views.append(attach_view)

        # Atakujący (gracz)
        label_y2 = preview_y + 70 + half_height
        label_surf2, _ = fonts.render_text("Twoje jednostki atakujące:", size_key="StoryScript S", color=WHITE, topleft=(preview_x + 20, label_y2))
        self.screen.blit(label_surf2, (preview_x + 20, label_y2))

        # Rysuj karty atakujących
        card_y2 = label_y2 + 70
        for i, card in enumerate(attackers):
            x = start_x + i * (card_width + spacing)
            view = CardView(card, self.localization)
            view.update_rect(x, card_y2, card_width, card_height)
            view.draw(self.screen, x, card_y2, card_width, card_height, language=self.logic.language)
            self.card_views.append(view)

            defense_type, defense_value = self.logic.get_defense_type(card)
            if defense_type:
                label = f"{defense_type} [Obrona: {defense_value}]"
                draw_text_bg(
                    self.screen, label,
                    fonts.get_font("StoryScript XXS"),
                    (200, 200, 255),
                    x, card_y2 - 35,
                    padding=8, bg_color=(20,20,20), bg_alpha=150
                )              

            if card.attached_cards:
                attach_offset_x = 25
                attach_offset_y = 25
                attach_width = card_width
                attach_height = card_height
                for j, attach_card in enumerate(card.attached_cards):
                    ax = x + attach_offset_x * (j + 1)
                    ay = card_y2 + attach_offset_y * (j + 1)
                    attach_view = CardView(attach_card, self.localization)
                    attach_view.update_rect(ax, ay, attach_width, attach_height)
                    attach_view.draw(self.screen, ax, ay, attach_width, attach_height, language=self.logic.language)
                    self.card_views.append(attach_view)

        # Przycisk "Potwierdź"
        btn_width = 200
        btn_height = 50
        btn_x = preview_x + preview_width - btn_width - 20
        btn_y = preview_y + preview_height - btn_height - 20
        self.confirm_button_rect = pygame.Rect(btn_x, btn_y, btn_width, btn_height)
        draw_button(
            self.screen,
            btn_x, btn_y, btn_width, btn_height,
            "Potwierdź",
            fonts.get_font("StoryScript M"),
            (0, 200, 0),
            WHITE,
            hover=False
        )

        # Przycisk "Anuluj"
        btn_x2 = btn_x - btn_width - 10
        self.cancel_button_rect = pygame.Rect(btn_x2, btn_y, btn_width, btn_height)
        draw_button(
            self.screen,
            btn_x2, btn_y, btn_width, btn_height,
            "Anuluj",
            fonts.get_font("StoryScript M"),
            (200, 0, 0),
            WHITE,
            hover=False
        )

    def add_message(self, text: str, msg_type: str = "info"):
        colors = {
            "info": (100, 150, 255),
            "error": (255, 80, 80),
            "success": (80, 255, 80),
        }
        color = colors.get(msg_type, (255, 255, 255))
        self.messages.append((text, color, time.time()))

    def draw_messages(self):
        now = time.time()
        self.messages = [m for m in self.messages if now - m[2] < self.message_duration]
        if not self.messages:
            return

        font = pygame.font.Font(None, self.message_font_size)
        line_height = font.get_height() + self.message_padding
        start_y = 80

        for i, (text, color, timestamp) in enumerate(self.messages):
            text_surf = font.render(text, True, color)
            text_rect = text_surf.get_rect()
            bg_width = text_rect.width + self.message_padding * 4
            bg_height = text_rect.height + self.message_padding * 2
            bg_x = (self.screen_width - bg_width) // 2
            bg_y = start_y + i * line_height

            draw_alpha_rect(
                self.screen,
                bg_x, bg_y, bg_width, bg_height,
                (0, 0, 0), 200,
                color, 2
            )

            text_x = bg_x + self.message_padding * 2
            text_y = bg_y + self.message_padding
            self.screen.blit(text_surf, (text_x, text_y))

    def update_size(self, width, height):
        self.screen_width = width
        self.screen_height = height

    def draw(self):
        self.card_views.clear()
        self.opponent_rects.clear()
        self.screen.blit(self.background_image, (0, 0))
        self.draw_info()
        self.draw_opponents()
        self.draw_zones()
        self.draw_deck()
        self.draw_discard()
        self.draw_hand()
        self.draw_initiative_bar()
        self.draw_resources()
        self.draw_attack_preview()
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

            is_allowed = (
                zone in allowed_zones and
                self.logic.check_requirements(self.logic.selected_card, player)
            )
            is_move_target = self.logic.is_move_mode() and zone in self.logic.get_move_targets()

            if is_move_target:
                bg_color = (255, 255, 0)
                bg_alpha = 80
                border_color = (255, 255, 0)
                border_width = 4
            elif is_allowed:
                bg_color = (60, 200, 60)
                bg_alpha = 80
                border_color = (0, 255, 0)
                border_width = 4
            else:
                bg_color = (60, 60, 80)
                bg_alpha = 75
                border_color = (200, 200, 200)
                border_width = 2

            draw_alpha_rect(
                self.screen,
                x, y, width, zone_height,
                bg_color, bg_alpha,
                border_color, border_width
            )

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

                    if card.attached_cards:
                        attach_offset_x = 15
                        attach_offset_y = 15
                        attach_width = card_width
                        attach_height = card_height
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

                # ---------- PRZYCISKI ATAKU ----------
                if zone == Zone.FRONT:
                    summary = self.logic.get_attack_summary()
                    self.attack_buttons = {}
                    btn_x = rect.right - 130
                    btn_y = rect.y + 8
                    btn_width = 120
                    btn_height = 25
                    btn_spacing = 4

                    for r in [1, 2, 3]:
                        s = summary.get(r, {"soft": 0, "hard": 0, "air": 0})
                        if s["soft"] > 0 or s["hard"] > 0 or s["air"] > 0:
                            btn_rect = pygame.Rect(btn_x, btn_y, btn_width, btn_height)
                            self.attack_buttons[r] = btn_rect

                            parts = []
                            if s["soft"] > 0:
                                parts.append(f"Soft: {s['soft']}")
                            if s["hard"] > 0:
                                parts.append(f"Hard: {s['hard']}")
                            if s["air"] > 0:
                                parts.append(f"Air: {s['air']}")
                            label = f"Zasięg: {r}: " + ", ".join(parts)

                            draw_button(
                                self.screen,
                                btn_rect.x, btn_rect.y, btn_rect.width, btn_rect.height,
                                label,
                                fonts.get_font("StoryScript XXS"),
                                (200, 50, 50),
                                WHITE,
                                hover=False
                            )
                            btn_y += btn_height + btn_spacing
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
        draw_alpha_rect(
            self.screen,
            0, 0, self.screen_width, info_height,
            (0, 0, 0), 100
        )
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
        font = fonts.get_font("StoryScript XS")
        draw_text_bg(
            self.screen,
            count_text,
            font,
            WHITE,
            deck_x + deck_width//2 - 20, deck_y + deck_height + 5,
            padding=6,
            bg_color=(0, 0, 0),
            bg_alpha=180
        )

    def draw_discard(self):
        player = self.logic.current_player
        discard_x = self.screen_width - 120
        discard_y = self.screen_height - 180
        discard_width = 100
        discard_height = 140
        self.discard_rect = pygame.Rect(discard_x, discard_y, discard_width, discard_height)

        can_discard = (self.logic.selected_card is not None and
                       self.logic.selected_card in player.hand and
                       player.initiative >= 1)
        can_draw_from_discard = (len(player.discard) > 0 and player.initiative >= 5 and len(player.hand) < player.max_hand_size)

        if can_discard:
            bg_color = (0, 200, 0)
            bg_alpha = 80
            border_color = (0, 255, 0)
            border_width = 4
        elif can_draw_from_discard:
            bg_color = (0, 100, 200)
            bg_alpha = 80
            border_color = (0, 200, 255)
            border_width = 4
        else:
            bg_color = (60, 60, 80)
            bg_alpha = 75
            border_color = (200, 200, 200)
            border_width = 2

        draw_alpha_rect(
            self.screen,
            discard_x, discard_y, discard_width, discard_height,
            bg_color, bg_alpha,
            border_color, border_width
        )

        for i in range(min(len(player.discard), 12)):
            offset = i * 2
            self.screen.blit(self.card_back_image, (discard_x + offset, discard_y - offset))

        count_text = str(len(player.discard))
        font = fonts.get_font("StoryScript M")
        draw_text_bg(
            self.screen,
            count_text,
            font,
            WHITE,
            discard_x + discard_width//2 - 20, discard_y + discard_height + 5,
            padding=6,
            bg_color=(0, 0, 0),
            bg_alpha=180
        )

        if can_discard:
            label = "Odrzuć (1 ini)"
            label_font = fonts.get_font("StoryScript XS")
            draw_text_bg(
                self.screen,
                label,
                label_font,
                (0, 255, 0),
                discard_x + 10, discard_y + discard_height + 20,
                padding=4,
                bg_color=(0, 0, 0),
                bg_alpha=150
            )
        elif can_draw_from_discard:
            label = "Weź (5 ini)"
            label_font = fonts.get_font("StoryScript XS")
            draw_text_bg(
                self.screen,
                label,
                label_font,
                (0, 200, 255),
                discard_x + 10, discard_y + discard_height + 20,
                padding=4,
                bg_color=(0, 0, 0),
                bg_alpha=150
            )

    def draw_hand(self):
        player = self.logic.current_player
        bottom_start = int(self.screen_height * 0.6)
        bottom_height = int(self.screen_height * 0.4)
        hand_height = bottom_height // 2.5
        hand_y = bottom_start + hand_height + 50
        hand_width = self.screen_width - 500
        hand_x = 150

        draw_alpha_rect(
            self.screen,
            hand_x, hand_y, hand_width, hand_height,
            (150, 150, 150), 80,
            (100, 100, 150), 2
        )

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
            ("food_production", "Żywność", player.food_production),
            ("production", "Produkcja", player.production),
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
        button_x = self.screen_width - 220
        button_y = self.screen_height - 70
        width = 200
        height = 50
        self.end_turn_button_rect = pygame.Rect(button_x, button_y, width, height)
        text = self.localization.get("end_turn", "Koniec tury")
        font = fonts.get_font("StoryScript M")
        draw_button(
            self.screen,
            button_x, button_y, width, height,
            text,
            font,
            (80, 80, 120),
            WHITE,
            hover=False
        )

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
            
            if self.logic.is_attack_preview_mode():
                if self.confirm_button_rect and self.confirm_button_rect.collidepoint(pos):
                    if self.logic.confirm_attack():
                        return ("attack_success", None)
                    else:
                        return ("attack_fail", None)
                elif self.cancel_button_rect and self.cancel_button_rect.collidepoint(pos):
                    self.logic.cancel_attack_preview()
                    return ("attack_cancel", None)
                else:
                    # Kliknięcie poza przyciskami – anuluj podgląd (opcjonalnie)
                    # self.logic.cancel_attack_preview()
                    # return ("attack_cancel", None)
                    return None
    
            deck_rect = pygame.Rect(50, self.screen_height - 220, 100, 140)
            if hasattr(self, 'discard_rect') and self.discard_rect.collidepoint(pos):
                if self.logic.selected_card is not None and self.logic.selected_card in self.logic.current_player.hand:
                    return "discard"
                else:
                    if self.logic.current_player.discard:
                        return "draw_from_discard"
                    else:
                        return None
            if deck_rect.collidepoint(pos):
                return "draw"
            
            # PRZYCISKI ATAKU
            if hasattr(self, 'attack_buttons') and self.attack_buttons:
                for attack_range, btn_rect in self.attack_buttons.items():
                    if btn_rect.collidepoint(pos):
                        if self.logic.start_attack_with_range(attack_range):
                            return ("attack_select", None)
                        else:
                            return ("attack_fail", None)

            player = self.logic.current_player

            for view in self.card_views:
                if view.rect and view.rect.collidepoint(pos):
                    if view.card in player.hand:
                        if self.logic.selected_card is not None and view.card != self.logic.selected_card:
                            if self.logic.can_attach_to_card(self.logic.selected_card, view.card):
                                for zone_cards in player.zones.values():
                                    if view.card in zone_cards:
                                        return ("attach", view.card)
                        if self.logic.selected_card == view.card:
                            return ("deselect", None)
                        else:
                            return ("select", view.card)
                    else:
                        if self.logic.selected_card is not None:
                            if self.logic.can_attach_to_card(self.logic.selected_card, view.card):
                                return ("attach", view.card)
                            else:
                                return ("deselect", None)
                        else:
                            # Karta w strefie – tylko przenoszenie (żołnierz)
                            if view.card.card_type == CardType.SOLDIER:
                                if self.logic.select_soldier_for_move(view.card):
                                    return ("move_select", None)
                            return ("deselect", None)

            for zone, rect in self.zone_rects.items():
                if rect.collidepoint(pos):
                    if self.logic.is_move_mode() and zone in self.logic.get_move_targets():
                        return ("move", zone)
                    elif self.logic.selected_card is not None:
                        return ("play", zone)
                    else:
                        return None
                    
            # Kliknięcie w panel przeciwnika w trybie ataku
            if self.logic.is_attack_mode():
                for opponent, rect in self.opponent_rects:
                    if rect.collidepoint(pos):
                        attack_zones = self.logic.get_attack_zones()
                        zones_for_opponent = attack_zones.get(opponent, [])
                        if zones_for_opponent:
                            zone = zones_for_opponent[0]  # wybierz pierwszą dostępną strefę
                            if self.logic.prepare_attack_preview(opponent, zone):
                                return ("attack_preview", None)
                            else:
                                return ("attack_fail", None)
                            
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
        opponents = [p for i, p in enumerate(self.logic.players) if i != self.logic.current_player_index]
        if not opponents:
            return

        top_margin = 80
        bottom_margin = (self.screen_height * 0.60) - 15
        available_height = bottom_margin - top_margin
        available_width = self.screen_width - 20
        num_opponents = len(opponents)
        panel_width = min(1000, available_width // num_opponents - 10)
        spacing = (available_width - panel_width * num_opponents) // (num_opponents + 1)
        x_start = spacing + 10

        self.opponent_rects.clear()

        for idx, opponent in enumerate(opponents):
            x = x_start + idx * (panel_width + spacing)
            y = top_margin
            rect = pygame.Rect(x, y, panel_width, available_height)
            self._draw_opponent_panel(opponent, rect)
            self.opponent_rects.append((opponent, rect))

    def _draw_opponent_panel(self, opponent, rect):
        draw_alpha_rect(
            self.screen,
            rect.x, rect.y, rect.width, rect.height,
            (50, 50, 50), 50,
            (200, 200, 200), 2
        )

        attack_zones = self.logic.get_attack_zones()
        attack_zones_for_opponent = attack_zones.get(opponent, [])

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

            # Podświetlenie strefy, jeśli jest celem ataku
            if zone in attack_zones_for_opponent:
                zone_rect = pygame.Rect(rect.x + 10, rect.y + y_offset, rect.width - 20, line_height - 4)
                pygame.draw.rect(self.screen, (255, 0, 0), zone_rect, 2)

            if cards:
                card_width = 40
                card_height = 58
                spacing = 4
                max_per_row = (rect.width - 20) // (card_width + spacing)
                row = 0
                col = 0
                for card in cards[:12]:
                    cx = rect.x + 10 + col * (card_width + spacing)
                    cy = rect.y + y_offset + 20 + row * (card_height + spacing)
                    if cy + card_height > rect.y + y_offset + line_height - 10:
                        break
                    view = CardView(card, self.localization)
                    view.update_rect(cx, cy, card_width, card_height)
                    view.draw(self.screen, cx, cy, card_width, card_height, language=self.logic.language)
                    self.card_views.append(view)
                    if card.attached_cards:
                        attach_offset_x = 6
                        attach_offset_y = 6
                        attach_width = card_width
                        attach_height = card_height
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