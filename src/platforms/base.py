"""
Base do sistema modular de plataformas.

Cada site suportado (TikTok, YouTube, Instagram, X/Twitter, ...) e descrito
por uma instancia de `Platform`. Os modulos de plataforma se registram
sozinhos ao serem importados (ver `src/platforms/__init__.py`), e a interface
usa apenas `detect_platform(url)` + os metadados genericos do objeto
retornado.

Consequencia pratica: para adicionar uma NOVA plataforma basta criar um
arquivo novo em `src/platforms/` que chame `register(Platform(...))`. Nada
na interface (app.py) precisa ser alterado.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class Platform:
    """Descreve uma plataforma suportada e como lidar com ela."""

    id: str                      # identificador interno: "youtube"
    name: str                    # nome exibido na interface: "YouTube"
    folder: str                  # subpasta de destino: "YouTube"
    color: str                   # cor da marca (hex) usada no icone/realce
    glyph: str                   # simbolo curto (fallback do icone)
    patterns: tuple = ()         # regex (str) que reconhecem a URL
    ydl_opts: dict = field(default_factory=dict)  # opcoes extras do yt-dlp
    supports_playlist: bool = False  # baixa colecoes (ex.: playlists do YouTube)

    def matches(self, url: str) -> bool:
        """A URL pertence a esta plataforma?"""
        return any(re.search(p, url, re.IGNORECASE) for p in self.patterns)


# Registro global das plataformas conhecidas. A ORDEM importa: o primeiro
# padrao que casar com a URL vence (por isso plataformas mais especificas
# devem ser registradas antes das mais genericas, se houver conflito).
_REGISTRY: list[Platform] = []


def register(platform: Platform) -> Platform:
    """Adiciona uma plataforma ao registro (chamado por cada modulo)."""
    # Evita duplicatas caso o modulo seja importado mais de uma vez.
    if not any(p.id == platform.id for p in _REGISTRY):
        _REGISTRY.append(platform)
    return platform


# Plataforma "curinga": usada quando o link e uma URL valida mas nao casa
# com nenhuma plataforma conhecida. O yt-dlp suporta centenas de sites, entao
# deixamos a tentativa acontecer mesmo assim (mantem compatibilidade futura).
GENERIC = Platform(
    id="generic",
    name="Outra plataforma",
    folder="Outros",
    color="#9A9AA8",
    glyph="?",
    patterns=(),
    supports_playlist=False,
)


def all_platforms() -> list[Platform]:
    """Retorna a lista das plataformas conhecidas (sem a curinga)."""
    return list(_REGISTRY)


def detect_platform(url: str) -> Optional[Platform]:
    """
    Identifica a plataforma de uma URL.

    Retorna:
        - a `Platform` correspondente, se o link casar com uma conhecida;
        - `GENERIC`, se for uma URL http(s) de site nao catalogado;
        - `None`, se a string nem parecer uma URL (entrada invalida).
    """
    if not url:
        return None
    url = url.strip()
    for platform in _REGISTRY:
        if platform.matches(url):
            return platform
    if re.match(r"https?://\S+", url, re.IGNORECASE):
        return GENERIC
    return None


def get_platform(platform_id: str) -> Platform:
    """Busca uma plataforma pelo id; devolve a curinga se nao achar."""
    for p in _REGISTRY:
        if p.id == platform_id:
            return p
    return GENERIC
