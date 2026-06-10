"""
Janela principal da aplicacao (CustomTkinter).

Responsavel por toda a interface: entrada do link, selecao de pasta,
botoes de download (MP4 e MP3), barra de progresso, logs, card de
informacoes com miniatura, historico, configuracoes e o seletor de
idioma (bandeiras Brasil / Ingles).

Regras importantes de arquitetura:
- O download roda em uma THREAD separada para nao travar a interface.
- A thread NUNCA toca em widgets diretamente (Tkinter nao e thread-safe).
  Em vez disso, ela coloca mensagens em uma `queue.Queue` que a thread
  principal consome periodicamente via `self.after(...)`.
- Todos os textos visiveis vem do tradutor (`self.i18n.t`), permitindo
  trocar o idioma em tempo real reconstruindo a interface.

Observacao sobre icones: usamos apenas glifos que existem na fonte
padrao do Windows (Segoe UI), como as setas e notas musicais, para
evitar "quadrados" (tofu) de emojis nao suportados.
"""

import os
import queue
import subprocess
import threading
import webbrowser
from datetime import datetime

import customtkinter as ctk

from .. import APP_NAME, __version__
from ..config import Config
from ..downloader import DownloadCancelled, TikTokDownloader
from ..history import History
from ..i18n import Translator
from ..notifications import notify
from ..updater import check_for_updates
from ..utils import extract_first_url, fit_size, is_valid_tiktok_url, resource_path
from . import flags, theme

# Tamanho da caixa da miniatura (formato vertical, como os videos do TikTok).
THUMB_W = 128
THUMB_H = 168


class TikTokDownloaderApp(ctk.CTk):
    """Aplicacao principal."""

    def __init__(self) -> None:
        super().__init__()

        # ---------------- Estado / servicos ----------------
        self.config_mgr = Config()
        self.history = History()
        self.downloader = TikTokDownloader()
        self.i18n = Translator(self.config_mgr.get("language", "pt"))

        self.msg_queue: "queue.Queue[dict]" = queue.Queue()
        self.cancel_event = threading.Event()
        self.worker: threading.Thread | None = None

        # Animacao do botao ativo durante o download.
        self._anim_running = False
        self._anim_step = 0
        self._active_button = None
        self._active_base = ""

        # Referencias de imagens (evita coleta de lixo do Tkinter).
        self._thumb_ref = None
        self._flag_imgs: dict = {}
        self.flag_btns: dict = {}

        # Historico de logs (para restaurar ao trocar de idioma).
        self._log_history: list[str] = []

        # Variaveis de texto criadas UMA vez (sobrevivem a reconstrucao).
        self.url_var = ctk.StringVar()
        self.url_var.trace_add("write", self._on_url_changed)
        self.folder_var = ctk.StringVar(value=self.config_mgr.get("download_folder"))

        # ---------------- Aparencia global ----------------
        ctk.set_appearance_mode(self.config_mgr.get("appearance_mode", "Dark"))
        ctk.set_default_color_theme(self.config_mgr.get("color_theme", "blue"))

        # ---------------- Janela ----------------
        self.title(f"{APP_NAME}  v{__version__}")
        self.geometry("940x870")
        self.minsize(860, 770)
        self.configure(fg_color=theme.COLOR_BG)
        self._set_window_icon()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ---------------- Construcao da UI ----------------
        self._build_main()

        # Log inicial (apenas na primeira montagem).
        self._log(self.i18n.t("log_welcome"))

        # Loop de leitura da fila de mensagens.
        self.after(80, self._process_queue)

        # Verifica atualizacoes em segundo plano (se habilitado e configurado).
        if self.config_mgr.get("check_updates", True):
            threading.Thread(target=self._check_updates_async, daemon=True).start()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ==================================================================
    # Montagem / reconstrucao da interface
    # ==================================================================
    def _build_main(self) -> None:
        """Monta cabecalho, barra de destaque e abas."""
        self._build_header()
        self.accent_bar = ctk.CTkFrame(self, height=3, fg_color=theme.COLOR_PRIMARY,
                                      corner_radius=2)
        self.accent_bar.grid(row=1, column=0, sticky="ew", padx=28, pady=(2, 8))
        self._build_tabs()

    def _rebuild_main(self) -> None:
        """Reconstroi a interface (usado ao trocar o idioma)."""
        self.header.destroy()
        self.accent_bar.destroy()
        self.tabs.destroy()
        self._build_main()
        self._restore_logs()  # reexibe o registro de atividades

    def _set_window_icon(self) -> None:
        ico = resource_path("assets/icon.ico")
        if os.path.isfile(ico):
            try:
                self.iconbitmap(ico)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Cabecalho (com seletor de idioma)
    # ------------------------------------------------------------------
    def _build_header(self) -> None:
        t = self.i18n.t
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.grid(row=0, column=0, sticky="ew", padx=28, pady=(22, 6))
        self.header.grid_columnconfigure(1, weight=1)

        # "Logo" num quadradinho arredondado.
        logo_box = ctk.CTkFrame(self.header, width=64, height=64, corner_radius=18,
                               fg_color=theme.COLOR_SURFACE)
        logo_box.grid(row=0, column=0, rowspan=2, padx=(0, 16))
        logo_box.grid_propagate(False)
        ctk.CTkLabel(logo_box, text="♫", font=(theme.FONT_FAMILY, 34, "bold"),
                    text_color=theme.COLOR_PRIMARY).place(relx=0.5, rely=0.5,
                                                         anchor="center")

        ctk.CTkLabel(self.header, text=APP_NAME, font=theme.FONT_TITLE,
                    text_color=theme.COLOR_TEXT).grid(row=0, column=1, sticky="sw")
        ctk.CTkLabel(self.header, text=t("subtitle"), font=theme.FONT_SUBTITLE,
                    text_color=theme.COLOR_TEXT_MUTED).grid(row=1, column=1, sticky="nw")

        # Painel direito: bandeiras + versao.
        right = ctk.CTkFrame(self.header, fg_color="transparent")
        right.grid(row=0, column=2, rowspan=2, sticky="ne")

        flags_frame = ctk.CTkFrame(right, fg_color="transparent")
        flags_frame.grid(row=0, column=0, sticky="e")
        self.flag_btns = {}
        self._build_flag_button(flags_frame, "pt", 0)
        self._build_flag_button(flags_frame, "en", 1)
        self._update_flag_highlight()

        ctk.CTkLabel(right, text=f"v{__version__}", font=theme.FONT_SMALL,
                    text_color=theme.COLOR_TEXT_MUTED).grid(row=1, column=0,
                                                           sticky="e", pady=(6, 0))

    def _build_flag_button(self, parent, lang: str, col: int) -> None:
        """Cria um botao-bandeira para selecionar o idioma."""
        pil = flags.get_flag(lang, 72, 48)
        img = ctk.CTkImage(light_image=pil, dark_image=pil, size=(38, 25))
        self._flag_imgs[lang] = img  # mantem referencia

        btn = ctk.CTkButton(
            parent, image=img, text="", width=50, height=34,
            fg_color=theme.COLOR_SURFACE, hover_color=theme.COLOR_SURFACE_2,
            border_width=2, corner_radius=8,
            command=lambda l=lang: self._set_language(l),
        )
        btn.grid(row=0, column=col, padx=4)
        self.flag_btns[lang] = btn

    def _update_flag_highlight(self) -> None:
        """Realca a bandeira do idioma atualmente selecionado."""
        for lang, btn in self.flag_btns.items():
            active = lang == self.i18n.lang
            btn.configure(border_color=theme.COLOR_PRIMARY if active else theme.COLOR_BORDER)

    def _set_language(self, lang: str) -> None:
        """Troca o idioma e reconstroi a interface."""
        if lang == self.i18n.lang:
            return
        if self.worker and self.worker.is_alive():
            return  # evita reconstruir durante um download
        self.config_mgr.set("language", lang)
        self.i18n.set_language(lang)
        self._rebuild_main()

    # ------------------------------------------------------------------
    # Abas
    # ------------------------------------------------------------------
    def _build_tabs(self) -> None:
        t = self.i18n.t
        self.tabs = ctk.CTkTabview(
            self, fg_color=theme.COLOR_SURFACE,
            segmented_button_fg_color=theme.COLOR_SURFACE_2,
            segmented_button_selected_color=theme.COLOR_PRIMARY,
            segmented_button_selected_hover_color=theme.COLOR_PRIMARY_HOVER,
            segmented_button_unselected_color=theme.COLOR_SURFACE_2,
            text_color=theme.COLOR_TEXT, corner_radius=theme.CORNER_RADIUS,
        )
        self.tabs.grid(row=2, column=0, sticky="nsew", padx=28, pady=(0, 22))

        self.tab_download = self.tabs.add(f"   {t('tab_download')}   ")
        self.tab_history = self.tabs.add(f"   {t('tab_history')}   ")
        self.tab_settings = self.tabs.add(f"   {t('tab_settings')}   ")

        self._build_download_tab()
        self._build_history_tab()
        self._build_settings_tab()

    # ------------------------------------------------------------------
    # Aba: Download
    # ------------------------------------------------------------------
    def _build_download_tab(self) -> None:
        t = self.i18n.t
        tab = self.tab_download
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(7, weight=1)

        # ---- Link + botao colar ----
        url_frame = ctk.CTkFrame(tab, fg_color="transparent")
        url_frame.grid(row=0, column=0, sticky="ew", padx=4, pady=(10, 2))
        url_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(url_frame, text=t("lbl_link"), font=theme.FONT_LABEL_BOLD,
                    text_color=theme.COLOR_TEXT, anchor="w").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))

        self.url_entry = ctk.CTkEntry(
            url_frame, textvariable=self.url_var, placeholder_text=t("ph_url"),
            height=48, font=theme.FONT_LABEL, fg_color=theme.COLOR_SURFACE_2,
            border_color=theme.COLOR_BORDER, corner_radius=theme.CORNER_RADIUS,
        )
        self.url_entry.grid(row=1, column=0, sticky="ew", padx=(0, 8))
        self.url_entry.bind("<Return>", lambda _e: self._on_download_click("video"))

        ctk.CTkButton(url_frame, text=t("btn_paste"), width=96, height=48,
                     font=theme.FONT_LABEL_BOLD, fg_color=theme.COLOR_SURFACE_2,
                     hover_color=theme.COLOR_BORDER, border_color=theme.COLOR_BORDER,
                     border_width=1, corner_radius=theme.CORNER_RADIUS,
                     command=self._on_paste_click).grid(row=1, column=1, sticky="e")

        self.url_status = ctk.CTkLabel(url_frame, text="", font=theme.FONT_SMALL,
                                      text_color=theme.COLOR_TEXT_MUTED, anchor="w")
        self.url_status.grid(row=2, column=0, columnspan=2, sticky="w", pady=(5, 0))
        self._on_url_changed()  # reavalia o estado do link apos reconstruir

        # ---- Pasta de destino ----
        folder_frame = ctk.CTkFrame(tab, fg_color="transparent")
        folder_frame.grid(row=1, column=0, sticky="ew", padx=4, pady=(4, 2))
        folder_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(folder_frame, text=t("lbl_folder"), font=theme.FONT_LABEL_BOLD,
                    text_color=theme.COLOR_TEXT, anchor="w").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))

        self.folder_entry = ctk.CTkEntry(
            folder_frame, textvariable=self.folder_var, height=44,
            font=theme.FONT_SMALL, fg_color=theme.COLOR_SURFACE_2,
            border_color=theme.COLOR_BORDER, corner_radius=theme.CORNER_RADIUS,
        )
        self.folder_entry.grid(row=1, column=0, sticky="ew", padx=(0, 8))

        ctk.CTkButton(folder_frame, text=t("btn_browse"), width=128, height=44,
                     font=theme.FONT_LABEL_BOLD, fg_color=theme.COLOR_SURFACE_2,
                     hover_color=theme.COLOR_BORDER, border_color=theme.COLOR_BORDER,
                     border_width=1, corner_radius=theme.CORNER_RADIUS,
                     command=self._on_browse_click).grid(row=1, column=1, sticky="e")

        # ---- Botoes de acao ----
        action_frame = ctk.CTkFrame(tab, fg_color="transparent")
        action_frame.grid(row=2, column=0, sticky="ew", padx=4, pady=(12, 4))
        action_frame.grid_columnconfigure(0, weight=1)

        # "↓" = seta para baixo (renderiza na Segoe UI, sem virar quadrado).
        self.download_btn = ctk.CTkButton(
            action_frame, text="↓   " + t("btn_video"), height=56,
            font=theme.FONT_BUTTON, fg_color=theme.COLOR_PRIMARY,
            hover_color=theme.COLOR_PRIMARY_HOVER, text_color="#06222B",
            corner_radius=theme.CORNER_RADIUS,
            command=lambda: self._on_download_click("video"))
        self.download_btn.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))

        # "♪" = nota musical.
        self.audio_btn = ctk.CTkButton(
            action_frame, text="♪   " + t("btn_audio"), height=48,
            font=theme.FONT_BUTTON, fg_color=theme.COLOR_AUDIO,
            hover_color=theme.COLOR_AUDIO_HOVER, text_color="#160A2B",
            corner_radius=theme.CORNER_RADIUS,
            command=lambda: self._on_download_click("audio"))
        self.audio_btn.grid(row=1, column=0, sticky="ew", padx=(0, 8))

        # "✕" = X de multiplicacao (cancelar).
        self.cancel_btn = ctk.CTkButton(
            action_frame, text="✕  " + t("btn_cancel"), width=150, height=48,
            font=theme.FONT_BUTTON, fg_color=theme.COLOR_ACCENT,
            hover_color=theme.COLOR_ACCENT_HOVER, text_color=theme.COLOR_TEXT,
            corner_radius=theme.CORNER_RADIUS, command=self._on_cancel_click,
            state="disabled")
        self.cancel_btn.grid(row=1, column=1, sticky="e")

        # ---- Card de informacoes (miniatura + detalhes) ----
        self.info_card = ctk.CTkFrame(tab, fg_color=theme.COLOR_SURFACE_2,
                                     corner_radius=theme.CORNER_RADIUS)
        self.info_card.grid(row=4, column=0, sticky="ew", padx=4, pady=(10, 4))
        self.info_card.grid_columnconfigure(1, weight=1)

        self.thumb_frame = ctk.CTkFrame(self.info_card, width=THUMB_W, height=THUMB_H,
                                       fg_color=theme.COLOR_BG, corner_radius=10)
        self.thumb_frame.grid(row=0, column=0, padx=16, pady=16)
        self.thumb_frame.grid_propagate(False)
        self.thumb_label = ctk.CTkLabel(self.thumb_frame, text="♫",
                                       font=(theme.FONT_FAMILY, 40),
                                       text_color=theme.COLOR_BORDER)
        self.thumb_label.place(relx=0.5, rely=0.5, anchor="center")

        details = ctk.CTkFrame(self.info_card, fg_color="transparent")
        details.grid(row=0, column=1, sticky="nsew", padx=(0, 16), pady=16)
        details.grid_columnconfigure((1, 3), weight=1)

        self.info_title = ctk.CTkLabel(details, text=t("info_none"),
                                      font=theme.FONT_LABEL_BOLD, text_color=theme.COLOR_TEXT,
                                      anchor="w", justify="left", wraplength=560)
        self.info_title.grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 12))

        self.info_author = self._info_field(details, t("f_author"), 1, 0)
        self.info_duration = self._info_field(details, t("f_duration"), 1, 2)
        self.info_resolution = self._info_field(details, t("f_resolution"), 2, 0)
        self.info_size = self._info_field(details, t("f_size"), 2, 2)

        # ---- Barra de progresso + status ----
        progress_frame = ctk.CTkFrame(tab, fg_color="transparent")
        progress_frame.grid(row=5, column=0, sticky="ew", padx=4, pady=(8, 2))
        progress_frame.grid_columnconfigure(0, weight=1)

        self.progress = ctk.CTkProgressBar(progress_frame, height=18, corner_radius=9,
                                          fg_color=theme.COLOR_SURFACE_2,
                                          progress_color=theme.COLOR_PRIMARY)
        self.progress.grid(row=0, column=0, sticky="ew", padx=(0, 12))
        self.progress.set(0)

        self.progress_pct = ctk.CTkLabel(progress_frame, text="0%",
                                        font=theme.FONT_LABEL_BOLD,
                                        text_color=theme.COLOR_PRIMARY, width=58)
        self.progress_pct.grid(row=0, column=1, sticky="e")

        self.status_label = ctk.CTkLabel(progress_frame, text=t("st_ready"),
                                        font=theme.FONT_SMALL,
                                        text_color=theme.COLOR_TEXT_MUTED, anchor="w")
        self.status_label.grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 0))

        # ---- Logs ----
        ctk.CTkLabel(tab, text=t("lbl_logs"), font=theme.FONT_LABEL_BOLD,
                    text_color=theme.COLOR_TEXT, anchor="w").grid(
            row=6, column=0, sticky="nw", padx=4, pady=(8, 4))

        self.log_box = ctk.CTkTextbox(tab, font=theme.FONT_MONO, fg_color=theme.COLOR_BG,
                                     text_color=theme.COLOR_TEXT_MUTED,
                                     corner_radius=theme.CORNER_RADIUS,
                                     border_color=theme.COLOR_BORDER, border_width=1,
                                     wrap="word")
        self.log_box.grid(row=7, column=0, sticky="nsew", padx=4, pady=(0, 8))
        self.log_box.configure(state="disabled")

    def _info_field(self, parent, label_text, row, col):
        ctk.CTkLabel(parent, text=label_text + ":", font=theme.FONT_SMALL,
                    text_color=theme.COLOR_TEXT_MUTED, anchor="w").grid(
            row=row, column=col, sticky="w", padx=(0, 8), pady=3)
        val = ctk.CTkLabel(parent, text="--", font=theme.FONT_LABEL,
                          text_color=theme.COLOR_TEXT, anchor="w")
        val.grid(row=row, column=col + 1, sticky="w", padx=(0, 16), pady=3)
        return val

    # ------------------------------------------------------------------
    # Aba: Historico
    # ------------------------------------------------------------------
    def _build_history_tab(self) -> None:
        t = self.i18n.t
        tab = self.tab_history
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        top = ctk.CTkFrame(tab, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=4, pady=(12, 6))
        top.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(top, text=t("hist_title"), font=theme.FONT_LABEL_BOLD,
                    text_color=theme.COLOR_TEXT, anchor="w").grid(row=0, column=0, sticky="w")

        ctk.CTkButton(top, text=t("btn_clear_history"), width=170, height=36,
                     font=theme.FONT_SMALL, fg_color=theme.COLOR_SURFACE_2,
                     hover_color=theme.COLOR_ACCENT_HOVER, border_width=1,
                     border_color=theme.COLOR_BORDER, corner_radius=theme.CORNER_RADIUS,
                     command=self._on_clear_history).grid(row=0, column=1, sticky="e")

        self.history_list = ctk.CTkScrollableFrame(tab, fg_color=theme.COLOR_BG,
                                                  corner_radius=theme.CORNER_RADIUS)
        self.history_list.grid(row=1, column=0, sticky="nsew", padx=4, pady=(6, 12))
        self.history_list.grid_columnconfigure(0, weight=1)

        self._refresh_history()

    def _refresh_history(self) -> None:
        for child in self.history_list.winfo_children():
            child.destroy()

        items = self.history.all()
        if not items:
            ctk.CTkLabel(self.history_list, text=self.i18n.t("hist_empty"),
                        font=theme.FONT_LABEL, text_color=theme.COLOR_TEXT_MUTED).grid(
                row=0, column=0, pady=24)
            return

        for idx, item in enumerate(items):
            self._history_row(idx, item)

    def _history_row(self, idx: int, item: dict) -> None:
        row = ctk.CTkFrame(self.history_list, fg_color=theme.COLOR_SURFACE,
                          corner_radius=theme.CORNER_RADIUS)
        row.grid(row=idx, column=0, sticky="ew", padx=4, pady=4)
        row.grid_columnconfigure(1, weight=1)

        fmt = item.get("format", "MP4")
        badge_color = theme.COLOR_AUDIO if fmt == "MP3" else theme.COLOR_PRIMARY
        ctk.CTkLabel(row, text=fmt, font=theme.FONT_SMALL, fg_color=badge_color,
                    text_color="#0E0E12", corner_radius=8, width=46, height=24).grid(
            row=0, column=0, rowspan=2, padx=(12, 10), pady=12)

        title = item.get("title", "--")
        if len(title) > 64:
            title = title[:64] + "..."
        ctk.CTkLabel(row, text=title, font=theme.FONT_LABEL_BOLD,
                    text_color=theme.COLOR_TEXT, anchor="w", justify="left").grid(
            row=0, column=1, sticky="w", pady=(10, 2))

        meta = (f"@{item.get('author', '--')}   |   {item.get('resolution', '--')}"
                f"   |   {item.get('duration', '--')}   |   {item.get('date', '')}")
        ctk.CTkLabel(row, text=meta, font=theme.FONT_SMALL,
                    text_color=theme.COLOR_TEXT_MUTED, anchor="w").grid(
            row=1, column=1, sticky="w", pady=(0, 10))

        filepath = item.get("filepath", "")
        if filepath and os.path.isfile(filepath):
            ctk.CTkButton(row, text=self.i18n.t("btn_open_folder"), width=110, height=32,
                         font=theme.FONT_SMALL, fg_color=theme.COLOR_SURFACE_2,
                         hover_color=theme.COLOR_BORDER, corner_radius=theme.CORNER_RADIUS,
                         command=lambda p=filepath: self._open_in_explorer(p)).grid(
                row=0, column=2, rowspan=2, padx=12)

    # ------------------------------------------------------------------
    # Aba: Configuracoes
    # ------------------------------------------------------------------
    def _build_settings_tab(self) -> None:
        t = self.i18n.t
        tab = self.tab_settings
        tab.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(tab, text=t("set_prefs"), font=theme.FONT_LABEL_BOLD,
                    text_color=theme.COLOR_TEXT, anchor="w").grid(
            row=0, column=0, sticky="w", padx=8, pady=(14, 8))

        # Qualidade preferida.
        self._setting_menu(tab, 1, t("set_quality"), ["best", "1080", "720", "480"],
                          self.config_mgr.get("preferred_quality", "best"),
                          lambda v: self.config_mgr.set("preferred_quality", v))

        # Aparencia.
        self._setting_menu(tab, 2, t("set_appearance"), ["Dark", "Light", "System"],
                          self.config_mgr.get("appearance_mode", "Dark"),
                          self._on_theme_change)

        # Switches.
        self._settings_switch(tab, 3, t("sw_notif"), "notifications_enabled")
        self._settings_switch(tab, 4, t("sw_openfolder"), "open_folder_after")
        self._settings_switch(tab, 5, t("sw_updates"), "check_updates")

        # Botoes utilitarios.
        util_frame = ctk.CTkFrame(tab, fg_color="transparent")
        util_frame.grid(row=6, column=0, sticky="ew", padx=8, pady=(12, 6))

        ctk.CTkButton(util_frame, text=t("btn_open_downloads"), height=40,
                     font=theme.FONT_LABEL, fg_color=theme.COLOR_SURFACE_2,
                     hover_color=theme.COLOR_BORDER, border_width=1,
                     border_color=theme.COLOR_BORDER, corner_radius=theme.CORNER_RADIUS,
                     command=lambda: self._open_in_explorer(self.folder_var.get())).grid(
            row=0, column=0, padx=(0, 8))

        ctk.CTkButton(util_frame, text=t("btn_check_updates"), height=40,
                     font=theme.FONT_LABEL, fg_color=theme.COLOR_SURFACE_2,
                     hover_color=theme.COLOR_BORDER, border_width=1,
                     border_color=theme.COLOR_BORDER, corner_radius=theme.CORNER_RADIUS,
                     command=lambda: threading.Thread(
                         target=self._check_updates_async, args=(True,),
                         daemon=True).start()).grid(row=0, column=1, padx=8)

        ctk.CTkLabel(tab, text=t("about", app=APP_NAME, ver=__version__),
                    font=theme.FONT_SMALL, text_color=theme.COLOR_TEXT_MUTED).grid(
            row=7, column=0, sticky="w", padx=8, pady=(16, 8))

    def _setting_menu(self, parent, row, label_text, values, current, command):
        frame = ctk.CTkFrame(parent, fg_color=theme.COLOR_SURFACE_2,
                            corner_radius=theme.CORNER_RADIUS)
        frame.grid(row=row, column=0, sticky="ew", padx=8, pady=6)
        frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(frame, text=label_text, font=theme.FONT_LABEL,
                    text_color=theme.COLOR_TEXT, anchor="w").grid(
            row=0, column=0, sticky="w", padx=16, pady=14)
        menu = ctk.CTkOptionMenu(frame, values=values, width=140, font=theme.FONT_LABEL,
                                fg_color=theme.COLOR_BG, button_color=theme.COLOR_PRIMARY,
                                button_hover_color=theme.COLOR_PRIMARY_HOVER,
                                corner_radius=theme.CORNER_RADIUS, command=command)
        menu.set(current)
        menu.grid(row=0, column=1, padx=16, pady=14)
        return menu

    def _settings_switch(self, parent, row, label_text, config_key):
        frame = ctk.CTkFrame(parent, fg_color=theme.COLOR_SURFACE_2,
                            corner_radius=theme.CORNER_RADIUS)
        frame.grid(row=row, column=0, sticky="ew", padx=8, pady=6)
        frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(frame, text=label_text, font=theme.FONT_LABEL,
                    text_color=theme.COLOR_TEXT, anchor="w").grid(
            row=0, column=0, sticky="w", padx=16, pady=14)
        var = ctk.BooleanVar(value=bool(self.config_mgr.get(config_key, True)))
        ctk.CTkSwitch(frame, text="", variable=var,
                     command=lambda: self.config_mgr.set(config_key, var.get()),
                     progress_color=theme.COLOR_PRIMARY, onvalue=True,
                     offvalue=False).grid(row=0, column=1, padx=16, pady=14)

    # ==================================================================
    # Eventos da interface
    # ==================================================================
    def _on_url_changed(self, *_args) -> None:
        url = self.url_var.get().strip()
        if not hasattr(self, "url_status"):
            return
        if not url:
            self.url_status.configure(text="")
        elif is_valid_tiktok_url(url):
            self.url_status.configure(text="✓  " + self.i18n.t("url_valid"),
                                     text_color=theme.COLOR_SUCCESS)
        else:
            self.url_status.configure(text="⚠  " + self.i18n.t("url_invalid"),
                                     text_color=theme.COLOR_WARNING)

    def _on_paste_click(self) -> None:
        try:
            clipboard = self.clipboard_get()
        except Exception:
            clipboard = ""
        self.url_var.set(extract_first_url(clipboard) or clipboard.strip())

    def _on_browse_click(self) -> None:
        from tkinter import filedialog
        folder = filedialog.askdirectory(
            initialdir=self.folder_var.get() or os.path.expanduser("~"),
            title=self.i18n.t("lbl_folder"))
        if folder:
            self.folder_var.set(folder)
            self.config_mgr.set("download_folder", folder)

    def _on_theme_change(self, mode: str) -> None:
        ctk.set_appearance_mode(mode)
        self.config_mgr.set("appearance_mode", mode)

    def _on_clear_history(self) -> None:
        self.history.clear()
        self._refresh_history()
        self._log(self.i18n.t("log_history_cleared"))

    def _on_download_click(self, mode: str) -> None:
        if self.worker and self.worker.is_alive():
            return

        url = self.url_var.get().strip()
        folder = self.folder_var.get().strip()

        if not url:
            self._log(self.i18n.t("st_paste_first"), level="warning")
            self._set_status(self.i18n.t("st_paste_first"), theme.COLOR_WARNING)
            return
        if not is_valid_tiktok_url(url):
            self._log(self.i18n.t("st_link_invalid"), level="warning")
            self._set_status(self.i18n.t("st_link_invalid"), theme.COLOR_WARNING)
            return
        if not folder:
            folder = self.config_mgr.get("download_folder")
            self.folder_var.set(folder)
        self.config_mgr.set("download_folder", folder)

        self.cancel_event.clear()
        self._reset_info_card()
        self.progress.set(0)
        self.progress_pct.configure(text="0%")
        self._set_buttons_downloading(True)
        self._start_anim(mode)

        label = self.i18n.t("kind_audio") if mode == "audio" else self.i18n.t("kind_video")
        self._log("=" * 52)
        self._log(self.i18n.t("log_new_download", label=label, url=url))

        quality = self.config_mgr.get("preferred_quality", "best")
        self.worker = threading.Thread(target=self._download_worker,
                                      args=(url, folder, quality, mode), daemon=True)
        self.worker.start()

    def _on_cancel_click(self) -> None:
        if self.worker and self.worker.is_alive():
            self.cancel_event.set()
            self._set_status(self.i18n.t("st_cancelling"), theme.COLOR_WARNING)
            self._log(self.i18n.t("log_cancel_requested"), level="warning")

    # ==================================================================
    # Thread de download
    # ==================================================================
    def _download_worker(self, url, folder, quality, mode) -> None:
        def log_cb(text): self.msg_queue.put({"type": "log", "text": text})
        def progress_cb(data): self.msg_queue.put({"type": "progress", "data": data})

        try:
            info = self.downloader.fetch_info(url)
            self.msg_queue.put({"type": "info", "data": info})

            thumb = self.downloader.fetch_thumbnail(info.get("thumbnail"))
            if thumb is not None:
                self.msg_queue.put({"type": "thumbnail", "image": thumb})

            final = self.downloader.download(
                url=url, output_folder=folder, progress_callback=progress_cb,
                log_callback=log_cb, cancel_event=self.cancel_event,
                preferred_quality=quality, mode=mode, info=info, tr=self.i18n.t)
            self.msg_queue.put({"type": "done", "data": final})
        except DownloadCancelled:
            self.msg_queue.put({"type": "cancelled"})
        except Exception as exc:
            self.msg_queue.put({"type": "error", "text": str(exc)})

    # ==================================================================
    # Consumo da fila (thread principal)
    # ==================================================================
    def _process_queue(self) -> None:
        try:
            while True:
                self._handle_message(self.msg_queue.get_nowait())
        except queue.Empty:
            pass
        finally:
            self.after(80, self._process_queue)

    def _handle_message(self, msg: dict) -> None:
        kind = msg.get("type")
        if kind == "log":
            self._log(msg["text"])
        elif kind == "info":
            self._fill_info_card(msg["data"])
        elif kind == "thumbnail":
            self._set_thumbnail(msg["image"])
        elif kind == "progress":
            self._update_progress(msg["data"])
        elif kind == "done":
            self._on_download_done(msg["data"])
        elif kind == "cancelled":
            self._on_download_cancelled()
        elif kind == "error":
            self._on_download_error(msg["text"])
        elif kind == "update":
            self._on_update_available(msg["data"])

    # ------------------------------------------------------------------
    # Progresso / estados
    # ------------------------------------------------------------------
    def _update_progress(self, data: dict) -> None:
        fraction = data.get("fraction", 0.0)
        self.progress.set(fraction)
        self.progress_pct.configure(text=f"{int(fraction * 100)}%")

        if data.get("status") == "downloading":
            text = self.i18n.t("st_downloading", downloaded=data.get("downloaded", "0 B"),
                              total=data.get("total", "?"), speed=data.get("speed", "--"))
            eta = data.get("eta")
            if eta:
                text += self.i18n.t("st_eta", eta=self._fmt_eta(eta))
            self._set_status(text, theme.COLOR_PRIMARY)
        elif data.get("status") == "processing":
            self._set_status(self.i18n.t("st_finalizing"), theme.COLOR_PRIMARY)

    def _fmt_eta(self, seconds) -> str:
        try:
            seconds = int(seconds)
            return f"{seconds // 60:02d}:{seconds % 60:02d}"
        except (TypeError, ValueError):
            return "--:--"

    def _on_download_done(self, final: dict) -> None:
        self._stop_anim()
        self.progress.set(1.0)
        self.progress_pct.configure(text="100%")
        self._set_status(self.i18n.t("st_completed"), theme.COLOR_SUCCESS)
        self._set_buttons_downloading(False)

        self.info_size.configure(text=final.get("filesize", "--"))
        if final.get("resolution"):
            self.info_resolution.configure(text=final["resolution"])

        self.history.add(final)
        self._refresh_history()
        self._log(self.i18n.t("log_file_saved", path=final.get("filepath", "")),
                 level="success")

        if self.config_mgr.get("notifications_enabled", True):
            notify(self.i18n.t("notif_title"),
                  self.i18n.t("notif_body", title=final.get("title", "Arquivo"),
                            fmt=final.get("format", "")))

        if self.config_mgr.get("open_folder_after", False) and final.get("filepath"):
            self._open_in_explorer(final["filepath"])

    def _on_download_cancelled(self) -> None:
        self._stop_anim()
        self.progress.set(0)
        self.progress_pct.configure(text="0%")
        self._set_status(self.i18n.t("st_cancelled"), theme.COLOR_WARNING)
        self._set_buttons_downloading(False)
        self._log(self.i18n.t("st_cancelled"), level="warning")

    def _on_download_error(self, message: str) -> None:
        self._stop_anim()
        self.progress.set(0)
        self.progress_pct.configure(text="0%")
        self._set_status(message, theme.COLOR_ERROR)
        self._set_buttons_downloading(False)
        self._log(message, level="error")

    # ------------------------------------------------------------------
    # Card de informacoes / miniatura
    # ------------------------------------------------------------------
    def _fill_info_card(self, info: dict) -> None:
        self.info_title.configure(text=info.get("title", "--"))
        self.info_author.configure(text=f"@{info.get('author', '--')}")
        self.info_duration.configure(text=info.get("duration", "--:--"))
        self.info_resolution.configure(text=info.get("resolution", "--"))
        self.info_size.configure(text=self.i18n.t("val_calculating"))
        self._log(self.i18n.t("log_video_info", title=info.get("title"),
                            author=info.get("author"), duration=info.get("duration"),
                            resolution=info.get("resolution")))

    def _set_thumbnail(self, pil_image) -> None:
        try:
            w, h = fit_size(pil_image.width, pil_image.height, THUMB_W - 8, THUMB_H - 8)
            img = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(w, h))
            self._thumb_ref = img
            self.thumb_label.configure(image=img, text="")
        except Exception:
            pass

    def _reset_info_card(self) -> None:
        self.info_title.configure(text=self.i18n.t("info_loading"))
        for field in (self.info_author, self.info_duration,
                      self.info_resolution, self.info_size):
            field.configure(text="--")
        self._thumb_ref = None
        self.thumb_label.configure(image=None, text="♫")

    # ------------------------------------------------------------------
    # Animacao do botao ativo
    # ------------------------------------------------------------------
    def _start_anim(self, mode: str) -> None:
        self._active_button = self.audio_btn if mode == "audio" else self.download_btn
        self._active_base = self.i18n.t("anim_audio") if mode == "audio" else self.i18n.t("anim_video")
        self._anim_running = True
        self._anim_step = 0
        self._animate()

    def _animate(self) -> None:
        if not self._anim_running or not self._active_button:
            return
        dots = "." * (self._anim_step % 4)
        try:
            self._active_button.configure(text=f"⧖  {self._active_base}{dots}")
        except Exception:
            return
        self._anim_step += 1
        self.after(400, self._animate)

    def _stop_anim(self) -> None:
        self._anim_running = False
        try:
            self.download_btn.configure(text="↓   " + self.i18n.t("btn_video"))
            self.audio_btn.configure(text="♪   " + self.i18n.t("btn_audio"))
        except Exception:
            pass
        self._active_button = None

    # ------------------------------------------------------------------
    # Helpers de estado / logs
    # ------------------------------------------------------------------
    def _set_buttons_downloading(self, downloading: bool) -> None:
        state = "disabled" if downloading else "normal"
        self.download_btn.configure(state=state)
        self.audio_btn.configure(state=state)
        self.url_entry.configure(state=state)
        self.cancel_btn.configure(state="normal" if downloading else "disabled")
        # Bloqueia a troca de idioma enquanto baixa (evita reconstruir a UI).
        for btn in self.flag_btns.values():
            btn.configure(state=state)

    def _set_status(self, text: str, color: str = None) -> None:
        self.status_label.configure(text=text, text_color=color or theme.COLOR_TEXT_MUTED)

    def _log(self, text: str, level: str = "info") -> None:
        prefix = {"info": "  ", "success": "[OK] ",
                  "warning": "[!]  ", "error": "[X]  "}.get(level, "  ")
        line = f"[{datetime.now().strftime('%H:%M:%S')}] {prefix}{text}\n"
        self._log_history.append(line)
        self._log_history = self._log_history[-500:]  # limita o tamanho

        self.log_box.configure(state="normal")
        self.log_box.insert("end", line)
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _restore_logs(self) -> None:
        """Reexibe o historico de logs apos reconstruir a interface."""
        self.log_box.configure(state="normal")
        for line in self._log_history:
            self.log_box.insert("end", line)
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    # ------------------------------------------------------------------
    # Utilitarios
    # ------------------------------------------------------------------
    def _open_in_explorer(self, path: str) -> None:
        try:
            if os.path.isfile(path):
                subprocess.Popen(["explorer", "/select,", os.path.normpath(path)])
            elif os.path.isdir(path):
                os.startfile(path)  # type: ignore[attr-defined]
        except Exception as exc:
            self._log(self.i18n.t("log_open_fail", error=exc), level="warning")

    # ------------------------------------------------------------------
    # Atualizacoes
    # ------------------------------------------------------------------
    def _check_updates_async(self, manual: bool = False) -> None:
        result = check_for_updates()
        if result:
            self.msg_queue.put({"type": "update", "data": result})
        elif manual:
            self.msg_queue.put({"type": "log", "text": self.i18n.t("log_already_latest")})

    def _on_update_available(self, data: dict) -> None:
        t = self.i18n.t
        version = data.get("version", "?")
        url = data.get("url", "")
        self._log(t("log_update_available", version=version), level="warning")

        win = ctk.CTkToplevel(self)
        win.title(t("upd_title"))
        win.geometry("420x200")
        win.configure(fg_color=theme.COLOR_BG)
        win.transient(self)
        win.grab_set()

        ctk.CTkLabel(win, text=t("upd_msg", version=version), font=theme.FONT_LABEL_BOLD,
                    text_color=theme.COLOR_TEXT).pack(pady=(28, 8))
        ctk.CTkLabel(win, text=t("upd_question"), font=theme.FONT_LABEL,
                    text_color=theme.COLOR_TEXT_MUTED).pack(pady=(0, 16))

        btns = ctk.CTkFrame(win, fg_color="transparent")
        btns.pack(pady=8)
        ctk.CTkButton(btns, text=t("btn_open_page"), fg_color=theme.COLOR_PRIMARY,
                     hover_color=theme.COLOR_PRIMARY_HOVER, text_color="#06222B",
                     command=lambda: (webbrowser.open(url), win.destroy())).grid(
            row=0, column=0, padx=6)
        ctk.CTkButton(btns, text=t("btn_not_now"), fg_color=theme.COLOR_SURFACE_2,
                     hover_color=theme.COLOR_BORDER, command=win.destroy).grid(
            row=0, column=1, padx=6)

    # ------------------------------------------------------------------
    def _on_close(self) -> None:
        self.cancel_event.set()
        self.destroy()

    def run(self) -> None:
        self.mainloop()
