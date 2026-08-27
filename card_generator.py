# card_generator.py
import os
import pygame
from card import Card
from fonts import fonts  # <-- DODAJEMY IMPORT
from card_renderer import (
    load_image, get_card_color, get_frame_def, scale_image_contain,
    CARDS_IMAGES_DIR, FRAMES_DIR, ICONS_DIR,
    _image_cache, _frame_cache, _icon_cache, _flag_cache
)
from localization import Localization

RENDERED_DIR = "rendered_cards"
CARD_WIDTH = 512
CARD_HEIGHT = 768

def ensure_rendered_dir():
    if not os.path.exists(RENDERED_DIR):
        os.makedirs(RENDERED_DIR)

def get_rendered_path(card, language):
    name_key = card.name_key if card.name_key else f"card_{card.id[:8]}"
    filename = f"{name_key}_{language}.png"
    return os.path.join(RENDERED_DIR, filename)

def is_card_rendered(card, language):
    return os.path.exists(get_rendered_path(card, language))

def render_card_raw(surface, card, x, y, width, height, language, localization):
    """
    Renderuje kartę bezpośrednio na powierzchnię – NIE używa gotowych plików.
    Używane przez generator.
    """
    # Pobierz definicję ramki
    frame_def = get_frame_def(card)
    frame_image_name = frame_def.get("image")
    offset_x = frame_def.get("offset_x", 0)
    offset_y = frame_def.get("offset_y", 0)
    text_color = frame_def.get("text_color", (0, 0, 0))
    font_key = frame_def.get("font", "StoryScript XS")  # <-- klucz czcionki z ramki
    title_offset_x = frame_def.get("title_offset_x", 0)
    title_offset_y = frame_def.get("title_offset_y", 0)
    icon_offset_x = frame_def.get("icon_offset_x", 0)
    icon_offset_y = frame_def.get("icon_offset_y", 0)

    # Wczytaj obrazek karty (z oryginalnych plików, nie z rendered)
    img = load_image(card.image_path, _image_cache, CARDS_IMAGES_DIR)
    
    # Rysuj obrazek karty
    if img is None:
        color = get_card_color(card.card_type)
        pygame.draw.rect(surface, color, (x, y, width, height))
        pygame.draw.rect(surface, (0, 0, 0), (x, y, width, height), 2)
    else:
        scaled_img = pygame.transform.smoothscale(img, (width, height))
        surface.blit(scaled_img, (x, y))
        
    # ---------- FLAGA FRAKCJI (PRAWA STRONA) ----------
    flag_filename = f"{card.faction.value}.png"
    flag_img = load_image(flag_filename, _flag_cache, ICONS_DIR)  # <-- używamy _flag_cache
    if flag_img is not None:
        # Docelowy rozmiar flagi: 180x768 (skalowane proporcjonalnie)
        target_flag_width = 180
        target_flag_height = 768
        
        # Skaluj flagę do docelowego rozmiaru (zachowując proporcje)
        flag_width, flag_height = flag_img.get_size()
        scale_x = target_flag_width / flag_width
        scale_y = target_flag_height / flag_height
        scale = min(scale_x, scale_y)  # zachowaj proporcje
        new_w = int(flag_width * scale)
        new_h = int(flag_height * scale)
        scaled_flag = pygame.transform.smoothscale(flag_img, (new_w, new_h))
        scaled_flag.set_alpha(200)
        
        # Pozycja: prawa strona karty, wyśrodkowana w pionie
        flag_x = x + width - new_w  # przyklejona do prawej krawędzi
        flag_y = y + (height - new_h) // 2  # wyśrodkowana w pionie
        surface.blit(scaled_flag, (flag_x, flag_y))

    # Wczytaj ramkę
    frame_img = None
    if frame_image_name:
        frame_img = load_image(frame_image_name, _frame_cache, FRAMES_DIR)
        
    # Rysuj ramkę
    if frame_img is not None:
        scaled_frame, f_offset_x, f_offset_y = scale_image_contain(frame_img, width, height)
        scaled_frame.set_alpha(180)
        surface.blit(scaled_frame, (x + f_offset_x + offset_x, y + f_offset_y + offset_y))
    else:
        pygame.draw.rect(surface, (0, 0, 0), (x, y, width, height), 2)

    # Ikona typu
    icon_filename = f"{card.card_type.value}.png"
    icon_img = load_image(icon_filename, _icon_cache, ICONS_DIR)
    if icon_img is not None:
        icon_size = int(width * 0.33)
        icon_width, icon_height = icon_img.get_size()
        scale = min(icon_size / icon_width, icon_size / icon_height)
        new_w = int(icon_width * scale)
        new_h = int(icon_height * scale)
        scaled_icon = pygame.transform.smoothscale(icon_img, (new_w, new_h))
        icon_x = x + 50 + icon_offset_x
        icon_y = y + icon_offset_y + int(height * 0.30) - new_h // 2
        surface.blit(scaled_icon, (icon_x, icon_y))

    # ---------- TEKST: NAZWA I KOSZT (używamy fonts.render_text) ----------
    # Nazwa
    display_name = localization.get_card_name(card.name_key) if card.name_key else card.name or "Bez nazwy"
    if display_name:
        max_chars = int(width / 10)
        if len(display_name) > max_chars and max_chars > 3:
            display_name = display_name[:max_chars-3] + "..."
        
        # Użyj fonts.render_text z kluczem czcionki z ramki
        name_surf, name_rect = fonts.render_text(
            display_name,
            size_key=font_key,  # np. "StoryScript XXS"
            color=text_color,
            topleft=(x + 210 + title_offset_x, y + height*0.035 + title_offset_y)
        )
        surface.blit(name_surf, name_rect)

    # Koszt
    cost_text = f"K:{card.cost_initiative}"
    cost_surf, cost_rect = fonts.render_text(
        cost_text,
        size_key=font_key,
        color=text_color,
        center=(x + width//2, y + height - height*0.05)
    )
    surface.blit(cost_surf, cost_rect)

def render_card_to_file(card, language, localization):
    ensure_rendered_dir()
    path = get_rendered_path(card, language)
    surface = pygame.Surface((CARD_WIDTH, CARD_HEIGHT), pygame.SRCALPHA)
    render_card_raw(surface, card, 0, 0, CARD_WIDTH, CARD_HEIGHT, language, localization)
    pygame.image.save(surface, path)
    print(f"Wygenerowano kartę: {path}")

def render_all_cards(cards, language):
    localization = Localization(language)
    for card in cards:
        if not is_card_rendered(card, language):
            render_card_to_file(card, language, localization)
        else:
            print(f"Pomijam: {card.name_key} ({language}) – już istnieje")

def regenerate_all_cards(cards, languages):
    import shutil
    if os.path.exists(RENDERED_DIR):
        shutil.rmtree(RENDERED_DIR)
    os.makedirs(RENDERED_DIR)
    for lang in languages:
        render_all_cards(cards, lang)