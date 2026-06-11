"""Plataforma: TikTok (videos sem marca d'agua)."""

from .base import Platform, register

register(Platform(
    id="tiktok",
    name="TikTok",
    folder="TikTok",
    color="#25F4EE",          # ciano da marca
    glyph="♪",           # nota musical
    patterns=(
        # www./m./vm./vt. .tiktok.com/...  e tambem o dominio sem subdominio.
        r"https?://(?:[\w-]+\.)?tiktok\.com/\S+",
    ),
    supports_playlist=False,
))
