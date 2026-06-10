"""
TikTok Ultimate Downloader
==========================
Pacote principal da aplicacao.

Aqui ficam metadados globais (nome, versao, autor) usados em varias
partes do programa: barra de titulo, verificacao de atualizacoes,
janela "Sobre", etc.
"""

# Versao atual do aplicativo. E comparada com a ultima release no GitHub
# pelo modulo `updater` para avisar quando ha uma nova versao.
__version__ = "1.2.0"

# Nome exibido na interface e nas notificacoes.
APP_NAME = "TikTok Ultimate Downloader"

# Autor / organizacao (aparece na aba "Sobre").
APP_AUTHOR = "TikTok Ultimate Downloader"

# Repositorio usado para checar atualizacoes (formato: "usuario/repo").
# Deixe vazio para DESLIGAR a verificacao online (padrao). Preencha com
# o seu repositorio real (ex.: "seu-usuario/tiktok-downloader") para
# habilitar o aviso automatico de novas versoes.
GITHUB_REPO = ""
