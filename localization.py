# localization.py
import os
import yaml
from typing import Dict

class Localization:
    def __init__(self, lang: str = "pl"):
        self.lang = lang
        self.ui_texts: Dict[str, str] = {}
        self.load()

    def load(self):
        base_path = os.path.join("translations", self.lang)
        ui_path = os.path.join(base_path, "ui_texts.yaml")
        if os.path.exists(ui_path):
            with open(ui_path, "r", encoding="utf-8") as f:
                self.ui_texts = yaml.safe_load(f) or {}
        card_names_path = os.path.join(base_path, "card_names.yaml")
        if os.path.exists(card_names_path):
            with open(card_names_path, "r", encoding="utf-8") as f:
                self.card_names = yaml.safe_load(f) or {}

    def get(self, key: str, default: str = None) -> str:
        return self.ui_texts.get(key, default or key)
    
    def get_card_name(self, key):
        return self.card_names.get(key, key)  # fallback – key

    def set_language(self, lang: str):
        self.lang = lang
        self.load()
        
    def get_card_type_name(self, card_type):
        """Zwraca przetłumaczoną nazwę typu karty."""
        key = f"card_type_{card_type.value}"
        return self.get(key, card_type.value)

    def get_stat_name(self, stat_key):
        """Zwraca przetłumaczoną nazwę statystyki."""
        return self.get(f"stat_{stat_key}", stat_key)