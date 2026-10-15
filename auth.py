import streamlit as st
from datetime import datetime, timedelta
from db import verify_user, register_user, get_user_exp, is_key_used, mark_key_used
from security import RateLimiter, password_strength, sanitize_alphanumeric

_rate_limiter = RateLimiter(max_attempts=5, base_block=60, max_block=3600)

def login_screen():
    st.markdown("""
    <style>
    .login-box {
        max-width: 420px; margin: 80px auto; padding: 40px;
        border-radius: 20px;
        background: linear-gradient(135deg, rgba(0,255,136,0.05), rgba(189,147,249,0.08));
        border: 1px solid rgba(0,255,136,0.2);
    }
    </style>
    <div class="login-box">
    """, unsafe_allow_html=True)

    st.markdown("## 🔐 Iniciar Sesión")

    # Rate limiting
    allowed, wait = _rate_limiter.check(st.session_state, "login")
    if not allowed:
        st.error(f"🚫 Demasiados intentos. Espera **{wait} segundos** antes de reintentar.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    with st.form("login_form"):
        username = st.text_input("👤 Usuario", max_chars=50)
        password = st.text_input("🔑 Contraseña", type="password", max_chars=128)
        submitted = st.form_submit_button("🚀 ENTRAR", use_container_width=True)

        if submitted:
            if not username or not password:
                st.error("❌ Ingresa usuario y contraseña")
            else:
                user = verify_user(username, password)
                if user:
                    _rate_limiter.reset(st.session_state, "login")
                    st.session_state["user"] = user
                    st.session_state["login_attempts"] = 0
                    st.toast(f"✅ Bienvenido {username}!", icon="👋")
                    st.rerun()
                else:
                    block_time = _rate_limiter.record_failure(st.session_state, "login")
                    attempts = st.session_state.get("login_attempts", 1)
                    remaining = 5 - attempts if attempts < 5 else 0
                    if block_time > 0:
                        st.error(f"🚫 Bloqueado por **{int(block_time)}s** por seguridad.")
                    else:
                        st.error(f"❌ Incorrecto ({remaining} intentos restantes)")

    st.markdown("---")
    with st.expander("📝 Registrarse"):
        with st.form("register_form"):
            new_user = st.text_input("👤 Nuevo usuario", max_chars=50)
            new_pass = st.text_input("🔑 Contraseña", type="password", key="rp", max_chars=128)
            new_pass2 = st.text_input("🔑 Confirmar contraseña", type="password", key="rp2", max_chars=128)
            license_key = st.text_input("🎫 Licencia (opcional)", max_chars=100)
            reg_btn = st.form_submit_button("✅ CREAR CUENTA", use_container_width=True)

            if new_pass:
                score, label = password_strength(new_pass)
                if score < 2:
                    st.warning(f"⚠️ {label}")
                else:
                    st.info(label)

            if reg_btn:
                if not new_user or not new_pass:
                    st.error("❌ Datos incompletos")
                elif new_pass != new_pass2:
                    st.error("❌ Las contraseñas no coinciden")
                elif len(new_pass) < 4:
                    st.error("❌ Contraseña muy corta (mínimo 4 caracteres)")
                else:
                    if license_key:
                        if is_key_used(license_key):
                            st.error("❌ Licencia ya usada")
                        else:
                            if register_user(new_user, new_pass, tenant_id=1, role="despachador"):
                                mark_key_used(license_key, new_user)
                                st.success("✅ Cuenta creada con licencia. Inicia sesión.")
                            else:
                                st.error("❌ Error al registrar (¿usuario ya existe?)")
                    else:
                        if register_user(new_user, new_pass, tenant_id=1, role="despachador"):
                            st.success("✅ Cuenta creada. Inicia sesión.")
                        else:
                            st.error("❌ El usuario ya existe")

    st.markdown("</div>", unsafe_allow_html=True)

def check_access(user_data):
    exp = user_data.get("exp_date", "")
    if exp:
        for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                if datetime.now() > datetime.strptime(exp, fmt):
                    return False
            except:
                continue
    return True

def paywall_screen(user_data):
    st.markdown("## 🔒 Suscripción Vencida")
    st.warning("Tu acceso ha expirado. Contacta al administrador.")
    exp = user_data.get("exp_date", "")
    if exp:
        st.info(f"Expiró: {exp}")

def get_subscription_info(user_data):
    exp = user_data.get("exp_date", "")
    role = user_data.get("role", "")
    if role == "superadmin":
        return "👑 SuperAdmin"
    if not exp:
        return "⏳ Sin fecha"
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            exp_dt = datetime.strptime(exp, fmt)
            days_left = (exp_dt - datetime.now()).days
            if days_left <= 0: return f"🔴 Vencida ({days_left}d)"
            elif days_left <= 7: return f"🟡 {days_left}d restantes"
            else: return f"🟢 {days_left}d restantes"
        except:
            continue
    return "⏳ Fecha inválida"