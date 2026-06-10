"""
Gerador do icone do aplicativo (assets/icon.ico).

Cria programaticamente um icone com as cores do TikTok (ciano + magenta
sobre fundo escuro) e uma nota musical no centro. Assim nao dependemos
de nenhum arquivo de imagem externo.

Uso:
    python assets/create_icon.py
"""

import os

from PIL import Image, ImageDraw, ImageFont


def _load_font(size: int):
    """Tenta carregar uma fonte do sistema; cai para a padrao se falhar."""
    for name in ("seguisym.ttf", "segoeui.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def make_icon(path: str) -> None:
    # Renderizamos grande (512px) e depois geramos os varios tamanhos.
    size = 512
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Fundo: retangulo arredondado escuro.
    radius = 110
    draw.rounded_rectangle(
        [(16, 16), (size - 16, size - 16)],
        radius=radius,
        fill=(14, 14, 18, 255),
    )

    # Efeito "duplo" da marca: nota magenta deslocada + nota ciano.
    note = "♫"  # nota musical dupla
    font = _load_font(300)

    # Centraliza o glifo.
    bbox = draw.textbbox((0, 0), note, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    cx = (size - tw) / 2 - bbox[0]
    cy = (size - th) / 2 - bbox[1]

    # Sombra magenta (deslocada).
    draw.text((cx - 14, cy - 10), note, font=font, fill=(254, 44, 85, 230))
    # Sombra ciano (deslocada para o outro lado).
    draw.text((cx + 14, cy + 10), note, font=font, fill=(37, 244, 238, 230))
    # Nota principal branca por cima.
    draw.text((cx, cy), note, font=font, fill=(244, 244, 245, 255))

    # Salva como .ico com varios tamanhos (Windows usa o adequado).
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    img.save(path, format="ICO", sizes=sizes)
    print(f"Icone gerado em: {path}")


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
    make_icon(out)
