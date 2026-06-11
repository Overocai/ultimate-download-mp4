"""
Gerador do icone do aplicativo (assets/icon.ico).

Cria programaticamente o icone do "Ultimate Download MP4": um fundo escuro
arredondado com uma SETA DE DOWNLOAD (estilo "salvar") nas cores da marca
(ciano + magenta) e o selo "MP4" na base. Assim nao dependemos de nenhum
arquivo de imagem externo.

Uso:
    python assets/create_icon.py
"""

import os

from PIL import Image, ImageDraw, ImageFont

CYAN = (37, 244, 238)
MAGENTA = (254, 44, 85)
WHITE = (244, 244, 245)
BG = (14, 14, 18, 255)


def _load_font(size: int):
    for name in ("segoeuib.ttf", "segoeui.ttf", "arialbd.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _draw_download(draw, size, dx, dy, color):
    """Desenha uma seta de download (haste + ponta) sobre uma bandeja."""
    cx = size / 2 + dx

    # Haste vertical.
    stem_w = size * 0.13
    draw.rectangle(
        [cx - stem_w / 2, size * 0.20 + dy, cx + stem_w / 2, size * 0.49 + dy],
        fill=color)

    # Ponta da seta (triangulo apontando para baixo).
    head_w = size * 0.30
    head_top = size * 0.46 + dy
    draw.polygon(
        [(cx - head_w, head_top), (cx + head_w, head_top), (cx, size * 0.66 + dy)],
        fill=color)

    # Bandeja (base) sugerindo "salvar/baixar".
    tray_w, tray_h = size * 0.46, size * 0.085
    tray_y = size * 0.73 + dy
    draw.rounded_rectangle(
        [cx - tray_w, tray_y, cx + tray_w, tray_y + tray_h],
        radius=tray_h / 2, fill=color)


def make_icon(path: str) -> None:
    size = 512
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Fundo: retangulo arredondado escuro.
    draw.rounded_rectangle([(16, 16), (size - 16, size - 16)], radius=110, fill=BG)

    # Efeito "duplo" da marca: sombra magenta deslocada + seta ciano por cima.
    off = size * 0.018
    _draw_download(draw, size, off, off, MAGENTA + (235,))
    _draw_download(draw, size, -off, -off, CYAN + (255,))

    # Selo "MP4" na base.
    font = _load_font(int(size * 0.13))
    text = "MP4"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    draw.text(((size - tw) / 2 - bbox[0], size * 0.80), text, font=font, fill=WHITE)

    # Salva como .ico com varios tamanhos (Windows usa o adequado).
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    img.save(path, format="ICO", sizes=sizes)
    print(f"Icone gerado em: {path}")


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
    make_icon(out)
