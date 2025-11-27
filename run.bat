@echo off
TITLE Servidor ProteinTrack
COLOR 0A

echo ===============================================
echo   INICIANDO SISTEMA PROTEINTRACK
echo ===============================================
echo.
echo Esperando 10 segundos para conexion de red...
timeout /t 30 /nobreak >nul

:: Ir a la carpeta del proyecto
cd /d "%~dp0"

echo.
echo Verificando librerias instaladas...

:: --- AGREGAMOS python-dotenv AL FINAL ---
python -m pip install flask flask-cors pandas openpyxl psycopg2-binary werkzeug python-dotenv

echo.
echo Iniciando servidor...
echo.

:: Ejecutar la App
python -m src.app

:: Si falla, no cerrar la ventana
echo.
echo ===============================================
echo  EL SERVIDOR SE DETUVO O OCURRIO UN ERROR
echo ===============================================
pause