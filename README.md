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