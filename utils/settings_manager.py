import json
import os
from typing import Dict, Any

class SettingsManager:
    _instance = None
    _settings = {}
    _default_settings = {
        "parser": {
            "max_pdf_size": 5,
            "enabled_features": ["Contact Details", "Education", "Work Experience", "Skills"],
            "deep_parsing": True
        },
        "database": {
            "host": "localhost",
            "name": "resume_parser_db",
            "auto_backup": True
        },
        "security": {
            "admin_email": "admin@example.com",
            "session_timeout": 15,
            "two_factor": False
        },
        "api": {
            "api_key": "",
            "ai_model": "GPT-3.5"
        }
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.settings_file = 'data/system_settings.json'
        self.load_settings()

    def load_settings(self):
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    self._settings = json.load(f)
            else:
                self._settings = self._default_settings
                self.save_settings()
        except Exception as e:
            print(f"Error loading settings: {e}")
            self._settings = self._default_settings

    def save_settings(self):
        try:
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            with open(self.settings_file, 'w') as f:
                json.dump(self._settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def get_setting(self, category: str, key: str) -> Any:
        return self._settings.get(category, {}).get(key, self._default_settings[category][key])

    def update_setting(self, category: str, key: str, value: Any):
        if category not in self._settings:
            self._settings[category] = {}
        self._settings[category][key] = value
        self.save_settings()