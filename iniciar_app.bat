@echo off
echo Iniciando LogiTrack...

:: Intentar activar el entorno virtual (probando ambas ubicaciones posibles)
set "VENV_ACTIVATED=0"

if exist "venv\Scripts\activate.bat" (
    echo Activando entorno virtual desde venv...
    call "venv\Scripts\activate.bat"
    set "VENV_ACTIVATED=1"
) else if exist ".venv\Scripts\activate.bat" (
    echo Activando entorno virtual desde .venv...
    call ".venv\Scripts\activate.bat"
    set "VENV_ACTIVATED=1"
)

if "%VENV_ACTIVATED%"=="0" (
    echo Error: No se encuentra el entorno virtual.
    echo Por favor, ejecute primero instalar_dependencias.bat
    pause
    exit /b 1
)

:: Verificar que Python está disponible
python --version > nul 2>&1
if errorlevel 1 (
    echo Error: Python no esta disponible en el entorno virtual
    pause
    exit /b 1
)

:: Verificar que uvicorn está instalado
python -c "import uvicorn" > nul 2>&1
if errorlevel 1 (
    echo Uvicorn no esta instalado. Instalando...
    pip install uvicorn
    if errorlevel 1 (
        echo Error: No se pudo instalar uvicorn
        pause
        exit /b 1
    )
)

echo.
echo ============================================
echo   Iniciando servidor web LogiTrack
echo ============================================
echo.
echo ^> El servidor se esta iniciando...
echo ^> Una vez iniciado, abre tu navegador en:
echo.
echo     http://127.0.0.1:8000
echo.
echo ^> Presiona Ctrl+C para detener el servidor
echo ============================================
echo.
uvicorn app:app --reload --host 127.0.0.1 --port 8000 --ws none --timeout-keep-alive 5
echo.
echo Servidor detenido.
pause
