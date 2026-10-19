import streamlit as st
import os
import base64
from datetime import datetime, timedelta
from db import verify_user, register_user, get_user_exp, is_key_used, mark_key_used, validate_subscription_key, update_user_exp
from security import RateLimiter, password_strength, sanitize_alphanumeric
from config import (TRIAL_DAYS, PRICING_INFO, SUBSCRIPTION_KEYS,
                    WHATSAPP_VENTAS, WHATSAPP_SOPORTE, EMAIL_VENTAS,
                    TELEFONO_VENTAS, SITIO_WEB)

_rate_limiter = RateLimiter(max_attempts=5, base_block=60, max_block=3600)


def _mostrar_logo():
    """Muestra el logo de CyberFuel AI centrado, si existe el archivo."""
    logo_path = "assets/logo.png"
    if os.path.exists(logo_path):
        try:
            with open(logo_path, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode()
            st.markdown(
                f"""
                <div style="text-align:center; margin-bottom: 25px; margin-top: 10px;">
                    <img src="data:image/png;base64,{img_b64}"
                         alt="CyberFuel AI"
                         style="width: 130px; height: auto; border-radius: 16px;
                                box-shadow: 0 4px 24px rgba(0,255,136,0.35);
                                border: 2px solid rgba(0,255,136,0.4);
                                padding: 8px; background: #0a0a0f;">
                </div>
                """,
                unsafe_allow_html=True,
            )
        except Exception:
            pass


def login_screen():
    st.markdown("""
    <style>
    .login-box {
        max-width: 420px; margin: 40px auto; padding: 40px;
        border-radius: 20px;
        background: linear-gradient(135deg, rgba(0,255,136,0.05), rgba(189,147,249,0.08));
        border: 1px solid rgba(0,255,136,0.2);
    }
    </style>
    <div class="login-box">
    """, unsafe_allow_html=True)

    # Mostrar logo centrado arriba del login
    _mostrar_logo()

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
    with st.expander("📝 Registrarse (Prueba GRATIS 7 días)"):
        with st.form("register_form"):
            new_user = st.text_input("👤 Nuevo usuario", max_chars=50)
            new_pass = st.text_input("🔑 Contraseña", type="password", key="rp", max_chars=128)
            new_pass2 = st.text_input("🔑 Confirmar contraseña", type="password", key="rp2", max_chars=128)
            license_key = st.text_input("🎫 Licencia (opcional - si ya pagaste)", max_chars=100)
            reg_btn = st.form_submit_button("✅ CREAR CUENTA GRATIS", use_container_width=True)

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
                        # Sin licencia = trial de 7 días
                        if register_user(new_user, new_pass, tenant_id=1, role="despachador"):
                            # Asignar trial de 7 días
                            exp_date = datetime.now() + timedelta(days=TRIAL_DAYS)
                            update_user_exp(new_user, exp_date)
                            st.success(f"✅ Cuenta creada. Tienes {TRIAL_DAYS} días GRATIS. Inicia sesión.")
                        else:
                            st.error("❌ El usuario ya existe")

    st.markdown("</div>", unsafe_allow_html=True)


def check_access(user_data):
    exp = user_data.get("exp_date", "")
    if not exp:
        # Si no tiene fecha de expiración, darle trial de 7 días automáticamente
        # (solo si no es superadmin)
        if user_data.get("role") == "superadmin":
            return True
        # Asignar trial
        try:
            from db import update_user_exp
            exp_date = datetime.now() + timedelta(days=TRIAL_DAYS)
            update_user_exp(user_data.get("username", ""), exp_date)
            user_data["exp_date"] = str(exp_date)
            return True
        except:
            return True
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            if datetime.now() > datetime.strptime(exp, fmt):
                return False
        except:
            continue
    return True


def paywall_screen(user_data):
    """Pantalla de pago cuando el trial expira"""
    st.markdown("""
        <div style="background:linear-gradient(135deg,#0a0a0f 0%,#1a1a2e 100%);
                    padding:40px;border-radius:20px;text-align:center;margin:20px 0;
                    border:2px solid #ff5555;">
            <h1 style="color:#ff5555;font-size:2.5rem;margin:0;">⏰ Tu prueba gratis ha terminado</h1>
            <p style="color:#f8f8f2;font-size:1.2rem;margin:10px 0;">Tu periodo de prueba de 7 días ha expirado.</p>
            <p style="color:#bd93f9;font-size:1.1rem;margin:5px 0;">Para seguir usando CyberFuel AI, activa tu suscripción:</p>
        </div>
    """, unsafe_allow_html=True)

    # Mostrar planes
    st.markdown(f"""
        <div style="background:rgba(20,20,35,0.8);border:2px solid #00ff88;border-radius:20px;padding:30px;margin:20px 0;">
            <h2 style="color:#00ff88;text-align:center;margin:0 0 15px 0;">💎 Planes disponibles</h2>
            <pre style="color:#f8f8f2;font-size:1.1rem;white-space:pre-wrap;margin:0;">{PRICING_INFO}</pre>
        </div>
    """, unsafe_allow_html=True)

    # Formulario para ingresar llave
    st.markdown("### 🔑 ¿Ya tienes tu llave de activación?")
    with st.form("activate_key"):
        key_input = st.text_input("Ingresa tu llave de suscripción:", placeholder="CYBER-XXX-XXXX")
        activate_btn = st.form_submit_button("⚡ ACTIVAR SUSCRIPCIÓN", use_container_width=True)

        if activate_btn:
            if key_input.strip():
                ok, msg = validate_subscription_key(key_input.strip(), user_data['username'])
                if ok:
                    # Activar suscripción
                    new_exp = datetime.now() + timedelta(days=msg * 30)
                    update_user_exp(user_data['username'], new_exp)
                    st.success(f"✅ ¡Suscripción activada por {msg} mes(es)!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")
            else:
                st.warning("⚠️ Ingresa una llave válida")

    # Sección de contacto
    st.markdown("---")
    st.markdown("""
        <div style="background:rgba(189,147,249,0.1);border:2px solid #bd93f9;border-radius:20px;padding:30px;margin:20px 0;">
            <h2 style="color:#bd93f9;text-align:center;margin:0 0 15px 0;">💬 ¿No tienes llave? Contáctanos</h2>
            <p style="color:#f8f8f2;text-align:center;font-size:1.1rem;margin:0;">
                Escríbenos y te activamos en menos de 5 minutos
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Botones de contacto
    col1, col2, col3 = st.columns(3)

    with col1:
        if WHATSAPP_VENTAS:
            wa_link = f"https://wa.me/{WHATSAPP_VENTAS.replace('+','')}?text=Hola%20CyberFuel%2C%20quiero%20comprar%20una%20licencia.%20Mi%20usuario%20es%3A%20{user_data['username']}"
            st.markdown(f"""
                <a href="{wa_link}" target="_blank" style="display:block;text-align:center;
                   background:linear-gradient(135deg,#25D366,#128C7E);color:white;padding:15px 20px;
                   border-radius:12px;text-decoration:none;font-weight:bold;margin:5px 0;">
                    📱 WhatsApp<br/><small>{WHATSAPP_VENTAS}</small>
                </a>
            """, unsafe_allow_html=True)
        else:
            st.info("📱 WhatsApp no configurado")

    with col2:
        if EMAIL_VENTAS:
            st.markdown(f"""
                <a href="mailto:{EMAIL_VENTAS}?subject=Licencia CyberFuel AI&body=Hola, quiero comprar una licencia. Mi usuario es: {user_data['username']}"
                   target="_blank" style="display:block;text-align:center;
                   background:linear-gradient(135deg,#00ff88,#00cc6a);color:#0a0a0f;padding:15px 20px;
                   border-radius:12px;text-decoration:none;font-weight:bold;margin:5px 0;">
                    📧 Email<br/><small>{EMAIL_VENTAS}</small>
                </a>
            """, unsafe_allow_html=True)
        else:
            st.info("📧 Email no configurado")

    with col3:
        if SITIO_WEB:
            st.markdown(f"""
                <a href="{SITIO_WEB}" target="_blank" style="display:block;text-align:center;
                   background:linear-gradient(135deg,#bd93f9,#9b59b6);color:white;padding:15px 20px;
                   border-radius:12px;text-decoration:none;font-weight:bold;margin:5px 0;">
                    🌐 Ver planes<br/><small>{SITIO_WEB}</small>
                </a>
            """, unsafe_allow_html=True)
        else:
            st.info("🌐 Web no configurada")

    # Mensaje final
    st.markdown("""
        <p style="text-align:center;color:#9ca3af;margin-top:30px;font-size:0.9rem;">
            ⚡ Atención inmediata en horario laboral · Respuesta en menos de 1 hora
        </p>
    """, unsafe_allow_html=True)

    st.stop()


def show_trial_warning(user_data):
    """Muestra advertencia cuando el trial está por expirar (menos de 3 días)"""
    exp = user_data.get("exp_date", "")
    if not exp:
        return
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            exp_dt = datetime.strptime(exp, fmt)
            days_left = (exp_dt - datetime.now()).days
            if 0 < days_left <= 3:
                if days_left == 1:
                    msg = f"⚠️ Tu prueba gratis termina MAÑANA. Contacta para activar tu licencia."
                else:
                    msg = f"⚠️ Tu prueba gratis termina en {days_left} días. ¡Activa tu licencia a tiempo!"
                st.markdown(f"""
                    <div style="background:rgba(255,85,85,0.1);border:1px solid #ff5555;
                                border-radius:12px;padding:15px;margin:10px 0;">
                        <p style="color:#ff5555;margin:0;font-weight:600;">{msg}</p>
                    </div>
                """, unsafe_allow_html=True)
                # Botón de WhatsApp rápido
                if WHATSAPP_VENTAS:
                    wa_link = f"https://wa.me/{WHATSAPP_VENTAS.replace('+','')}?text=Hola%2C%20quiero%20activar%20mi%20licencia.%20Usuario%3A%20{user_data['username']}"
                    st.markdown(f"""
                        <a href="{wa_link}" target="_blank" style="display:inline-block;
                           background:#25D366;color:white;padding:8px 16px;border-radius:8px;
                           text-decoration:none;font-weight:bold;font-size:0.9rem;">
                            📱 Activar por WhatsApp
                        </a>
                    """, unsafe_allow_html=True)
            break
        except:
            continue


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
            if days_left <= 0:
                return f"🔴 Vencida ({days_left}d)"
            elif days_left <= 7:
                return f"🟡 {days_left}d restantes"
            else:
                return f"🟢 {days_left}d restantes"
        except:
            continue
    return "⏳ Fecha inválida"
