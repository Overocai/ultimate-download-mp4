"""
Gera as imagens do assistente de instalacao (estilo Node.js).

Cria dois arquivos BMP usados pelo Inno Setup:
  - wizard_large.bmp (164x314): banner vertical das paginas de
    boas-vindas e de conclusao (a "imagem lateral" grande).
  - wizard_small.bmp (55x58): logo pequeno no topo das paginas internas.

Tudo desenhado programaticamente com Pillow (sem imagens externas).

Uso:
    python assets/create_installer_images.py
"""

import os

from PIL import Image, ImageDraw, ImageFont

ASSETS = os.path.dirname(os.path.abspath(__file__))

# Cores da identidade visual (mesmas do app).
BG_TOP = (14, 14, 18)       # #0E0E12
BG_BOTTOM = (24, 24, 34)    # #181822
CYAN = (37, 244, 238)       # #25F4EE
MAGENTA = (254, 44, 85)     # #FE2C55
WHITE = (244, 244, 245)
MUTED = (150, 150, 168)
SURFACE = (23, 23, 31)      # #17171F


def _font(size, bold=False):
    names = (["segoeuib.ttf", "segoeui.ttf"] if bold else ["segoeui.ttf"]) + ["arial.ttf"]
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _sym_font(size):
    for name in ("seguisym.ttf", "segoeui.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _vgradient(w, h, top, bottom):
    """Cria um fundo com gradiente vertical."""
    img = Image.new("RGB", (w, h), top)
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(1, h - 1)
        color = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        d.line([(0, y), (w, y)], fill=color)
    return img


def _hgradient_bar(draw, x0, y0, x1, y1, left, right):
    """Desenha uma barra horizontal com gradiente (acento ciano->magenta)."""
    width = x1 - x0
    for i in range(width):
        t = i / max(1, width - 1)
        color = tuple(int(left[j] + (right[j] - left[j]) * t) for j in range(3))
        draw.line([(x0 + i, y0), (x0 + i, y1)], fill=color)


def _center(draw, text, font, cx, y, fill):
    w = draw.textlength(text, font=font)
    draw.text((cx - w / 2, y), text, font=font, fill=fill)


def make_large(path):
    W, H = 164, 314
    img = _vgradient(W, H, BG_TOP, BG_BOTTOM)
    d = ImageDraw.Draw(img)

    cx = W // 2

    # Logo: quadrado arredondado com a nota musical.
    box = 60
    bx0, by0 = cx - box // 2, 46
    d.rounded_rectangle([bx0, by0, bx0 + box, by0 + box], radius=16,
                        fill=SURFACE, outline=CYAN, width=2)
    note_font = _sym_font(34)
    _center(d, "♫", note_font, cx, by0 + 8, CYAN)

    # Titulo em tres linhas.
    _center(d, "TikTok", _font(22, bold=True), cx, 124, CYAN)
    _center(d, "Ultimate", _font(18, bold=True), cx, 152, WHITE)
    _center(d, "Downloader", _font(18, bold=True), cx, 174, WHITE)

    # Subtitulo.
    _center(d, "Sem marca d'agua", _font(11), cx, 208, MUTED)
    _center(d, "MP4  -  MP3", _font(11), cx, 224, MUTED)

    # Barra de acento ciano->magenta na base.
    _hgradient_bar(d, 0, H - 10, W, H, CYAN, MAGENTA)

    img.save(path, format="BMP")
    print("Gerado:", path)


def make_small(path):
    W, H = 55, 58
    img = Image.new("RGB", (W, H), BG_TOP)
    d = ImageDraw.Draw(img)

    # Quadrado arredondado (chip) com a nota musical, centralizado.
    box = 44
    bx0, by0 = (W - box) // 2, (H - box) // 2
    d.rounded_rectangle([bx0, by0, bx0 + box, by0 + box], radius=12,
                        fill=SURFACE, outline=CYAN, width=2)
    _center(d, "♫", _sym_font(26), W // 2, by0 + 5, CYAN)

    img.save(path, format="BMP")
    print("Gerado:", path)


if __name__ == "__main__":
    make_large(os.path.join(ASSETS, "wizard_large.bmp"))
    make_small(os.path.join(ASSETS, "wizard_small.bmp"))
