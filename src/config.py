"""
Gerenciador de configuracoes (persistidas em JSON).

As configuracoes ficam em:
    %APPDATA%\\TikTokUltimateDownloader\\config.json

Tudo e carregado na inicializacao e salvo automaticamente sempre que
o usuario altera algo (pasta de destino, tema, notificacoes, etc.).
"""

import json
import os

from .utils import app_data_dir, default_download_dir


class Config:
    """Carrega, guarda e salva as preferencias do usuario."""

    def __init__(self) -> None:
        self._path = os.path.join(app_data_dir(), "config.json")

        # Valores padrao. Servem de base se o arquivo nao existir
        # ou se faltar alguma chave (compatibilidade entre versoes).
        self._defaults = {
            "download_folder": default_download_dir(),
            "language": "pt",                   # idioma da interface: pt | en
            "appearance_mode": "Dark",          # Dark / Light / System
            "color_theme": "blue",              # tema de cor do CustomTkinter
            "notifications_enabled": True,        # notificacao ao terminar
            "check_updates": True,                # checar versao ao abrir
            "open_folder_after": False,           # abrir pasta ao concluir
            "preferred_quality": "best",          # best | 1080 | 720 | 480
        }

        # Dicionario efetivo de configuracoes em memoria.
        self._data = dict(self._defaults)
        self.load()

    # ------------------------------------------------------------------
    # Leitura / escrita em disco
    # ------------------------------------------------------------------
    def load(self) -> None:
        """Le o config.json; se houver erro, mantem os padroes."""
        if not os.path.isfile(self._path):
            self.save()  # cria o arquivo na primeira execucao
            return

        try:
            with open(self._path, "r", encoding="utf-8") as fp:
                saved = json.load(fp)
            # Mescla: padroes como base + o que estava salvo por cima.
            merged = dict(self._defaults)
            merged.update({k: v for k, v in saved.items() if k in self._defaults})
            self._data = merged
        except (json.JSONDecodeError, OSError):
            # Arquivo corrompido: volta para os padroes sem travar o app.
            self._data = dict(self._defaults)

    def save(self) -> None:
        """Grava as configuracoes atuais no disco."""
        try:
            with open(self._path, "w", encoding="utf-8") as fp:
                json.dump(self._data, fp, indent=4, ensure_ascii=False)
        except OSError:
            # Falha ao salvar nao deve derrubar a aplicacao.
            pass

    # ------------------------------------------------------------------
    # Acesso estilo dicionario
    # ------------------------------------------------------------------
    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def set(self, key: str, value) -> None:
        """Define um valor e persiste imediatamente."""
        self._data[key] = value
        self.save()

    @property
    def path(self) -> str:
        return self._path
