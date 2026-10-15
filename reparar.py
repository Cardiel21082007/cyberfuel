import re

with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Encontrar donde empieza la seccion del mapa
marker = '# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n#  🗺️ MAPA GPS'
if marker not in code:
    marker = '#  🗺️ MAPA GPS'

pos = code.find(marker)
if pos == -1:
    print('ERROR: No encontre la seccion del mapa')
    input('Enter para salir')
    exit()

# Encontrar donde termina el archivo - buscar el ultimo show_aggrid(users_df)
end_marker = "if not users_df.empty: show_aggrid(users_df)"
end_pos = code.find(end_marker, pos)
if end_pos == -1:
    print('ERROR: No encontre el final')
    input('Enter para salir')
    exit()

end_pos = end_pos + len(end_marker)

# Nueva seccion completa
new_section = '''# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  🗺️ MAPA GPS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if is_admin:
    with tabs[7]:
        section_header('🗺️', 'Mapa GPS', 'Ubicación de cargas con coordenadas')
        df = get_data(active_tid)
        if not df.empty:
            gps = df[(df['latitud'].notna()) & (df['longitud'].notna()) & (df['latitud'] != 0) & (df['longitud'] != 0)].copy()
            if gps.empty:
                st.info('📭 Sin coordenadas GPS registradas')
            else:
                try:
                    import folium
                    from streamlit_folium import st_folium
                    clat = float(gps['latitud'].mean())
                    clon = float(gps['longitud'].mean())
                    fmap = folium.Map(location=[clat, clon], zoom_start=12)
                    for _, rw in gps.iterrows():
                        ptitle = str(rw.get('vehiculo','')) + ' | ' + str(rw.get('fecha','')) + ' | $' + '{:,.2f}'.format(rw.get('custo',0))
                        al = str(rw.get('alerta_anomalia',''))
                        clr = 'red' if al == 'ANOMALIA' else 'green'
                        folium.Marker([float(rw['latitud']), float(rw['longitud'])], popup=ptitle, icon=folium.Icon(color=clr, icon='gas-pump', prefix='fa')).add_to(fmap)
                    st_folium(fmap, width=900, height=500)
                except Exception as ex:
                    st.warning('⚠️ Instala: pip install folium streamlit-folium')
                    try:
                        st.map(gps.rename(columns={'latitud':'lat','longitud':'lon'})[['lat','lon']])
                    except:
                        pass

    with tabs[8]:
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
                st.toast('✅ Configuración guardada!')
        logo_bytes = get_logo_bytes(active_tid)
        if logo_bytes: st.image(io.BytesIO(logo_bytes), width=150)
        logo_file = st.file_uploader('🖼️ Subir logo', type=['png','jpg','jpeg'], key='logo_up')
        if logo_file:
            cfg['logo_b64'] = base64.b64encode(logo_file.read()).decode()
            save_config(cfg, active_tid)
            st.toast('✅ Logo guardado!'); st.rerun()

    with tabs[9]:
        section_header('🏢', 'Organizaciones', 'Administra organizaciones y usuarios')
        with st.form('f_new_org'):
            c1,c2,c3 = st.columns(3)
            with c1: on = st.text_input('📝 Nombre*')
            with c2: orfc = st.text. st.text_input('📄 RFC')
            with c3: oplan = st.selectbox('📦 Plan', ['basic','pro','enterprise'])
            if st.form_submit_button('➕ CREAR ORG'):
                if on:
                    new_id = create_organization(on, orfc, plan=oplan)
                    if new_id: st.toast('✅ Organización creada!'); st.rerun()
        orgs = get_all_organizations()
        if not orgs.empty: show_aggrid(orgs)
        st.markdown('---')
        section_header('👤', 'Crear Usuario', 'Nuevo usuario para una organización')
        with st.form('f_org_admin'):
            c1,c2,c3 = st.columns(3)
            with c1: sel_org = st.selectbox('🏢 Org', [str(r['id']) + ': ' + rC['nombre'] for _, r in orgs.iterrows()], key='sel_org')
            with c2: a_user = st.text_input('👤 Usuario'); a_pass = st.text_input('🔑 Password', type='password')
            with c3: a_role = st.selectbox('🏷️ Rol', ['admin','despachador'])
            if st.form_submit_button('➕ CREAR USUARIO'):
                if a_user and a_pass:
                    org_id = int(sel_org.split(':')[0])
                    if register_user(a_user, a_pass, tenant_id=org_id, role=a_role):
                        st.toast('✅ Usuario creado!')
                    else: st.error('❌ Ya existe')
        st.markdown('---')
        sel_org2 = st.selectbox('👥 Ver usuarios de:', [str(r['id']) + ': ' + r['nombre'] for _, r in orgs.iterrows()], key='sel_org2')
        org_id2 = int(sel_org2.split(':')[0])
        users_df = get_all_users(tenant_id=org_id2)
        if not users_df.empty: show_aggrid(users_df)
'''

new_code = code[:pos] + new_section
with open('app.py', 'w', encoding='utf-8') as f:
    f.write(new_code)

print('✅ app.py reparado exitosamente!')
input('Enter para salir')