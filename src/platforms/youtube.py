"""Plataforma: YouTube (videos, Shorts, playlists e lives gravadas)."""

from .base import Platform, register

register(Platform(
    id="youtube",
    name="YouTube",
    folder="YouTube",
    color="#FF0033",          # vermelho da marca
    glyph="▶",           # triangulo de "play"
    patterns=(
        # watch?v=, shorts/, playlist?list=, live/, @canal, etc.
        r"https?://(?:www\.|m\.|music\.)?youtube\.com/\S+",
        # links curtos youtu.be/<id>
        r"https?://youtu\.be/\S+",
    ),
    # O YouTube e a unica plataforma daqui que entrega playlists/colecoes.
    # A decisao de baixar a playlist inteira ou so um item e feita no
    # downloader a partir da URL (presenca de "list=").
    supports_playlist=True,
))
