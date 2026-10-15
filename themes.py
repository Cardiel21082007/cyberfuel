import streamlit as st

DARK_CSS = """
<style>
    .stApp { background: linear-gradient(135deg, #0e1117 0%, #1a1d23 50%, #0e1117 100%) !important; }
    .stSidebar { background: rgba(22, 27, 34, 0.95) !important; border-right: 1px solid #00ff88 !important; }
    h1 { color: #00ff88 !important; font-family: Courier New; letter-spacing: 2px; }
    h3 { color: #bd93f9 !important; }
    label, .stForm label { color: #ffffff !important; font-weight: bold !important; }
    .stForm { background: rgba(22, 27, 34, 0.8) !important; border: 1px solid #30363d !important; border-radius: 15px !important; }
    .stFormSubmitButton button { background: linear-gradient(45deg, #00ff88, #0d6efd) !important; color: black !important; font-weight: bold !important; border-radius: 8px !important; }
    .stTextInput > div > div > input, .stNumberInput > div > div > input, .stSelectbox > div > div > div { background-color: #0d1117 !important; color: #00ff88 !important; border: 1px solid #30363d !important; border-radius: 8px !important; }
    [data-testid="stMetricValue"] { color: #ff5555 !important; font-weight: 900 !important; font-size: 2rem !important; }
    [data-testid="stMetricLabel"] { color: #bd93f9 !important; font-weight: bold !important; }
    .stDownloadButton button { background: linear-gradient(45deg, #bd93f9, #ff5555) !important; color: white !important; font-weight: bold !important; border-radius: 8px !important; }
    .stTabs { background-color: #161b22 !important; border-bottom: 2px solid #00ff88 !important; padding-top: 10px; border-radius: 10px 10px 0 0; }
    .stTabs button { color: #8b949e !important; font-weight: bold !important; font-size: 15px !important; border-radius: 0 !important; padding: 15px 25px !important; }
    .stTabs button:hover { color: #00ff88 !important; background-color: #21262d !important; }
    .stTabs button[data-baseweb="tab-selected"] { color: #00ff88 !important; background-color: #0e1117 !important; border-bottom: 3px solid #00ff88 !important; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
</style>
"""

LIGHT_CSS = """
<style>
    .stApp { background: linear-gradient(135deg, #f0f4f8 0%, #ffffff 50%, #f0f4f8 100%) !important; }
    .stSidebar { background: rgba(240, 244, 248, 0.98) !important; border-right: 1px solid #004080 !important; }
    h1 { color: #004080 !important; font-family: Courier New; letter-spacing: 2px; }
    h3 { color: #1a5276 !important; }
    label, .stForm label { color: #1a1a1a !important; font-weight: bold !important; }
    .stForm { background: rgba(255, 255, 255, 0.95) !important; border: 1px solid #bdc3c7 !important; border-radius: 15px !important; }
    .stFormSubmitButton button { background: linear-gradient(45deg, #004080, #0d6efd) !important; color: white !important; font-weight: bold !important; border-radius: 8px !important; }
    .stTextInput > div > div > input, .stNumberInput > div > div > input, .stSelectbox > div > div > div { background-color: #ffffff !important; color: #1a1a1a !important; border: 1px solid #bdc3c7 !important; border-radius: 8px !important; }
    [data-testid="stMetricValue"] { color: #c0392b !important; font-weight: 900 !important; font-size: 2rem !important; }
    [data-testid="stMetricLabel"] { color: #004080 !important; font-weight: bold !important; }
    .stDownloadButton button { background: linear-gradient(45deg, #004080, #1a5276) !important; color: white !important; font-weight: bold !important; border-radius: 8px !important; }
    .stTabs { background-color: #eaf2f8 !important; border-bottom: 2px solid #004080 !important; padding-top: 10px; border-radius: 10px 10px 0 0; }
    .stTabs button { color: #5d6d7e !important; font-weight: bold !important; font-size: 15px !important; border-radius: 0 !important; padding: 15px 25px !important; }
    .stTabs button:hover { color: #004080 !important; background-color: #d4e6f1 !important; }
    .stTabs button[data-baseweb="tab-selected"] { color: #004080 !important; background-color: #ffffff !important; border-bottom: 3px solid #004080 !important; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
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