"""
Geracao das bandeiras (Brasil e Ingles/EUA) usadas no seletor de idioma.

As bandeiras sao desenhadas programaticamente com Pillow, retornando
objetos PIL.Image. Assim nao dependemos de arquivos de imagem externos
e elas ficam nitidas em qualquer tamanho.
"""

from PIL import Image, ImageDraw


def brazil_flag(w: int = 72, h: int = 48) -> Image.Image:
    """Bandeira do Brasil (verde, losango amarelo e circulo azul)."""
    img = Image.new("RGB", (w, h), (1, 137, 54))  # verde
    d = ImageDraw.Draw(img)

    # Losango amarelo.
    m = int(w * 0.08)
    d.polygon(
        [(w // 2, m), (w - m, h // 2), (w // 2, h - m), (m, h // 2)],
        fill=(255, 223, 0),
    )

    # Circulo azul central.
    r = int(h * 0.23)
    d.ellipse([w // 2 - r, h // 2 - r, w // 2 + r, h // 2 + r], fill=(0, 39, 118))
    return img


def english_flag(w: int = 72, h: int = 48) -> Image.Image:
    """Bandeira (EUA) que representa o idioma Ingles."""
    img = Image.new("RGB", (w, h), (255, 255, 255))
    d = ImageDraw.Draw(img)

    # 13 listras (vermelho/branco).
    stripes = 13
    sh = h / stripes
    for i in range(stripes):
        if i % 2 == 0:
            d.rectangle([0, i * sh, w, (i + 1) * sh], fill=(178, 34, 52))

    # Canton azul no canto superior esquerdo.
    cw, ch = int(w * 0.42), int(sh * 7)
    d.rectangle([0, 0, cw, ch], fill=(60, 59, 110))

    # Estrelas simplificadas (pontos brancos).
    for ry in range(4):
        for rx in range(5):
            x = (rx + 0.7) * (cw / 5.6)
            y = (ry + 0.7) * (ch / 4.6)
            d.ellipse([x - 1.1, y - 1.1, x + 1.1, y + 1.1], fill=(255, 255, 255))
    return img


def get_flag(lang: str, w: int = 72, h: int = 48) -> Image.Image:
    """Retorna a imagem da bandeira para o codigo de idioma informado."""
    return english_flag(w, h) if lang == "en" else brazil_flag(w, h)
