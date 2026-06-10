"""
TikTok Ultimate Downloader
==========================
Ponto de entrada do aplicativo.

Este e o arquivo que deve ser executado (e o usado pelo PyInstaller
para gerar o .exe). Ele apenas inicializa e abre a janela principal,
tratando qualquer erro fatal de forma amigavel.

Execucao:
    python main.py
"""

import sys
import traceback


def main() -> None:
    try:
        # Import tardio: assim, se faltar alguma dependencia, mostramos
        # uma mensagem clara em vez de um traceback cru.
        from src.gui.app import TikTokDownloaderApp

        app = TikTokDownloaderApp()
        app.run()

    except ImportError as exc:
        # Geralmente significa que `pip install -r requirements.txt`
        # ainda nao foi executado.
        msg = (
            "Dependencia ausente: {erro}\n\n"
            "Instale as dependencias com:\n"
            "    pip install -r requirements.txt"
        ).format(erro=exc)
        _fatal(msg)

    except Exception:
        _fatal("Erro inesperado:\n\n" + traceback.format_exc())


def _fatal(message: str) -> None:
    """Mostra o erro numa caixa de dialogo (e no console) e encerra."""
    print(message, file=sys.stderr)
    try:
        # Tenta exibir uma janela de erro nativa do Windows.
        import ctypes

        ctypes.windll.user32.MessageBoxW(
            0, message, "TikTok Ultimate Downloader - Erro", 0x10
        )
    except Exception:
        pass
    sys.exit(1)


if __name__ == "__main__":
    main()
