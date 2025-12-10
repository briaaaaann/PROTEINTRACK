@echo off
TITLE Servidor ProteinTrack
COLOR 0A

echo ===============================================
echo   INICIANDO SISTEMA PROTEINTRACK
echo ===============================================
echo.
echo Esperando 10 segundos para conexion de red...
timeout /t 30 /nobreak >nul

cd /d "%~dp0"

echo.
echo Verificando librerias instaladas...

python -m pip install flask flask-cors pandas openpyxl psycopg2-binary werkzeug python-dotenv

echo.
echo Iniciando servidor...
echo.

python -m src.app

echo.
echo ===============================================
echo  EL SERVIDOR SE DETUVO O OCURRIO UN ERROR
echo ===============================================
pause



