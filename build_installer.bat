@echo off
REM ============================================================
REM  Gera o INSTALADOR (Setup.exe) do Ultimate Download MP4
REM ============================================================
REM  Requisitos:
REM   1) O executavel ja deve existir em dist\ (rode build.bat antes).
REM   2) Inno Setup 6 instalado (winget install JRSoftware.InnoSetup).
REM
REM  Resultado: UltimateDownloadMP4-Setup-<versao>.exe
REM ============================================================

setlocal
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo ============================================================
echo   Gerando o instalador...
echo ============================================================
echo.

REM ---- Verifica se o executavel existe ----
if not exist "dist\UltimateDownloadMP4.exe" (
    echo [ERRO] dist\UltimateDownloadMP4.exe nao encontrado.
    echo        Rode build.bat primeiro para gerar o executavel.
    pause
    exit /b 1
)

REM ---- Localiza o compilador do Inno Setup (ISCC.exe) ----
set "ISCC="
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"

if not defined ISCC (
    echo [ERRO] Inno Setup nao encontrado.
    echo        Instale com:  winget install JRSoftware.InnoSetup
    pause
    exit /b 1
)

echo Usando: %ISCC%
echo.

REM ---- Gera as imagens do assistente (banner lateral + logo) ----
echo Gerando imagens do assistente...
python "assets\create_installer_images.py"

REM ---- Compila o instalador ----
"%ISCC%" "installer.iss"
if errorlevel 1 (
    echo.
    echo [ERRO] Falha ao gerar o instalador.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   Instalador gerado: UltimateDownloadMP4-Setup-2.0.0.exe
echo ============================================================
echo.
pause
endlocal
