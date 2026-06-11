"""
Ultimate Download MP4
=====================
Pacote principal da aplicacao.

Aqui ficam metadados globais (nome, versao, autor) usados em varias
partes do programa: barra de titulo, verificacao de atualizacoes,
janela "Sobre", etc.

O app baixa videos e audios de varias plataformas (TikTok, YouTube,
Instagram e X/Twitter) usando o yt-dlp como motor principal, com deteccao
automatica da plataforma pelo link.
"""

# Versao atual do aplicativo. E comparada com a ultima release no GitHub
# pelo modulo `updater` para avisar quando ha uma nova versao.
__version__ = "2.0.0"

# Nome exibido na interface, no titulo da janela e nas notificacoes.
APP_NAME = "Ultimate Download MP4"

# Autor / organizacao (aparece na aba "Sobre").
APP_AUTHOR = "Ultimate Download MP4"

# Repositorio usado para checar atualizacoes (formato: "usuario/repo").
# Deixe vazio para DESLIGAR a verificacao online (padrao). Preencha com
# o seu repositorio real para habilitar o aviso automatico de novas versoes.
GITHUB_REPO = ""
