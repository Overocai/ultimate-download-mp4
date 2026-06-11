"""
Motor de download baseado no yt-dlp (multi-plataforma).

O yt-dlp e a biblioteca mais robusta e mantida para baixar videos de
centenas de sites. Aqui ele e usado como mecanismo principal para TikTok,
YouTube, Instagram e X/Twitter (e, como curinga, qualquer outro site
suportado por ele). Por padrao entrega a maior qualidade disponivel e,
no TikTok, a versao SEM marca d'agua.

Esta camada e independente da interface: recebe callbacks para reportar
progresso e logs, e um `threading.Event` para cancelamento. Assim a GUI
nunca trava (o download roda em uma thread separada).

Suporta dois modos:
    - "video": baixa o video em MP4 (maxima qualidade).
    - "audio": extrai apenas o audio em MP3 (192 kbps).

E tres formatos de conteudo:
    - midia unica (video/reel/tweet/short);
    - playlists (YouTube) -> baixa todos os itens numa subpasta.

Para o MP3 (e para mesclar video+audio quando necessario) usamos o FFmpeg.
Se ele nao estiver no sistema, baixamos automaticamente um binario estatico
sob demanda (so na primeira vez que se usa o MP3), mantendo o .exe pequeno.
"""

import io
import os
import shutil
import time
import urllib.request
from typing import Callable, Optional

import yt_dlp
from yt_dlp.utils import DownloadCancelled as _YDLCancelled

from .i18n import Translator
from .platforms import GENERIC, Platform, detect_platform, get_platform
from .utils import (
    format_duration,
    format_filesize,
    format_speed,
    sanitize_filename,
)
from .utils import app_data_dir

# Tradutor padrao (Portugues) usado quando nenhum e fornecido pela GUI.
_default_tr = Translator("pt").t

# URL direta de um ffmpeg.exe estatico para Windows (repositorio oficial do
# projeto imageio-binaries). Usado para baixar o FFmpeg sob demanda APENAS
# quando o usuario decide baixar em MP3 - assim o .exe do app fica pequeno.
FFMPEG_URL = (
    "https://github.com/imageio/imageio-binaries/raw/master/ffmpeg/"
    "ffmpeg-win-x86_64-v7.1.exe"
)

# Intervalo minimo (s) entre dois relatorios de progresso "downloading" para a
# interface. O yt-dlp chama o hook a cada fragmento (centenas de vezes por
# segundo); sem este limite, a GUI receberia eventos demais e travaria ao
# baixar videos longos ou playlists. Eventos de mudanca de estado
# (finished/processing) NUNCA sao limitados.
PROGRESS_MIN_INTERVAL = 0.12


class DownloadCancelled(Exception):
    """Lancada para a GUI quando o usuario cancela o download."""


class MediaDownloader:
    """Encapsula a logica de extracao de metadados e download (multi-site)."""

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

        Para MP4 NUNCA forcamos o download do ffmpeg. Se ele ja estiver
        disponivel, mesclamos video+audio; senao, pegamos o melhor arquivo
        unico (muitos videos - TikTok, por ex. - ja vem assim).
        """
        height_filter = ""
        if preferred_quality in ("1080", "720", "480"):
            height_filter = f"[height<={preferred_quality}]"

        if self._ffmpeg_ready:
            return f"bestvideo{height_filter}+bestaudio/best{height_filter}/best"
        return f"best{height_filter}/best"

    # ------------------------------------------------------------------
    # Deteccao de playlist
    # ------------------------------------------------------------------
    def _is_playlist_url(self, url: str, platform: Platform) -> bool:
        """
        A URL pede uma PLAYLIST inteira?

        So vale para plataformas que suportam (YouTube). Tratamos como
        playlist os links de "/playlist?list=..."; ja um video normal que
        apenas pertence a uma playlist (watch?v=...&list=...) baixa so o video.
        """
        if not platform.supports_playlist:
            return False
        low = url.lower()
        if "/playlist" in low:
            return True
        has_list = "list=" in low
        is_single = "watch?" in low or "/shorts/" in low or "youtu.be/" in low
        return has_list and not is_single

    # ------------------------------------------------------------------
    # 1) Extrair metadados (sem baixar)
    # ------------------------------------------------------------------
    def fetch_info(self, url: str, platform: Optional[Platform] = None) -> dict:
        """Obtem titulo, autor, duracao, resolucao e tamanho SEM baixar."""
        platform = platform or detect_platform(url) or GENERIC
        is_playlist = self._is_playlist_url(url, platform)

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
        }
        if is_playlist:
            # Extracao "rasa": pega titulo + lista de itens rapidamente.
            ydl_opts["extract_flat"] = "in_playlist"
            ydl_opts["noplaylist"] = False
        else:
            ydl_opts["noplaylist"] = True
        ydl_opts.update(platform.ydl_opts)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            raw = ydl.extract_info(url, download=False)

        if raw.get("_type") == "playlist" or "entries" in raw:
            return self._parse_playlist(raw, platform)
        return self._parse_info(raw, platform)

    def _resolution_str(self, raw: dict) -> str:
        width, height = raw.get("width"), raw.get("height")
        if width and height:
            return f"{width}x{height}"
        if height:
            return f"{height}p"
        return "--"

    def _parse_info(self, raw: dict, platform: Optional[Platform] = None) -> dict:
        """Converte o dicionario bruto do yt-dlp (midia unica) em formato simples."""
        platform = platform or GENERIC
        author = (
            raw.get("uploader")
            or raw.get("creator")
            or raw.get("channel")
            or raw.get("uploader_id")
            or "--"
        )
        size_bytes = self._estimate_filesize(raw)

        return {
            "id": raw.get("id", ""),
            "title": raw.get("title") or raw.get("description") or f"Conteudo {platform.name}",
            "author": author,
            "duration": format_duration(raw.get("duration")),
            "duration_seconds": raw.get("duration") or 0,
            "resolution": self._resolution_str(raw),
            "thumbnail": raw.get("thumbnail") or self._first_thumb(raw),
            "webpage_url": raw.get("webpage_url", ""),
            "is_playlist": False,
            "entry_count": 1,
            "filesize_bytes": size_bytes,
            "filesize_estimate": format_filesize(size_bytes) if size_bytes else None,
            "platform_id": platform.id,
            "platform_name": platform.name,
        }

    def _parse_playlist(self, raw: dict, platform: Platform) -> dict:
        """Monta um resumo de uma playlist para o card de informacoes."""
        entries = [e for e in (raw.get("entries") or []) if e]
        count = raw.get("playlist_count") or len(entries)
        first = entries[0] if entries else {}
        author = (
            raw.get("uploader")
            or raw.get("channel")
            or first.get("uploader")
            or first.get("channel")
            or "--"
        )
        return {
            "id": raw.get("id", ""),
            "title": raw.get("title") or f"Playlist {platform.name}",
            "author": author,
            "duration": "--:--",
            "duration_seconds": 0,
            "resolution": "Playlist",
            "thumbnail": first.get("thumbnail") or self._first_thumb(first),
            "webpage_url": raw.get("webpage_url", ""),
            "is_playlist": True,
            "entry_count": count,
            "filesize_bytes": 0,
            "filesize_estimate": None,
            "platform_id": platform.id,
            "platform_name": platform.name,
        }

    def _first_thumb(self, raw: dict) -> Optional[str]:
        """Pega a melhor miniatura disponivel na lista 'thumbnails'."""
        thumbs = raw.get("thumbnails") or []
        for t in reversed(thumbs):  # geralmente as ultimas sao maiores
            url = t.get("url")
            if url:
                return url
        return None

    def _estimate_filesize(self, raw: dict) -> int:
        """
        Estima o tamanho do arquivo (em bytes) ANTES de baixar.

        E uma aproximacao: combina o melhor video + melhor audio, ou usa o
        bitrate medio x duracao quando os tamanhos exatos nao sao expostos.
        """
        for key in ("filesize", "filesize_approx"):
            if raw.get(key):
                return int(raw[key])

        formats = raw.get("formats") or []

        def fsize(f):
            return f.get("filesize") or f.get("filesize_approx") or 0

        best_combined = best_video = best_audio = 0
        for f in formats:
            v, a = f.get("vcodec"), f.get("acodec")
            s = fsize(f)
            if v and v != "none" and a and a != "none":
                best_combined = max(best_combined, s)
            elif v and v != "none":
                best_video = max(best_video, s)
            elif a and a != "none":
                best_audio = max(best_audio, s)

        cand = (best_video + best_audio) if (best_video and best_audio) else best_combined
        if cand:
            return int(cand)

        duration = raw.get("duration") or 0
        if duration:
            tbr = raw.get("tbr") or (max((f.get("tbr") or 0) for f in formats) if formats else 0)
            if tbr:
                return int(duration * tbr * 1000 / 8)
        return 0

    # ------------------------------------------------------------------
    # Miniatura (thumbnail) para a interface
    # ------------------------------------------------------------------
    def fetch_thumbnail(self, thumbnail_url: Optional[str]):
        """
        Baixa a imagem de capa e retorna um objeto PIL.Image (ou None).

        A imagem e usada apenas para exibir a previa na interface; qualquer
        falha simplesmente retorna None sem travar nada.
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

    # ==================================================================
    # 2) Baixar (video MP4 ou audio MP3)
    # ==================================================================
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
        platform: Optional[Platform] = None,
        tr=None,
    ) -> dict:
        """
        Baixa o conteudo na melhor qualidade.

        `output_folder` ja deve ser a subpasta da plataforma (ex.:
        <base>\\YouTube). Para playlists, criamos ainda uma subpasta com o
        nome da playlist dentro dela.

        mode: "video" -> MP4 (video+audio); "audio" -> MP3 (192 kbps).
        """
        tr = tr or _default_tr
        if platform is None:
            platform = (
                get_platform(info["platform_id"]) if info and info.get("platform_id")
                else detect_platform(url) or GENERIC
            )
        os.makedirs(output_folder, exist_ok=True)

        if info is None:
            log_callback(tr("dl_fetching"))
            info = self.fetch_info(url, platform)

        if info.get("is_playlist") and platform.supports_playlist:
            return self._download_playlist(
                url, output_folder, info, platform, mode, preferred_quality,
                progress_callback, log_callback, cancel_event, tr)
        return self._download_single(
            url, output_folder, info, platform, mode, preferred_quality,
            progress_callback, log_callback, cancel_event, tr)

    # ------------------------------------------------------------------
    # Download de uma midia unica
    # ------------------------------------------------------------------
    def _download_single(self, url, output_folder, info, platform, mode,
                         preferred_quality, progress_callback, log_callback,
                         cancel_event, tr) -> dict:
        is_audio = mode == "audio"

        # Nome de arquivo seguro: "Autor - Titulo".
        base_name = sanitize_filename(f"{info['author']} - {info['title']}")
        outtmpl = os.path.join(output_folder, base_name + ".%(ext)s")

        throttle = {"t": 0.0}

        def progress_hook(d: dict) -> None:
            if cancel_event.is_set():
                raise _YDLCancelled()
            if d.get("status") == "downloading":
                now = time.monotonic()
                if now - throttle["t"] < PROGRESS_MIN_INTERVAL:
                    return  # limita a frequencia de atualizacao da interface
                throttle["t"] = now
            self._emit_single_progress(d, progress_callback, log_callback, is_audio, tr)

        ydl_opts = self._base_ydl_opts(outtmpl, [progress_hook], platform, single=True)
        ff_ready = self._apply_format_and_ffmpeg(
            ydl_opts, is_audio, preferred_quality, log_callback,
            progress_callback, cancel_event, tr)
        log_callback(tr("dl_start_audio") if is_audio else tr("dl_start_video"))

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                result = ydl.extract_info(url, download=True)
                filepath = self._resolve_final_path(
                    ydl, result, output_folder, base_name, is_audio)
        except _YDLCancelled:
            self._cleanup_partial(output_folder, base_name)
            raise DownloadCancelled()
        except DownloadCancelled:
            self._cleanup_partial(output_folder, base_name)
            raise
        except yt_dlp.utils.DownloadError as exc:
            raise RuntimeError(self._friendly_error(str(exc), tr)) from exc

        final = dict(info)
        final["filepath"] = filepath
        final["format"] = "MP3" if is_audio else "MP4"
        final["filesize"] = (
            format_filesize(os.path.getsize(filepath))
            if os.path.isfile(filepath) else "--"
        )
        if is_audio:
            final["resolution"] = tr("res_audio")
        else:
            res = self._resolution_str(result)
            if res != "--":
                final["resolution"] = res

        log_callback(tr("dl_completed"))
        return final

    # ------------------------------------------------------------------
    # Download de uma playlist inteira
    # ------------------------------------------------------------------
    def _download_playlist(self, url, output_folder, info, platform, mode,
                          preferred_quality, progress_callback, log_callback,
                          cancel_event, tr) -> dict:
        is_audio = mode == "audio"
        total = max(1, int(info.get("entry_count") or 1))

        # Cada playlist ganha sua propria subpasta.
        playlist_dir = os.path.join(
            output_folder, sanitize_filename(info.get("title") or f"Playlist {platform.name}"))
        os.makedirs(playlist_dir, exist_ok=True)
        outtmpl = os.path.join(playlist_dir, "%(playlist_index)03d - %(title).80s.%(ext)s")

        progressed = {"max_index": 0}
        throttle = {"t": 0.0}

        def progress_hook(d: dict) -> None:
            if cancel_event.is_set():
                raise _YDLCancelled()
            if d.get("status") == "downloading":
                now = time.monotonic()
                if now - throttle["t"] < PROGRESS_MIN_INTERVAL:
                    return  # limita a frequencia de atualizacao da interface
                throttle["t"] = now
            self._emit_playlist_progress(
                d, progress_callback, log_callback, total, progressed, tr)

        ydl_opts = self._base_ydl_opts(outtmpl, [progress_hook], platform, single=False)
        # Um item com erro nao deve derrubar a playlist inteira.
        ydl_opts["ignoreerrors"] = True
        self._apply_format_and_ffmpeg(
            ydl_opts, is_audio, preferred_quality, log_callback,
            progress_callback, cancel_event, tr)
        log_callback(tr("dl_playlist_start", count=total))

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                result = ydl.extract_info(url, download=True)
        except _YDLCancelled:
            raise DownloadCancelled()
        except DownloadCancelled:
            raise
        except yt_dlp.utils.DownloadError as exc:
            raise RuntimeError(self._friendly_error(str(exc), tr)) from exc

        if cancel_event.is_set():
            raise DownloadCancelled()

        # Monta um item de historico por arquivo efetivamente baixado.
        entries_info = []
        for entry in (result.get("entries") or []):
            if not entry:
                continue
            fp = self._entry_filepath(entry, is_audio)
            if not fp:
                continue
            entries_info.append({
                "title": entry.get("title") or "--",
                "author": entry.get("uploader") or info.get("author") or "--",
                "resolution": tr("res_audio") if is_audio else self._resolution_str(entry),
                "duration": format_duration(entry.get("duration")),
                "filepath": fp,
                "format": "MP3" if is_audio else "MP4",
                "platform_name": platform.name,
            })

        total_bytes = sum(
            os.path.getsize(e["filepath"]) for e in entries_info
            if e["filepath"] and os.path.isfile(e["filepath"]))

        final = dict(info)
        final.update({
            "format": "MP3" if is_audio else "MP4",
            "filepath": playlist_dir,
            "filesize": format_filesize(total_bytes) if total_bytes else "--",
            "resolution": tr("res_playlist", count=len(entries_info)),
            "entries": entries_info,
        })
        log_callback(tr("dl_playlist_done", count=len(entries_info)))
        return final

    # ------------------------------------------------------------------
    # Opcoes / progresso compartilhados
    # ------------------------------------------------------------------
    def _base_ydl_opts(self, outtmpl, hooks, platform, single: bool) -> dict:
        opts = {
            "outtmpl": outtmpl,
            "progress_hooks": hooks,
            "quiet": True,
            "no_warnings": True,
            "noplaylist": single,
            "overwrites": True,
            "retries": 5,
            "fragment_retries": 5,
        }
        opts.update(platform.ydl_opts)
        return opts

    def _apply_format_and_ffmpeg(self, ydl_opts, is_audio, preferred_quality,
                                log_callback, progress_callback, cancel_event, tr) -> bool:
        """
        Define formato (video/audio) e resolve o FFmpeg.

        Tambem embute metadados (titulo/autor) quando o FFmpeg esta
        disponivel. Retorna True se o FFmpeg ficou disponivel.
        """
        if is_audio:
            ff_dir = self.ensure_ffmpeg(log_callback, progress_callback, cancel_event, tr)
        else:
            ff_dir = self._ffmpeg_dir_for_ydl()
        if ff_dir:
            ydl_opts["ffmpeg_location"] = ff_dir

        ff_ready = bool(self._system_ffmpeg) or ff_dir is not None or os.path.isfile(self._cache_ffmpeg)

        postprocessors = []
        if is_audio:
            ydl_opts["format"] = "bestaudio/best"
            postprocessors.append({
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            })
        else:
            ydl_opts["format"] = self._format_selector(preferred_quality)
            ydl_opts["merge_output_format"] = "mp4"

        # Mantem metadados (titulo, autor/artista, data) quando ha FFmpeg.
        if ff_ready:
            postprocessors.append({"key": "FFmpegMetadata", "add_metadata": True})
        if postprocessors:
            ydl_opts["postprocessors"] = postprocessors
        return ff_ready

    def _emit_single_progress(self, d, progress_callback, log_callback, is_audio, tr) -> None:
        status = d.get("status")
        if status == "downloading":
            downloaded = d.get("downloaded_bytes", 0)
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            fraction = (downloaded / total) if total else 0.0
            progress_callback({
                "fraction": max(0.0, min(fraction, 1.0)),
                "downloaded": format_filesize(downloaded),
                "total": format_filesize(total) if total else "?",
                "speed": format_speed(d.get("speed")),
                "eta": d.get("eta"),
                "status": "downloading",
            })
        elif status == "finished":
            progress_callback({"fraction": 1.0, "status": "processing"})
            log_callback(tr("dl_converting") if is_audio else tr("dl_processing"))

    def _emit_playlist_progress(self, d, progress_callback, log_callback,
                               total, progressed, tr) -> None:
        idict = d.get("info_dict") or {}
        idx = idict.get("playlist_index") or (progressed["max_index"] + 1)
        n = idict.get("n_entries") or idict.get("playlist_count") or total
        status = d.get("status")
        if status == "downloading":
            downloaded = d.get("downloaded_bytes", 0)
            tot = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            file_frac = (downloaded / tot) if tot else 0.0
            overall = ((idx - 1) + file_frac) / max(1, n)
            progress_callback({
                "fraction": max(0.0, min(overall, 1.0)),
                "downloaded": format_filesize(downloaded),
                "total": format_filesize(tot) if tot else "?",
                "speed": format_speed(d.get("speed")),
                "eta": d.get("eta"),
                "status": "downloading",
                "index": idx,
                "count": n,
            })
        elif status == "finished":
            progressed["max_index"] = max(progressed["max_index"], idx)
            log_callback(tr("dl_playlist_item_done", index=idx, count=n,
                          title=idict.get("title", "")))
            progress_callback({"fraction": min(idx / max(1, n), 1.0), "status": "processing"})

    # ------------------------------------------------------------------
    # Auxiliares
    # ------------------------------------------------------------------
    def _resolve_final_path(self, ydl, result, folder, base_name, is_audio) -> str:
        """Descobre o caminho real do arquivo salvo apos o pos-processamento."""
        prepared = ydl.prepare_filename(result)
        stem = os.path.splitext(prepared)[0]

        exts = [".mp3"] if is_audio else [".mp4", os.path.splitext(prepared)[1]]
        for ext in exts:
            candidate = stem + ext
            if os.path.isfile(candidate):
                return candidate

        if os.path.isfile(prepared):
            return prepared

        try:
            wanted_ext = ".mp3" if is_audio else ".mp4"
            for fname in os.listdir(folder):
                if fname.startswith(base_name) and fname.lower().endswith(wanted_ext):
                    return os.path.join(folder, fname)
        except OSError:
            pass

        return prepared

    def _entry_filepath(self, entry: dict, is_audio: bool) -> str:
        """Tenta achar o caminho final de um item baixado de uma playlist."""
        candidates = []
        for rd in (entry.get("requested_downloads") or []):
            fp = rd.get("filepath") or rd.get("_filename")
            if fp:
                candidates.append(fp)
        if entry.get("filepath"):
            candidates.append(entry["filepath"])

        wanted = ".mp3" if is_audio else ".mp4"
        for fp in candidates:
            stem = os.path.splitext(fp)[0]
            if os.path.isfile(stem + wanted):
                return stem + wanted
            if os.path.isfile(fp):
                return fp
        return candidates[0] if candidates else ""

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
        if "login" in msg or "log in" in msg or "cookies" in msg or "rate-limit" in msg:
            return tr("err_login")
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


# Alias de compatibilidade: codigo/anotacoes antigas podem referir-se ao
# nome anterior. Aponta para a nova classe multi-plataforma.
TikTokDownloader = MediaDownloader
