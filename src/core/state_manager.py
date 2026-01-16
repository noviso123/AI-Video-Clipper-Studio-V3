"""
Gerenciador de Estado (Fase 19)
Salva o progresso e dados do projeto em disco para permitir recarregamento da página.
"""
import json
import os
from threading import Lock
from pathlib import Path

STATE_FILE = os.path.join(os.getcwd(), "state.json")
lock = Lock()

class StateManager:
    def __init__(self):
        self._load_state()

    def _load_state(self):
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, 'r', encoding='utf-8') as f:
                    self.state = json.load(f)
            except:
                self.state = self._default_state()
        else:
            self.state = self._default_state()

    def _default_state(self):
        return {
            "current_project": None, # dict com info do video
            "status": "idle", # processing, error, done
            "logs": [],
            "generated_clips": [], # lista de dicts
            "last_updated": 0
        }

    def save_state(self):
        with lock:
            with open(STATE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=2)

    def update_status(self, status):
        self.state["status"] = status
        self.save_state()

    def add_log(self, message):
        with lock:
            self.state["logs"].append(message)
            # Limitar logs para não explodir arquivo
            if len(self.state["logs"]) > 2000:
                self.state["logs"] = self.state["logs"][-2000:]
        self.save_state()

    def set_project(self, input_val, mode):
        self.state["current_project"] = {"input": input_val, "mode": mode}
        self.state["logs"] = [] # Reset logs no novo projeto
        self.state["generated_clips"] = []
        self.state["status"] = "processing"
        self.save_state()

    def get_full_state(self):
        return self.state
