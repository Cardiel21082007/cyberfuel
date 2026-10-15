@echo off
title CyberFuel ULTRA AI
color 0A
echo.
echo ============================================
echo    CYBERFUEL ULTRA AI - Iniciando Sistema
echo ============================================
echo.

REM Crear carpeta de datos si no existe
if not exist "data" mkdir data

REM Verificar si Python esta instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no esta instalado o no esta en el PATH.
    echo Por favor instala Python 3.9+ desde python.org
    pause
    exit
)

echo [1/3] Instalando/Actualizando dependencias...
pip install -r requirements.txt -q

echo [2/3] Cargando configuracion (.env)...
REM Crear .env si no existe
if not exist ".env" (
    echo SMTP_SERVER=smtp.gmail.com> .env
    echo SMTP_PORT=587>> .env
    echo SMTP_USER=>> .env
    echo SMTP_PASSWORD=>> .env
    echo ALERT_EMAIL=>> .env
    echo TWILIO_ACCOUNT_SID=>> .env
    echo TWILIO_AUTH_TOKEN=>> .env
    echo ADMIN_WHATSAPP=>> .env
    echo STRIPE_SECRET_KEY=>> .env
    echo STRIPE_PUBLIC_KEY=>> .env
    echo STRIPE_PRO_PRICE_ID=>> .env
    echo.
    echo Se ha creado un archivo .env. Por favor edita tus API Keys ahi y vuelve a correr.
    pause
    exit
)

echo [3/3] Encendiendo motor Streamlit...
echo.
echo ¡Sistema listo! Abriendo navegador...
streamlit run app.py --browser.gatherUsageStats=False
pause