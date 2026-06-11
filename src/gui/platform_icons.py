"""
Icones das plataformas, desenhados programaticamente com Pillow.

Cada icone e gerado em memoria (sem arquivos externos) e cacheado por
(plataforma, tamanho). A interface envolve a imagem retornada em um
`CTkImage`.

Para uma plataforma nova/desconhecida, cai num emblema generico que usa a
cor e o glifo definidos no proprio objeto `Platform`. Assim, ao adicionar
uma nova plataforma, ela JA ganha um icone decente sem precisar mexer aqui
(embora se possa, opcionalmente, registrar um desenho dedicado em _DRAWERS).
"""

from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont

from ..platforms import GENERIC, get_platform

_SS = 4  # fator de supersampling (desenha grande e reduz -> bordas suaves)


# ----------------------------------------------------------------------
# Helpers de desenho
# ----------------------------------------------------------------------
def _hex(color: str) -> tuple:
    color = color.lstrip("#")
    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))


def _canvas(px: int):
    img = Image.new("RGBA", (px, px), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def _rounded_bg(draw, px: int, color, radius_ratio: float = 0.28) -> None:
    r = int(px * radius_ratio)
    if len(color) == 3:
        color = color + (255,)
    draw.rounded_rectangle([0, 0, px - 1, px - 1], radius=r, fill=color)


def _font(px: int, ratio: float = 0.6):
    size = max(8, int(px * ratio))
    for name in ("segoeuib.ttf", "arialbd.ttf", "segoeui.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _sym_font(px: int, ratio: float = 0.55):
    size = max(8, int(px * ratio))
    for name in ("seguisym.ttf", "segoeui.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _center_text(draw, text, font, px, fill, dx=0.0, dy=0.0) -> None:
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (px - tw) / 2 - bbox[0] + dx
    y = (px - th) / 2 - bbox[1] + dy
    draw.text((x, y), text, font=font, fill=fill)


# ----------------------------------------------------------------------
# Desenhos por plataforma
# ----------------------------------------------------------------------
def _draw_youtube(px: int, platform) -> Image.Image:
    img, d = _canvas(px)
    _rounded_bg(d, px, _hex("#FF0033"))
    cx, cy = px / 2, px / 2
    w = px * 0.20
    d.polygon([(cx - w * 0.65, cy - w), (cx - w * 0.65, cy + w),
               (cx + w, cy)], fill=(255, 255, 255, 255))
    return img


def _draw_tiktok(px: int, platform) -> Image.Image:
    img, d = _canvas(px)
    _rounded_bg(d, px, _hex("#0E0E12"))
    f = _sym_font(px, 0.58)
    off = px * 0.05
    # Efeito "duplo" da marca: nota magenta + ciano deslocadas, branca por cima.
    _center_text(d, "♪", f, px, _hex("#FE2C55") + (235,), off, off)
    _center_text(d, "♪", f, px, _hex("#25F4EE") + (235,), -off, -off)
    _center_text(d, "♪", f, px, (244, 244, 245, 255))
    return img


def _draw_instagram(px: int, platform) -> Image.Image:
    # Fundo com gradiente diagonal (laranja -> rosa -> roxo).
    c_lo, c_mid, c_hi = _hex("#F58529"), _hex("#DD2A7B"), _hex("#515BD4")
    grad = Image.new("RGB", (px, px))
    gpx = grad.load()
    denom = max(1, 2 * (px - 1))
    for y in range(px):
        for x in range(px):
            t = (x + y) / denom  # 0 (canto sup-esq) -> 1 (canto inf-dir)
            if t < 0.5:
                k = t / 0.5
                col = tuple(int(c_lo[i] + (c_mid[i] - c_lo[i]) * k) for i in range(3))
            else:
                k = (t - 0.5) / 0.5
                col = tuple(int(c_mid[i] + (c_hi[i] - c_mid[i]) * k) for i in range(3))
            gpx[x, y] = col

    mask = Image.new("L", (px, px), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, px - 1, px - 1], radius=int(px * 0.28), fill=255)
    out = Image.new("RGBA", (px, px), (0, 0, 0, 0))
    out.paste(grad, (0, 0), mask)

    d = ImageDraw.Draw(out)
    white = (255, 255, 255, 255)
    m = px * 0.26
    lw = max(2, int(px * 0.05))
    d.rounded_rectangle([m, m, px - m, px - m], radius=int(px * 0.11),
                        outline=white, width=lw)
    r = px * 0.13
    cx = cy = px / 2
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=white, width=lw)
    fr = px * 0.035
    fx, fy = px - m - px * 0.06, m + px * 0.06
    d.ellipse([fx - fr, fy - fr, fx + fr, fy + fr], fill=white)
    return out


def _draw_twitter(px: int, platform) -> Image.Image:
    img, d = _canvas(px)
    _rounded_bg(d, px, (0, 0, 0, 255))  # preto (marca atual do X)
    m = px * 0.30
    lw = max(2, int(px * 0.085))
    white = (255, 255, 255, 255)
    d.line([(m, m), (px - m, px - m)], fill=white, width=lw)
    d.line([(px - m, m), (m, px - m)], fill=white, width=lw)
    return img


def _draw_generic(px: int, platform) -> Image.Image:
    img, d = _canvas(px)
    _rounded_bg(d, px, _hex(platform.color))
    _center_text(d, platform.glyph or "?", _font(px, 0.55), px, (255, 255, 255, 255))
    return img


_DRAWERS = {
    "tiktok": _draw_tiktok,
    "youtube": _draw_youtube,
    "instagram": _draw_instagram,
    "twitter": _draw_twitter,
}


# ----------------------------------------------------------------------
# API publica
# ----------------------------------------------------------------------
@lru_cache(maxsize=64)
def _render_cached(platform_id: str, size: int) -> Image.Image:
    platform = get_platform(platform_id)
    px = size * _SS
    drawer = _DRAWERS.get(platform_id, _draw_generic)
    img = drawer(px, platform)
    return img.resize((size, size), Image.LANCZOS)


def render(platform, size: int = 40) -> Image.Image:
    """Retorna o icone (PIL.Image RGBA) da plataforma no tamanho pedido."""
    pid = platform.id if platform is not None else GENERIC.id
    return _render_cached(pid, size)
