"""
Internacionalizacao (i18n) do aplicativo.

Mantem os textos da interface em dois idiomas (Portugues do Brasil e
Ingles) e oferece um tradutor simples baseado em chaves. O idioma e
trocado em tempo real pelas bandeiras no cabecalho.

Uso:
    tr = Translator("pt")
    tr.t("btn_video")                       -> "Baixar Video (MP4)"
    tr.t("log_new_download", label="MP4", url="...")
"""

# Dicionario de traducoes: { idioma: { chave: texto } }.
# As chaves sao iguais nos dois idiomas; o texto e que muda.
TRANSLATIONS = {
    # ============================ PORTUGUES ============================
    "pt": {
        "subtitle": "Baixe videos e audios   -   TikTok, YouTube, Instagram e X/Twitter   -   MP4 ou MP3",
        # Abas
        "tab_download": "Download",
        "tab_history": "Historico",
        "tab_settings": "Configuracoes",
        # Link / pasta
        "lbl_link": "Link do conteudo",
        "ph_url": "Cole o link (TikTok, YouTube, Instagram ou X/Twitter)",
        "btn_paste": "Colar",
        "url_detected": "Link de {platform} detectado",
        "url_generic": "Link detectado - tentaremos baixar",
        "url_invalid": "Isso nao parece um link valido",
        "platform_unknown": "Outra plataforma",
        "lbl_folder": "Pasta de destino",
        "btn_browse": "Procurar...",
        "folder_help": "Cada plataforma e salva em sua propria subpasta (YouTube, TikTok, Instagram, Twitter).",
        # Botoes de acao
        "btn_video": "Baixar Video (MP4)",
        "btn_audio": "Baixar Audio (MP3)",
        "btn_cancel": "Cancelar",
        "anim_video": "Baixando video",
        "anim_audio": "Baixando audio",
        # Card de informacoes
        "info_none": "Nenhum conteudo carregado",
        "info_loading": "Carregando informacoes...",
        "f_platform": "Plataforma",
        "f_author": "Autor",
        "f_duration": "Duracao",
        "f_resolution": "Resolucao",
        "f_size": "Tamanho estimado",
        "val_calculating": "calculando...",
        "res_audio": "Audio (MP3)",
        "res_playlist": "Playlist ({count} itens)",
        # Progresso / status
        "st_ready": "Pronto para baixar.",
        "st_paste_first": "Cole um link primeiro.",
        "st_link_invalid": "Link invalido.",
        "st_cancelling": "Cancelando...",
        "st_completed": "Download concluido com sucesso!",
        "st_cancelled": "Download cancelado.",
        "st_finalizing": "Finalizando arquivo...",
        "st_downloading": "Baixando  {downloaded} / {total}   -   {speed}",
        "st_eta": "   -   resta {eta}",
        "st_item_suffix": "   -   item {index}/{count}",
        # Logs
        "lbl_logs": "Registro de atividades",
        "log_welcome": "Bem-vindo! Cole um link de TikTok, YouTube, Instagram ou X/Twitter para comecar.",
        "log_ffmpeg_warn": "Aviso: FFmpeg nao encontrado; o download de MP3 pode falhar.",
        "log_new_download": "Novo download [{label}]: {url}",
        "kind_video": "VIDEO (MP4)",
        "kind_audio": "AUDIO (MP3)",
        "log_video_info": "Conteudo: \"{title}\"  |  @{author}  |  {duration}  |  {resolution}",
        "log_file_saved": "Arquivo salvo em: {path}",
        "log_history_cleared": "Historico limpo.",
        "log_cancel_requested": "Cancelamento solicitado pelo usuario...",
        "log_already_latest": "Voce ja esta na versao mais recente.",
        "log_update_available": "Nova versao disponivel: {version}.",
        "log_open_fail": "Nao foi possivel abrir a pasta: {error}",
        # Historico
        "hist_title": "Downloads recentes",
        "btn_clear_history": "Limpar historico",
        "hist_empty": "Nenhum download ainda.",
        "btn_open_folder": "Abrir pasta",
        # Configuracoes
        "set_prefs": "Preferencias",
        "set_quality": "Qualidade preferida do video",
        "set_appearance": "Aparencia",
        "set_language": "Idioma",
        "sw_notif": "Mostrar notificacao ao concluir o download",
        "sw_openfolder": "Abrir a pasta automaticamente ao terminar",
        "sw_updates": "Verificar atualizacoes ao iniciar",
        "btn_open_downloads": "Abrir pasta de downloads",
        "btn_check_updates": "Verificar atualizacoes",
        "about": "{app} v{ver}  -  Feito com Python, CustomTkinter e yt-dlp.",
        # Notificacao
        "notif_title": "Download concluido!",
        "notif_body": "{title} ({fmt}) baixado com sucesso.",
        # Janela de atualizacao
        "upd_title": "Atualizacao disponivel",
        "upd_msg": "Nova versao {version} disponivel!",
        "upd_question": "Deseja abrir a pagina de download?",
        "btn_open_page": "Abrir pagina",
        "btn_not_now": "Agora nao",
        # Mensagens do motor de download
        "dl_fetching": "Obtendo informacoes do conteudo...",
        "dl_ffmpeg_download": "Baixando o FFmpeg (necessario para MP3, apenas na primeira vez)...",
        "dl_start_video": "Iniciando download em alta qualidade...",
        "dl_start_audio": "Iniciando download do audio (MP3 192 kbps)...",
        "dl_processing": "Processando arquivo final...",
        "dl_converting": "Convertendo para MP3...",
        "dl_completed": "Download concluido com sucesso!",
        "dl_playlist_start": "Iniciando download da playlist ({count} itens)...",
        "dl_playlist_item_done": "Baixado {index}/{count}: {title}",
        "dl_playlist_done": "Playlist concluida: {count} arquivo(s) baixado(s).",
        # Erros amigaveis
        "err_mp3_ffmpeg": "Para baixar em MP3 e necessario o FFmpeg (pip install imageio-ffmpeg).",
        "err_ffmpeg_download": "Falha ao baixar o FFmpeg. Verifique sua internet e tente novamente.",
        "err_login": "Conteudo privado ou que exige login. Tente um link publico.",
        "err_private": "Este conteudo e privado e nao pode ser baixado.",
        "err_unavailable": "Conteudo indisponivel ou removido.",
        "err_extract": "Nao foi possivel extrair o conteudo. O link pode estar incorreto.",
        "err_404": "Conteudo nao encontrado (erro 404).",
        "err_ffmpeg": "Falha na conversao (FFmpeg). Tente novamente.",
        "err_timeout": "Falha de conexao. Verifique sua internet e tente novamente.",
        "err_generic": "Erro ao baixar: {detail}",
    },
    # ============================= INGLES ==============================
    "en": {
        "subtitle": "Download videos and audio   -   TikTok, YouTube, Instagram and X/Twitter   -   MP4 or MP3",
        "tab_download": "Download",
        "tab_history": "History",
        "tab_settings": "Settings",
        "lbl_link": "Content link",
        "ph_url": "Paste the link (TikTok, YouTube, Instagram or X/Twitter)",
        "btn_paste": "Paste",
        "url_detected": "{platform} link detected",
        "url_generic": "Link detected - we'll try to download it",
        "url_invalid": "This doesn't look like a valid link",
        "platform_unknown": "Other platform",
        "lbl_folder": "Destination folder",
        "btn_browse": "Browse...",
        "folder_help": "Each platform is saved in its own subfolder (YouTube, TikTok, Instagram, Twitter).",
        "btn_video": "Download Video (MP4)",
        "btn_audio": "Download Audio (MP3)",
        "btn_cancel": "Cancel",
        "anim_video": "Downloading video",
        "anim_audio": "Downloading audio",
        "info_none": "No content loaded",
        "info_loading": "Loading information...",
        "f_platform": "Platform",
        "f_author": "Author",
        "f_duration": "Duration",
        "f_resolution": "Resolution",
        "f_size": "Estimated size",
        "val_calculating": "calculating...",
        "res_audio": "Audio (MP3)",
        "res_playlist": "Playlist ({count} items)",
        "st_ready": "Ready to download.",
        "st_paste_first": "Paste a link first.",
        "st_link_invalid": "Invalid link.",
        "st_cancelling": "Cancelling...",
        "st_completed": "Download completed successfully!",
        "st_cancelled": "Download cancelled.",
        "st_finalizing": "Finalizing file...",
        "st_downloading": "Downloading  {downloaded} / {total}   -   {speed}",
        "st_eta": "   -   {eta} left",
        "st_item_suffix": "   -   item {index}/{count}",
        "lbl_logs": "Activity log",
        "log_welcome": "Welcome! Paste a TikTok, YouTube, Instagram or X/Twitter link to begin.",
        "log_ffmpeg_warn": "Warning: FFmpeg not found; MP3 download may fail.",
        "log_new_download": "New download [{label}]: {url}",
        "kind_video": "VIDEO (MP4)",
        "kind_audio": "AUDIO (MP3)",
        "log_video_info": "Content: \"{title}\"  |  @{author}  |  {duration}  |  {resolution}",
        "log_file_saved": "File saved to: {path}",
        "log_history_cleared": "History cleared.",
        "log_cancel_requested": "Cancellation requested by user...",
        "log_already_latest": "You are already on the latest version.",
        "log_update_available": "New version available: {version}.",
        "log_open_fail": "Could not open the folder: {error}",
        "hist_title": "Recent downloads",
        "btn_clear_history": "Clear history",
        "hist_empty": "No downloads yet.",
        "btn_open_folder": "Open folder",
        "set_prefs": "Preferences",
        "set_quality": "Preferred video quality",
        "set_appearance": "Appearance",
        "set_language": "Language",
        "sw_notif": "Show a notification when the download finishes",
        "sw_openfolder": "Open the folder automatically when done",
        "sw_updates": "Check for updates on startup",
        "btn_open_downloads": "Open downloads folder",
        "btn_check_updates": "Check for updates",
        "about": "{app} v{ver}  -  Made with Python, CustomTkinter and yt-dlp.",
        "notif_title": "Download completed!",
        "notif_body": "{title} ({fmt}) downloaded successfully.",
        "upd_title": "Update available",
        "upd_msg": "New version {version} available!",
        "upd_question": "Do you want to open the download page?",
        "btn_open_page": "Open page",
        "btn_not_now": "Not now",
        "dl_fetching": "Getting content information...",
        "dl_ffmpeg_download": "Downloading FFmpeg (required for MP3, first time only)...",
        "dl_start_video": "Starting high-quality download...",
        "dl_start_audio": "Starting audio download (MP3 192 kbps)...",
        "dl_processing": "Processing final file...",
        "dl_converting": "Converting to MP3...",
        "dl_completed": "Download completed successfully!",
        "dl_playlist_start": "Starting playlist download ({count} items)...",
        "dl_playlist_item_done": "Downloaded {index}/{count}: {title}",
        "dl_playlist_done": "Playlist finished: {count} file(s) downloaded.",
        "err_mp3_ffmpeg": "FFmpeg is required to download MP3 (pip install imageio-ffmpeg).",
        "err_ffmpeg_download": "Failed to download FFmpeg. Check your internet and try again.",
        "err_login": "Private content or login required. Try a public link.",
        "err_private": "This content is private and cannot be downloaded.",
        "err_unavailable": "Content unavailable or removed.",
        "err_extract": "Could not extract the content. The link may be incorrect.",
        "err_404": "Content not found (error 404).",
        "err_ffmpeg": "Conversion failed (FFmpeg). Please try again.",
        "err_timeout": "Connection failed. Check your internet and try again.",
        "err_generic": "Download error: {detail}",
    },
}

# Idiomas disponiveis (codigo -> nome exibido).
LANGUAGES = {"pt": "Portugues (BR)", "en": "English"}


class Translator:
    """Tradutor simples baseado em chaves, com fallback para o Portugues."""

    def __init__(self, lang: str = "pt") -> None:
        self.lang = lang if lang in TRANSLATIONS else "pt"

    def set_language(self, lang: str) -> None:
        if lang in TRANSLATIONS:
            self.lang = lang

    def t(self, key: str, **kwargs) -> str:
        """
        Retorna o texto da chave no idioma atual.

        Se a chave nao existir no idioma atual, tenta o Portugues; se
        ainda assim faltar, devolve a propria chave (evita quebrar).
        `kwargs` sao substituidos via str.format (ex.: {url}).
        """
        text = (
            TRANSLATIONS.get(self.lang, {}).get(key)
            or TRANSLATIONS["pt"].get(key)
            or key
        )
        if kwargs:
            try:
                text = text.format(**kwargs)
            except (KeyError, IndexError, ValueError):
                pass
        return text
