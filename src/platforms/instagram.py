"""Plataforma: Instagram (Posts, Reels, IGTV e videos publicos)."""

from .base import Platform, register

register(Platform(
    id="instagram",
    name="Instagram",
    folder="Instagram",
    color="#E1306C",          # rosa/magenta da marca
    glyph="◉",           # circulo (lente da camera)
    patterns=(
        # /p/, /reel/, /reels/, /tv/, /<usuario>/...
        r"https?://(?:www\.)?instagram\.com/\S+",
        r"https?://instagr\.am/\S+",
    ),
    supports_playlist=False,
))
