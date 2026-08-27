# card_renderer.py
import pygame
import os
from card import Card
from fonts import fonts

_image_cache = {}
_frame_cache = {}
_icon_cache = {}
_flag_cache = {}
_frame_defs = {}
_loaded_card_cache = {}

CARDS_IMAGES_DIR = "images/cards/"
FRAMES_DIR = "images/cards/borders/"
ICONS_DIR = "images/cards/icons/"
FRAMES_DEF_FILE = os.path.join("defines", "frames.lua")

def lua_color_to_tuple(lua_color):
    if lua_color is None:
        return (0, 0, 0)
    if isinstance(lua_color, (tuple, list)):
        return tuple(lua_color[:3])
    try:
        r = lua_color[1] if lua_color[1] is not None else 0
        g = lua_color[2] if lua_color[2] is not None else 0
        b = lua_color[3] if lua_color[3] is not None else 0
        return (int(r), int(g), int(b))
    except:
        return (0, 0, 0)

def load_frame_defs():
    global _frame_defs
    try:
        import lupa
        from lupa import LuaRuntime
        lua = LuaRuntime(unpack_returned_tuples=True)
        with open(FRAMES_DEF_FILE, "r", encoding="utf-8") as f:
            result = lua.execute(f.read())
        if result is not None:
            frames_table = result
        else:
            frames_table = lua.globals().get("frames")
            if frames_table is None:
                raise ValueError("Nie znaleziono tabeli 'frames' w pliku Lua")
        
        for key, defn in frames_table.items():
            if defn is None:
                continue
            try:
                defn_dict = dict(defn)
            except Exception as e:
                print(f"Błąd konwersji dla klucza {key}: {e}")
                continue
            
            _frame_defs[key] = {
                "image": defn_dict.get("image"),
                "offset_x": defn_dict.get("offset_x", 0),
                "offset_y": defn_dict.get("offset_y", 0),
                "text_color": lua_color_to_tuple(defn_dict.get("text_color")),
                "font": defn_dict.get("font", "StoryScript XS"),
                "title_offset_x": defn_dict.get("title_offset_x", 0),
                "title_offset_y": defn_dict.get("title_offset_y", 0),
                "icon_offset_x": defn_dict.get("icon_offset_x", 0),
                "icon_offset_y": defn_dict.get("icon_offset_y", 0),
            }
        print(f"Wczytano {len(_frame_defs)} definicji ramek z {FRAMES_DEF_FILE}")
    except Exception as e:
        print(f"Nie udało się wczytać {FRAMES_DEF_FILE}: {e}, używam domyślnych ramek.")
        import traceback
        traceback.print_exc()
        _frame_defs["default"] = {
            "image": None,
            "offset_x": 0,
            "offset_y": 0,
            "text_color": (0, 0, 0),
            "font": "StoryScript XS",
            "title_offset_x": 0,
            "title_offset_y": 0,
            "icon_offset_x": 0,
            "icon_offset_y": 0,
        }

load_frame_defs()

def load_image(path, cache_dict, subdir=""):
    if path is None:
        return None
    if path not in cache_dict:
        try:
            if not os.path.dirname(path):
                full_path = os.path.join(subdir, path)
            else:
                full_path = path
            cache_dict[path] = pygame.image.load(full_path).convert_alpha()
        except (pygame.error, FileNotFoundError) as e:
            print(f"Nie można wczytać obrazka {path}: {e}")
            cache_dict[path] = None
    return cache_dict[path]

def get_card_color(card_type):
    from card import CardType
    if card_type == CardType.SOLDIER:
        return (210, 210, 210)
    elif card_type == CardType.WORKER:
        return (200, 180, 100)
    elif card_type == CardType.TANK:
        return (150, 150, 200)
    elif card_type == CardType.TERRAIN:
        return (120, 200, 120)
    elif card_type == CardType.WEAPON:
        return (200, 120, 120)
    elif card_type == CardType.CITY:
        return (180, 180, 220)
    elif card_type == CardType.BUILDING:
        return (180, 200, 200)
    else:
        return (180, 180, 180)

def get_frame_def(card):
    frame_key = getattr(card, "frame_key", None)
    if frame_key and frame_key in _frame_defs:
        return _frame_defs[frame_key]
    return _frame_defs.get("default", {
        "image": None,
        "offset_x": 0,
        "offset_y": 0,
        "text_color": (0, 0, 0),
        "font": "StoryScript XS",
        "title_offset_x": 0,
        "title_offset_y": 0,
        "icon_offset_x": 0,
        "icon_offset_y": 0,
    })

def scale_image_contain(image, target_width, target_height):
    img_width, img_height = image.get_size()
    scale_x = target_width / img_width
    scale_y = target_height / img_height
    scale = min(scale_x, scale_y)
    new_width = int(img_width * scale)
    new_height = int(img_height * scale)
    scaled = pygame.transform.smoothscale(image, (new_width, new_height))
    x_offset = (target_width - new_width) // 2
    y_offset = (target_height - new_height) // 2
    return scaled, x_offset, y_offset

def load_rendered_card(card, language, target_width, target_height):
    from card_generator import get_rendered_path
    cache_key = (card.name_key, language, target_width, target_height)
    if cache_key in _loaded_card_cache:
        return _loaded_card_cache[cache_key]
    
    path = get_rendered_path(card, language)
    if os.path.exists(path):
        try:
            img = pygame.image.load(path).convert_alpha()
        except:
            print(f"Nie można wczytać {path}")
            return None
        if img.get_width() != target_width or img.get_height() != target_height:
            img = pygame.transform.smoothscale(img, (target_width, target_height))
        _loaded_card_cache[cache_key] = img
        return img
    return None

def draw_card(surface, card, x, y, width, height, language="pl"):
    """Wczytuje gotową kartę z pliku PNG i skaluje."""
    img = load_rendered_card(card, language, width, height)
    if img is None:
        # Fallback – kolorowy prostokąt z nazwą
        pygame.draw.rect(surface, (80, 80, 120), (x, y, width, height))
        pygame.draw.rect(surface, (0, 0, 0), (x, y, width, height), 2)
        font = pygame.font.Font(None, int(width * 0.1))
        text = font.render(card.name_key or "?", True, (255,255,255))
        text_rect = text.get_rect(center=(x+width//2, y+height//2))
        surface.blit(text, text_rect)
    else:
        surface.blit(img, (x, y))
            
def draw_tooltip(surface, card, x, y, localization, font_small, font_medium=None, padding=10):
    """
    Rysuje tooltip z opisem karty w pozycji (x, y) – domyślnie prawy górny róg.
    """
    if card is None:
        return
    
    # Pobierz nazwę karty z tłumaczeń
    display_name = localization.get_card_name(card.name_key) if card.name_key else card.name or "Bez nazwy"
    
    # Pobierz przetłumaczoną nazwę typu
    type_name = localization.get_card_type_name(card.card_type)
    
    # Przygotuj linie tekstu
    lines = [
        display_name,
        f"Typ: {type_name}",
        f"Koszt inicjatywy: {card.cost_initiative}",
        f"Generowana inicjatywa: {card.initiative}",
        f"Koszt produkcji: {card.cost_production}",
        f"Produkcja: {card.production}",
    ]
    
    # Dodaj dodatkowe statystyki, jeśli >0
    stats = [
        ("max_workers", "Maks. robotników", card.max_workers),
        ("food_production", "Produkcja żywności", card.food_production),
        ("iron_ore_production", "Produkcja rudy", card.iron_ore_production),
        ("oil_production", "Produkcja ropy", card.oil_production),
        ("steal_production", "Produkcja stali", card.steal_production),
        ("fuel_production", "Produkcja paliwa", card.fuel_production),
        ("food_consumption", "Konsumpcja żywności", card.food_consumption),
        ("oil_consumption", "Konsumpcja ropy", card.oil_consumption),
        ("cost_steal", "Koszt w stali", card.cost_steal),
    ]
    for stat_key, stat_label, value in stats:
        if value > 0:
            lines.append(f"{stat_label}: {value}")
    
    # Jeśli są wymagania
    if card.requirements:
        req_text = "Wymagania: "
        req_parts = []
        for zone, req_type, count in card.requirements:
            zone_name = localization.get(f"zone_{zone.value}", zone.value)
            type_name_req = localization.get_card_type_name(req_type)
            req_parts.append(f"{count}x {type_name_req} w {zone_name}")
        lines.append(req_text + ", ".join(req_parts))
    
    # Jeśli są dozwolone załączniki
    if card.allowed_attachments:
        attach_names = [localization.get_card_type_name(a) for a in card.allowed_attachments]
        lines.append(f"Można dołączyć: {', '.join(attach_names)}")
    
    # Użyj font_small do mierzenia
    if font_medium is None:
        font_medium = font_small
    
    line_height = font_small.get_height() + 4
    max_width = 0
    for line in lines:
        w, _ = font_small.size(line)
        if w > max_width:
            max_width = w
    
    # Szerokość i wysokość tooltipa
    tooltip_width = max_width + 2 * padding
    tooltip_height = len(lines) * line_height + 2 * padding
    
    # Pozycja – domyślnie prawy górny róg, z marginesem
    if x is None:
        x = surface.get_width() - tooltip_width - 20
    if y is None:
        y = 20
    
    # Rysuj półprzezroczyste tło
    bg = pygame.Surface((tooltip_width, tooltip_height), pygame.SRCALPHA)
    bg.fill((0, 0, 0, 220))
    surface.blit(bg, (x, y))
    pygame.draw.rect(surface, (200, 200, 200), (x, y, tooltip_width, tooltip_height), 1)
    
    # Rysuj tekst
    for i, line in enumerate(lines):
        # Pierwsza linia (nazwa) – pogrubiona (można użyć font_medium)
        if i == 0 and font_medium is not None:
            text_surf = font_medium.render(line, True, (255, 255, 200))
        else:
            text_surf = font_small.render(line, True, (255, 255, 255))
        surface.blit(text_surf, (x + padding, y + padding + i * line_height))