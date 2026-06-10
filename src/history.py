"""
Historico dos ultimos downloads.

Cada item guarda titulo, autor, resolucao, caminho do arquivo e a
data/hora. E persistido em JSON em:
    %APPDATA%\\TikTokUltimateDownloader\\history.json
"""

import json
import os
from datetime import datetime

from .utils import app_data_dir


class History:
    """Mantem uma lista dos downloads mais recentes."""

    def __init__(self, max_items: int = 50) -> None:
        self._path = os.path.join(app_data_dir(), "history.json")
        self._max_items = max_items
        self._items: list[dict] = []
        self.load()

    # ------------------------------------------------------------------
    def load(self) -> None:
        if not os.path.isfile(self._path):
            return
        try:
            with open(self._path, "r", encoding="utf-8") as fp:
                data = json.load(fp)
            if isinstance(data, list):
                self._items = data[: self._max_items]
        except (json.JSONDecodeError, OSError):
            self._items = []

    def save(self) -> None:
        try:
            with open(self._path, "w", encoding="utf-8") as fp:
                json.dump(self._items, fp, indent=4, ensure_ascii=False)
        except OSError:
            pass

    # ------------------------------------------------------------------
    def add(self, info: dict) -> None:
        """
        Adiciona um download ao topo do historico.

        `info` deve conter as chaves: title, author, resolution,
        duration, filepath.
        """
        entry = {
            "title": info.get("title", "Sem titulo"),
            "author": info.get("author", "Desconhecido"),
            "resolution": info.get("resolution", "--"),
            "duration": info.get("duration", "--:--"),
            "filepath": info.get("filepath", ""),
            "format": info.get("format", "MP4"),  # MP4 (video) ou MP3 (audio)
            "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
        }
        # Insere no inicio (mais recente primeiro) e corta o excesso.
        self._items.insert(0, entry)
        self._items = self._items[: self._max_items]
        self.save()

    def all(self) -> list[dict]:
        """Retorna uma copia da lista (mais recentes primeiro)."""
        return list(self._items)

    def clear(self) -> None:
        self._items = []
        self.save()
