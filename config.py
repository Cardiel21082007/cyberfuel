import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DB_MODE = os.getenv("DB_MODE", "sqlite")
DB_NAME = "data/combustible.db"

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

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

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
ALERT_EMAIL = os.getenv("ALERT_EMAIL", "")
EMAIL_ENABLED = bool(SMTP_USER and SMTP_PASSWORD and ALERT_EMAIL)

APP_NAME = "CyberFuel AI"
TIPO_COMB_OPTIONS = ["Diesel", "Gasolina Magna", "Gasolina Premium", "Gas LP"]

# ━━ BOMBA 3: TWILIO WHATSAPP ━━
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886") # Número de Sandbox por defecto
ADMIN_WHATSAPP = os.getenv("ADMIN_WHATSAPP", "") # Número del admin ej: +521551234567
WHATSAPP_ENABLED = bool(TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and ADMIN_WHATSAPP)