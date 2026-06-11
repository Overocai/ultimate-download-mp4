@echo off
REM ============================================================
REM  Ultimate Download MP4 - Script de build (.exe)
REM ============================================================
REM  Gera um unico executavel (onefile) em /dist usando PyInstaller.
REM  Basta dar duplo clique neste arquivo OU rodar no terminal:
REM       build.bat
REM ============================================================

setlocal
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo ============================================================
echo   Ultimate Download MP4 - Build
echo ============================================================
echo.

REM ---- 1) Garante que o Python esta disponivel -------------
where python >nul 2>nul
if errorlevel 1 (
    echo [ERRO] Python nao encontrado no PATH.
    echo        Instale o Python 3.10+ em https://www.python.org/downloads/
    pause
    exit /b 1
)

REM ---- 2) (Opcional) cria/usa um ambiente virtual ----------
if not exist "venv\" (
    echo [1/5] Criando ambiente virtual...
    python -m venv venv
)
call "venv\Scripts\activate.bat"

REM ---- 3) Instala as dependencias --------------------------
echo [2/5] Instalando dependencias...
python -m pip install --upgrade pip >nul
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERRO] Falha ao instalar as dependencias.
    pause
    exit /b 1
)

REM ---- 4) Gera o icone -------------------------------------
echo [3/5] Gerando icone...
python "assets\create_icon.py"

REM ---- 5) Limpa builds anteriores --------------------------
echo [4/5] Limpando builds anteriores...
if exist "build\" rmdir /s /q "build"
if exist "dist\"  rmdir /s /q "dist"

REM ---- 6) Compila com o PyInstaller ------------------------
echo [5/5] Compilando o executavel (isso pode demorar alguns minutos)...
REM  Observacao: NAO embutimos o FFmpeg no .exe (ele tem ~80 MB!). O app
REM  baixa o FFmpeg automaticamente, uma unica vez, somente se o usuario
REM  optar por baixar em MP3. Assim o executavel fica bem mais leve e o
REM  download de video (MP4) funciona normalmente sem ele.
REM  O --collect-submodules src.platforms garante que todas as plataformas
REM  (TikTok, YouTube, Instagram, X/Twitter) entrem no pacote.
pyinstaller --noconfirm --onefile --windowed ^
    --name "UltimateDownloadMP4" ^
    --icon "assets\icon.ico" ^
    --add-data "assets\icon.ico;assets" ^
    --collect-submodules src.platforms ^
    --collect-all customtkinter ^
    --collect-all yt_dlp ^
    --collect-all plyer ^
    --exclude-module imageio_ffmpeg ^
    --exclude-module plyer.platforms.android ^
    --exclude-module plyer.platforms.ios ^
    --exclude-module plyer.platforms.linux ^
    --exclude-module plyer.platforms.macosx ^
    --hidden-import plyer.platforms.win.notification ^
    main.py

if errorlevel 1 (
    echo.
    echo [ERRO] A compilacao falhou. Verifique as mensagens acima.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   Build concluido com sucesso!
echo   Executavel: dist\UltimateDownloadMP4.exe
echo ============================================================
echo.
pause
endlocal
