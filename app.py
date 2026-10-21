import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import base64, io, sqlite3

from config import APP_NAME, TIPO_COMB_OPTIONS, EMAIL_ENABLED, ALERT_EMAIL
from themes import apply_theme, pwa_meta
# ━━ IMPORTS DE ESCRITURA (DIRECTOS A DB) ━━
from db import (init_db, insert_carga, delete_carga, get_vehiculos,
                insert_vehiculo, check_duplicate, evaluar_vehiculo, refresh_user,
                get_all_users, _use_supabase, update_vehiculo,
                create_organization, update_organization,
                get_org_info, register_user, update_user_role, update_user_tenant,
                change_password, delete_vehiculo,
                init_estaciones, insert_estacion,
                delete_estacion, update_estacion,
                init_conductores, insert_conductor, delete_conductor,
                init_presupuestos, set_presupuesto, check_presupuesto,
                init_precios, insert_precio, delete_precio, get_precios,
                init_report_schedules, insert_report_schedule,
                update_schedule_last_sent, toggle_report_schedule, delete_report_schedule,
                init_notification_settings, ensure_default_notifications,
                save_notification_setting, update_notification_last_sent,
                create_subscription_key, validate_subscription_key,
                get_all_subscription_keys, deactivate_subscription_key)
# ━━ IMPORTS DE LECTURA (VÍA CACHE PARA QUE VUELE) ━━
from data_cache import (get_data, get_all_vehiculos, get_presupuestos, get_all_estaciones,
                        get_all_conductores, get_notification_settings, get_all_report_schedules,
                        get_audit_log, get_all_organizations, clear_all_cache)

from auth import login_screen, paywall_screen, check_access, get_subscription_info
from scheduler import start_scheduler, is_scheduler_running
from alerts import (enviar_alerta_email, test_email,
                    enviar_alerta_mantenimiento, enviar_alerta_presupuesto)
from ml import predecir_gasto
from exports import show_aggrid, generar_excel, generar_pdf, generar_plantilla
from company import load_config, save_config, get_logo_bytes
from security import check_session_timeout

try:
    from db import DB_NAME
except ImportError:
    DB_NAME = 'data/combustible.db'

st.set_page_config(page_title=APP_NAME, layout='wide', initial_sidebar_state='expanded', page_icon="⛽")

# Ocultar menús de Streamlit para look profesional
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

init_db()
init_estaciones()
init_conductores()
init_presupuestos()
init_precios()
init_report_schedules()
init_notification_settings()
start_scheduler()

st.markdown('''
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
:root{--bg-primary:#0a0a0f;--bg-secondary:#12121a;--bg-card:rgba(20,20,35,0.8);--accent:#00ff88;--accent-2:#bd93f9;--accent-3:#ff5555;--text-primary:#f8f8f2;--text-secondary:#9ca3af;--border:rgba(255,255,255,0.08);--glow:0 0 20px rgba(0,255,136,0.15)}
.stApp{background:var(--bg-primary);font-family:'Inter',sans-serif}
header[data-testid="stHeader"]{background:linear-gradient(135deg,#0a0a0f 0%,#1a1a2e 50%,#0a0a0f 100%);border-bottom:1px solid var(--border);backdrop-filter:blur(20px)}
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#0f0f1a 0%,#1a1a2e 50%,#0f0f1a 100%)!important;border-right:1px solid var(--border)}
section[data-testid="stSidebar"]>div{background:transparent!important}
.stExpander,.stForm{border:1px solid var(--border)!important;border-radius:16px!important;background:var(--bg-card)!important;backdrop-filter:blur(10px);box-shadow:0 4px 24px rgba(0,0,0,0.3);transition:all 0.3s ease}
.stExpander:hover,.stForm:hover{border-color:rgba(0,255,136,0.2)!important;box-shadow:var(--glow)}
.stButton>button{border-radius:12px!important;font-weight:700!important;font-family:'Inter',sans-serif!important;background:linear-gradient(135deg,#00ff88,#00cc6a)!important;color:#0a0a0f!important;border:none!important;padding:10px 24px!important;transition:all 0.3s ease!important;box-shadow:0 4px 15px rgba(0,255,136,0.3)!important;letter-spacing:0.5px!important;text-transform:uppercase!important;font-size:0.85rem!important}
.stButton>button:hover{transform:translateY(-2px)!important;box-shadow:0 8px 25px rgba(0,255,136,0.4)!important}
.stDownloadButton>button{border-radius:12px!important;font-weight:700!important;font-family:'Inter',sans-serif!important;background:linear-gradient(135deg,#bd93f9,#9b59b6)!important;color:#fff!important;border:none!important;padding:10px 24px!important;transition:all 0.3s ease!important;box-shadow:0 4px 15px rgba(189,147,249,0.3)!important;letter-spacing:0.5px!important;text-transform:uppercase!important;font-size:0.85rem!important}
.stDownloadButton>button:hover{transform:translateY(-2px)!important;box-shadow:0 8px 25px rgba(189,147,249,0.4)!important}
.stFormSubmitButton>button{background:linear-gradient(135deg,#00ff88,#00cc6a)!important;color:#0a0a0f!important;font-weight:800!important;border-radius:12px!important;border:none!important;padding:12px 32px!important;text-transform:uppercase!important;letter-spacing:1px!important;font-size:0.9rem!important;box-shadow:0 4px 20px rgba(0,255,136,0.35)!important;transition:all 0.3s ease!important}
.stFormSubmitButton>button:hover{transform:translateY(-2px)!important;box-shadow:0 8px 30px rgba(0,255,136,0.5)!important}
[data-testid="stMetricValue"]{font-size:1.8rem!important;font-weight:800!important;background:linear-gradient(135deg,#00ff88,#8be9fd);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
[data-testid="stMetricLabel"]{font-size:0.8rem!important;font-weight:600!important;text-transform:uppercase!important;letter-spacing:1.5px!important;color:var(--text-secondary)!important}
.stTabs [data-baseweb="tab-list"]{gap:6px!important;background:var(--bg-secondary)!important;border-radius:18px!important;padding:8px!important;border:1px solid var(--border)!important;box-shadow:0 4px 24px rgba(0,0,0,0.3) inset!important}
.stTabs [data-baseweb="tab"]{border-radius:14px!important;padding:14px 22px!important;font-weight:700!important;font-family:'Inter',sans-serif!important;transition:all 0.4s cubic-bezier(0.4,0,0.2,1)!important;color:var(--text-secondary)!important;font-size:1.05rem!important;letter-spacing:0.3px!important;display:flex!important;align-items:center!important;gap:8px!important}
.stTabs [data-baseweb="tab"]:hover{background:rgba(0,255,136,0.08)!important;color:#f8f8f2!important;transform:translateY(-1px)!important;box-shadow:0 4px 12px rgba(0,255,136,0.15)!important}
.stTabs [aria-selected="true"]{background:linear-gradient(135deg,rgba(0,255,136,0.25),rgba(0,255,136,0.1))!important;color:#00ff88!important;box-shadow:0 0 24px rgba(0,255,136,0.2),0 4px 16px rgba(0,255,136,0.15)!important;border:1px solid rgba(0,255,136,0.5)!important;font-weight:800!important;transform:translateY(-2px)!important}
.stTabs [aria-selected="true"]::before{content:'✦'!important;margin-right:6px!important;color:#00ff88!important;font-size:0.85rem!important;animation:pulse 2s ease-in-out infinite!important}
@keyframes pulse{0%,100%{opacity:0.6}50%{opacity:1}}
.stTabs [data-baseweb="tab"] svg{width:22px!important;height:22px!important}
.stTextInput>div>div>input,.stNumberInput>div>div>input,.stSelectbox>div>div>select,.stTextArea>div>div>textarea{border-radius:10px!important;border:1px solid var(--border)!important;background:rgba(20,20,35,0.6)!important;font-family:'Inter',sans-serif!important;transition:all 0.3s ease!important}
.stTextInput>div>div>input:focus,.stNumberInput>div>div>input:focus{border-color:rgba(0,255,136,0.5)!important;box-shadow:0 0 15px rgba(0,255,136,0.1)!important}
.stDataFrame{border-radius:16px!important;border:1px solid var(--border)!important;overflow:hidden}
.stToast{border-radius:12px!important;backdrop-filter:blur(20px)!important}
.stSuccess,.stWarning,.stError,.stInfo{border-radius:12px!important}
::-webkit-scrollbar{width:8px;height:8px}
::-webkit-scrollbar-track{background:var(--bg-primary)}
::-webkit-scrollbar-thumb{background:linear-gradient(180deg,#00ff88,#bd93f9);border-radius:4px}
hr{border:none!important;height:1px!important;background:linear-gradient(90deg,transparent,rgba(0,255,136,0.3),transparent)!important}
.stProgress>div>div>div>div{background:linear-gradient(90deg,#00ff88,#8be9fd)!important;border-radius:10px!important}
</style>
''', unsafe_allow_html=True)

def metric_card(icon, label, value, color='#00ff88'):
    st.markdown(f'''<div style="background:rgba(20,20,35,0.8);border:1px solid rgba(255,255,255,0.08);border-radius:16px;padding:18px 12px;text-align:center;backdrop-filter:blur(10px);"><div style="font-size:1.8rem;margin-bottom:6px;">{icon}</div><div style="font-size:0.65rem;text-transform:uppercase;letter-spacing:1.5px;color:#9ca3af;font-weight:600;margin-bottom:8px;">{label}</div><div style="font-size:1.6rem;font-weight:800;color:{color};">{value}</div></div>''', unsafe_allow_html=True)

def role_badge(role):
    colors = {'superadmin':('linear-gradient(135deg,#ff5555,#ff7979)','👑 SuperAdmin'),'admin':('linear-gradient(135deg,#bd93f9,#9b59b6)','🛡️ Admin'),'despachador':('linear-gradient(135deg,#00ff88,#00cc6a)','⛽ Despachador')}
    bg, txt = colors.get(role, ('linear-gradient(135deg,#6272a4,#44475a)', '👤 ' + role))
    st.markdown(f'''<div style="display:inline-block;background:{bg};color:{'#0a0a0f' if role=='despachador' else '#fff'};padding:5px 16px;border-radius:20px;font-size:0.75rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;">{txt}</div>''', unsafe_allow_html=True)

def section_header(icon, title, subtitle=''):
    sub = f'<div style="font-size:0.85rem;color:#9ca3af;margin-top:2px;">{subtitle}</div>' if subtitle else ''
    st.markdown(f'''<div style="margin-bottom:20px;"><div style="font-size:1.8rem;font-weight:800;display:flex;align-items:center;gap:10px;"><span style="font-size:2rem;">{icon}</span><span style="background:linear-gradient(135deg,#00ff88,#8be9fd,#bd93f9);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">{title}</span></div>{sub}</div>''', unsafe_allow_html=True)

def veh_select_options(active_tid):
    dv = get_all_vehiculos(active_tid)
    options = {}
    if not dv.empty:
        for _, r in dv.iterrows():
            marca = r.get('marca', '') or ''
            modelo = r.get('modelo', '') or ''
            desc = f"{marca} {modelo}".strip()
            label = f"🚛 {r['placa']}  —  {desc}" if desc else f"🚛 {r['placa']}"
            options[label] = r['placa']
    return options

if 'theme' not in st.session_state:
    st.session_state['theme'] = 'dark'
apply_theme(st.session_state['theme'])
pwa_meta()

if not st.session_state.get('user'):
    login_screen()
    st.stop()

if st.session_state.get('session_expired'):
    st.session_state.pop('session_expired', None)
    st.warning('⚠️ Sesión expirada')
    login_screen()
    st.stop()

if not check_session_timeout(st.session_state):
    st.warning('⚠️ Sesión expirada')
    login_screen()
    st.stop()

ud = st.session_state['user']
if not check_access(ud):
    paywall_screen(ud)
    st.stop()

rl = ud['role']
nm = ud['username']
tid = ud.get('tenant_id', 1)

if rl == 'superadmin':
    if 'view_tid' not in st.session_state:
        st.session_state['view_tid'] = tid
    active_tid = st.session_state['view_tid']
else:
    active_tid = tid

cfg = load_config(active_tid)

with st.sidebar:
    st.markdown(f'''<div style="text-align:center;padding:10px 0 5px 0;"><div style="font-size:2.5rem;">⛽</div><div style="font-size:1.3rem;font-weight:800;background:linear-gradient(135deg,#00ff88,#8be9fd);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">{cfg.get('empresa','CyberFuel')}</div></div>''', unsafe_allow_html=True)
    st.markdown('---')
    st.markdown(f'''<div style="background:rgba(20,20,35,0.8);border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:14px;margin-bottom:10px;backdrop-filter:blur(10px);"><div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;"><div style="width:40px;height:40px;border-radius:50%;background:linear-gradient(135deg,#00ff88,#bd93f9);display:flex;align-items:center;justify-content:center;font-size:1.2rem;font-weight:800;color:#0a0a0f;">{nm[0].upper()}</div><div><div style="font-weight:700;font-size:0.95rem;color:#f8f8f2;">{nm}</div><div style="font-size:0.75rem;color:#9ca3af;">Activo <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#00ff88;box-shadow:0 0 6px #00ff88;vertical-align:middle;margin-left:4px;"></span></div></div></div></div>''', unsafe_allow_html=True)
    role_badge(rl)
    if rl != 'superadmin' and tid > 0:
        org_info = get_org_info(tid)
        st.markdown(f'<div style="font-size:0.8rem;color:#9ca3af;margin-top:8px;">🏢 {org_info.get("nombre","?")}</div>', unsafe_allow_html=True)
    st.markdown('---')
    if rl == 'superadmin':
        st.markdown('**👑 SuperAdmin Panel**')
        orgs_df = get_all_organizations()
        if not orgs_df.empty:
            org_options = {'🌐 Todas': None}
            for _, o in orgs_df.iterrows():
                org_options[f'🏢 {o["nombre"]}'] = o['id']
            sel = st.selectbox('Ver datos de:', list(org_options.keys()), key='org_switch')
            new_tid = org_options[sel]
            if new_tid != st.session_state.get('view_tid'):
                st.session_state['view_tid'] = new_tid
                st.rerun()
        st.markdown('---')
    if st.button('🎨 Cambiar Tema'):
        st.session_state['theme'] = 'light' if st.session_state['theme'] == 'dark' else 'dark'
        st.rerun()
    with st.expander('🔑 Cambiar Password'):
        with st.form('f_cp'):
            cp1 = st.text_input('Actual', type='password', key='cp1')
            cp2 = st.text_input('Nueva', type='password', key='cp2')
            cp3 = st.text_input('Confirmar', type='password', key='cp3')
            if st.form_submit_button('✅ Cambiar'):
                if cp2 != cp3: st.error('❌ No coinciden')
                elif len(cp2) < 4: st.error('❌ Mínimo 4 caracteres')
                else:
                    from db import verify_user as _vu
                    if _vu(nm, cp1):
                        if change_password(nm, cp2): clear_all_cache(); st.toast('✅ Password actualizada!')
                        else: st.error('❌ Error al guardar')
                    else: st.error('❌ Password actual incorrecta')
    st.markdown('---')
    if st.button('🚪 Cerrar Sesión'):
        del st.session_state['user']
        st.rerun()

CC = ['#00ff88','#bd93f9','#ff5555','#f1fa8c','#8be9fd','#50fa7b','#ffb86c','#6272a4']
lv = get_vehiculos(active_tid)

def clean_tipo(raw):
    if pd.isna(raw): return 'Diesel'
    txt = str(raw).strip().lower()
    if 'diesel' in txt: return 'Diesel'
    if 'premium' in txt: return 'Gasolina Premium'
    if 'magna' in txt: return 'Gasolina Magna'
    if 'lp' in txt: return 'Gas LP'
    return 'Diesel'

is_admin = rl in ('admin', 'superadmin')

if is_admin:
    tab_list = ['📊 Dashboard','⛽ Carga','✏️ Editar','📋 Informes','🚨 Alertas','🚛 Flotilla','👤 Conductores','💰 Presupuesto','📥 Masiva','🗺️ Mapa','⚙️ Config','🏢 Orgs']
    tabs = st.tabs(tab_list)
else:
    tabs = st.tabs(['⛽ Carga','✏️ Editar','📥 Masiva'])

# ━━━ DASHBOARD ━━━
if is_admin:
    with tabs[0]:
        section_header('📊', 'Dashboard Ejecutivo', 'Centro de mando inteligente de la flotilla')
        df = get_data(active_tid)
        if not df.empty:
            cf1,cf2,cf3 = st.columns(3)
            with cf1: vh = st.multiselect('🚗 Vehículos', df['vehiculo'].unique(), df['vehiculo'].unique(), key='dv')
            with cf2: tc = st.multiselect('⛽ Combustible', df['tipo_combustible'].unique(), df['tipo_combustible'].unique(), key='dc')
            with cf3: es = st.multiselect('📍 Estaciones', df['estacion'].unique(), df['estacion'].unique(), key='de')
            ff = df[(df['vehiculo'].isin(vh)) & (df['tipo_combustible'].isin(tc)) & (df['estacion'].isin(es))].copy()
            ff['fdt'] = pd.to_datetime(ff['fecha'], format='mixed')
            
            now = datetime.now()
            ff_mes = ff[(ff['fdt'].dt.month == now.month) & (ff['fdt'].dt.year == now.year)]
            ff_mes_ant = ff[(ff['fdt'].dt.month == (now.month - 1) if now.month > 1 else 12) & (ff['fdt'].dt.year == (now.year if now.month > 1 else now.year - 1))]

            tg_mes = ff_mes['custo'].sum()
            tg_ant = ff_mes_ant['custo'].sum()
            tl_mes = ff_mes['litros'].sum()
            tl_ant = ff_mes_ant['litros'].sum()
            ar = ff_mes[ff_mes['rendimento'] > 0]['rendimento'].mean()
            anomalias_count = ff_mes[ff_mes['alerta_anomalia'].isin(['ANOMALIA', 'ANOMALIA_AI'])].shape[0]

            # ━━ KPIs EJECUTIVOS CON TENDENCIA ━━
            k1, k2, k3, k4 = st.columns(4)
            with k1:
                fig_gasto = go.Figure(go.Indicator(mode="number+delta", value=tg_mes, number={'prefix':'$','font':{'size':36}}, delta={'reference':tg_ant, 'relative':True, 'font':{'size':18}}, title={'text':'Gasto Mes Actual','font':{'size':14}}))
                fig_gasto.update_layout(height=150, margin=dict(t=30,b=0,l=30,r=30), paper_bgcolor='rgba(0,0,0,0)', font={'color':'#f8f8f2'})
                st.plotly_chart(fig_gasto, width="stretch")
            with k2:
                fig_litros = go.Figure(go.Indicator(mode="number+delta", value=tl_mes, number={'font':{'size':36},'suffix':' L'}, delta={'reference':tl_ant, 'relative':True, 'font':{'size':18}}, title={'text':'Litros Consumidos','font':{'size':14}}))
                fig_litros.update_layout(height=150, margin=dict(t=30,b=0,l=30,r=30), paper_bgcolor='rgba(0,0,0,0)', font={'color':'#f8f8f2'})
                st.plotly_chart(fig_litros, use_container_width=True)
            with k3:
                fig_rend = go.Figure(go.Indicator(mode="number+delta", value=ar if not pd.isna(ar) else 0, number={'font':{'size':36},'suffix':' km/l'}, title={'text':'Rendimiento Promedio','font':{'size':14}}))
                fig_rend.update_layout(height=150, margin=dict(t=30,b=0,l=30,r=30), paper_bgcolor='rgba(0,0,0,0)', font={'color':'#00ff88' if not pd.isna(ar) and ar > 0 else '#ff5555'})
                st.plotly_chart(fig_rend, use_container_width=True)
            with k4:
                color_anom = '#ff5555' if anomalias_count > 0 else '#00ff88'
                fig_anom = go.Figure(go.Indicator(mode="number", value=anomalias_count, number={'font':{'size':36,'color':color_anom}}, title={'text':'Anomalías IA Detectadas','font':{'size':14}}))
                fig_anom.update_layout(height=150, margin=dict(t=30,b=0,l=30,r=30), paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_anom, use_container_width=True)

            st.markdown('---')

                        # ━━ PREDICCIÓN IA Y RANKINGS ━━
            pr = predecir_gasto(ff)
            r1, r2 = st.columns([1, 1])
            with r1:
                if pr:
                    st.markdown('#### 🤖 IA — Predicción de Gasto Siguiente Mes')
                    try:
                        lm = ff.groupby(ff['fdt'].dt.to_period('M'))['custo'].sum().iloc[-1]
                        fg = go.Figure(go.Indicator(mode='gauge+number+delta', value=pr, number={'prefix':'$','font':{'size':28}}, delta={'reference':lm,'font':{'size':16}}, gauge={'axis':{'range':[None,pr*1.5]},'bar':{'color':'#00ff88'},'steps':[{'range':[0,lm],'color':'rgba(0,255,136,0.1)'},{'range':[lm,pr*1.5],'color':'rgba(255,85,85,0.1)'}]}))
                        fg.update_layout(template='plotly_dark', height=220, font={'family':'Inter','color':'#f8f8f2'}, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                        st.plotly_chart(fg, use_container_width=True)
                    except: pass
                else:
                    st.info('ℹ️ Se necesitan más datos para la predicción IA.')
            with r2:
                st.markdown('#### 🏆 Ranking de Flotilla (Mes Actual)')
                rend_mes = ff_mes[ff_mes['rendimento'] > 0].groupby('vehiculo')['rendimento'].mean().sort_values(ascending=False)
                if not rend_mes.empty:
                    top5 = rend_mes.head(5)
                    worst5 = rend_mes.tail(5)
                    c_top, c_worst = st.columns(2)
                    with c_top:
                        st.markdown('<div style="font-size:0.85rem;color:#00ff88;font-weight:700;">🥇 TOP Eficientes</div>', unsafe_allow_html=True)
                        for i, (veh, ren) in enumerate(top5.items()):
                            st.markdown(f'<div style="font-size:0.8rem;color:#f8f8f2;">{i+1}. {veh} <span style="color:#8be9fd;">({ren:.2f} km/l)</span></div>', unsafe_allow_html=True)
                    with c_worst:
                        st.markdown('<div style="font-size:0.85rem;color:#ff5555;font-weight:700;">⚠️ PEOR Rendimiento</div>', unsafe_allow_html=True)
                        for i, (veh, ren) in enumerate(worst5.items()):
                            st.markdown(f'<div style="font-size:0.8rem;color:#f8f8f2;">{i+1}. {veh} <span style="color:#ff7979;">({ren:.2f} km/l)</span></div>', unsafe_allow_html=True)
                else:
                    st.info('Sin datos de rendimiento este mes.')

            st.markdown('---')
            presup_df = get_presupuestos(active_tid)
            if not presup_df.empty:
                for _, pra in presup_df.iterrows():
                    pcat = pra['categoria']; plim = pra['limite_mensual']; ptip = pra['tipo']
                    if ptip == 'vehiculo':
                        ppla = pcat.split('—')[0].strip().replace('🚛','').strip() if '—' in pcat else pcat
                        pgasto = ff_mes[ff_mes['vehiculo'].str.upper().str.contains(ppla.upper(), na=False)]['custo'].sum()
                    else:
                        pgasto = ff_mes[ff_mes['estacion'] == pcat]['custo'].sum()
                    ppct = (pgasto / plim * 100) if plim > 0 else 0
                    if ppct >= 80:
                        st.warning('⚠️ Presupuesto al ' + str(int(ppct)) + '%: ' + pcat + ' ($' + '{:,.2f}'.format(pgasto) + ' / $' + '{:,.2f}'.format(plim) + ')')

            # ━━ GRÁFICAS ━━
            g1,g2,g3 = st.columns(3)
            with g1:
                dr = ff[ff['rendimento'] > 0]
                if not dr.empty:
                    fig_r = px.line(dr, x='fecha', y='rendimento', color='vehiculo', markers=True, color_discrete_sequence=CC, title='⚡ Tendencia Rendimiento')
                    fig_r.update_layout(template='plotly_dark', font={'family':'Inter'}, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_r, use_container_width=True)
            with g2:
                dm = ff.groupby(ff['fdt'].dt.to_period('M')).agg(Gasto=('custo','sum')).reset_index()
                dm['fs'] = dm['fdt'].astype(str)
                if not dm.empty:
                    fig_m = px.bar(dm, x='fs', y='Gasto', text_auto=True, color_discrete_sequence=['#00ff88'], title='💰 Gasto Mensual Histórico')
                    fig_m.update_layout(template='plotly_dark', showlegend=False, font={'family':'Inter'}, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_m, use_container_width=True)
            with g3:
                de = ff.groupby('estacion')['custo'].sum().reset_index()
                if not de.empty:
                    fig_e = px.pie(de, values='custo', names='estacion', hole=0.4, color_discrete_sequence=CC, title='📍 Distribución Estaciones')
                    fig_e.update_layout(template='plotly_dark', font={'family':'Inter'}, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_e, use_container_width=True)
        else:
            st.info('📭 Sin datos disponibles — Registra tu primera carga')
# ━━━ CARGA ━━━
with tabs[1] if is_admin else tabs[0]:
    section_header('⛽', 'Registrar Carga', 'Captura una nueva carga de combustible')
    estaciones_df = get_all_estaciones(active_tid)
    est_options = {}
    if not estaciones_df.empty:
        for _, er in estaciones_df.iterrows():
            est_options[er['nombre']] = {'lat': er.get('latitud', 0), 'lon': er.get('longitud', 0)}
    try:
        import folium
        from streamlit_folium import st_folium
        with st.expander('🗺️ Seleccionar ubicación en el mapa (haz clic)'):
            mc_lat = st.session_state.get('click_lat', 19.4326)
            mc_lon = st.session_state.get('click_lon', -99.1332)
            fmap = folium.Map(location=[mc_lat, mc_lon], zoom_start=13)
            if st.session_state.get('click_lat', 0) != 0:
                folium.Marker([st.session_state['click_lat'], st.session_state['click_lon']], tooltip='Ubicacion seleccionada', icon=folium.Icon(color='green', icon='map-marker', prefix='fa')).add_to(fmap)
            if not estaciones_df.empty:
                for _, er in estaciones_df.iterrows():
                    if er.get('latitud', 0) != 0:
                        folium.Marker([er['latitud'], er['longitud']], popup=er['nombre'], icon=folium.Icon(color='blue', icon='gas-pump', prefix='fa')).add_to(fmap)
            clicked = st_folium(fmap, width=700, height=400, key='gps_select')
            if clicked and clicked.get('last_clicked'):
                st.session_state['click_lat'] = round(clicked['last_clicked']['lat'], 8)
                st.session_state['click_lon'] = round(clicked['last_clicked']['lng'], 8)
                st.rerun()
            clat = st.session_state.get('click_lat', 0.0)
            clon = st.session_state.get('click_lon', 0.0)
            if clat != 0: st.success('Lat: ' + str(clat) + ' | Lon: ' + str(clon))
            if st.button('Borrar ubicacion', key='clear_gps'):
                st.session_state.pop('click_lat', None)
                st.session_state.pop('click_lon', None)
                st.rerun()
    except:
        pass
    with st.form('fc'):
        c1,c2,c3 = st.columns(3)
        with c1:
            fe = st.date_input('📅 Fecha', datetime.today())
            veh_opts = veh_select_options(active_tid)
            if veh_opts:
                sel_ve = st.selectbox('🚗 Vehículo', list(veh_opts.keys()))
                ve = veh_opts[sel_ve]
            else:
                ve = st.text_input('🚗 Vehículo (placa)')
            cond_df = get_all_conductores(active_tid)
            cond_activos = cond_df[cond_df['estatus'] == 'Activo'] if not cond_df.empty else cond_df
            if not cond_activos.empty:
                co = st.selectbox('👤 Conductor', [''] + cond_activos['nombre'].tolist())
            else:
                co = st.text_input('👤 Conductor')
            tb = st.selectbox('⛽ Tipo', TIPO_COMB_OPTIONS)
            km = st.number_input('📏 Kilometraje', min_value=0.0, step=1.0)
        with c2:
            li = st.number_input('🛢️ Litros', min_value=0.0, step=0.1)
            cu = st.number_input('💰 Costo', min_value=0.0, step=0.01)
            fa = st.text_input('🧾 Factura')
            if est_options:
                sel_est = st.selectbox('📍 Estación', [''] + list(est_options.keys()))
            else:
                sel_est = st.text_input('📍 Estación')
            va = st.text_input('🎫 Vale')
        with c3:
            if est_options and sel_est and sel_est in est_options:
                def_lat = est_options[sel_est]['lat'] if est_options[sel_est]['lat'] != 0 else st.session_state.get('click_lat', 0.0)
                def_lon = est_options[sel_est]['lon'] if est_options[sel_est]['lon'] != 0 else st.session_state.get('click_lon', 0.0)
            else:
                def_lat = st.session_state.get('click_lat', 0.0)
                def_lon = st.session_state.get('click_lon', 0.0)
            lat = st.number_input('🌐 Latitud', value=def_lat, step=0.00000001, format='%.8f')
            lon = st.number_input('🌐 Longitud', value=def_lon, step=0.00000001, format='%.8f')
            st.caption('💡 Selecciona estación o haz clic en el mapa')
        if st.form_submit_button('💾 GUARDAR CARGA'):
            dup = False
            if fa and check_duplicate('factura', fa, active_tid): st.error('❌ Factura ya existe'); dup = True
            if va and check_duplicate('vale', va, active_tid): st.error('❌ Vale ya existe'); dup = True
            if not dup:
                if not ve or li == 0 or cu == 0: st.error('❌ Datos incompletos')
                else:
                    r, ck, aa, am = evaluar_vehiculo(ve, km, li, cu, tenant_id=active_tid)
                    try:
                        dv_temp = get_all_vehiculos(active_tid)
                        v_info = dv_temp[dv_temp['placa'] == ve.upper()]
                        if not v_info.empty and v_info.iloc[0].get('rendimiento_min', 0) > 0:
                            rmin = v_info.iloc[0]['rendimiento_min']
                            if r > 0 and r < rmin: aa = 'ANOMALIA'
                    except: pass
                    est_name = sel_est if sel_est else ''
                    datos = (str(fe), ve.upper(), co, tb, km, li, cu, fa, est_name, va, r, ck, aa, am, lat, lon)
                    insert_carga(datos, nm, active_tid)
                    if aa == 'ANOMALIA' and EMAIL_ENABLED:
                        try:
                            ns = get_notification_settings(active_tid)
                            na = ns[ns['tipo'] == 'anomalia']
                            if not na.empty and na.iloc[0].get('activo', 0):
                                edest = na.iloc[0].get('email', '') or ALERT_EMAIL
                                if edest:
                                    enviar_alerta_email(ve.upper(), 'ANOMALIA', f'Rendimiento {r} km/l bajo de lo esperado', costo=cu, rendimiento=r)
                        except: pass
                    if EMAIL_ENABLED:
                        try:
                            dv_chk = get_all_vehiculos(active_tid)
                            vi = dv_chk[dv_chk['placa'] == ve.upper()]
                            if not vi.empty:
                                vrow_n = vi.iloc[0]
                                kmin = vrow_n.get('km_proximo_servicio', 0)
                                if kmin and kmin > 0 and km >= kmin:
                                    ns2 = get_notification_settings(active_tid)
                                    nm2 = ns2[ns2['tipo'] == 'mantenimiento']
                                    if not nm2.empty and nm2.iloc[0].get('activo', 0):
                                        edest2 = nm2.iloc[0].get('email', '') or ALERT_EMAIL
                                        if edest2:
                                            enviar_alerta_mantenimiento(ve.upper(), km, kmin, vrow_n.get('tipo_servicio', ''), email_dest=edest2)
                        except: pass
                    st.session_state.pop('click_lat', None)
                    st.session_state.pop('click_lon', None)
                    clear_all_cache(); st.toast('✅ Carga guardada!'); st.rerun()

# ━━━ EDITAR ━━━
with tabs[2] if is_admin else tabs[1]:
    section_header('✏️', 'Editar / Eliminar', 'Modifica o elimina registros existentes')
    df = get_data(active_tid)
    if not df.empty:
        df['Op'] = df['id'].astype(str) + ' | ' + df['vehiculo'] + ' | ' + df['fecha']
        sid = int(st.selectbox('🔍 Seleccionar:', df['Op'].tolist(), key='es').split(' | ')[0])
        ca = df[df['id'] == sid].iloc[0]
        with st.form('fe'):
            c1,c2 = st.columns(2)
            with c1:
                ef = st.date_input('📅 Fecha', pd.to_datetime(ca['fecha'], format='mixed'))
                ev = st.text_input('🚗 Vehículo', ca['vehiculo'] or '')
                ec = st.text_input('👤 Conductor', ca['conductor'] or '')
                et = st.selectbox('⛽ Tipo', TIPO_COMB_OPTIONS)
                ek = st.number_input('📏 Km', value=float(ca['kilometraje'] or 0), step=1.0)
            with c2:
                el = st.number_input('🛢️ Litros', value=float(ca['litros'] or 0), step=0.1)
                eu = st.number_input('💰 Costo', value=float(ca['custo'] or 0), step=0.01)
                ef2 = st.text_input('🧾 Factura', ca['factura'] or '')
                ee = st.text_input('📍 Estación', ca['estacion'] or '')
            b1,b2 = st.columns(2)
            with b1: bu = st.form_submit_button('✅ ACTUALIZAR')
            with b2: bd = st.form_submit_button('🗑️ ELIMINAR')
            if bu:
                delete_carga(sid, nm)
                r,ck,aa,am = evaluar_vehiculo(ev,ek,el,eu, exclude_id=sid, tenant_id=active_tid)
                datos = (str(ef), ev.upper(), ec, et, ek, el, eu, ef2, ee, '', r, ck, aa, am, 0, 0)
                insert_carga(datos, nm, active_tid)
                clear_all_cache(); st.toast('✅ Actualizada'); st.rerun()
            if bd:
                delete_carga(sid, nm)
                clear_all_cache(); st.toast('🗑️ Eliminada'); st.rerun()

# ━━━ INFORMES ━━━
if is_admin:
    with tabs[3]:
        section_header('📋', 'Informes', 'Exporta reportes detallados')
        df = get_data(active_tid)
        if not df.empty:
            show_aggrid(df)
            d1,d2 = st.columns(2)
            with d1: st.download_button('📊 Descargar EXCEL', generar_excel(df, 'Reporte', active_tid), 'Reporte.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            with d2: st.download_button('📄 Descargar PDF', generar_pdf(df, 'Reporte', active_tid), 'Reporte.pdf', mime='application/pdf')

    with tabs[4]:
        section_header('🚨', 'Alertas IA', 'Anomalías detectadas por inteligencia artificial')
        df = get_data(active_tid)
        da = df[df['alerta_anomalia'].isin(['ANOMALIA', 'ANOMALIA_AI'])]
        if da.empty:
            st.markdown('<div style="background:rgba(0,255,136,0.1);border:1px solid rgba(0,255,136,0.3);border-radius:14px;padding:20px;text-align:center;color:#00ff88;font-weight:600;">✅ Sin anomalías detectadas</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="background:rgba(255,85,85,0.1);border:1px solid rgba(255,85,85,0.3);border-radius:14px;padding:15px;text-align:center;color:#ff5555;font-weight:600;margin-bottom:15px;">⚠️ {len(da)} anomalía(s) detectada(s)</div>', unsafe_allow_html=True)
            show_aggrid(da)

    with tabs[5]:
        section_header('🚛', 'Flotilla', 'Gestión de vehículos y mantenimiento')
        with st.form('fv'):
            c1,c2,c3 = st.columns(3)
            with c1: vp = st.text_input('🚗 Placa').upper(); vm = st.text_input('🏷️ Marca')
            with c2: vmod = st.text_input('🚘 Modelo'); vtcomb = st.selectbox('⛽ Combustible', TIPO_COMB_OPTIONS)
            with c3: vdepto = st.text_input('🏢 Departamento'); vc = st.number_input('🛢️ Capacidad (L)', min_value=0.0, step=10.0)
            c4,c5,c6 = st.columns(3)
            with c4: vk = st.number_input('📏 Km Inicial', min_value=0.0, step=1.0); vr = st.number_input('⚡ Rend. Mínimo', min_value=0.0, step=0.5, value=0.0)
            with c5: vkm = st.number_input('🔧 Próx. Servicio (km)', min_value=0.0, step=1000.0, value=0.0); vpol = st.text_input('🛡️ Póliza Seguro')
            with c6: vtel = st.text_input('📞 Tel. Operador')
            if st.form_submit_button('💾 GUARDAR VEHÍCULO'):
                if vp:
                    if insert_vehiculo((vp,vm,vmod,vtcomb,vdepto,vc,vk,vr,vkm,0,'','',vpol,vtel), nm, active_tid):
                        clear_all_cache(); st.toast('✅ Vehículo agregado!'); st.rerun()
                    else: st.toast('⚠️ Ya existe!')
        dv = get_all_vehiculos(active_tid)
        if not dv.empty: show_aggrid(dv)
        st.markdown('---')
        section_header('✏️', 'Editar / Eliminar Vehículo', 'Modifica o elimina unidades de la flotilla')
        if not dv.empty:
            veh_edit_opts = {}
            for _, r in dv.iterrows():
                marca = r.get('marca', '') or ''; modelo = r.get('modelo', '') or ''
                desc = f"{marca} {modelo}".strip()
                label = f"🚛 {r['placa']}  —  {desc}" if desc else f"🚛 {r['placa']}"
                veh_edit_opts[label] = r['placa']
            sel_veh_edit = st.selectbox('🔍 Seleccionar vehículo:', list(veh_edit_opts.keys()), key='veh_edit_sel')
            edit_placa = veh_edit_opts[sel_veh_edit]
            vrow = dv[dv['placa'] == edit_placa].iloc[0]
            with st.form('fve'):
                c1,c2,c3 = st.columns(3)
                with c1:
                    st.markdown(f'<div style="font-size:0.8rem;color:#9ca3af;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;">🚗 PLACA</div><div style="font-size:1.1rem;font-weight:700;color:#00ff88;margin-bottom:16px;">{edit_placa}</div>', unsafe_allow_html=True)
                    ev_marca = st.text_input('🏷️ Marca', vrow.get('marca', '') or '', key='ev_marca')
                with c2:
                    ev_modelo = st.text_input('🚘 Modelo', vrow.get('modelo', '') or '', key='ev_modelo')
                    ev_comb_idx = 0
                    try: ev_comb_idx = list(TIPO_COMB_OPTIONS).index(vrow.get('tipo_combustible', 'Diesel'))
                    except: pass
                    ev_comb = st.selectbox('⛽ Combustible', TIPO_COMB_OPTIONS, index=ev_comb_idx, key='ev_comb')
                with c3:
                    ev_depto = st.text_input('🏢 Departamento', vrow.get('departamento', '') or '', key='ev_depto')
                    ev_cap = st.number_input('🛢️ Capacidad (L)', value=float(vrow.get('capacidade', 0) or 0), step=10.0, key='ev_cap')
                c4,c5,c6 = st.columns(3)
                with c4:
                    ev_km = st.number_input('📏 Km Inicial', value=float(vrow.get('km_inicial', 0) or 0), step=1.0, key='ev_km')
                    ev_rend = st.number_input('⚡ Rend. Mínimo', value=float(vrow.get('rendimiento_min', 0) or 0), step=0.5, key='ev_rend')
                with c5:
                    ev_prox = st.number_input('🔧 Próx. Servicio (km)', value=float(vrow.get('km_proximo_servicio', 0) or 0), step=1000.0, key='ev_prox')
                    ev_pol = st.text_input('🛡️ Póliza Seguro', vrow.get('poliza_seguro', '') or '', key='ev_pol')
                with c6:
                    ev_tel = st.text_input('📞 Tel. Operador', vrow.get('tel_operador', '') or '', key='ev_tel')
                    ev_int = st.number_input('🔄 Intervalo (km)', value=float(vrow.get('intervalo_km_servicio', 0) or 0), step=1000.0, key='ev_int')
                
                # ━━ NUEVOS CAMPOS: PAPELES VENCIDOS ━━
                st.markdown('---')
                st.markdown('**📄 Fechas de Vencimiento (Alertas Automáticas)**')
                c7,c8,c9 = st.columns(3)
                with c7:
                    ev_seg_val = vrow.get('vencimiento_seguro', '') or '2099-12-31'
                    ev_seg = st.date_input('🛡️ Venc. Seguro', value=pd.to_datetime(ev_seg_val, errors='coerce') or datetime(2099,12,31), key='ev_seg')
                with c8:
                    ev_ver_val = vrow.get('vencimiento_verificacion', '') or '2099-12-31'
                    ev_ver = st.date_input('📄 Venc. Verificación', value=pd.to_datetime(ev_ver_val, errors='coerce') or datetime(2099,12,31), key='ev_ver')
                with c9:
                    ev_tar_val = vrow.get('vencimiento_tarjeton', '') or '2099-12-31'
                    ev_tar = st.date_input('📋 Venc. Tarjetón', value=pd.to_datetime(ev_tar_val, errors='coerce') or datetime(2099,12,31), key='ev_tar')

                b1, b2 = st.columns(2)
                with b1: bupd = st.form_submit_button('✅ ACTUALIZAR VEHÍCULO')
                with b2: bdel = st.form_submit_button('🗑️ ELIMINAR VEHÍCULO')
                if bupd:
                    update_vehiculo(edit_placa, tenant_id=active_tid, marca=ev_marca, modelo=ev_modelo, tipo_combustible=ev_comb, departamento=ev_depto, capacidad=ev_cap, km_inicial=ev_km, rendimiento_min=ev_rend, km_proximo_servicio=ev_prox, poliza=ev_pol, tel_operador=ev_tel, intervalo_km_servicio=ev_int, vencimiento_seguro=str(ev_seg), vencimiento_verificacion=str(ev_ver), vencimiento_tarjeton=str(ev_tar))
                    clear_all_cache(); st.toast('✅ Vehículo actualizado!'); st.rerun()
                if bdel:
                    delete_vehiculo(edit_placa, tenant_id=active_tid)
                    clear_all_cache(); st.toast('🗑️ Vehículo eliminado!'); st.rerun()
        else:
            st.info('📭 No hay vehículos registrados')

        # ━━━ CONDUCTORES ━━━
    with tabs[6]:
        section_header('👤', 'Conductores', 'Gestión de conductores y asignación de vehículos')
        with st.form('f_cond'):
            cc1,cc2,cc3 = st.columns(3)
            with cc1: cnombre = st.text_input('👤 Nombre*')
            with cc2: clicencia = st.text_input('🪪 Licencia')
            with cc3: cvigencia = st.text_input('📅 Vigencia Licencia')
            cc4,cc5,cc6 = st.columns(3)
            with cc4: ctelefono = st.text_input('📞 Teléfono')
            with cc5:
                vasig_opts = veh_select_options(active_tid)
                if vasig_opts: cveh = st.selectbox('🚗 Vehículo Asignado', [''] + list(vasig_opts.keys()))
                else: cveh = st.text_input('🚗 Vehículo Asignado')
            with cc6: cestatus = st.selectbox('📌 Estatus', ['Activo','Inactivo','Vacaciones','Baja'])
            if st.form_submit_button('💾 GUARDAR CONDUCTOR'):
                if cnombre:
                    nid = insert_conductor(cnombre, clicencia, cvigencia, ctelefono, cveh, cestatus, active_tid)
                    if nid: clear_all_cache(); st.toast('✅ Conductor guardado!'); st.rerun()
                    else: st.error('❌ Error al guardar')
                else: st.error('❌ Nombre requerido')
        cdf = get_all_conductores(active_tid)
        if not cdf.empty:
            show_aggrid(cdf)
            st.markdown('---')
            
            # ━━ EDITAR CONDUCTOR ━━
            section_header('✏️', 'Editar Conductor', 'Modifica los datos de un conductor existente')
            edit_cond_opts = {}
            for _, r in cdf.iterrows():
                veh = r.get('vehiculo_asignado', '') or ''
                estatus_icon = '🟢' if r.get('estatus') == 'Activo' else '🔴'
                label = f"{estatus_icon} {r['nombre']} — {veh}" if veh else f"{estatus_icon} {r['nombre']}"
                edit_cond_opts[label] = r['id']
            
            sel_edit_cond = st.selectbox('🔍 Seleccionar conductor a editar:', list(edit_cond_opts.keys()), key='edit_cond_sel')
            edit_cond_id = edit_cond_opts[sel_edit_cond]
            edit_cond_row = cdf[cdf['id'] == edit_cond_id].iloc[0]
            
            with st.form('f_edit_cond'):
                ec1, ec2, ec3 = st.columns(3)
                with ec1:
                    st.markdown(f'<div style="font-size:0.8rem;color:#9ca3af;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;">👤 NOMBRE ACTUAL</div><div style="font-size:1.1rem;font-weight:700;color:#00ff88;margin-bottom:16px;">{edit_cond_row["nombre"]}</div>', unsafe_allow_html=True)
                    e_cnombre = st.text_input('📝 Nuevo nombre', value=edit_cond_row['nombre'], key='ec_nombre')
                with ec2:
                    e_clicencia = st.text_input('🪪 Licencia', value=edit_cond_row.get('licencia', '') or '', key='ec_licencia')
                    e_cvigencia = st.text_input('📅 Vigencia Licencia', value=edit_cond_row.get('vigencia_lic', '') or '', key='ec_vigencia')
                with ec3:
                    e_ctelefono = st.text_input('📞 Teléfono', value=edit_cond_row.get('telefono', '') or '', key='ec_telefono')
                    # Vehículo asignado
                    current_veh = edit_cond_row.get('vehiculo_asignado', '') or ''
                    evasig_opts = veh_select_options(active_tid)
                    if evasig_opts:
                        # Crear lista con opción vacía + vehículos + el actual si no está en la lista
                        veh_keys = ['(Sin asignar)'] + list(evasig_opts.keys())
                        try:
                            current_idx = 0
                            for k, v in evasig_opts.items():
                                if v == current_veh:
                                    current_idx = veh_keys.index(k)
                                    break
                            e_cveh_label = st.selectbox('🚗 Vehículo Asignado', veh_keys, index=current_idx, key='ec_veh')
                            e_cveh = evasig_opts.get(e_cveh_label, '') if e_cveh_label != '(Sin asignar)' else ''
                        except:
                            e_cveh = st.text_input('🚗 Vehículo Asignado', value=current_veh, key='ec_veh_text')
                    else:
                        e_cveh = st.text_input('🚗 Vehículo Asignado', value=current_veh, key='ec_veh_text2')
                
                # Estatus (segunda fila)
                ec4, ec5 = st.columns(2)
                with ec4:
                    current_estatus = edit_cond_row.get('estatus', 'Activo') or 'Activo'
                    estatus_list = ['Activo','Inactivo','Vacaciones','Baja']
                    try:
                        estatus_idx = estatus_list.index(current_estatus)
                    except:
                        estatus_idx = 0
                    e_cestatus = st.selectbox('📌 Estatus', estatus_list, index=estatus_idx, key='ec_estatus')
                with ec5:
                    st.markdown(f'<div style="font-size:0.8rem;color:#9ca3af;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;">🆔 ID</div><div style="font-size:1.1rem;font-weight:700;color:#bd93f9;margin-bottom:16px;">{edit_cond_id}</div>', unsafe_allow_html=True)
                
                # Botones
                b1, b2 = st.columns(2)
                with b1: bupd_cond = st.form_submit_button('✅ ACTUALIZAR CONDUCTOR', use_container_width=True)
                with b2: bdel_cond = st.form_submit_button('🗑️ ELIMINAR CONDUCTOR', use_container_width=True)
                
                if bupd_cond:
                    if e_cnombre:
                        from db import update_conductor
                        if update_conductor(edit_cond_id, tenant_id=active_tid,
                                            nombre=e_cnombre, licencia=e_clicencia,
                                            vigencia_lic=e_cvigencia, telefono=e_ctelefono,
                                            vehiculo_asignado=e_cveh, estatus=e_cestatus):
                            clear_all_cache(); st.toast('✅ Conductor actualizado!'); st.rerun()
                        else:
                            st.error('❌ Error al actualizar')
                    else:
                        st.error('❌ El nombre es obligatorio')
                
                if bdel_cond:
                    delete_conductor(edit_cond_id, active_tid)
                    clear_all_cache(); st.toast('🗑️ Conductor eliminado!'); st.rerun()
        else:
            st.info('📭 No hay conductores registrados. Crea uno con el formulario de arriba.')

    # ━━━ PRESUPUESTO ━━━
    with tabs[7]:
        section_header('💰', 'Presupuesto', 'Límites de gasto mensual por vehículo y departamento')
        presup_d = get_presupuestos(active_tid)
        with st.form('f_presup'):
            pc1,pc2,pc3 = st.columns(3)
            with pc1: ptipo = st.selectbox('📌 Tipo', ['vehiculo', 'departamento'])
            with pc2:
                if ptipo == 'vehiculo':
                    vopts = veh_select_options(active_tid)
                    pcategoria = st.selectbox('🚗 Vehículo', list(vopts.keys()) if vopts else [''])
                else:
                    df_data = get_data(active_tid)
                    depts = sorted(df_data['estacion'].dropna().unique().tolist()) if not df_data.empty else ['']
                    pcategoria = st.selectbox('🏢 Departamento/Estación', depts)
            with pc3: plimite = st.number_input('💵 Límite mensual ($)', min_value=0.0, step=100.0)
            if st.form_submit_button('💾 GUARDAR PRESUPUESTO'):
                if pcategoria and plimite > 0:
                    set_presupuesto(pcategoria, plimite, ptipo, active_tid)
                    clear_all_cache(); st.toast('✅ Presupuesto guardado!'); st.rerun()
                else: st.error('❌ Datos incompletos')
        if not presup_d.empty:
            st.markdown('#### Presupuestos configurados')
            show_aggrid(presup_d)
        st.markdown('---')
        st.markdown('#### Estado actual del mes')
        df_mes = get_data(active_tid)
        if not presup_d.empty and not df_mes.empty:
            now = datetime.now()
            df_mes['fdt'] = pd.to_datetime(df_mes['fecha'], format='mixed')
            df_mes = df_mes[(df_mes['fdt'].dt.month == now.month) & (df_mes['fdt'].dt.year == now.year)]
            for _, pr in presup_d.iterrows():
                cat = pr['categoria']; lim = pr['limite_mensual']; tip = pr['tipo']
                if tip == 'vehiculo':
                    placa = cat.split('—')[0].strip().replace('🚛','').strip() if '—' in cat else cat
                    gasto = df_mes[df_mes['vehiculo'].str.upper().str.contains(placa.upper(), na=False)]['custo'].sum()
                else:
                    gasto = df_mes[df_mes['estacion'] == cat]['custo'].sum()
                pct = (gasto / lim * 100) if lim > 0 else 0
                color = '#ff5555' if pct >= 100 else '#f1fa8c' if pct >= 80 else '#00ff88'
                icon = '🔴' if pct >= 100 else '🟡' if pct >= 80 else '🟢'
                st.markdown(f'<div style="background:rgba(20,20,35,0.8);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:12px;margin-bottom:8px;"><b>{icon} {cat}</b> — ${gasto:,.2f} / ${lim:,.2f} <span style="color:{color};font-weight:700;">({pct:.1f}%)</span></div>', unsafe_allow_html=True)

# ━━━ CARGA MASIVA ━━━
with tabs[8] if is_admin else tabs[2]:
    section_header('📥', 'Carga Masiva', 'Importa múltiples registros desde Excel o CSV')
    st.download_button('📥 DESCARGAR PLANTILLA', generar_plantilla(), 'Plantilla.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    uf = st.file_uploader('📂 Selecciona archivo', type=['xlsx','xls','csv'])
    if uf is not None:
        try:
            du = pd.read_excel(uf) if 'xls' in uf.name else pd.read_csv(uf)
            st.markdown(f'<div style="font-size:1rem;color:#8be9fd;font-weight:600;">📄 {len(du)} registros encontrados</div>', unsafe_allow_html=True)
            if st.button('⚡ PROCESAR'):
                pb = st.progress(0); ins = 0
                for idx, row in du.iterrows():
                    try:
                        ct = clean_tipo(row.get('tipo_combustible', 'Diesel'))
                        datos = (str(pd.to_datetime(str(row['fecha']),format='mixed').date()), str(row['vehiculo']).upper().strip(), str(row.get('conductor','')).strip(), ct, float(row.get('kilometraje',0) or 0), float(row.get('litros',0) or 0), float(row.get('custo',0) or 0), str(row.get('factura','')).strip(), str(row.get('estacion','')).strip(), str(row.get('vale','')).strip(), 0.0, 0.0, 'Normal', 'OK', 0, 0)
                        insert_carga(datos, nm, active_tid)
                        ins += 1
                    except Exception as e: st.warning('⚠️ Error fila ' + str(idx+2) + ': ' + str(e))
                    pb.progress((idx + 1) / len(du))
                clear_all_cache(); st.toast(f'✅ {ins} registros insertados!'); st.rerun()
        except Exception as e: st.error('❌ Error: ' + str(e))

# ━━━ MAPA GPS ━━━
if is_admin:
    with tabs[9]:
        section_header('🗺️', 'Mapa GPS', 'Ubicación de cargas con coordenadas')
        df = get_data(active_tid)
        if not df.empty:
            gps = df[(df['latitud'].notna()) & (df['longitud'].notna()) & (df['latitud'] != 0) & (df['longitud'] != 0)].copy()
            if gps.empty: st.info('📭 Sin coordenadas GPS registradas')
            else:
                try:
                    import folium
                    from streamlit_folium import st_folium
                    clat = float(gps['latitud'].mean()); clon = float(gps['longitud'].mean())
                    fmap = folium.Map(location=[clat, clon], zoom_start=12)
                    for _, rw in gps.iterrows():
                        ptitle = str(rw.get('vehiculo','')) + ' | ' + str(rw.get('fecha','')) + ' | $' + '{:,.2f}'.format(rw.get('custo',0))
                        al = str(rw.get('alerta_anomalia',''))
                        clr = 'red' if al == 'ANOMALIA' else 'green'
                        folium.Marker([float(rw['latitud']), float(rw['longitud'])], popup=ptitle, icon=folium.Icon(color=clr, icon='gas-pump', prefix='fa')).add_to(fmap)
                    st_folium(fmap, width=900, height=500)
                except Exception as ex:
                    st.warning('⚠️ Instala: pip install folium streamlit-folium')
                    try: st.map(gps.rename(columns={'latitud':'lat','longitud':'lon'})[['lat','lon']])
                    except: pass

    with tabs[10]:
        section_header('⚙️', 'Configuración', 'Datos de tu empresa')
        cfg = load_config(active_tid)
        with st.form('fc_company'):
            c1,c2 = st.columns(2)
            with c1:
                e_nombre = st.text_input('🏢 Empresa', cfg.get('empresa',''))
                e_rfc = st.text_input('📄 RFC', cfg.get('rfc',''))
            with c2:
                e_telefono = st.text_input('📞 Teléfono', cfg.get('telefono',''))
                e_email = st.text_input('📧 Email', cfg.get('email',''))
            if st.form_submit_button('💾 GUARDAR'):
                cfg.update({'empresa':e_nombre,'rfc':e_rfc,'telefono':e_telefono,'email':e_email})
                save_config(cfg, active_tid)
                clear_all_cache(); st.toast('✅ Configuración guardada!')
        logo_bytes = get_logo_bytes(active_tid)
        if logo_bytes: st.image(io.BytesIO(logo_bytes), width=150)
        logo_file = st.file_uploader('🖼️ Subir logo', type=['png','jpg','jpeg'], key='logo_up')
        if logo_file:
            cfg['logo_b64'] = base64.b64encode(logo_file.read()).decode()
            save_config(cfg, active_tid)
            clear_all_cache(); st.toast('✅ Logo guardado!'); st.rerun()
        # Estaciones
        st.markdown('---')
        section_header('⛽', 'Estaciones de Servicio', 'Registra estaciones para seleccionarlas al cargar combustible')
        with st.form('f_est'):
            ec1,ec2,ec3 = st.columns(3)
            with ec1: enombre = st.text_input('📛 Nombre*')
            with ec2: edir = st.text_input('📍 Dirección')
            with ec3: emarca = st.selectbox('🏷️ Marca', ['Pemex','BP','Shell','G500','Otro',''])
            ec4,ec5 = st.columns(2)
            with ec4: elat = st.number_input('🌐 Latitud', value=st.session_state.get('click_lat', 0.0), step=0.00000001, format='%.8f')
            with ec5: elon = st.number_input('🌐 Longitud', value=st.session_state.get('click_lon', 0.0), step=0.00000001, format='%.8f')
            st.caption('💡 Usa el mapa en la pestaña Carga para obtener coordenadas')
            if st.form_submit_button('💾 GUARDAR ESTACIÓN'):
                if enombre:
                    nid = insert_estacion(enombre, edir, emarca, elat, elon, active_tid)
                    if nid: clear_all_cache(); st.toast('✅ Estación registrada!'); st.rerun()
                    else: st.error('❌ Error al guardar')
                else: st.error('❌ Nombre requerido')
        est_list = get_all_estaciones(active_tid)
        if not est_list.empty:
            show_aggrid(est_list)
            st.markdown('---')
            del_est = st.selectbox('🗑️ Eliminar estación:', [''] + est_list['nombre'].tolist(), key='del_est')
            if del_est and st.button('Eliminar', key='btn_del_est'):
                eid = est_list[est_list['nombre'] == del_est]['id'].iloc[0]
                delete_estacion(eid, active_tid)
                clear_all_cache(); st.toast('🗑️ Estación eliminada!'); st.rerun()
        # Precios
        st.markdown('---')
        section_header('📊', 'Precios Combustible', 'Historial de precios por estación')
        with st.form('f_precio'):
            prc1,prc2,prc3,prc4 = st.columns(4)
            with prc1:
                est_d = get_all_estaciones(active_tid)
                pr_est = st.selectbox('⛽ Estación', est_d['nombre'].tolist() if not est_d.empty else [''])
            with prc2: pr_tipo = st.selectbox('🛢️ Tipo', TIPO_COMB_OPTIONS)
            with prc3: pr_precio = st.number_input('💵 Precio/L', min_value=0.0, step=0.01, format='%.2f')
            with prc4: pr_fecha = st.date_input('📅 Fecha', datetime.today())
            if st.form_submit_button('💾 GUARDAR PRECIO'):
                if pr_est and pr_precio > 0:
                    insert_precio(pr_est, pr_tipo, pr_precio, str(pr_fecha), active_tid)
                    clear_all_cache(); st.toast('✅ Precio guardado!'); st.rerun()
        prdf = get_precios(active_tid)
        if not prdf.empty:
            show_aggrid(prdf.head(50))
            try:
                prchart = prdf.copy()
                prchart['fdt'] = pd.to_datetime(prchart['fecha'], format='mixed')
                for t in prchart['tipo_combustible'].unique():
                    sub = prchart[prchart['tipo_combustible'] == t]
                    if len(sub) > 1:
                        fig_p = px.line(sub.sort_values('fdt'), x='fdt', y='precio', color='estacion', title='💲 Precio/L — ' + t, color_discrete_sequence=CC)
                        fig_p.update_layout(template='plotly_dark', font={'family':'Inter'}, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                        st.plotly_chart(fig_p, width='stretch')
            except: pass
        # Backup
        st.markdown('---')
        section_header('📦', 'Backup / Restore', 'Respalda o restaura toda la base de datos')
        bk1, bk2 = st.columns(2)
        with bk1:
            if st.button('📥 GENERAR BACKUP'):
                try:
                    conn = sqlite3.connect(DB_NAME)
                    buf_bk = io.BytesIO()
                    for line in conn.iterdump():
                        buf_bk.write((line + '\n').encode('utf-8'))
                    conn.close()
                    buf_bk.seek(0)
                    st.download_button('💾 Descargar Backup', buf_bk.getvalue(), 'cyberfuel_backup_' + datetime.now().strftime('%Y%m%d_%H%M') + '.sql', mime='text/plain')
                except Exception as e: st.error('Error: ' + str(e))
        with bk2:
            bk_file = st.file_uploader('📤 Restaurar Backup', type=['sql'])
            if bk_file and st.button('⚠️ RESTAURAR'):
                try:
                    sql_text = bk_file.read().decode('utf-8')
                    conn = sqlite3.connect(DB_NAME)
                    cur = conn.cursor()
                    cur.executescript(sql_text)
                    conn.commit(); conn.close()
                    clear_all_cache(); st.toast('✅ BD restaurada!'); st.rerun()
                except Exception as e: st.error('Error: ' + str(e))
        # Auditoría
        st.markdown('---')
        section_header('🔍', 'Auditoría', 'Registro de acciones del sistema')
        audit_df = get_audit_log(tenant_id=active_tid, limit=200)
        if not audit_df.empty: show_aggrid(audit_df, height=350)
        else: st.info('📭 Sin registros de auditoría')
        # ━━━ REPORTES AUTOMÁTICOS ━━━
        st.markdown('---')
        section_header('📬', 'Reportes Automáticos', 'Programa envíos periódicos de reportes por email')
        if not EMAIL_ENABLED:
            st.warning('⚠️ Email no configurado. Configura SMTP en variables de entorno.')
            st.write("🔍 DEBUG EMAIL_ENABLED:", EMAIL_ENABLED)
            st.write("🔍 DEBUG SMTP_SERVER:", repr(SMTP_SERVER))
            st.write("🔍 DEBUG SMTP_USER:", repr(SMTP_USER))
            st.write("🔍 DEBUG SMTP_PASSWORD:", "***" if SMTP_PASSWORD else "(vacío)")
            st.write("🔍 DEBUG ALERT_EMAIL:", repr(ALERT_EMAIL))
        else:
            scheduler_on = is_scheduler_running()
            if scheduler_on:
                st.markdown('<div style="background:rgba(0,255,136,0.1);border:1px solid rgba(0,255,136,0.3);border-radius:12px;padding:10px;text-align:center;color:#00ff88;font-weight:600;">✅ Scheduler activo — revisando cada 15 min</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div style="background:rgba(255,85,85,0.1);border:1px solid rgba(255,85,85,0.3);border-radius:12px;padding:10px;text-align:center;color:#ff5555;font-weight:600;">⏸️ Scheduler inactivo</div>', unsafe_allow_html=True)
            with st.form('f_sched'):
                sc1, sc2, sc3 = st.columns(3)
                with sc1:
                    snombre = st.text_input('📛 Nombre del reporte*')
                    sfrec = st.selectbox('📅 Frecuencia', ['diario', 'semanal', 'mensual'])
                    stipo = st.selectbox('📋 Tipo', ['completo', 'anomalias', 'flotilla', 'presupuesto'], format_func=lambda x: {'completo':'📊 Completo','anomalias':'🚨 Anomalías','flotilla':'🚛 Flotilla','presupuesto':'💰 Presupuesto'}[x])
                with sc2:
                    sdia_sem = st.selectbox('📆 Día semana', ['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo'], index=0)
                    sdia_mes = st.number_input('📅 Día del mes', min_value=1, max_value=31, value=1)
                    shora = st.number_input('🕐 Hora de envío (0-23)', min_value=0, max_value=23, value=8)
                with sc3:
                    sformato = st.selectbox('📎 Formato', ['pdf', 'excel', 'ambos'], format_func=lambda x: {'pdf':'📄 PDF','excel':'📊 Excel','ambos':'📄📊 Ambos'}[x])
                    sdest = st.text_input('📧 Destinatarios (separados por coma)')
                if st.form_submit_button('💾 GUARDAR HORARIO'):
                    if snombre and sdest:
                        dia_sem_map = {'Lunes':0,'Martes':1,'Miércoles':2,'Jueves':3,'Viernes':4,'Sábado':5,'Domingo':6}
                        nid = insert_report_schedule(snombre, frecuencia=sfrec, dia_semana=dia_sem_map.get(sdia_sem, 0), dia_mes=int(sdia_mes), hora=int(shora), formato=sformato, destinatarios=sdest, tipo_reporte=stipo, tenant_id=active_tid)
                        if nid: clear_all_cache(); st.toast('✅ Horario guardado!'); st.rerun()
                        else: st.error('❌ Error al guardar')
                    else: st.error('❌ Nombre y destinatarios requeridos')
            sched_df = get_all_report_schedules(active_tid)
            if not sched_df.empty:
                st.markdown('#### Horarios configurados')
                for _, sr in sched_df.iterrows():
                    freq_txt = {'diario':'📅 Diario','semanal':'📅 Semanal','mensual':'📅 Mensual'}.get(sr['frecuencia'], sr['frecuencia'])
                    tipo_txt = {'completo':'📊 Completo','anomalias':'🚨 Anomalías','flotilla':'🚛 Flotilla','presupuesto':'💰 Presupuesto'}.get(sr['tipo_reporte'], sr['tipo_reporte'])
                    fmt_txt = {'pdf':'📄 PDF','excel':'📊 Excel','ambos':'📄📊 Ambos'}.get(sr['formato'], sr['formato'])
                    status_icon = '🟢' if sr.get('activo', 0) else '🔴'
                    ultimo = sr.get('ultimo_envio', '') or 'Nunca'
                    with st.expander(f"{status_icon} {sr['nombre']} — {freq_txt} — {tipo_txt}"):
                        sc_a, sc_b, sc_c = st.columns(3)
                        with sc_a: st.markdown(f"**Formato:** {fmt_txt}")
                        with sc_b: st.markdown(f"**Hora:** {sr.get('hora', 8)}:00")
                        with sc_c: st.markdown(f"**Último envío:** {ultimo}")
                        st.markdown(f"**Destinatarios:** {sr.get('destinatarios', '')}")
                        btn_a, btn_b, btn_c = st.columns(3)
                        with btn_a:
                            if sr.get('activo', 0):
                                if st.button('⏸️ Pausar', key='pause_' + str(sr['id'])):
                                    toggle_report_schedule(sr['id'], False, active_tid)
                                    clear_all_cache(); st.toast('⏸️ Pausado'); st.rerun()
                            else:
                                if st.button('▶️ Activar', key='act_' + str(sr['id'])):
                                    toggle_report_schedule(sr['id'], True, active_tid)
                                    clear_all_cache(); st.toast('▶️ Activado'); st.rerun()
                        with btn_b:
                            if st.button('📤 Enviar ahora', key='send_' + str(sr['id'])):
                                from alerts import enviar_reporte_email
                                ok, msg = enviar_reporte_email(sr)
                                if ok: st.toast('✅ Enviado!')
                                else: st.error(f'❌ {msg}')
                        with btn_c:
                            if st.button('🗑️ Eliminar', key='del_' + str(sr['id'])):
                                delete_report_schedule(sr['id'], active_tid)
                                clear_all_cache(); st.toast('🗑️ Eliminado'); st.rerun()
            else:
                st.info('📭 No hay horarios configurados')
        # ━━━ NOTIFICACIONES PUSH ━━━
        st.markdown('---')
        section_header('🔔', 'Notificaciones Push', 'Configura qué alertas se envían por email automáticamente')
        if not EMAIL_ENABLED:
            st.warning('⚠️ Email no configurado')
        else:
            notif_df = get_notification_settings(active_tid)
            if notif_df.empty:
                ensure_default_notifications(active_tid)
                notif_df = get_notification_settings(active_tid)
            tipo_labels = {
                'anomalia': ('🔴', 'Anomalía detectada', 'Email al registrar carga con rendimiento anómalo'),
                'mantenimiento': ('🔧', 'Mantenimiento vencido', 'Email cuando un vehículo excede km de servicio'),
                'presupuesto_80': ('🟡', 'Presupuesto al 80%', 'Email al alcanzar 80% del límite mensual'),
                'presupuesto_100': ('🔴', 'Presupuesto excedido', 'Email al superar el 100% del límite'),
            }
            for _, nr in notif_df.iterrows():
                nt = nr['tipo']
                if nt not in tipo_labels: continue
                ic, lbl, desc = tipo_labels[nt]
                is_on = nr.get('activo', 0) == 1
                curr_email = nr.get('email', '') or ALERT_EMAIL
                status = '🟢 Activo' if is_on else '🔴 Pausado'
                with st.expander(f'{ic} {lbl} — {status}'):
                    st.markdown(f'**{desc}**')
                    n1, n2, n3 = st.columns(3)
                    with n1: new_activo = st.checkbox('Activado', value=is_on, key='nact_' + nt)
                    with n2: new_email = st.text_input('📧 Email destino', value=curr_email, key='nemail_' + nt)
                    with n3:
                        ultimo = nr.get('ultimo_envio', '') or 'Nunca'
                        st.markdown(f'**Último envío:** {ultimo}')
                    if st.button('💾 Guardar', key='nsave_' + nt):
                        save_notification_setting(nt, new_activo, new_email, active_tid)
                        clear_all_cache(); st.toast('✅ Guardado!'); st.rerun()

    with tabs[11]:
        section_header('🏢', 'Organizaciones', 'Administra organizaciones y usuarios')
        with st.form('f_new_org'):
            c1,c2,c3 = st.columns(3)
            with c1: on = st.text_input('📝 Nombre*')
            with c2: orfc = st.text_input('📄 RFC')
            with c3: oplan = st.selectbox('📦 Plan', ['basic','pro','enterprise'])
            if st.form_submit_button('➕ CREAR ORG'):
                if on:
                    new_id = create_organization(on, orfc, plan=oplan)
                    if new_id: clear_all_cache(); st.toast('✅ Organización creada!'); st.rerun()
        orgs = get_all_organizations()
        if not orgs.empty:
            show_aggrid(orgs)
                      # ━━━ GENERADOR DE LLAVES DE SUSCRIPCIÓN ━━━
            st.markdown('---')
            section_header('🔐', 'Generador de Llaves', 'Crea llaves de suscripción para tus clientes')
            
            with st.form('f_gen_key'):
                k1, k2 = st.columns(2)
                with k1:
                    key_plan = st.selectbox('📦 Plan', ['mensual', 'trimestral', 'anual'])
                with k2:
                    key_notes = st.text_input('📝 Notas (ej. "Cliente Juan - $499 - 20/10/2025")')
                
                if st.form_submit_button('⚡ GENERAR LLAVE'):
                    duration = {'mensual': 1, 'trimestral': 3, 'anual': 12}.get(key_plan, 1)
                    new_key, msg = create_subscription_key(key_plan, duration, key_notes)
                    if new_key:
                        st.success(f'✅ Llave generada exitosamente!')
                        st.markdown(f'### 🎉 Tu llave:')
                        st.code(new_key, language='text')
                        st.markdown('📋 Cópiala y envíala a tu cliente por WhatsApp')
                    else:
                        st.error(f'❌ {msg}')
            
            # Mostrar llaves existentes
            keys_df = get_all_subscription_keys()
            if not keys_df.empty:
                st.markdown('#### 📋 Llaves generadas')
                # Formatear para mostrar
                display_df = keys_df[['key_code', 'plan_type', 'duration_months', 'is_used', 'is_active', 'used_by', 'notes', 'created_at']].copy()
                display_df.columns = ['Llave', 'Plan', 'Meses', 'Usada', 'Activa', 'Usada por', 'Notas', 'Creada']
                st.dataframe(display_df, use_container_width=True, hide_index=True)
                
                # Botón para desactivar llave
                st.markdown('#### 🚫 Desactivar llave robada o cancelada')
                deact_key = st.text_input('Pega aquí la llave a desactivar:')
                if st.button('🚫 DESACTIVAR LLAVE') and deact_key:
                    if deactivate_subscription_key(deact_key.strip()):
                        clear_all_cache()
                        st.success(f'✅ Llave {deact_key} desactivada')
                        st.rerun()
                    else:
                        st.error('❌ No se pudo desactivar (revisa que esté bien escrita)')
            else:
                st.info('📭 No hay llaves generadas aún. Crea la primera con el formulario de arriba.')
            st.markdown('---')
            section_header('👤', 'Crear Usuario', 'Nuevo usuario para una organización')
            org_list = [str(r['id']) + ': ' + r['nombre'] for _, r in orgs.iterrows()]
            with st.form('f_org_admin'):
                c1,c2,c3 = st.columns(3)
                with c1: sel_org = st.selectbox('🏢 Org', org_list, key='sel_org')
                with c2: a_user = st.text_input('👤 Usuario'); a_pass = st.text_input('🔑 Password', type='password')
                with c3: a_role = st.selectbox('🏷️ Rol', ['admin','despachador'])
                if st.form_submit_button('➕ CREAR USUARIO'):
                    if a_user and a_pass:
                        org_id = int(sel_org.split(':')[0])
                        if register_user(a_user, a_pass, tenant_id=org_id, role=a_role): clear_all_cache(); st.toast('✅ Usuario creado!')
                        else: st.error('❌ Ya existe')
            st.markdown('---')
            sel_org2 = st.selectbox('👥 Ver usuarios de:', org_list, key='sel_org2')
            org_id2 = int(sel_org2.split(':')[0])
            users_df = get_all_users(tenant_id=org_id2)
            if not users_df.empty: show_aggrid(users_df)
        else:
            st.info('📭 No hay organizaciones registradas. Crea una primero.')
          

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SISTEMA DE LLAVES DE SUSCRIPCIÓN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
import random
import string


def generate_key_code(plan_prefix="MES"):
    """Genera un código único tipo CYBER-MES-AB12"""
    letters = ''.join(random.choices(string.ascii_uppercase, k=2))
    digits = ''.join(random.choices(string.digits, k=2))
    return f"CYBER-{plan_prefix}-{letters}{digits}"


def create_subscription_key(plan_type='mensual', duration_months=1, notes=''):
    """Crea una nueva llave de suscripción en Supabase"""
    if not _use_supabase:
        return None, "Solo disponible en modo Supabase"

    plan_prefix_map = {
        'mensual': 'MES',
        'trimestral': 'TRIM',
        'anual': 'ANO'
    }
    plan_prefix = plan_prefix_map.get(plan_type, 'MES')

    # Generar llave única (intentar 5 veces si hay colisión)
    for _ in range(5):
        key_code = generate_key_code(plan_prefix)
        try:
            r = _sb.table("subscription_keys").insert({
                "key_code": key_code,
                "plan_type": plan_type,
                "duration_months": duration_months,
                "is_used": False,
                "is_active": True,
                "created_at": str(datetime.now()),
                "notes": notes
            }).execute()
            return key_code, "Llave creada exitosamente"
        except:
            continue
    return None, "No se pudo crear la llave"


def validate_subscription_key(key_code, username):
    """Valida y canjea una llave de suscripción"""
    if not _use_supabase:
        return False, "Solo disponible en modo Supabase"

    try:
        r = _sb.table("subscription_keys").select("*").eq("key_code", key_code).execute()
        if not r.data:
            return False, "Llave no existe"

        key_data = r.data[0]

        if not key_data.get("is_active", True):
            return False, "Llave desactivada (contacta soporte)"

        if key_data.get("is_used", False):
            return False, "Llave ya fue utilizada"

        # Marcar como usada
        _sb.table("subscription_keys").update({
            "is_used": True,
            "used_by": username,
            "used_date": str(datetime.now())
        }).eq("key_code", key_code).execute()

        return True, key_data["duration_months"]
    except Exception as e:
        return False, f"Error: {str(e)}"


def get_all_subscription_keys(only_available=False):
    """Obtiene todas las llaves (para el panel de administración)"""
    if not _use_supabase:
        return pd.DataFrame()

    q = _sb.table("subscription_keys").select("*").order("created_at", desc=True)
    if only_available:
        q = q.eq("is_used", False).eq("is_active", True)
    r = q.execute()
    return pd.DataFrame(r.data) if r.data else pd.DataFrame()


def deactivate_subscription_key(key_code):
    """Desactiva una llave (si te la roban o quieres cancelar)"""
    if not _use_supabase:
        return False
    try:
        _sb.table("subscription_keys").update({"is_active": False}).eq("key_code", key_code).execute()
        return True
    except:
        return False
