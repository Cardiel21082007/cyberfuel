import streamlit as st

DARK_CSS = """
<style>
    /* ━━ FONDO Y LAYOUT PRINCIPAL ━━ */
    .stApp { background: linear-gradient(135deg, #0e1117 0%, #1a1d23 50%, #0e1117 100%) !important; }
    .stSidebar { background: rgba(22, 27, 34, 0.95) !important; border-right: 1px solid #00ff88 !important; }
    
    /* ━━ TIPOGRAFÍA ━━ */
    h1 { color: #00ff88 !important; font-family: 'Inter', Courier New; letter-spacing: 2px; }
    h3 { color: #bd93f9 !important; }
    label, .stForm label { color: #ffffff !important; font-weight: bold !important; }
    
    /* ━━ FORMULARIOS ━━ */
    .stForm { background: rgba(22, 27, 34, 0.8) !important; border: 1px solid #30363d !important; border-radius: 15px !important; }
    .stFormSubmitButton button { background: linear-gradient(45deg, #00ff88, #0d6efd) !important; color: black !important; font-weight: bold !important; border-radius: 8px !important; }
    .stTextInput > div > div > input, .stNumberInput > div > div > input, .stSelectbox > div > div > div { background-color: #0d1117 !important; color: #00ff88 !important; border: 1px solid #30363d !important; border-radius: 8px !important; }
    
    /* ━━ MÉTRICAS ━━ */
    [data-testid="stMetricValue"] { color: #ff5555 !important; font-weight: 900 !important; font-size: 2rem !important; }
    [data-testid="stMetricLabel"] { color: #bd93f9 !important; font-weight: bold !important; }
    
    /* ━━ BOTONES DE DESCARGA ━━ */
    .stDownloadButton button { background: linear-gradient(45deg, #bd93f9, #ff5555) !important; color: white !important; font-weight: bold !important; border-radius: 8px !important; }
    
    /* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
    /*  PESTAÑAS GRANDES Y ESTÉTICAS - DARK MODE  */
    /* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
    .stTabs { background-color: transparent !important; padding-top: 10px; border-radius: 0; border-bottom: none !important; }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px !important;
        background: #12121a !important;
        border-radius: 18px !important;
        padding: 10px !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        box-shadow: 0 4px 24px rgba(0,0,0,0.4) inset !important;
    }
    
    .stTabs [data-baseweb="tab"],
    .stTabs button {
        border-radius: 14px !important;
        padding: 18px 28px !important;
        font-weight: 700 !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.4s cubic-bezier(0.4,0,0.2,1) !important;
        color: #9ca3af !important;
        font-size: 1.25rem !important;
        letter-spacing: 0.3px !important;
        min-height: 60px !important;
        background: transparent !important;
        border: 1px solid transparent !important;
        display: flex !important;
        align-items: center !important;
        gap: 10px !important;
        line-height: 1.5 !important;
    }
    
    .stTabs [data-baseweb="tab"]:hover,
    .stTabs button:hover {
        background: rgba(0,255,136,0.08) !important;
        color: #f8f8f2 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 16px rgba(0,255,136,0.2) !important;
        border: 1px solid rgba(0,255,136,0.3) !important;
    }
    
    .stTabs [aria-selected="true"],
    .stTabs button[data-baseweb="tab-selected"] {
        background: linear-gradient(135deg, rgba(0,255,136,0.25), rgba(0,255,136,0.1)) !important;
        color: #00ff88 !important;
        box-shadow: 0 0 24px rgba(0,255,136,0.3), 0 4px 16px rgba(0,255,136,0.2) !important;
        border: 1px solid rgba(0,255,136,0.5) !important;
        font-weight: 800 !important;
        transform: translateY(-2px) !important;
        font-size: 1.35rem !important;
        border-bottom: none !important;
    }
    
    .stTabs [aria-selected="true"]::before,
    .stTabs button[data-baseweb="tab-selected"]::before {
        content: '✦' !important;
        margin-right: 8px !important;
        color: #00ff88 !important;
        font-size: 1rem !important;
        animation: pulse 2s ease-in-out infinite !important;
    }
    
    @keyframes pulse {
        0%,100% { opacity: 0.6; }
        50% { opacity: 1; }
    }
    
    .stTabs [data-baseweb="tab"] svg,
    .stTabs [data-baseweb="tab"] [role="img"],
    .stTabs [data-baseweb="tab"] span {
        font-size: 1.3rem !important;
        width: auto !important;
    }
    
    /* Quitar bordes azules viejos de Streamlit */
    .stTabs [data-baseweb="tab-highlight"] { background-color: transparent !important; height: 0 !important; }
    .stTabs [data-baseweb="tab-border"] { display: none !important; }
    
    /* ━━ OCULTAR MENÚ ━━ */
    #MainMenu {visibility: hidden;} 
    footer {visibility: hidden;}
</style>
"""

LIGHT_CSS = """
<style>
    /* ━━ FONDO Y LAYOUT PRINCIPAL ━━ */
    .stApp { background: linear-gradient(135deg, #f0f4f8 0%, #ffffff 50%, #f0f4f8 100%) !important; }
    .stSidebar { background: rgba(240, 244, 248, 0.98) !important; border-right: 1px solid #004080 !important; }
    
    /* ━━ TIPOGRAFÍA ━━ */
    h1 { color: #004080 !important; font-family: 'Inter', Courier New; letter-spacing: 2px; }
    h3 { color: #1a5276 !important; }
    label, .stForm label { color: #1a1a1a !important; font-weight: bold !important; }
    
    /* ━━ FORMULARIOS ━━ */
    .stForm { background: rgba(255, 255, 255, 0.95) !important; border: 1px solid #bdc3c7 !important; border-radius: 15px !important; }
    .stFormSubmitButton button { background: linear-gradient(45deg, #004080, #0d6efd) !important; color: white !important; font-weight: bold !important; border-radius: 8px !important; }
    .stTextInput > div > div > input, .stNumberInput > div > div > input, .stSelectbox > div > div > div { background-color: #ffffff !important; color: #1a1a1a !important; border: 1px solid #bdc3c7 !important; border-radius: 8px !important; }
    
    /* ━━ MÉTRICAS ━━ */
    [data-testid="stMetricValue"] { color: #c0392b !important; font-weight: 900 !important; font-size: 2rem !important; }
    [data-testid="stMetricLabel"] { color: #004080 !important; font-weight: bold !important; }
    
    /* ━━ BOTONES DE DESCARGA ━━ */
    .stDownloadButton button { background: linear-gradient(45deg, #004080, #1a5276) !important; color: white !important; font-weight: bold !important; border-radius: 8px !important; }
    
    /* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
    /*  PESTAÑAS GRANDES Y ESTÉTICAS - LIGHT MODE  */
    /* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
    .stTabs { background-color: transparent !important; padding-top: 10px; border-radius: 0; border-bottom: none !important; }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px !important;
        background: #ffffff !important;
        border-radius: 18px !important;
        padding: 10px !important;
        border: 1px solid #bdc3c7 !important;
        box-shadow: 0 4px 24px rgba(0,64,128,0.15) inset !important;
    }
    
    .stTabs [data-baseweb="tab"],
    .stTabs button {
        border-radius: 14px !important;
        padding: 18px 28px !important;
        font-weight: 700 !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.4s cubic-bezier(0.4,0,0.2,1) !important;
        color: #5d6d7e !important;
        font-size: 1.25rem !important;
        letter-spacing: 0.3px !important;
        min-height: 60px !important;
        background: transparent !important;
        border: 1px solid transparent !important;
        display: flex !important;
        align-items: center !important;
        gap: 10px !important;
        line-height: 1.5 !important;
    }
    
    .stTabs [data-baseweb="tab"]:hover,
    .stTabs button:hover {
        background: rgba(0,64,128,0.08) !important;
        color: #004080 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 16px rgba(0,64,128,0.2) !important;
        border: 1px solid rgba(0,64,128,0.3) !important;
    }
    
    .stTabs [aria-selected="true"],
    .stTabs button[data-baseweb="tab-selected"] {
        background: linear-gradient(135deg, rgba(0,64,128,0.15), rgba(0,64,128,0.05)) !important;
        color: #004080 !important;
        box-shadow: 0 0 24px rgba(0,64,128,0.2), 0 4px 16px rgba(0,64,128,0.15) !important;
        border: 1px solid rgba(0,64,128,0.5) !important;
        font-weight: 800 !important;
        transform: translateY(-2px) !important;
        font-size: 1.35rem !important;
        border-bottom: none !important;
    }
    
    .stTabs [aria-selected="true"]::before,
    .stTabs button[data-baseweb="tab-selected"]::before {
        content: '✦' !important;
        margin-right: 8px !important;
        color: #004080 !important;
        font-size: 1rem !important;
        animation: pulse 2s ease-in-out infinite !important;
    }
    
    @keyframes pulse {
        0%,100% { opacity: 0.6; }
        50% { opacity: 1; }
    }
    
    .stTabs [data-baseweb="tab"] svg,
    .stTabs [data-baseweb="tab"] [role="img"],
    .stTabs [data-baseweb="tab"] span {
        font-size: 1.3rem !important;
        width: auto !important;
    }
    
    /* Quitar bordes azules viejos de Streamlit */
    .stTabs [data-baseweb="tab-highlight"] { background-color: transparent !important; height: 0 !important; }
    .stTabs [data-baseweb="tab-border"] { display: none !important; }
    
    /* ━━ OCULTAR MENÚ ━━ */
    #MainMenu {visibility: hidden;} 
    footer {visibility: hidden;}
</style>
"""

def apply_theme(theme):
    css = DARK_CSS if theme == "dark" else LIGHT_CSS
    st.markdown(css, unsafe_allow_html=True)

def pwa_meta():
    st.markdown("""
    <link rel="manifest" href="/static/manifest.json">
    <meta name="theme-color" content="#00ff88">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    """, unsafe_allow_html=True)
