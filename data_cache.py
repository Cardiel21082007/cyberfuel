import streamlit as st
import pandas as pd

# Importamos las funciones originales de tu BD que hacen consultas pesadas
from db import get_data as _get_data_db
from db import get_all_vehiculos as _get_vehiculos_db
from db import get_presupuestos as _get_presupuestos_db
from db import get_all_estaciones as _get_estaciones_db
from db import get_all_conductores as _get_conductores_db
from db import get_notification_settings as _get_notif_db
from db import get_all_report_schedules as _get_sched_db
from db import get_audit_log as _get_audit_db
from db import get_all_organizations as _get_orgs_db

@st.cache_data(ttl=60, show_spinner=False)
def get_data(tenant_id=None):
    return _get_data_db(tenant_id)

@st.cache_data(ttl=300, show_spinner=False)
def get_all_vehiculos(tenant_id=None):
    return _get_vehiculos_db(tenant_id)

@st.cache_data(ttl=300, show_spinner=False)
def get_presupuestos(tenant_id=None):
    return _get_presupuestos_db(tenant_id)

@st.cache_data(ttl=600, show_spinner=False)
def get_all_estaciones(tenant_id=None):
    return _get_estaciones_db(tenant_id)

@st.cache_data(ttl=300, show_spinner=False)
def get_all_conductores(tenant_id=None):
    return _get_conductores_db(tenant_id)

@st.cache_data(ttl=60, show_spinner=False)
def get_notification_settings(tenant_id=1):
    return _get_notif_db(tenant_id)

@st.cache_data(ttl=60, show_spinner=False)
def get_all_report_schedules(tenant_id=None):
    return _get_sched_db(tenant_id)

@st.cache_data(ttl=120, show_spinner=False)
def get_audit_log(tenant_id=None, limit=200):
    return _get_audit_db(tenant_id, limit)

@st.cache_data(ttl=300, show_spinner=False)
def get_all_organizations():
    return _get_orgs_db()

def clear_all_cache():
    """Llama esto después de guardar/borrar para que refresque la RAM"""
    st.cache_data.clear()