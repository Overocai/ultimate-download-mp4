"""Plataforma: X / Twitter (videos publicados em tweets)."""

from .base import Platform, register

register(Platform(
    id="twitter",
    name="X / Twitter",
    folder="Twitter",
    color="#1D9BF0",          # azul classico do Twitter
    glyph="X",                # logo atual do X
    patterns=(
        # twitter.com/... e x.com/... (com ou sem www./mobile.)
        r"https?://(?:www\.|mobile\.)?(?:twitter|x)\.com/\S+",
        # encurtador oficial
        r"https?://t\.co/\S+",
    ),
    supports_playlist=False,
))
