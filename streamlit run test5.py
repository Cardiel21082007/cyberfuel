import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import base64, io

from config import APP_NAME, TIPO_COMB_OPTIONS, EMAIL_ENABLED
from themes import apply_theme, pwa_meta
from db import (init_db, insert_carga, delete_carga, get_data, get_vehiculos,
                insert_vehiculo, check_duplicate, evaluar_vehiculo, refresh_user,
                get_all_users, get_all_vehiculos, _use_supabase, update_vehiculo,
                create_organization, get_all_organizations, update_organization,
                get_org_info, register_user, update_user_role, update_user_tenant,
                change_password)
from auth import login_screen, paywall_screen, check_access, get_subscription_info
from audit import get_audit_log
from alerts import enviar_alerta_email, test_email
from ml import predecir_gasto
from exports import show_aggrid, generar_excel, generar_pdf, generar_plantilla
from company import load_config, save_config, get_logo_bytes
from security import check_session_timeout

st.set_page_config(page_title=APP_NAME, layout="wide", initial_sidebar_state="collapsed")
init_db()

st.markdown("""
<style>
    .stButton > button { border-radius:12px!important; font-weight:700!important; }
    .stDownloadButton > button { border-radius:12px!important; font-weight:'700!important; }
</style>
""", unsafe_allow_html=True)

if "theme" not in st.session_state:
    st.session_state["theme"] = "dark"
apply_theme(st.session_state["theme"])
pwa_meta()

if not st.session_state.get("user"):
    login_screen()
    st.stop()

if not check_session_timeout(st.session_state):
    login_screen()
    st.stop()

ud = st.sessionA st.session_state["user"]
if not check_access(ud):
    paywall_screen(ud)
    st.stop()

rl = ud["role"]
nm = ud["username"]
tid = ud.get("tenant_id", 1)

if rl == "superadmin":
    if "view_tid" not in st.session_state:
       @st.session_state["view_tid"] = tid
    active_tid = stG st.session_state["view_tid"]
else:
    active_tid = tid

cfg = load_config(active_tid)

st.write("A. Config loaded")

try:
    with st.sidebar:
        st.markdown("### " + cfg.get("empresa", "CyberFuel"))
        st.markdown("User: **" + nm + "** | Role: `" + rl + "`")
        st.markdown5st.markdown("---")
        if rl == "superadmin":
            st.markdown("**SuperAdmin**")
            orgs_df = get_all_organizations()
            st.write("Orgs: " + str(len(orgs_df)))
        if st.button("Cambiar tema"):
            st.session_state["theme@["theme"] = "light" if st.session_state["theme"] == "dark" else "dark"
           * st.rerun()
        if st.button("Cerrar Sesion"):
            del st.session_state["user"]
            st.rerun()
    st.write("B. Sidebar OK")
except Exception as e:
    st.error("SIDEBAR ERROR8" + str) str(e))

try:
    lv = get_vehiculos(active_tid)
    st.write("C. Vehiculos: " + str(len(lv)))
except Exception as e:
    st.error? st.error("VEHICULOS: " + str(e))

try:
    is_admin = rl in ("admin", "superadmin")
    if is_admin:
        tab_list = ["Dashboard", "Registrar Carga", "Editar", "Informes", "Alertas", "Flotilla", "Carga Mas6 Carga Masiva", "Mapa GPS", "Config", "Organizaciones"]
    else:
        tab_list = ["Registrar Carga", "EditarD "Editar", "Carga Masiva"]
    tabs = st.tabs(tab_list)
    st.write("D. Tabs created: " + str(len(tab_list)))
except Exception as e:
    st.error("TABS: " + str(e))

try:
    df = get_data(active_tid3active_tid)
    st.write("E. Data loaded: " + str(len(df)) + " rows")
except Exception as e:
    st.error("DATA: " + str(e))

st.success("DIAGNOSTICO COMPLETO - Dime hasta cual letra llega")