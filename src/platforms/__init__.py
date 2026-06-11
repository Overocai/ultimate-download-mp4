"""
Sistema modular de plataformas do Ultimate Download MP4.

Importar este pacote ja registra todas as plataformas suportadas. A
interface (e o motor de download) trabalham apenas com:

    detect_platform(url) -> Platform | None
    all_platforms()      -> list[Platform]
    get_platform(id)     -> Platform
    GENERIC              -> plataforma curinga (sites nao catalogados)

Para adicionar uma nova plataforma no futuro, basta:
    1) criar um modulo aqui (ex.: `vimeo.py`) que chame `register(Platform(...))`;
    2) adiciona-lo a linha de imports abaixo.
Nenhuma alteracao na INTERFACE (app.py) e necessaria.

Os imports sao explicitos (e nao dinamicos) de proposito: assim o
PyInstaller detecta e embute todos os modulos ao gerar o .exe. A ordem dos
imports define a prioridade de deteccao quando houver padroes concorrentes.
"""

from .base import (
    GENERIC,
    Platform,
    all_platforms,
    detect_platform,
    get_platform,
    register,
)

# Cada import abaixo registra a sua plataforma (via register()).
from . import tiktok, youtube, instagram, twitter  # noqa: E402,F401

__all__ = [
    "GENERIC",
    "Platform",
    "all_platforms",
    "detect_platform",
    "get_platform",
    "register",
]
