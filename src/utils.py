"""
Funcoes utilitarias compartilhadas por toda a aplicacao.

Inclui:
- Validacao/extracao de links (delegada ao sistema modular de plataformas).
- Formatacao de duracao e tamanho de arquivo.
- Sanitizacao de nomes de arquivo.
- Resolucao de caminhos compativel com PyInstaller e pastas por plataforma.
"""

import os
import re
import sys

from .platforms import Platform, detect_platform

# ----------------------------------------------------------------------
# Validacao / extracao de links
# ----------------------------------------------------------------------
# A deteccao de plataforma fica centralizada no pacote `src/platforms`.
# Aqui apenas oferecemos atalhos usados pela interface.

# Regex generico para achar uma URL http(s) dentro de um texto colado.
_URL_REGEX = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)


def is_supported_url(url: str) -> bool:
    """
    Retorna True se a string contiver um link que o app sabe tratar.

    Considera valida tanto uma plataforma conhecida (TikTok, YouTube,
    Instagram, X/Twitter) quanto qualquer outra URL http(s) - nesse caso o
    yt-dlp ainda pode conseguir baixar (curinga), mantendo compatibilidade.
    """
    return detect_platform(url) is not None


def url_platform(url: str):
    """Atalho para `detect_platform` (devolve a Platform ou None)."""
    return detect_platform(url)


def extract_first_url(text: str) -> "str | None":
    """
    Extrai a primeira URL util de um texto colado.

    Preferimos a primeira URL de uma plataforma CONHECIDA; se nenhuma for
    reconhecida, devolvemos a primeira URL http(s) encontrada. Util quando o
    usuario cola algo como: "Olha esse video https://x.com/.../status/1 kkk".
    """
    if not text:
        return None
    urls = _URL_REGEX.findall(text.strip())
    if not urls:
        return None
    for candidate in urls:
        p = detect_platform(candidate)
        if p is not None and p.id != "generic":
            return candidate
    return urls[0]


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


def fit_size(orig_w: int, orig_h: int, box_w: int, box_h: int) -> "tuple[int, int]":
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
        return "video"

    # Caracteres proibidos no Windows: \ / : * ? " < > |
    cleaned = re.sub(r'[\\/:*?"<>|]', "", name)
    # Substitui quebras de linha e espacos multiplos por um espaco simples.
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    # Remove pontos/espacos no final (o Windows nao permite).
    cleaned = cleaned.rstrip(". ")

    if not cleaned:
        cleaned = "video"

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

    Usa %APPDATA%\\Ultimate Download MP4 no Windows; cria se nao existir.
    """
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    path = os.path.join(base, "Ultimate Download MP4")
    os.makedirs(path, exist_ok=True)
    return path


def default_download_dir() -> str:
    """
    Pasta-base padrao de download.

    Os arquivos sao organizados em subpastas por plataforma DENTRO desta
    pasta (ex.: <base>\\YouTube, <base>\\TikTok). Usamos a pasta "Downloads"
    do usuario quando ela existe; caso contrario, a pasta pessoal.
    """
    downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    base = downloads if os.path.isdir(downloads) else os.path.expanduser("~")
    os.makedirs(base, exist_ok=True)
    return base


def platform_output_dir(base_folder: str, platform: Platform) -> str:
    """
    Devolve (criando se preciso) a subpasta de uma plataforma dentro da
    pasta-base escolhida pelo usuario: <base_folder>\\<platform.folder>.
    """
    folder = os.path.join(base_folder, platform.folder)
    os.makedirs(folder, exist_ok=True)
    return folder
