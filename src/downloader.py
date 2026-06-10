"""
Motor de download baseado no yt-dlp.

O yt-dlp e a biblioteca mais robusta e mantida para baixar videos do
TikTok. Por padrao ele entrega a versao SEM marca d'agua (o "play
address") e na maior qualidade disponivel.

Esta camada e independente da interface: recebe callbacks para
reportar progresso e logs, e um `threading.Event` para cancelamento.
Assim a GUI nunca trava (o download roda em uma thread separada).

Suporta dois modos:
    - "video": baixa o video em MP4 (maxima qualidade, sem marca d'agua).
    - "audio": extrai apenas o audio em MP3 (192 kbps).

Para o MP3 (e para mesclar video+audio quando necessario) usamos o
FFmpeg. Se ele nao estiver instalado no sistema, usamos automaticamente
o binario embutido pelo pacote `imageio-ffmpeg`, sem o usuario precisar
instalar nada manualmente.
"""

import io
import os
import shutil
import urllib.request
from typing import Callable, Optional

import yt_dlp

from .i18n import Translator
from .utils import (
    app_data_dir,
    format_duration,
    format_filesize,
    format_speed,
    sanitize_filename,
)

# Tradutor padrao (Portugues) usado quando nenhum e fornecido pela GUI.
_default_tr = Translator("pt").t

# URL direta de um ffmpeg.exe estatico para Windows (repositorio oficial do
# projeto imageio-binaries, hospedado no GitHub). Usado para baixar o FFmpeg
# sob demanda APENAS quando o usuario decide baixar em MP3 - assim o
# executavel do app fica pequeno (nao precisamos embutir ~80 MB de FFmpeg).
FFMPEG_URL = (
    "https://github.com/imageio/imageio-binaries/raw/master/ffmpeg/"
    "ffmpeg-win-x86_64-v7.1.exe"
)


class DownloadCancelled(Exception):
    """Lancada internamente quando o usuario cancela o download."""


class TikTokDownloader:
    """Encapsula a logica de extracao de metadados e download."""

    def __init__(self) -> None:
        # FFmpeg do sistema (se o usuario ja tiver instalado no PATH).
        self._system_ffmpeg = shutil.which("ffmpeg")

        # Pasta de cache onde guardamos/baixamos o ffmpeg.exe (uma unica vez).
        self._cache_dir = os.path.join(app_data_dir(), "ffmpeg")
        self._cache_ffmpeg = os.path.join(self._cache_dir, "ffmpeg.exe")

    # ------------------------------------------------------------------
    # Resolucao do FFmpeg
    # ------------------------------------------------------------------
    @property
    def _ffmpeg_ready(self) -> bool:
        """O FFmpeg ja esta disponivel AGORA (sem precisar baixar)?"""
        if self._system_ffmpeg or os.path.isfile(self._cache_ffmpeg):
            return True
        return self._imageio_path() is not None

    # Mantido por compatibilidade (usado pela interface ao iniciar).
    @property
    def _has_ffmpeg(self) -> bool:
        return self._ffmpeg_ready

    def _imageio_path(self) -> Optional[str]:
        """Caminho do ffmpeg do pacote imageio-ffmpeg (apenas em dev)."""
        try:
            import imageio_ffmpeg

            p = imageio_ffmpeg.get_ffmpeg_exe()
            return p if p and os.path.isfile(p) else None
        except Exception:
            return None

    def _ffmpeg_dir_for_ydl(self) -> Optional[str]:
        """
        Retorna o diretorio do ffmpeg para passar ao yt-dlp, SEM baixar nada.

        - ffmpeg no sistema -> None (o yt-dlp encontra sozinho no PATH).
        - ffmpeg em cache   -> a pasta de cache.
        - (dev) imageio     -> copia para o cache e retorna a pasta.
        - nada disponivel   -> None.
        """
        if self._system_ffmpeg:
            return None
        if os.path.isfile(self._cache_ffmpeg):
            return self._cache_dir

        src = self._imageio_path()  # disponivel apenas rodando via Python (dev)
        if src:
            try:
                os.makedirs(self._cache_dir, exist_ok=True)
                if not os.path.isfile(self._cache_ffmpeg):
                    shutil.copy2(src, self._cache_ffmpeg)
                return self._cache_dir
            except Exception:
                return None
        return None

    def ensure_ffmpeg(self, log_callback, progress_callback, cancel_event, tr) -> Optional[str]:
        """
        Garante que o FFmpeg exista, BAIXANDO-O se necessario (uma unica vez).

        Retorna o diretorio para o yt-dlp (ou None se for o ffmpeg do sistema).
        Lanca RuntimeError se o download falhar (ex.: sem internet).
        """
        ready = self._ffmpeg_dir_for_ydl()
        if self._system_ffmpeg or ready:
            return ready

        # Precisamos baixar o FFmpeg (primeira vez que se usa o MP3).
        log_callback(tr("dl_ffmpeg_download"))
        self._download_ffmpeg(progress_callback, cancel_event, tr)
        return self._cache_dir

    def _download_ffmpeg(self, progress_callback, cancel_event, tr) -> None:
        """Baixa o ffmpeg.exe para o cache, reportando o progresso."""
        os.makedirs(self._cache_dir, exist_ok=True)
        tmp = self._cache_ffmpeg + ".part"
        try:
            req = urllib.request.Request(FFMPEG_URL, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as resp, open(tmp, "wb") as out:
                total = int(resp.headers.get("Content-Length") or 0)
                downloaded = 0
                while True:
                    if cancel_event.is_set():
                        raise DownloadCancelled()
                    chunk = resp.read(256 * 1024)
                    if not chunk:
                        break
                    out.write(chunk)
                    downloaded += len(chunk)
                    progress_callback({
                        "fraction": (downloaded / total) if total else 0.0,
                        "downloaded": format_filesize(downloaded),
                        "total": format_filesize(total) if total else "?",
                        "speed": "--",
                        "status": "downloading",
                    })
            os.replace(tmp, self._cache_ffmpeg)
        except DownloadCancelled:
            self._safe_remove(tmp)
            raise
        except Exception as exc:
            self._safe_remove(tmp)
            raise RuntimeError(tr("err_ffmpeg_download")) from exc

    def _safe_remove(self, path: str) -> None:
        try:
            if os.path.isfile(path):
                os.remove(path)
        except OSError:
            pass

    # ------------------------------------------------------------------
    # Selecao de formato (qualidade)
    # ------------------------------------------------------------------
    def _format_selector(self, preferred_quality: str = "best") -> str:
        """
        Monta a string de selecao de formato do yt-dlp para VIDEO.

        - "best": maior qualidade possivel.
        - "1080"/"720"/"480": limita a altura maxima do video.

        Importante: para MP4 NUNCA forcamos o download do ffmpeg. Se ele ja
        estiver disponivel, mesclamos video+audio; senao, pegamos o melhor
        arquivo unico (os videos do TikTok costumam vir assim mesmo).
        """
        height_filter = ""
        if preferred_quality in ("1080", "720", "480"):
            height_filter = f"[height<={preferred_quality}]"

        if self._ffmpeg_ready:
            return f"bestvideo{height_filter}+bestaudio/best{height_filter}/best"
        return f"best{height_filter}/best"

    # ------------------------------------------------------------------
    # 1) Extrair metadados (sem baixar)
    # ------------------------------------------------------------------
    def fetch_info(self, url: str) -> dict:
        """Obtem titulo, autor, duracao e resolucao SEM baixar o video."""
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "skip_download": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            raw = ydl.extract_info(url, download=False)
        return self._parse_info(raw)

    def _parse_info(self, raw: dict) -> dict:
        """Converte o dicionario bruto do yt-dlp num formato simples."""
        width = raw.get("width")
        height = raw.get("height")
        if width and height:
            resolution = f"{width}x{height}"
        elif height:
            resolution = f"{height}p"
        else:
            resolution = "--"

        author = (
            raw.get("uploader")
            or raw.get("creator")
            or raw.get("uploader_id")
            or "Desconhecido"
        )

        return {
            "id": raw.get("id", ""),
            "title": raw.get("title") or raw.get("description") or "Video do TikTok",
            "author": author,
            "duration": format_duration(raw.get("duration")),
            "duration_seconds": raw.get("duration") or 0,
            "resolution": resolution,
            "thumbnail": raw.get("thumbnail"),
            "webpage_url": raw.get("webpage_url", ""),
        }

    # ------------------------------------------------------------------
    # Miniatura (thumbnail) para a interface
    # ------------------------------------------------------------------
    def fetch_thumbnail(self, thumbnail_url: Optional[str]):
        """
        Baixa a imagem de capa do video e retorna um objeto PIL.Image.

        Retorna None em caso de falha (sem travar nada). A imagem e usada
        apenas para exibir a previa na interface.
        """
        if not thumbnail_url:
            return None
        try:
            import requests
            from PIL import Image

            resp = requests.get(
                thumbnail_url,
                timeout=8,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            if resp.status_code != 200:
                return None
            return Image.open(io.BytesIO(resp.content)).convert("RGB")
        except Exception:
            return None

    # ------------------------------------------------------------------
    # 2) Baixar (video MP4 ou audio MP3)
    # ------------------------------------------------------------------
    def download(
        self,
        url: str,
        output_folder: str,
        progress_callback: Callable[[dict], None],
        log_callback: Callable[[str], None],
        cancel_event,
        preferred_quality: str = "best",
        mode: str = "video",
        info: Optional[dict] = None,
        tr=None,
    ) -> dict:
        """
        Baixa o conteudo na melhor qualidade, sem marca d'agua.

        mode:
            "video" -> salva MP4 (video + audio).
            "audio" -> salva MP3 (somente audio, 192 kbps).
        tr:
            funcao de traducao (Translator.t). Permite que os logs/erros
            saiam no idioma escolhido na interface.
        """
        tr = tr or _default_tr  # fallback para Portugues
        os.makedirs(output_folder, exist_ok=True)
        is_audio = mode == "audio"

        if info is None:
            log_callback(tr("dl_fetching"))
            info = self.fetch_info(url)

        # Nome de arquivo seguro: "Autor - Titulo".
        base_name = sanitize_filename(f"{info['author']} - {info['title']}")
        outtmpl = os.path.join(output_folder, base_name + ".%(ext)s")

        # ----------------------------------------------------------------
        # Hook de progresso chamado pelo yt-dlp durante o download.
        # ----------------------------------------------------------------
        def progress_hook(d: dict) -> None:
            if cancel_event.is_set():
                raise DownloadCancelled()

            status = d.get("status")
            if status == "downloading":
                downloaded = d.get("downloaded_bytes", 0)
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                fraction = (downloaded / total) if total else 0.0
                progress_callback(
                    {
                        "fraction": max(0.0, min(fraction, 1.0)),
                        "downloaded": format_filesize(downloaded),
                        "total": format_filesize(total) if total else "?",
                        "speed": format_speed(d.get("speed")),
                        "eta": d.get("eta"),
                        "status": "downloading",
                    }
                )
            elif status == "finished":
                progress_callback({"fraction": 1.0, "status": "processing"})
                log_callback(tr("dl_converting") if is_audio else tr("dl_processing"))

        # ----------------------------------------------------------------
        # Opcoes do yt-dlp (diferem entre video e audio).
        # ----------------------------------------------------------------
        ydl_opts = {
            "outtmpl": outtmpl,
            "progress_hooks": [progress_hook],
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "overwrites": True,
            "retries": 5,
            "fragment_retries": 5,
        }

        # Resolve o ffmpeg. Para MP3 garantimos que ele exista (baixando se
        # for a primeira vez); para MP4 usamos apenas se ja estiver disponivel.
        if is_audio:
            ff_dir = self.ensure_ffmpeg(log_callback, progress_callback,
                                       cancel_event, tr)
        else:
            ff_dir = self._ffmpeg_dir_for_ydl()
        if ff_dir:
            ydl_opts["ffmpeg_location"] = ff_dir

        if is_audio:
            # Baixa o melhor audio e converte para MP3.
            ydl_opts["format"] = "bestaudio/best"
            ydl_opts["postprocessors"] = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ]
            log_callback(tr("dl_start_audio"))
        else:
            ydl_opts["format"] = self._format_selector(preferred_quality)
            ydl_opts["merge_output_format"] = "mp4"
            log_callback(tr("dl_start_video"))

        # ----------------------------------------------------------------
        # Execucao do download.
        # ----------------------------------------------------------------
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                result = ydl.extract_info(url, download=True)
                filepath = self._resolve_final_path(
                    ydl, result, output_folder, base_name, is_audio
                )
        except DownloadCancelled:
            self._cleanup_partial(output_folder, base_name)
            raise
        except yt_dlp.utils.DownloadError as exc:
            raise RuntimeError(self._friendly_error(str(exc), tr)) from exc

        # Monta o dicionario final retornado para a interface/historico.
        final = dict(info)
        final["filepath"] = filepath
        final["format"] = "MP3" if is_audio else "MP4"
        final["filesize"] = (
            format_filesize(os.path.getsize(filepath))
            if os.path.isfile(filepath)
            else "--"
        )
        if is_audio:
            # Para audio nao faz sentido falar em resolucao de video.
            final["resolution"] = tr("res_audio")
        else:
            parsed = self._parse_info(result)
            if parsed.get("resolution") != "--":
                final["resolution"] = parsed["resolution"]

        log_callback(tr("dl_completed"))
        return final

    # ------------------------------------------------------------------
    # Auxiliares
    # ------------------------------------------------------------------
    def _resolve_final_path(self, ydl, result, folder, base_name, is_audio) -> str:
        """
        Descobre o caminho real do arquivo salvo apos o pos-processamento.

        O yt-dlp baixa primeiro num formato bruto (ex.: .m4a/.webm) e, no
        caso do MP3/MP4, gera um novo arquivo com a extensao final.
        """
        prepared = ydl.prepare_filename(result)
        stem = os.path.splitext(prepared)[0]

        # Extensoes candidatas conforme o modo.
        exts = [".mp3"] if is_audio else [".mp4", os.path.splitext(prepared)[1]]
        for ext in exts:
            candidate = stem + ext
            if os.path.isfile(candidate):
                return candidate

        # O proprio arquivo preparado existe?
        if os.path.isfile(prepared):
            return prepared

        # Ultima tentativa: procura na pasta por algo com o mesmo nome base.
        try:
            wanted_ext = ".mp3" if is_audio else ".mp4"
            for fname in os.listdir(folder):
                if fname.startswith(base_name) and fname.lower().endswith(wanted_ext):
                    return os.path.join(folder, fname)
        except OSError:
            pass

        return prepared  # melhor palpite

    def _cleanup_partial(self, folder: str, base_name: str) -> None:
        """Apaga arquivos temporarios/parciais de um download cancelado."""
        try:
            for fname in os.listdir(folder):
                if fname.startswith(base_name) and (
                    fname.endswith(".part") or fname.endswith(".ytdl")
                ):
                    try:
                        os.remove(os.path.join(folder, fname))
                    except OSError:
                        pass
        except OSError:
            pass

    def _friendly_error(self, raw_message: str, tr=None) -> str:
        """Traduz erros tecnicos do yt-dlp em mensagens amigaveis."""
        tr = tr or _default_tr
        msg = raw_message.lower()
        if "private" in msg:
            return tr("err_private")
        if "not available" in msg or "unavailable" in msg:
            return tr("err_unavailable")
        if "unable to extract" in msg or "no video" in msg:
            return tr("err_extract")
        if "http error 404" in msg:
            return tr("err_404")
        if "ffmpeg" in msg:
            return tr("err_ffmpeg")
        if "timed out" in msg or "timeout" in msg or "connection" in msg:
            return tr("err_timeout")
        short = raw_message.strip().splitlines()[-1][:160]
        return tr("err_generic", detail=short)
