# render_utils.py
import pygame

def draw_alpha_rect(surface, x, y, width, height, color, alpha=200, border_color=None, border_width=0):
    """
    Rysuje na powierzchni 'surface' półprzezroczysty prostokąt.
    color – krotka RGB (np. (0,0,0))
    alpha – przezroczystość (0-255)
    border_color – opcjonalny kolor ramki (RGB)
    border_width – szerokość ramki
    """
    rect = pygame.Rect(x, y, width, height)
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    surf.fill((*color, alpha))
    surface.blit(surf, (x, y))
    if border_color:
        pygame.draw.rect(surface, border_color, rect, border_width)

def draw_shadow(surface, x, y, width, height, offset=(6,6), color=(0,0,0), alpha=60):
    """
    Rysuje cień pod prostokątem.
    """
    shadow_x = x + offset[0]
    shadow_y = y + offset[1]
    draw_alpha_rect(surface, shadow_x, shadow_y, width, height, color, alpha)

def draw_button(surface, x, y, width, height, text, font, bg_color, text_color, hover=False):
    """
    Rysuje przycisk z tekstem.
    """
    color = bg_color if not hover else (
        min(255, bg_color[0] + 50),
        min(255, bg_color[1] + 50),
        min(255, bg_color[2] + 50)
    )
    pygame.draw.rect(surface, color, (x, y, width, height))
    pygame.draw.rect(surface, (0,0,0), (x, y, width, height), 2)
    text_surf = font.render(text, True, text_color)
    surface.blit(text_surf, text_surf.get_rect(center=(x + width//2, y + height//2)))

def draw_text_bg(surface, text, font, color, x, y, padding=10, bg_color=(0,0,0), bg_alpha=200):
    """
    Rysuje tekst z półprzezroczystym tłem.
    """
    text_surf = font.render(text, True, color)
    text_rect = text_surf.get_rect()
    bg_width = text_rect.width + padding * 2
    bg_height = text_rect.height + padding * 2
    draw_alpha_rect(surface, x, y, bg_width, bg_height, bg_color, bg_alpha)
    surface.blit(text_surf, (x + padding, y + padding))