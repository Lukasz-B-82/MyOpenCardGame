# 🃏 OpenCardGame – gra karciana w Pygame

Otwarta gra karciana inspirowana grami strategicznymi, w której gracze zarządzają zasobami, rozwijają swoje terytoria i walczą o dominację.  
Projekt jest w fazie rozwoju – zapraszamy do współtworzenia!

---

## 📋 Spis treści

- [Opis gry](#-opis-gry)
- [Główne cechy](#-główne-cechy)
- [Wymagania systemowe](#-wymagania-systemowe)
- [Instalacja i uruchomienie](#-instalacja-i-uruchomienie)
- [Struktura projektu](#-struktura-projektu)
- [Konfiguracja i rozszerzanie](#-konfiguracja-i-rozszerzanie)
- [Tworzenie własnych kart](#-tworzenie-własnych-kart)
- [Tłumaczenia](#-tłumaczenia)
- [Licencja](#-licencja)

---

## 🎮 Opis gry

Gracze wcielają się w dowódców, którzy:
- **Zagrywają karty** (żołnierze, robotnicy, pojazdy, broń, tereny, miasta, budynki) w czterech strefach: *Front, Druga linia, Zaplecze, Państwo*.
- **Zarządzają zasobami**: żywność, produkcja, ruda żelaza, ropa, stal, paliwo.
- **Dołączają karty** do innych (np. robotnika do terenu, broń do żołnierza).
- **Rywalizują** z przeciwnikami (hot‑seat, gra lokalna) – każdy gracz ma swoją talię i ekran.

Gra oferuje:
- Dynamiczną mechanikę tury (zbiórka zasobów, koszty utrzymania, inicjatywa).
- Edytor talii (tworzenie i zapisywanie talii w plikach JSON).
- Generator kart na podstawie plików Lua (obrazki PNG + ramki).
- Wielojęzyczność (obsługa tłumaczeń YAML).

---

## ✨ Główne cechy

- ✅ **Rozbudowany system kart** – każda karta ma statystyki, koszty, wymagania, możliwość dołączania.
- ✅ **Interfejs w Pygame** – plansza z czterema strefami, ręką, paskami zasobów i inicjatywy.
- ✅ **Edytor talii** – przeglądanie wszystkich kart, dodawanie/usuwanie kopii, zapis/odczyt.
- ✅ **Generator kart** – tworzy obrazki PNG (512×768) z ramkami, ikonami, flagami frakcji i tekstem.
- ✅ **System zasobów** – żywność, produkcja, surowce (ropa, ruda, stal, paliwo) z automatycznym bilansowaniem.
- ✅ **Dołączanie kart** – robotnicy do terenów/budynków, broń/pojazdy do żołnierzy.
- ✅ **Wieloosobowość lokalna** – obsługa od 2 do 8 graczy (hot‑seat).
- ✅ **Tłumaczenia** – pliki YAML dla UI, nazw kart, typów.
- ✅ **Pełny ekran i zmiana rozmiaru** – okno można dowolnie skalować.

---

## 🔧 Wymagania systemowe

- Python 3.10+
- Pygame 2.6+
- Pillow (PIL)
- Lupa (do odczytu plików Lua)
- PyYAML

---

## 🚀 Instalacja i uruchomienie

1. **Sklonuj repozytorium**
   ```bash
   git clone https://github.com/twoja-nazwa/OpenCardGame.git
   cd OpenCardGame

2. **Zainstaluj zależności**
    ```bash
    pip install pygame pillow lupa pyyaml

2. **Uruchom grę**
    ```bash
    python main.py

## 📁 Struktura projektu

```text
    📁 OpenCardGame/
    │
    ├── main.py                 # Punkt wejścia
    ├── menu.py                 # Menu główne
    ├── game.py                 # Główna pętla gry (łączy logikę i widok)
    ├── game_logic.py           # Logika gry (zagrywanie, dołączanie, tury, zasoby)
    ├── game_view.py            # Rysowanie całej planszy (strefy, ręka, przeciwnicy)
    ├── player.py               # Klasa gracza (ręka, talia, strefy, zasoby)
    ├── card.py                 # Klasa karty i enuny (CardType, Faction, Zone)
    ├── card_view.py            # Wyświetlanie pojedynczej karty (tooltip, podgląd)
    ├── card_renderer.py        # Renderowanie kart (ładowanie obrazków, ramek)
    ├── card_generator.py       # Generowanie plików PNG kart
    ├── deck_editor.py          # Edytor talii
    ├── fonts.py                # Zarządzanie czcionkami (singleton)
    ├── localization.py         # Obsługa tłumaczeń (YAML)
    ├── constants.py            # Stałe (rozmiary, kolory, ścieżki)
    ├── README.md               # Ten plik
    │
    ├── 📁 defines/             # Pliki konfiguracyjne w Lua
    │   ├── cards.lua           # Definicje wszystkich kart
    │   ├── frames.lua          # Definicje ramek
    │   └── game.lua            # Konfiguracja gry (inicjatywa, max_hand_size, itp.)
    │
    ├── 📁 decks/               # Talie graczy (JSON)
    │   └── default.json
    │
    ├── 📁 images/              # Zasoby graficzne
    │   ├── 📁 cards/           # Obrazki kart
    │   │   ├── backs/          # Rewersy kart
    │   │   ├── borders/        # Ramki
    │   │   └── icons/          # Ikony typów i flagi frakcji
    │   ├── 📁 board/           # Tła planszy
    │   └── 📁 start_screen/    # Tła menu
    │
    ├── 📁 fonts/               # Pliki czcionek (TTF)
    │   ├── StoryScript-Regular.ttf
    │   ├── BIZUDGothic-Regular.ttf
    │   └── BIZUDGothic-Bold.ttf
    │
    ├── 📁 translations/        # Tłumaczenia (YAML)
    │   ├── 📁 pl/              # Polskie
    │   │   ├── ui_texts.yaml
    │   │   └── card_names.yaml
    │   └── 📁 en/              # Angielskie
    │       ├── ui_texts.yaml
    │       └── card_names.yaml
    │
    └── 📁 rendered_cards/      # Wygenerowane obrazki kart (PNG)

## ⚙️ Konfiguracja i rozszerzanie
