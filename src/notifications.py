"""
Notificacoes nativas do sistema operacional.

Usa a biblioteca `plyer` (multiplataforma). Caso ela nao esteja
disponivel ou falhe, recorremos a um simples 'beep' do Windows como
fallback, sem nunca derrubar a aplicacao.
"""

from . import APP_NAME
from .utils import resource_path


def notify(title: str, message: str) -> None:
    """Exibe uma notificacao do sistema (best-effort)."""
    # 1) Tentativa principal: plyer.
    try:
        from plyer import notification  # import tardio (so quando preciso)

        icon = ""
        ico_path = resource_path("assets/icon.ico")
        # plyer no Windows aceita .ico; em outros SOs preferimos sem icone.
        import os

        if os.path.isfile(ico_path):
            icon = ico_path

        notification.notify(
            title=title,
            message=message,
            app_name=APP_NAME,
            app_icon=icon,
            timeout=8,
        )
        return
    except Exception:
        # Qualquer falha cai para o fallback abaixo.
        pass

    # 2) Fallback: um beep discreto no Windows.
    try:
        import winsound

        winsound.MessageBeep(winsound.MB_ICONASTERISK)
    except Exception:
        pass
