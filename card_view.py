# card_view.py
import pygame
from card import Card
from card_renderer import draw_card
from fonts import fonts
from localization import Localization

class CardView:
    """
    Klasa odpowiedzialna za wyświetlanie pojedynczej karty, tooltip i podgląd.
    """
    def __init__(self, card: Card, localization: Localization):
        self.card = card
        self.localization = localization
        self.selected = False
        self.hovered = False
        self.rect = None  # aktualny prostokąt

    def update_rect(self, x, y, width, height):
        """Aktualizuje prostokąt karty."""
        self.rect = pygame.Rect(x, y, width, height)

    def draw(self, surface, x, y, width, height, language='pl'):
        """Rysuje kartę na powierzchni."""
        self.update_rect(x, y, width, height)
        draw_card(surface, self.card, x, y, width, height, language)

    def draw_selected_effect(self, surface):
        """Rysuje efekt zaznaczenia: cień + niebieska ramka."""
        if self.rect is None:
            return
        # Cień (przesunięty prostokąt)
        shadow_rect = self.rect.copy()
        shadow_rect.x += 6
        shadow_rect.y += 6
        shadow = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        shadow.fill((0, 0, 0, 60))
        surface.blit(shadow, (shadow_rect.x, shadow_rect.y))
        # Niebieska ramka
        pygame.draw.rect(surface, (100, 200, 255), self.rect, 3)

    def draw_tooltip(self, surface, x=None, y=None, font_small=None, font_medium=None, padding=10, game_logic=None):
        """
        Rysuje tooltip z opisem karty.
        Pozycja domyślnie w prawym górnym rogu.
        """
        if not self.card:
            return
        if font_small is None:
            font_small = pygame.font.Font(None, 16)
        if font_medium is None:
            font_medium = pygame.font.Font(None, 20)

        display_name = self.localization.get_card_name(self.card.name_key) if self.card.name_key else self.card.name or "Bez nazwy"
        type_name = self.localization.get_card_type_name(self.card.card_type)

        # ---------- BUDUJEMY LISTĘ LINII (z kolorami) ----------
        lines = []          # lista (tekst, kolor)
        
        # Podstawowe informacje
        lines.append((display_name, (255, 255, 200)))  # nazwa – żółtawy
        lines.append((f"Typ: {type_name}", (255, 255, 255)))
        lines.append((f"Koszt inicjatywy: {self.card.cost_initiative}", (255, 255, 255)))
        lines.append((f"Generowana inicjatywa: {self.card.initiative}", (255, 255, 255)))
        lines.append((f"Koszt produkcji: {self.card.cost_production}", (255, 255, 255)))
        lines.append((f"Produkcja: {self.card.production}", (255, 255, 255)))

        # Statystyki
        stats = [
            ("max_workers", "Maks. ilość robotników", self.card.max_workers),
            ("food_production", "Produkcja żywności", self.card.food_production),
            ("iron_ore_production", "Produkcja rudy", self.card.iron_ore_production),
            ("oil_production", "Produkcja ropy", self.card.oil_production),
            ("steal_production", "Produkcja stali", self.card.steal_production),
            ("fuel_production", "Produkcja paliwa", self.card.fuel_production),
            ("food_consumption", "Konsumpcja żywności", self.card.food_consumption),
            ("fuel_consumption", "Zużycie paliwa", self.card.fuel_consumption),
            ("cost_steal", "Koszt w stali", self.card.cost_steal),
        ]
        for stat_key, stat_label, value in stats:
            if value > 0:
                lines.append((f"{stat_label}: {value}", (255, 255, 255)))

        # ---------- WYMAGANIA (z kolorami) ----------
        if self.card.requirements:
            if game_logic is not None:
                statuses = game_logic.get_requirements_status(self.card, game_logic.current_player)
                for satisfied, desc in statuses:
                    color = (0, 255, 0) if satisfied else (255, 0, 0)
                    lines.append((f"  {desc}", color))
            else:
                # Fallback – jeśli brak game_logic, wyświetl surowe wymagania
                req_text = "Wymagania: "
                req_parts = []
                for zone, req_type, count in self.card.requirements:
                    zone_name = self.localization.get(f"zone_{zone.value}", zone.value)
                    type_name_req = self.localization.get_card_type_name(req_type)
                    req_parts.append(f"{count}x {type_name_req} w {zone_name}")
                lines.append((req_text + ", ".join(req_parts), (255, 255, 255)))

        # Dozwolone załączniki
        if self.card.allowed_attachments:
            attach_names = [self.localization.get_card_type_name(a) for a in self.card.allowed_attachments]
            lines.append((f"Można dołączyć: {', '.join(attach_names)}", (255, 255, 255)))

        # ---------- OBLICZANIE ROZMIARU TOOLTIPA ----------
        line_height = font_small.get_height() + 4
        max_width = 0
        for text, color in lines:
            # Dla pierwszej linii używamy font_medium, reszta font_small
            font = font_medium if text == lines[0][0] else font_small
            w, _ = font.size(text)
            if w > max_width:
                max_width = w

        tooltip_width = max_width + 2 * padding
        tooltip_height = len(lines) * line_height + 2 * padding

        if x is None:
            x = surface.get_width() - tooltip_width - 20
        if y is None:
            y = 20

        # ---------- RYSOWANIE TŁA ----------
        bg = pygame.Surface((tooltip_width, tooltip_height), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 220))
        surface.blit(bg, (x, y))
        pygame.draw.rect(surface, (200, 200, 200), (x, y, tooltip_width, tooltip_height), 1)

        # ---------- RYSOWANIE TEKSTU ----------
        for i, (text, color) in enumerate(lines):
            font = font_medium if i == 0 else font_small
            text_surf = font.render(text, True, color)
            surface.blit(text_surf, (x + padding, y + padding + i * line_height))

    def draw_preview(self, surface, x, y, width, height, language='pl', overlay_alpha=180, show_attachments=True):
        """
        Rysuje powiększoną kartę z przyciemnionym tłem.
        Jeśli show_attachments=True, rysuje również dołączone karty jako mniejsze.
        """
        if not self.card:
            return
        overlay = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, overlay_alpha))
        surface.blit(overlay, (0, 0))
        
        # Rysuj główną kartę
        self.draw(surface, x, y, width, height, language)

        # Ramka wokół podglądu
        pygame.draw.rect(surface, (200, 200, 200), (x-2, y-2, width+4, height+4), 2)
        
        # Rysuj dołączone karty (jeśli istnieją)
        if show_attachments and self.card.attached_cards:
            attach_scale = 1  # skala załącznika
            attach_width = int(width * attach_scale)
            attach_height = int(height * attach_scale)
            attach_offset_x = 275
            attach_offset_y = 125
            
            for attach_card in self.card.attached_cards:
                ax = x + attach_offset_x
                ay = y + attach_offset_y
                attach_view = CardView(attach_card, self.localization)
                attach_view.draw(surface, ax, ay, attach_width, attach_height, language)
                pygame.draw.rect(surface, (200, 200, 200), (ax-2, ay-2, attach_width+4, attach_height+4), 2)
                attach_offset_x += 100
                attach_offset_y += 100
        
