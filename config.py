import os

# Intentamos importar Streamlit para leer los secrets de la nube
try:
    import streamlit as st
except ImportError:
    st = None  # Si no está instalado (caso raro), es None

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# ━━ FUNCIÓN MÁGICA ━━
# Lee de Streamlit Cloud primero, si no lo encuentra, lee de .env local
def get_env(key, default=""):
    if st and hasattr(st, 'secrets') and key in st.secrets:
        return st.secrets[key]
    return os.getenv(key, default)


# ━━ CONFIGURACIÓN DE BASE DE DATOS ━━
DB_MODE = get_env("DB_MODE", "sqlite")
DB_NAME = "data/combustible.db"

SUPABASE_URL = get_env("SUPABASE_URL", "")
SUPABASE_KEY = get_env("SUPABASE_KEY", "")

# ━━ CONFIGURACIÓN DE SUSCRIPCIONES ━━
TRIAL_DAYS = 7
PRICING_INFO = (
    "Planes CyberFuel AI:\n"
    "- Mensual: $499 MXN / mes\n"
    "- Trimestral: $1,269 MXN / 3 meses\n"
    "- Anual: $4,790 MXN / 12 meses"
)
SUBSCRIPTION_KEYS = {
    "CYBER-MES-A1B2": 1,
    "CYBER-MES-C3D4": 1,
    "CYBER-TRIM-G7H8": 3,
    "CYBER-TRIM-J9K0": 3,
    "CYBER-ANO-P3Q4": 12,
    "CYBER-ANO-R5S6": 12,
}

# ━━ CONFIGURACIÓN SMTP (EMAIL) ━━
SMTP_SERVER = get_env("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(get_env("SMTP_PORT", "587"))
SMTP_USER = get_env("SMTP_USER", "")
SMTP_PASSWORD = get_env("SMTP_PASSWORD", "")
ALERT_EMAIL = get_env("ALERT_EMAIL", "")
EMAIL_ENABLED = bool(SMTP_USER and SMTP_PASSWORD and ALERT_EMAIL)

# ━━ CONTACTO DE VENTAS Y SOPORTE ━━
WHATSAPP_VENTAS = get_env("WHATSAPP_VENTAS", "")
WHATSAPP_SOPORTE = get_env("WHATSAPP_SOPORTE", "")
EMAIL_VENTAS = get_env("EMAIL_VENTAS", ALERT_EMAIL)
TELEFONO_VENTAS = get_env("TELEFONO_VENTAS", "")
SITIO_WEB = get_env("SITIO_WEB", "")

# ━━ CONFIGURACIÓN GENERAL DE LA APP ━━
APP_NAME = "CyberFuel AI"
TIPO_COMB_OPTIONS = ["Diesel", "Gasolina Magna", "Gasolina Premium", "Gas LP"]

# ━━ BOMBA 3: TWILIO WHATSAPP ━━
TWILIO_ACCOUNT_SID = get_env("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = get_env("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_FROM = get_env("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")  # Número de Sandbox por defecto
ADMIN_WHATSAPP = get_env("ADMIN_WHATSAPP", "")  # Número del admin ej: +521551234567
WHATSAPP_ENABLED = bool(TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and ADMIN_WHATSAPP)
