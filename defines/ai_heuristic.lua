-- defines/ai_heuristic.lua
-- =============================================================================
-- AI HEURYSTYCZNE – DOMYŚLNE WAGI
-- =============================================================================
-- Ten plik definiuje punkt startowy dla HeuristicAI (game_ai/heuristic_ai.py).
--
-- Struktura:
--   * Klucze najwyższego poziomu = wagi globalne (np. min_score).
--   * Sekcje zagnieżdżone grupują wagi powiązane z jedną akcją.
--   * Loader (game_ai/config.py) spłaszcza zagnieżdżenia:
--         play.base  →  play_base
--         attach.worker_base  →  attach_worker_base
--
-- Jak eksperymentować:
--   1. Zmień wartość, zapisz plik, uruchom grę ponownie.
--   2. Aby zachować oryginał, skopiuj plik jako ai_heuristic_local.lua
--      i wczytaj inną ścieżką (weights_path=...).
--   3. W przyszłości te same klucze posłużą do meta-tuningu
--      przez sieć neuronową (ścieżka A z planu).
-- =============================================================================

local weights = {

    -- =========================================================================
    -- PROGI GLOBALNE
    -- =========================================================================
    -- Decydują, kiedy AI w ogóle wykona akcję, a kiedy woli zakończyć turę.
    -- Poniżej min_score AI zawsze wybierze end_turn.
    -- =========================================================================
    min_score = 5.0,
    end_turn  = 0.0,

    -- =========================================================================
    -- META – informacje o wersji (nie używane do oceny, przydatne w logach).
    -- =========================================================================
    meta = {
        version     = "1.0",
        description = "Punkt startowy dla HeuristicAI – wagi dobrane ręcznie.",
    },

    -- =========================================================================
    -- ZAGRANIE KARTY Z RĘKI ("play")
    -- =========================================================================
    play = {
        -- Baza dla każdej zagranej karty.
        base = 20.0,

        -- Premia za strefę:
        --   STATE – karty ekonomiczne (terrain, building, city)
        --   FRONT – jednostki militarne
        bonus_state = 10.0,
        bonus_front = 8.0,

        -- Premia za typ karty – budynki zwracają się dopiero po kilku turach,
        -- ale dają trwałą produkcję, więc są cenne.
        bonus_building = 15.0,

        -- Wartość jednostkowa każdego punktu produkcji, jaki daje karta.
        -- To jest to samo "w_food" co w DEFAULT_WEIGHTS w Pythonie.
        w_food  = 3.0,
        w_prod  = 2.0,
        w_init  = 2.0,
        w_steal = 4.0,
        w_oil   = 3.0,
        w_iron  = 3.0,
        w_fuel  = 3.0,
    },

    -- =========================================================================
    -- DOŁĄCZENIE KARTY Z RĘKI DO CELU ("attach")
    -- =========================================================================
    attach = {
        -- Robotnik: wartość zależy od tego, ile produkcji „obudzi” w celu.
        worker_base     = 15.0,
        worker_per_food = 3.0,
        worker_per_iron = 3.0,
        worker_per_oil  = 3.0,

        -- Broń: wartość rośnie z zasięgiem.
        weapon_base      = 20.0,
        weapon_per_range = 10.0,
    },

    -- =========================================================================
    -- RUCH ŻOŁNIERZA ("move")
    -- =========================================================================
    -- Ruch kosztuje logistykę i inicjatywę – dlatego baza jest niska.
    -- Premia za każdy krok w stronę frontu (BACK=0, SECOND=1, FRONT=2).
    -- =========================================================================
    move = {
        base                  = 5.0,
        per_step_toward_front = 8.0,
    },

    -- =========================================================================
    -- ATAK ("attack")
    -- =========================================================================
    -- Punktacja opiera się na wyniku GameLogic.calculate_attack_simulation:
    --   P(zabicia)          – im wyższa, tym lepiej
    --   ryzyko kontrataku   – suma szans trafienia dla każdego atakującego
    -- =========================================================================
    attack = {
        base                = 10.0,
        per_success_chance  = 100.0,   -- × P(zabicia)
        per_counter_risk    = -50.0,   -- × suma szans kontrataku
    },

    -- =========================================================================
    -- DOBRANIE KARTY ("draw")
    -- =========================================================================
    draw = {
        -- Premia, gdy mamy miejsce w ręce.
        base = 8.0,
        -- Kara, gdy ręka jest prawie pełna (nie opłaca się dobierać).
        when_full = -50.0,
    },
}

return weights