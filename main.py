import pygame
import sys
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, FPS
from fonts import fonts
from menu import menu_loop
from deck_editor import ALL_CARDS
from card_generator import render_all_cards
from game import game_loop

def main():
    pygame.init()
    fonts.initialize()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("Gra karciana")
    clock = pygame.time.Clock()
    
    languages = ["pl", "en"]
    for lang in languages:
        render_all_cards(ALL_CARDS, lang)

    while True:
        language, players_config, open_editor = menu_loop(screen, clock)
        if open_editor:
            from deck_editor import deck_editor_loop
            deck_editor_loop(screen, clock, language)
            continue
        else:
            # Uruchom właściwą grę z players i language
            print(f"Uruchamiam grę z {len(players_config)} graczami, język: {language}")
            # game_loop(screen, clock, players, language)  # na razie tylko print
            game_loop(screen, clock, players_config, language)
            continue

if __name__ == "__main__":
    main()