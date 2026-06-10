@echo off
REM ============================================================
REM  Executa o aplicativo SEM gerar o .exe (modo desenvolvimento)
REM ============================================================
setlocal
chcp 65001 >nul
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo [ERRO] Python nao encontrado no PATH.
    pause
    exit /b 1
)

REM Instala dependencias apenas na primeira vez (marcador .deps_ok).
if not exist ".deps_ok" (
    echo Instalando dependencias...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERRO] Falha ao instalar dependencias.
        pause
        exit /b 1
    )
    echo ok> ".deps_ok"
)

python main.py
endlocal
