"""
Verificacao automatica de atualizacoes.

Consulta a API publica de releases do GitHub e compara a ultima
versao publicada com a versao atual (`__version__`). A checagem roda
em segundo plano para nao atrasar a abertura do programa.
"""

from typing import Optional

import requests

from . import GITHUB_REPO, __version__


def _parse_version(text: str) -> tuple:
    """
    Converte algo como 'v1.2.3' em (1, 2, 3) para comparar numericamente.
    Partes nao numericas viram 0, evitando excecoes.
    """
    text = text.strip().lstrip("vV")
    parts = []
    for piece in text.split("."):
        num = "".join(ch for ch in piece if ch.isdigit())
        parts.append(int(num) if num else 0)
    return tuple(parts)


def check_for_updates(timeout: int = 6) -> Optional[dict]:
    """
    Retorna informacoes da nova versao se houver uma mais recente.

    Retorno:
        - dict com {"version", "url", "notes"} se houver atualizacao;
        - None se ja estiver atualizado ou em caso de erro/sem rede.
    """
    # Sem repositorio configurado: verificacao desligada (evita falsos
    # avisos de "nova versao"). Configure GITHUB_REPO em src/__init__.py.
    if not GITHUB_REPO:
        return None

    api_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    try:
        resp = requests.get(
            api_url,
            timeout=timeout,
            headers={"Accept": "application/vnd.github+json"},
        )
        if resp.status_code != 200:
            return None

        data = resp.json()
        latest_tag = data.get("tag_name", "")
        if not latest_tag:
            return None

        if _parse_version(latest_tag) > _parse_version(__version__):
            return {
                "version": latest_tag,
                "url": data.get("html_url", f"https://github.com/{GITHUB_REPO}"),
                "notes": (data.get("body") or "").strip()[:500],
            }
        return None
    except (requests.RequestException, ValueError):
        # Sem internet ou resposta invalida: simplesmente nao avisa nada.
        return None
