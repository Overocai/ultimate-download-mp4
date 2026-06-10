"""
Funcoes utilitarias compartilhadas por toda a aplicacao.

Inclui:
- Validacao/normalizacao de links do TikTok.
- Formatacao de duracao e tamanho de arquivo.
- Sanitizacao de nomes de arquivo.
- Resolucao de caminhos compativel com PyInstaller.
"""

import os
import re
import sys

# ----------------------------------------------------------------------
# Validacao de links do TikTok
# ----------------------------------------------------------------------
# Cobre os principais formatos de URL do TikTok:
#   - https://www.tiktok.com/@usuario/video/1234567890123456789
#   - https://vm.tiktok.com/XXXXXXX/   (link curto compartilhado)
#   - https://vt.tiktok.com/XXXXXXX/
#   - https://m.tiktok.com/v/123456.html
#   - https://www.tiktok.com/t/XXXXXXX/
_TIKTOK_REGEX = re.compile(
    r"https?://"
    r"(?:www\.|m\.|vm\.|vt\.)?"      # subdominios opcionais
    r"tiktok\.com/"                  # dominio principal
    r"\S+",                          # restante do caminho
    re.IGNORECASE,
)


def is_valid_tiktok_url(url: str) -> bool:
    """Retorna True se a string contiver um link valido do TikTok."""
    if not url:
        return False
    return bool(_TIKTOK_REGEX.search(url.strip()))


def extract_first_url(text: str) -> str | None:
    """
    Extrai o primeiro link do TikTok encontrado em um texto.

    Util quando o usuario cola algo como:
    "Olha esse video https://vm.tiktok.com/ABC123/ kkkk"
    """
    if not text:
        return None
    match = _TIKTOK_REGEX.search(text.strip())
    return match.group(0) if match else None


# ----------------------------------------------------------------------
# Formatacao para exibicao na interface
# ----------------------------------------------------------------------
def format_duration(seconds) -> str:
    """Converte segundos em uma string legivel (mm:ss ou hh:mm:ss)."""
    try:
        seconds = int(float(seconds))
    except (TypeError, ValueError):
        return "--:--"

    if seconds < 0:
        return "--:--"

    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)

    if hours > 0:
        return f"{hours:d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def format_filesize(num_bytes) -> str:
    """Converte bytes em uma string amigavel (KB, MB, GB)."""
    try:
        num_bytes = float(num_bytes)
    except (TypeError, ValueError):
        return "0 B"

    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:3.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} PB"


def format_speed(bytes_per_sec) -> str:
    """Formata velocidade de download (ex.: '2.3 MB/s')."""
    if not bytes_per_sec:
        return "--"
    return f"{format_filesize(bytes_per_sec)}/s"


def fit_size(orig_w: int, orig_h: int, box_w: int, box_h: int) -> tuple[int, int]:
    """
    Calcula o tamanho para encaixar uma imagem dentro de uma caixa,
    preservando a proporcao (usado na miniatura do video).
    """
    if not orig_w or not orig_h:
        return box_w, box_h
    scale = min(box_w / orig_w, box_h / orig_h)
    return max(1, int(orig_w * scale)), max(1, int(orig_h * scale))


def sanitize_filename(name: str, max_length: int = 120) -> str:
    """
    Remove caracteres invalidos para nomes de arquivo no Windows
    e limita o tamanho para evitar caminhos longos demais.
    """
    if not name:
        return "tiktok_video"

    # Caracteres proibidos no Windows: \ / : * ? " < > |
    cleaned = re.sub(r'[\\/:*?"<>|]', "", name)
    # Substitui quebras de linha e espacos multiplos por um espaco simples.
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    # Remove pontos/espacos no final (o Windows nao permite).
    cleaned = cleaned.rstrip(". ")

    if not cleaned:
        cleaned = "tiktok_video"

    return cleaned[:max_length]


# ----------------------------------------------------------------------
# Caminhos / recursos (compativel com PyInstaller)
# ----------------------------------------------------------------------
def resource_path(relative_path: str) -> str:
    """
    Retorna o caminho absoluto de um recurso (ex.: icone).

    Quando rodando como .exe gerado pelo PyInstaller, os arquivos
    ficam em uma pasta temporaria apontada por `sys._MEIPASS`.
    Em desenvolvimento, usamos a raiz do projeto.
    """
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS  # type: ignore[attr-defined]
    else:
        # Sobe um nivel a partir de /src para chegar na raiz do projeto.
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    return os.path.join(base_path, relative_path)


def app_data_dir() -> str:
    """
    Pasta onde guardamos configuracoes e historico do usuario.

    Usa %APPDATA%\\TikTokUltimateDownloader no Windows; cria se nao existir.
    """
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    path = os.path.join(base, "TikTokUltimateDownloader")
    os.makedirs(path, exist_ok=True)
    return path


def default_download_dir() -> str:
    """Pasta padrao de download: Videos\\TikTok Downloads do usuario."""
    videos = os.path.join(os.path.expanduser("~"), "Videos")
    if not os.path.isdir(videos):
        videos = os.path.expanduser("~")
    path = os.path.join(videos, "TikTok Downloads")
    os.makedirs(path, exist_ok=True)
    return path
