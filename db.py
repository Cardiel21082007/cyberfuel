import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from config import DB_MODE, DB_NAME, SUPABASE_URL, SUPABASE_KEY
from audit import log_audit
from security import (
    hash_password, verify_password, is_legacy_hash,
    sanitize_text, sanitize_alphanumeric, sanitize_placa,
    sanitize_number, validate_field, ALLOWED_DUPLICATE_FIELDS,
)

_use_supabase = DB_MODE == "supabase" and bool(SUPABASE_URL) and bool(SUPABASE_KEY)
_sb = None

if _use_supabase:
    try:
        from supabase import create_client
        _sb = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print("Supabase error: " + str(e))
        _use_supabase = False


def migrate_db():
    if _use_supabase:
        return
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    v_cols = [
        ("modelo", "TEXT DEFAULT ''"),
        ("tipo_combustible", "TEXT DEFAULT 'Diesel'"),
        ("departamento", "TEXT DEFAULT ''"),
        ("rendimiento_min", "REAL DEFAULT 0"),
        ("km_proximo_servicio", "REAL DEFAULT 0"),
        ("intervalo_km_servicio", "REAL DEFAULT 0"),
        ("tipo_servicio", "TEXT DEFAULT ''"),
        ("fecha_ultimo_servicio", "TEXT DEFAULT ''"),
        ("poliza_seguro", "TEXT DEFAULT ''"),
        ("tel_operador", "TEXT DEFAULT ''"),
        ("vencimiento_seguro", "TEXT DEFAULT ''"),
        ("vencimiento_verificacion", "TEXT DEFAULT ''"),
        ("vencimiento_tarjeton", "TEXT DEFAULT ''"),
    ]
    for col_name, col_type in v_cols:
        try:
            c.execute("ALTER TABLE vehiculos ADD COLUMN " + col_name + " " + col_type)
        except:
            pass
    tenant_cols = [
        ("users_db", "tenant_id", "INTEGER DEFAULT 1"),
        ("cargas", "tenant_id", "INTEGER DEFAULT 1"),
        ("vehiculos", "tenant_id", "INTEGER DEFAULT 1"),
    ]
    for table, col, ctype in tenant_cols:
        try:
            c.execute("ALTER TABLE " + table + " ADD COLUMN " + col + " " + ctype)
        except:
            pass
    try:
        c.execute("UPDATE users_db SET tenant_id=1 WHERE tenant_id IS NULL")
    except:
        pass
    try:
        c.execute("UPDATE cargas SET tenant_id=1 WHERE tenant_id IS NULL")
    except:
        pass
    try:
        c.execute("UPDATE vehiculos SET tenant_id=1 WHERE tenant_id IS NULL")
    except:
        pass
    conn.commit()
    conn.close()


def init_db():
    if _use_supabase:
        # ━━ CREAR ORGANIZACIÓN POR DEFECTO SI NO EXISTE ━━
        try:
            r_org = _sb.table("organizations").select("id").eq("id", 1).execute()
            if not r_org.data:
                _sb.table("organizations").insert({
                    "id": 1,
                    "nombre": "Organizacion Principal",
                    "rfc": "",
                    "direccion": "",
                    "ciudad": "",
                    "telefono": "",
                    "email": "",
                    "logo_b64": "",
                    "color_primario": "#00ff88",
                    "plan": "basic",
                    "max_users": 5,
                    "max_vehicles": 50,
                    "activo": 1,
                    "fecha_creacion": str(datetime.now()),
                }).execute()
                print("[init_db] Organizacion Principal creada en Supabase")
        except Exception as e:
            print("Error creating default org: " + str(e))

        # ━━ CREAR USUARIO ADMIN POR DEFECTO SI NO EXISTE ━━
        try:
            r = _sb.table("users_db").select("username").eq("username", "admin").execute()
            if not r.data:
                admin_hash = hash_password("admin123")
                now_str = str(datetime.now())
                exp_str = str(datetime.now() + timedelta(days=3650))
                _sb.table("users_db").insert({
                    "username": "admin",
                    "password_hash": admin_hash,
                    "role": "superadmin",
                    "reg_date": now_str,
                    "expiration_date": exp_str,
                    "tenant_id": 0,
                }).execute()
                print("[init_db] Usuario admin creado en Supabase")
        except Exception as e:
            print("Error creating admin: " + str(e))
        return

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "CREATE TABLE IF NOT EXISTS organizations ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, rfc TEXT DEFAULT '',"
        "direccion TEXT DEFAULT '', ciudad TEXT DEFAULT '', telefono TEXT DEFAULT '',"
        "email TEXT DEFAULT '', logo_b64 TEXT DEFAULT '', color_primario TEXT DEFAULT '#00ff88',"
        "plan TEXT DEFAULT 'basic', max_users INTEGER DEFAULT 5,"
        "max_vehicles INTEGER DEFAULT 50, activo INTEGER DEFAULT 1, fecha_creacion TEXT)"
    )
    c.execute(
        "CREATE TABLE IF NOT EXISTS cargas ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, vehiculo TEXT,"
        "conductor TEXT, tipo_combustible TEXT, kilometraje REAL, litros REAL,"
        "custo REAL, factura TEXT, estacion TEXT, vale TEXT, rendimento REAL,"
        "custo_por_km REAL, alerta_anomalia TEXT, alerta_mantenimiento TEXT,"
        "latitud REAL, longitud REAL, capturado_por TEXT, fecha_captura TEXT,"
        "tenant_id INTEGER DEFAULT 1)"
    )
    c.execute(
        "CREATE TABLE IF NOT EXISTS vehiculos ("
        "placa TEXT PRIMARY KEY, marca TEXT, modelo TEXT DEFAULT '',"
        "tipo_combustible TEXT DEFAULT 'Diesel', departamento TEXT DEFAULT '',"
        "capacidade REAL, km_inicial REAL, rendimiento_min REAL DEFAULT 0,"
        "km_proximo_servicio REAL DEFAULT 0, intervalo_km_servicio REAL DEFAULT 0,"
        "tipo_servicio TEXT DEFAULT '', fecha_ultimo_servicio TEXT DEFAULT '',"
        "poliza_seguro TEXT DEFAULT '', tel_operador TEXT DEFAULT '',"
        "tenant_id INTEGER DEFAULT 1)"
    )
    c.execute(
        "CREATE TABLE IF NOT EXISTS users_db ("
        "username TEXT PRIMARY KEY, password_hash TEXT, role TEXT,"
        "reg_date TEXT, expiration_date TEXT, tenant_id INTEGER DEFAULT 1)"
    )
    c.execute(
        "CREATE TABLE IF NOT EXISTS used_keys ("
        "key_text TEXT PRIMARY KEY, used_by TEXT, used_date TEXT)"
    )
    c.execute("SELECT * FROM organizations WHERE id=1")
    if not c.fetchone():
        now_str = str(datetime.now())
        c.execute(
            "INSERT INTO organizations VALUES (1,'Organizacion Principal','','','','','','','#00ff88','basic',5,50,1,?)",
            (now_str,),
        )
    c.execute("SELECT * FROM users_db WHERE username='admin'")
    if not c.fetchone():
        admin_hash = hash_password("admin123")
        now_str = str(datetime.now())
        exp_str = str(datetime.now() + timedelta(days=3650))
        c.execute(
            "INSERT INTO users_db VALUES (?,?,?,?,?,?)",
            ("admin", admin_hash, "superadmin", now_str, exp_str, 0),
        )
    migrate_db()
    conn.commit()
    conn.close()


def _migrate_legacy_pw(username, plain_password):
    try:
        new_hash = hash_password(plain_password)
        if _use_supabase:
            _sb.table("users_db").update({"password_hash": new_hash}).eq("username", username).execute()
        else:
            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            cur.execute("UPDATE users_db SET password_hash=? WHERE username=?", (new_hash, username))
            conn.commit()
            conn.close()
    except:
        pass


def create_organization(nombre, rfc="", direccion="", telefono="", email="", plan="basic", max_users=5, max_vehicles=50):
    try:
        nombre = sanitize_text(nombre, 100)
        rfc = sanitize_alphanumeric(rfc, 20)
        if not nombre:
            return None
        if _use_supabase:
            r = _sb.table("organizations").insert({
                "nombre": nombre, "rfc": rfc,
                "direccion": sanitize_text(direccion, 200),
                "telefono": sanitize_alphanumeric(telefono, 30),
                "email": sanitize_alphanumeric(email, 80),
                "plan": plan, "max_users": int(max_users), "max_vehicles": int(max_vehicles),
                "fecha_creacion": str(datetime.now()), "activo": 1,
                "color_primario": "#00ff88", "logo_b64": "",
            }).execute()
            return r.data[0]["id"] if r.data else None
        else:
            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO organizations (nombre,rfc,direccion,telefono,email,plan,max_users,max_vehicles,fecha_creacion,activo) VALUES (?,?,?,?,?,?,?,?,?,1)",
                (nombre, rfc, sanitize_text(direccion, 200), sanitize_alphanumeric(telefono, 30),
                 sanitize_alphanumeric(email, 80), plan, int(max_users), int(max_vehicles), str(datetime.now())),
            )
            org_id = cur.lastrowid
            conn.commit()
            conn.close()
            return org_id
    except Exception as e:
        print("Error creating org: " + str(e))
        return None


def get_all_organizations():
    if _use_supabase:
        r = _sb.table("organizations").select("*").order("id").execute()
        return pd.DataFrame(r.data)
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM organizations ORDER BY id", conn)
    conn.close()
    return df


def update_organization(org_id, **kwargs):
    if not kwargs:
        return
    safe = {}
    if "nombre" in kwargs:
        safe["nombre"] = sanitize_text(kwargs["nombre"], 100)
    if "rfc" in kwargs:
        safe["rfc"] = sanitize_alphanumeric(kwargs["rfc"], 20)
    if "direccion" in kwargs:
        safe["direccion"] = sanitize_text(kwargs["direccion"], 200)
    if "telefono" in kwargs:
        safe["telefono"] = sanitize_alphanumeric(kwargs["telefono"], 30)
    if "email" in kwargs:
        safe["email"] = sanitize_alphanumeric(kwargs["email"], 80)
    if "color_primario" in kwargs:
        import re as _re
        color = kwargs["color_primario"]
        if _re.match(r"^#[0-9a-fA-F]{6}$", color):
            safe["color_primario"] = color
    if "logo_b64" in kwargs:
        safe["logo_b64"] = kwargs["logo_b64"]
    if "plan" in kwargs and kwargs["plan"] in ("basic", "pro", "enterprise"):
        safe["plan"] = kwargs["plan"]
    if "max_users" in kwargs:
        safe["max_users"] = int(sanitize_number(kwargs["max_users"], 1, 1000))
    if "max_vehicles" in kwargs:
        safe["max_vehicles"] = int(sanitize_number(kwargs["max_vehicles"], 1, 10000))
    if "activo" in kwargs:
        safe["activo"] = 1 if kwargs["activo"] else 0
    if not safe:
        return
    if _use_supabase:
        _sb.table("organizations").update(safe).eq("id", int(org_id)).execute()
    else:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        set_clause = ", ".join([k + "=?" for k in safe.keys()])
        values = list(safe.values()) + [int(org_id)]
        cur.execute("UPDATE organizations SET " + set_clause + " WHERE id=?", values)
        conn.commit()
        conn.close()


def get_org_info(org_id):
    try:
        org_id = int(org_id)
    except:
        return {}
    if _use_supabase:
        r = _sb.table("organizations").select("*").eq("id", org_id).execute()
        return r.data[0] if r.data else {}
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM organizations WHERE id=?", conn, params=(org_id,))
    conn.close()
    return df.iloc[0].to_dict() if not df.empty else {}


def verify_user(username, password):
    username = sanitize_alphanumeric(username, 50)
    if not username or not password:
        return None
    if _use_supabase:
        r = _sb.table("users_db").select("username,role,reg_date,expiration_date,tenant_id,password_hash").eq("username", username).execute()
        if not r.data:
            return None
        u = r.data[0]
        stored_hash = u.get("password_hash", "")
    else:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT username,role,reg_date,expiration_date,tenant_id,password_hash FROM users_db WHERE username=?", (username,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        u = {"username": row[0], "role": row[1], "reg_date": row[2], "expiration_date": row[3], "tenant_id": row[4]}
        stored_hash = row[5] if len(row) > 5 else ""
    if not verify_password(password, stored_hash):
        return None
    if is_legacy_hash(stored_hash):
        _migrate_legacy_pw(username, password)
    tid = u.get("tenant_id", 0) or 0
    org = get_org_info(tid) if tid > 0 else {"nombre": "Global"}
    return {
        "username": u["username"], "role": u["role"],
        "reg_date": u["reg_date"], "exp_date": u["expiration_date"],
        "tenant_id": tid, "org_nombre": org.get("nombre", "?"),
    }


def register_user(username, password, tenant_id=1, role="despachador"):
    username = sanitize_alphanumeric(username, 50)
    if not username or not password or len(password) < 4:
        return False
    if role not in ("superadmin", "admin", "despachador"):
        role = "despachador"
    tenant_id = int(sanitize_number(tenant_id, 0, 9999))
    pw_hash = hash_password(password)
    try:
        if _use_supabase:
            _sb.table("users_db").insert({
                "username": username, "password_hash": pw_hash, "role": role,
                "reg_date": str(datetime.now()), "expiration_date": "", "tenant_id": tenant_id,
            }).execute()
        else:
            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            cur.execute("INSERT INTO users_db VALUES (?,?,?,?,?,?)", (username, pw_hash, role, str(datetime.now()), "", tenant_id))
            conn.commit()
            conn.close()
        log_audit(username, "REGISTER", "users_db", username)
        return True
    except:
        return False


def get_user_exp(username):
    username = sanitize_alphanumeric(username, 50)
    if _use_supabase:
        r = _sb.table("users_db").select("expiration_date").eq("username", username).execute()
        return r.data[0]["expiration_date"] if r.data else ""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT expiration_date FROM users_db WHERE username=?", (username,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else ""


def update_user_exp(username, new_exp):
    username = sanitize_alphanumeric(username, 50)
    if _use_supabase:
        _sb.table("users_db").update({"expiration_date": str(new_exp)}).eq("username", username).execute()
    else:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("UPDATE users_db SET expiration_date=? WHERE username=?", (str(new_exp), username))
        conn.commit()
        conn.close()


def update_user_role(username, new_role):
    username = sanitize_alphanumeric(username, 50)
    if new_role not in ("superadmin", "admin", "despachador"):
        return
    if _use_supabase:
        _sb.table("users_db").update({"role": new_role}).eq("username", username).execute()
    else:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("UPDATE users_db SET role=? WHERE username=?", (new_role, username))
        conn.commit()
        conn.close()


def update_user_tenant(username, tenant_id):
    username = sanitize_alphanumeric(username, 50)
    tenant_id = int(sanitize_number(tenant_id, 0, 9999))
    if _use_supabase:
        _sb.table("users_db").update({"tenant_id": tenant_id}).eq("username", username).execute()
    else:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("UPDATE users_db SET tenant_id=? WHERE username=?", (tenant_id, username))
        conn.commit()
        conn.close()


def change_password(username, new_password):
    username = sanitize_alphanumeric(username, 50)
    if not new_password or len(new_password) < 4:
        return False
    pw_hash = hash_password(new_password)
    try:
        if _use_supabase:
            _sb.table("users_db").update({"password_hash": pw_hash}).eq("username", username).execute()
        else:
            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            cur.execute("UPDATE users_db SET password_hash=? WHERE username=?", (pw_hash, username))
            conn.commit()
            conn.close()
        log_audit(username, "PASSWORD_CHANGE", "users_db", username)
        return True
    except:
        return False


def refresh_user(username):
    username = sanitize_alphanumeric(username, 50)
    if _use_supabase:
        r = _sb.table("users_db").select("username,role,reg_date,expiration_date,tenant_id").eq("username", username).execute()
        if r.data:
            u = r.data[0]
            tid = u.get("tenant_id", 0) or 0
            org = get_org_info(tid) if tid > 0 else {"nombre": "Global"}
            return {"username": u["username"], "role": u["role"], "reg_date": u["reg_date"], "exp_date": u["expiration_date"], "tenant_id": tid, "org_nombre": org.get("nombre", "?")}
        return None
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT username,role,reg_date,expiration_date,tenant_id FROM users_db WHERE username=?", (username,))
    u = cur.fetchone()
    conn.close()
    if u:
        tid = u[4] if u[4] else 0
        org = get_org_info(tid) if tid > 0 else {"nombre": "Global"}
        return {"username": u[0], "role": u[1], "reg_date": u[2], "exp_date": u[3], "tenant_id": tid, "org_nombre": org.get("nombre", "?")}
    return None


def get_all_users(tenant_id=None):
    if _use_supabase:
        q = _sb.table("users_db").select("username,role,expiration_date,tenant_id")
        if tenant_id is not None and tenant_id > 0:
            q = q.eq("tenant_id", tenant_id)
        r = q.execute()
        return pd.DataFrame(r.data)
    conn = sqlite3.connect(DB_NAME)
    if tenant_id is not None and tenant_id > 0:
        df = pd.read_sql_query("SELECT username,role,expiration_date,tenant_id FROM users_db WHERE tenant_id=?", conn, params=(tenant_id,))
    else:
        df = pd.read_sql_query("SELECT username,role,expiration_date,tenant_id FROM users_db", conn)
    conn.close()
    return df


def is_key_used(key):
    key = sanitize_alphanumeric(key, 100)
    if _use_supabase:
        r = _sb.table("used_keys").select("*").eq("key_text", key).execute()
        return bool(r.data)
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT * FROM used_keys WHERE key_text=?", (key,))
    used = cur.fetchone() is not None
    conn.close()
    return used


def mark_key_used(key, username):
    key = sanitize_alphanumeric(key, 100)
    username = sanitize_alphanumeric(username, 50)
    if _use_supabase:
        _sb.table("used_keys").insert({"key_text": key, "used_by": username, "used_date": str(datetime.now())}).execute()
    else:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("INSERT INTO used_keys VALUES (?,?,?)", (key, username, str(datetime.now())))
        conn.commit()
        conn.close()


def insert_carga(datos, username="system", tenant_id=1):
    username = sanitize_alphanumeric(username, 50)
    tenant_id = int(sanitize_number(tenant_id, 0, 9999))
    d = list(datos)
    d[0] = sanitize_text(d[0], 30)
    d[1] = sanitize_placa(d[1])
    d[2] = sanitize_text(d[2], 100)
    d[3] = sanitize_text(d[3], 30)
    d[4] = sanitize_number(d[4], 0, 9999999)
    d[5] = sanitize_number(d[5], 0, 99999)
    d[6] = sanitize_number(d[6], 0, 9999999)
    d[7] = sanitize_alphanumeric(d[7], 50)
    d[8] = sanitize_text(d[8], 100)
    d[9] = sanitize_alphanumeric(d[9], 50)
    d[10] = sanitize_number(d[10], 0, 999)
    d[11] = sanitize_number(d[11], 0, 999)
    d[12] = "ANOMALIA" if d[12] == "ANOMALIA" else "Normal"
    d[13] = "MANTENIMIENTO" if d[13] == "MANTENIMIENTO" else "OK"
    if len(d) > 14:
        d[14] = sanitize_number(d[14], -180, 180)
    if len(d) > 15:
        d[15] = sanitize_number(d[15], -180, 180)

    try:
        from ml import detectar_anomalia_ai
        if not _use_supabase:
            conn_ai = sqlite3.connect(DB_NAME)
            hist_df = pd.read_sql_query("SELECT litros, custo, kilometraje, fecha FROM cargas WHERE vehiculo=? AND tenant_id=? ORDER BY id DESC LIMIT 20", conn_ai, params=(d[1], tenant_id))
            conn_ai.close()
        else:
            r_ai = _sb.table("cargas").select("litros,custo,kilometraje,fecha").eq("vehiculo", d[1]).eq("tenant_id", tenant_id).order("id", desc=True).limit(20).execute()
            hist_df = pd.DataFrame(r_ai.data)

        if not hist_df.empty and len(hist_df) >= 8:
            nueva_carga_dict = {'litros': d[5], 'custo': d[6], 'kilometraje': d[4], 'hora': datetime.now().hour}
            es_anomalia_ai = detectar_anomalia_ai(hist_df, nueva_carga_dict)
            if es_anomalia_ai:
                d[12] = "ANOMALIA_AI"
                print(f"[AI] Anomalia AI detectada para vehiculo {d[1]}")
    except Exception as e:
        print(f"[AI] Error checking anomaly: {e}")

    if _use_supabase:
        doc = {
            "fecha": d[0], "vehiculo": d[1], "conductor": d[2], "tipo_combustible": d[3],
            "kilometraje": d[4], "litros": d[5], "custo": d[6], "factura": d[7],
            "estacion": d[8], "vale": d[9], "rendimento": d[10], "custo_por_km": d[11],
            "alerta_anomalia": d[12], "alerta_mantenimiento": d[13],
            "latitud": d[14] if len(d) > 14 else 0,
            "longitud": d[15] if len(d) > 15 else 0,
            "capturado_por": username, "tenant_id": tenant_id,
        }
        _sb.table("cargas").insert(doc).execute()
    else:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        if len(d) <= 14:
            d = d + [0.0, 0.0, username, str(datetime.now()), tenant_id]
        elif len(d) <= 16:
            d = d + [username, str(datetime.now()), tenant_id]
        else:
            while len(d) < 19:
                d.append("")
            d[17] = str(datetime.now())
            d[18] = tenant_id
        cur.execute("INSERT INTO cargas VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", d)
        conn.commit()
        conn.close()
    log_audit(username, "INSERT", "cargas", d[1], "Vehiculo:" + d[1] + " Km:" + str(d[4]))


def delete_carga(id_carga, username="system"):
    try:
        id_carga = int(id_carga)
    except:
        return
    username = sanitize_alphanumeric(username, 50)
    if _use_supabase:
        _sb.table("cargas").delete().eq("id", id_carga).execute()
    else:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("DELETE FROM cargas WHERE id=?", (id_carga,))
        conn.commit()
        conn.close()
    log_audit(username, "DELETE", "cargas", str(id_carga), "ID:" + str(id_carga))


def delete_vehiculo(placa, tenant_id=1, username="system"):
    placa = sanitize_placa(placa)
    if not placa:
        return False
    try:
        tenant_id = int(sanitize_number(tenant_id, 0, 9999))
    except:
        tenant_id = 1
    username = sanitize_alphanumeric(username, 50)
    try:
        if _use_supabase:
            _sb.table("vehiculos").delete().eq("placa", placa).eq("tenant_id", tenant_id).execute()
        else:
            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            cur.execute("DELETE FROM vehiculos WHERE placa=? AND tenant_id=?", (placa, tenant_id))
            conn.commit()
            conn.close()
        log_audit(username, "DELETE", "vehiculos", placa, "Placa:" + placa)
        return True
    except Exception as e:
        print("Error deleting vehiculo: " + str(e))
        return False


def get_data(tenant_id=None):
    if tenant_id is not None:
        tenant_id = int(sanitize_number(tenant_id, 0, 9999))
    # Columnas esperadas (para que el DataFrame nunca esté vacío de columnas)
    expected_cols = [
        'id', 'fecha', 'vehiculo', 'conductor', 'tipo_combustible',
        'kilometraje', 'litros', 'custo', 'factura', 'estacion', 'vale',
        'rendimento', 'custo_por_km', 'alerta_anomalia', 'alerta_mantenimiento',
        'latitud', 'longitud', 'capturado_por', 'fecha_captura', 'tenant_id'
    ]
    if _use_supabase:
        q = _sb.table("cargas").select("*").order("fecha", desc=True)
        if tenant_id is not None:
            q = q.eq("tenant_id", tenant_id)
        r = q.execute()
        df = pd.DataFrame(r.data)
        # Si el DataFrame está vacío, crear uno con todas las columnas esperadas
        if df.empty:
            df = pd.DataFrame(columns=expected_cols)
        else:
            # Asegurar que todas las columnas esperadas existan
            for col in expected_cols:
                if col not in df.columns:
                    df[col] = None
        return df
    conn = sqlite3.connect(DB_NAME)
    if tenant_id is not None:
        df = pd.read_sql_query("SELECT * FROM cargas WHERE tenant_id=? ORDER BY fecha DESC", conn, params=(tenant_id,))
    else:
        df = pd.read_sql_query("SELECT * FROM cargas ORDER BY fecha DESC", conn)
    conn.close()
    return df


def check_duplicate(field, value, tenant_id=1):
    try:
        validate_field(field, ALLOWED_DUPLICATE_FIELDS)
    except ValueError:
        return False
    if not value:
        return False
    value = sanitize_alphanumeric(value, 50)
    tenant_id = int(sanitize_number(tenant_id, 0, 9999))
    if _use_supabase:
        r = _sb.table("cargas").select("id").eq(field, value).eq("tenant_id", tenant_id).execute()
        return bool(r.data)
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT id FROM cargas WHERE " + field + "=? AND tenant_id=?", (value, tenant_id))
    exists = cur.fetchone() is not None
    conn.close()
    return exists


def evaluar_vehiculo(vehiculo, kilometraje_actual, litros, custo, exclude_id=None, tenant_id=None):
    vehiculo = sanitize_placa(vehiculo)
    kilometraje_actual = sanitize_number(kilometraje_actual, 0, 9999999)
    litros = sanitize_number(litros, 0, 99999)
    custo = sanitize_number(custo, 0, 9999999)
    if tenant_id is not None:
        tenant_id = int(sanitize_number(tenant_id, 0, 9999))
    try:
        exclude_id = int(exclude_id) if exclude_id else 0
    except:
        exclude_id = 0
    if _use_supabase:
        q = _sb.table("cargas").select("kilometraje,rendimento").eq("vehiculo", vehiculo).neq("id", exclude_id)
        if tenant_id is not None:
            q = q.eq("tenant_id", tenant_id)
        r = q.order("id", desc=True).limit(5).execute()
        rows = [(x["kilometraje"], x["rendimento"]) for x in r.data]
    else:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        if tenant_id is not None:
            cur.execute("SELECT kilometraje,rendimento FROM cargas WHERE vehiculo=? AND id!=? AND tenant_id=? ORDER BY id DESC LIMIT 5", (vehiculo, exclude_id, tenant_id))
        else:
            cur.execute("SELECT kilometraje,rendimento FROM cargas WHERE vehiculo=? AND id!=? ORDER BY id DESC LIMIT 5", (vehiculo, exclude_id))
        rows = cur.fetchall()
        conn.close()
    rend, ckm, a_anomalia, a_manto = 0.0, 0.0, "Normal", "OK"
    if rows:
        km_ant = rows[0][0] or 0.0
        km_rec = kilometraje_actual - km_ant
        if km_rec > 0 and litros > 0:
            rend = round(km_rec / litros, 2)
            ckm = round(custo / km_rec, 2)
            rend_ant = rows[0][1] or 0.0
            if rend_ant > 0 and rend < (rend_ant * 0.70):
                a_anomalia = "ANOMALIA"
            rends = [r[1] for r in rows if r[1] and r[1] > 0]
            if len(rends) >= 3:
                if rends[-1] < (sum(rends[:2]) / 2 * 0.90):
                    a_manto = "MANTENIMIENTO"
    return rend, ckm, a_anomalia, a_manto


def get_vehiculos(tenant_id=None):
    if tenant_id is not None:
        tenant_id = int(sanitize_number(tenant_id, 0, 9999))
    if _use_supabase:
        q = _sb.table("vehiculos").select("placa").order("placa")
        if tenant_id is not None:
            q = q.eq("tenant_id", tenant_id)
        r = q.execute()
        return [x["placa"] for x in r.data]
    conn = sqlite3.connect(DB_NAME)
    if tenant_id is not None:
        df = pd.read_sql_query("SELECT placa FROM vehiculos WHERE tenant_id=? ORDER BY placa", conn, params=(tenant_id,))
    else:
        df = pd.read_sql_query("SELECT placa FROM vehiculos ORDER BY placa", conn)
    conn.close()
    return df["placa"].tolist()


def insert_vehiculo(datos, username="system", tenant_id=1):
    username = sanitize_alphanumeric(username, 50)
    tenant_id = int(sanitize_number(tenant_id, 0, 9999))
    d = list(datos)
    while len(d) < 14:
        d.append("")
    d[0] = sanitize_placa(d[0])
    d[1] = sanitize_text(d[1], 50)
    d[2] = sanitize_text(d[2], 50)
    d[3] = sanitize_text(d[3], 30)
    d[4] = sanitize_text(d[4], 80)
    d[5] = sanitize_number(d[5], 0, 99999)
    d[6] = sanitize_number(d[6], 0, 9999999)
    d[7] = sanitize_number(d[7], 0, 999)
    d[8] = sanitize_number(d[8], 0, 9999999)
    d[9] = sanitize_number(d[9], 0, 9999999)
    d[10] = sanitize_text(d[10], 50)
    d[11] = sanitize_text(d[11], 30)
    d[12] = sanitize_alphanumeric(d[12], 50)
    d[13] = sanitize_alphanumeric(d[13], 30)
    if not d[0]:
        return False
    try:
        if _use_supabase:
            _sb.table("vehiculos").insert({
                "placa": d[0], "marca": d[1], "modelo": d[2], "tipo_combustible": d[3],
                "departamento": d[4], "capacidade": d[5], "km_inicial": d[6],
                "rendimiento_min": d[7], "km_proximo_servicio": d[8],
                "intervalo_km_servicio": d[9], "tipo_servicio": d[10],
                "fecha_ultimo_servicio": d[11], "poliza_seguro": d[12],
                "tel_operador": d[13], "tenant_id": tenant_id,
            }).execute()
        else:
            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            cur.execute("INSERT INTO vehiculos VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (d[0], d[1], d[2], d[3], d[4], d[5], d[6], d[7], d[8], d[9], d[10], d[11], d[12], d[13], tenant_id))
            conn.commit()
            conn.close()
        log_audit(username, "INSERT", "vehiculos", d[0], "Placa:" + d[0])
        return True
    except:
        return False


def get_all_vehiculos(tenant_id=None):
    if tenant_id is not None:
        tenant_id = int(sanitize_number(tenant_id, 0, 9999))
    if _use_supabase:
        q = _sb.table("vehiculos").select("*")
        if tenant_id is not None:
            q = q.eq("tenant_id", tenant_id)
        r = q.execute()
        return pd.DataFrame(r.data)
    conn = sqlite3.connect(DB_NAME)
    if tenant_id is not None:
        df = pd.read_sql_query("SELECT * FROM vehiculos WHERE tenant_id=?", conn, params=(tenant_id,))
    else:
        df = pd.read_sql_query("SELECT * FROM vehiculos", conn)
    conn.close()
    return df


def update_vehiculo(placa, tenant_id=None, **kwargs):
    placa = sanitize_placa(placa)
    if not placa:
        return
    safe = {}
    if "marca" in kwargs and kwargs["marca"] is not None:
        safe["marca"] = sanitize_text(kwargs["marca"], 50)
    if "modelo" in kwargs and kwargs["modelo"] is not None:
        safe["modelo"] = sanitize_text(kwargs["modelo"], 50)
    if "tipo_combustible" in kwargs and kwargs["tipo_combustible"] is not None:
        safe["tipo_combustible"] = sanitize_text(kwargs["tipo_combustible"], 30)
    if "departamento" in kwargs and kwargs["departamento"] is not None:
        safe["departamento"] = sanitize_text(kwargs["departamento"], 80)
    if "capacidad" in kwargs and kwargs["capacidad"] is not None:
        safe["capacidade"] = sanitize_number(kwargs["capacidad"], 0, 99999)
    if "capacidade" in kwargs and kwargs["capacidade"] is not None:
        safe["capacidade"] = sanitize_number(kwargs["capacidade"], 0, 99999)
    if "km_inicial" in kwargs and kwargs["km_inicial"] is not None:
        safe["km_inicial"] = sanitize_number(kwargs["km_inicial"], 0, 9999999)
    if "rendimiento_min" in kwargs and kwargs["rendimiento_min"] is not None:
        safe["rendimiento_min"] = sanitize_number(kwargs["rendimiento_min"], 0, 999)
    if "km_proximo_servicio" in kwargs and kwargs["km_proximo_servicio"] is not None:
        safe["km_proximo_servicio"] = sanitize_number(kwargs["km_proximo_servicio"], 0, 9999999)
    if "intervalo_km_servicio" in kwargs and kwargs["intervalo_km_servicio"] is not None:
        safe["intervalo_km_servicio"] = sanitize_number(kwargs["intervalo_km_servicio"], 0, 9999999)
    if "tipo_servicio" in kwargs and kwargs["tipo_servicio"] is not None:
        safe["tipo_servicio"] = sanitize_text(kwargs["tipo_servicio"], 50)
    if "fecha_ultimo_servicio" in kwargs and kwargs["fecha_ultimo_servicio"] is not None:
        safe["fecha_ultimo_servicio"] = sanitize_text(kwargs["fecha_ultimo_servicio"], 30)
    if "poliza" in kwargs and kwargs["poliza"] is not None:
        safe["poliza_seguro"] = sanitize_alphanumeric(kwargs["poliza"], 50)
    if "poliza_seguro" in kwargs and kwargs["poliza_seguro"] is not None:
        safe["poliza_seguro"] = sanitize_alphanumeric(kwargs["poliza_seguro"], 50)
    if "tel_operador" in kwargs and kwargs["tel_operador"] is not None:
        safe["tel_operador"] = sanitize_alphanumeric(kwargs["tel_operador"], 30)
    if not safe:
        return
    if _use_supabase:
        q = _sb.table("vehiculos").update(safe).eq("placa", placa)
        if tenant_id is not None:
            q = q.eq("tenant_id", int(tenant_id))
        q.execute()
    else:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        set_clause = ", ".join([k + "=?" for k in safe.keys()])
        values = list(safe.values())
        if tenant_id is not None:
            values = values + [placa, int(tenant_id)]
            cur.execute("UPDATE vehiculos SET " + set_clause + " WHERE placa=? AND tenant_id=?", values)
        else:
            values = values + [placa]
            cur.execute("UPDATE vehiculos SET " + set_clause + " WHERE placa=?", values)
        conn.commit()
        conn.close()


def init_estaciones():
    if _use_supabase:
        return
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "CREATE TABLE IF NOT EXISTS estaciones ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, "
        "direccion TEXT DEFAULT '', marca TEXT DEFAULT '', "
        "latitud REAL DEFAULT 0, longitud REAL DEFAULT 0, "
        "tenant_id INTEGER DEFAULT 1)"
    )
    conn.commit()
    conn.close()


def insert_estacion(nombre, direccion='', marca='', lat=0, lon=0, tenant_id=1):
    nombre = sanitize_text(nombre, 100)
    if not nombre:
        return None
    direccion = sanitize_text(direccion, 200)
    marca = sanitize_text(marca, 50)
    lat = sanitize_number(lat, -90, 90)
    lon = sanitize_number(lon, -180, 180)
    tenant_id = int(sanitize_number(tenant_id, 0, 9999))
    try:
        if _use_supabase:
            r = _sb.table("estaciones").insert({
                "nombre": nombre, "direccion": direccion, "marca": marca,
                "latitud": lat, "longitud": lon, "tenant_id": tenant_id
            }).execute()
            return r.data[0]["id"] if r.data else None
        else:
            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            cur.execute("INSERT INTO estaciones (nombre,direccion,marca,latitud,longitud,tenant_id) VALUES (?,?,?,?,?,?)",
                        (nombre, direccion, marca, lat, lon, tenant_id))
            eid = cur.lastrowid
            conn.commit()
            conn.close()
            return eid
    except:
        return None


def get_all_estaciones(tenant_id=None):
    if tenant_id is not None:
        tenant_id = int(sanitize_number(tenant_id, 0, 9999))
    if _use_supabase:
        q = _sb.table("estaciones").select("*").order("nombre")
        if tenant_id is not None:
            q = q.eq("tenant_id", tenant_id)
        r = q.execute()
        return pd.DataFrame(r.data)
    conn = sqlite3.connect(DB_NAME)
    if tenant_id is not None:
        df = pd.read_sql_query("SELECT * FROM estaciones WHERE tenant_id=? ORDER BY nombre", conn, params=(tenant_id,))
    else:
        df = pd.read_sql_query("SELECT * FROM estaciones ORDER BY nombre", conn)
    conn.close()
    return df


def delete_estacion(eid, tenant_id=1):
    try:
        eid = int(eid)
    except:
        return
    tenant_id = int(sanitize_number(tenant_id, 0, 9999))
    if _use_supabase:
        _sb.table("estaciones").delete().eq("id", eid).eq("tenant_id", tenant_id).execute()
    else:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("DELETE FROM estaciones WHERE id=? AND tenant_id=?", (eid, tenant_id))
        conn.commit()
        conn.close()


def update_estacion(eid, tenant_id=None, **kwargs):
    try:
        eid = int(eid)
    except:
        return
    safe = {}
    if "nombre" in kwargs and kwargs["nombre"] is not None:
        safe["nombre"] = sanitize_text(kwargs["nombre"], 100)
    if "direccion" in kwargs and kwargs["direccion"] is not None:
        safe["direccion"] = sanitize_text(kwargs["direccion"], 200)
    if "marca" in kwargs and kwargs["marca"] is not None:
        safe["marca"] = sanitize_text(kwargs["marca"], 50)
    if "latitud" in kwargs and kwargs["latitud"] is not None:
        safe["latitud"] = sanitize_number(kwargs["latitud"], -90, 90)
    if "longitud" in kwargs and kwargs["longitud"] is not None:
        safe["longitud"] = sanitize_number(kwargs["longitud"], -180, 180)
    if not safe:
        return
    if _use_supabase:
        q = _sb.table("estaciones").update(safe).eq("id", eid)
        if tenant_id is not None:
            q = q.eq("tenant_id", int(tenant_id))
        q.execute()
    else:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        set_clause = ", ".join([k + "=?" for k in safe.keys()])
        values = list(safe.values())
        if tenant_id is not None:
            values = values + [eid, int(tenant_id)]
            cur.execute("UPDATE estaciones SET " + set_clause + " WHERE id=? AND tenant_id=?", values)
        else:
            values = values + [eid]
            cur.execute("UPDATE estaciones SET " + set_clause + " WHERE id=?", values)
        conn.commit()
        conn.close()


def init_conductores():
    if _use_supabase:
        return
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "CREATE TABLE IF NOT EXISTS conductores ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, "
        "licencia TEXT DEFAULT '', vigencia_lic TEXT DEFAULT '', "
        "telefono TEXT DEFAULT '', vehiculo_asignado TEXT DEFAULT '', "
        "estatus TEXT DEFAULT 'Activo', tenant_id INTEGER DEFAULT 1)"
    )
    conn.commit()
    conn.close()


def insert_conductor(nombre, licencia='', vigencia='', telefono='', vehiculo='', estatus='Activo', tenant_id=1):
    nombre = sanitize_text(nombre, 100)
    if not nombre:
        return None
    try:
        if _use_supabase:
            r = _sb.table("conductores").insert({
                "nombre": nombre, "licencia": sanitize_alphanumeric(licencia, 30),
                "vigencia_lic": sanitize_text(vigencia, 30),
                "telefono": sanitize_alphanumeric(telefono, 30),
                "vehiculo_asignado": sanitize_placa(vehiculo),
                "estatus": sanitize_text(estatus, 20), "tenant_id": int(tenant_id)
            }).execute()
            return r.data[0]["id"] if r.data else None
        else:
            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            cur.execute("INSERT INTO conductores (nombre,licencia,vigencia_lic,telefono,vehiculo_asignado,estatus,tenant_id) VALUES (?,?,?,?,?,?,?)",
                        (nombre, licencia, vigencia, telefono, vehiculo, estatus, int(tenant_id)))
            eid = cur.lastrowid
            conn.commit()
            conn.close()
            return eid
    except:
        return None


def get_all_conductores(tenant_id=None):
    if tenant_id is not None:
        tenant_id = int(sanitize_number(tenant_id, 0, 9999))
    if _use_supabase:
        q = _sb.table("conductores").select("*").order("nombre")
        if tenant_id is not None:
            q = q.eq("tenant_id", tenant_id)
        r = q.execute()
        return pd.DataFrame(r.data)
    conn = sqlite3.connect(DB_NAME)
    if tenant_id is not None:
        df = pd.read_sql_query("SELECT * FROM conductores WHERE tenant_id=? ORDER BY nombre", conn, params=(tenant_id,))
    else:
        df = pd.read_sql_query("SELECT * FROM conductores ORDER BY nombre", conn)
    conn.close()
    return df


def delete_conductor(cid, tenant_id=1):
    try:
        cid = int(cid)
    except:
        return
    tenant_id = int(sanitize_number(tenant_id, 0, 9999))
    if _use_supabase:
        _sb.table("conductores").delete().eq("id", cid).eq("tenant_id", tenant_id).execute()
    else:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("DELETE FROM conductores WHERE id=? AND tenant_id=?", (cid, tenant_id))
        conn.commit()
        conn.close()


def init_presupuestos():
    if _use_supabase:
        return
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "CREATE TABLE IF NOT EXISTS presupuestos ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "categoria TEXT, limite_mensual REAL DEFAULT 0, "
        "tipo TEXT DEFAULT 'vehiculo', tenant_id INTEGER DEFAULT 1)"
    )
    conn.commit()
    conn.close()


def set_presupuesto(categoria, limite, tipo='vehiculo', tenant_id=1):
    categoria = sanitize_text(categoria, 100)
    limite = sanitize_number(limite, 0, 9999999)
    tipo = sanitize_text(tipo, 20)
    tenant_id = int(sanitize_number(tenant_id, 0, 9999))
    if _use_supabase:
        existing = _sb.table("presupuestos").select("id").eq("categoria", categoria).eq("tipo", tipo).eq("tenant_id", tenant_id).execute()
        if existing.data:
            _sb.table("presupuestos").update({"limite_mensual": limite}).eq("id", existing.data[0]["id"]).execute()
        else:
            _sb.table("presupuestos").insert({"categoria": categoria, "limite_mensual": limite, "tipo": tipo, "tenant_id": tenant_id}).execute()
    else:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT id FROM presupuestos WHERE categoria=? AND tipo=? AND tenant_id=?", (categoria, tipo, tenant_id))
        row = cur.fetchone()
        if row:
            cur.execute("UPDATE presupuestos SET limite_mensual=? WHERE id=?", (limite, row[0]))
        else:
            cur.execute("INSERT INTO presupuestos (categoria,limite_mensual,tipo,tenant_id) VALUES (?,?,?,?)", (categoria, limite, tipo, tenant_id))
        conn.commit()
        conn.close()


def get_presupuestos(tenant_id=None):
    if tenant_id is not None:
        tenant_id = int(sanitize_number(tenant_id, 0, 9999))
    if _use_supabase:
        q = _sb.table("presupuestos").select("*")
        if tenant_id is not None:
            q = q.eq("tenant_id", tenant_id)
        r = q.execute()
        return pd.DataFrame(r.data)
    conn = sqlite3.connect(DB_NAME)
    if tenant_id is not None:
        df = pd.read_sql_query("SELECT * FROM presupuestos WHERE tenant_id=?", conn, params=(tenant_id,))
    else:
        df = pd.read_sql_query("SELECT * FROM presupuestos", conn)
    conn.close()
    return df


def check_presupuesto(categoria, gasto_actual, tipo='vehiculo', tenant_id=1):
    presups = get_presupuestos(tenant_id)
    if presups.empty:
        return None
    match = presups[(presups['categoria'] == categoria) & (presups['tipo'] == tipo)]
    if match.empty:
        return None
    limite = match.iloc[0]['limite_mensual']
    pct = (gasto_actual / limite * 100) if limite > 0 else 0
    return {'limite': limite, 'gasto': gasto_actual, 'pct': pct, 'alerta': pct >= 80}


def init_precios():
    if _use_supabase:
        return
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "CREATE TABLE IF NOT EXISTS precios_comb ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "estacion TEXT, tipo_combustible TEXT, "
        "precio REAL DEFAULT 0, fecha TEXT, "
        "tenant_id INTEGER DEFAULT 1)"
    )
    conn.commit()
    conn.close()


def insert_precio(estacion, tipo, precio, fecha, tenant_id=1):
    estacion = sanitize_text(estacion, 100)
    tipo = sanitize_text(tipo, 30)
    precio = sanitize_number(precio, 0, 999)
    fecha = sanitize_text(fecha, 30)
    tenant_id = int(sanitize_number(tenant_id, 0, 9999))
    if _use_supabase:
        _sb.table("precios_comb").insert({
            "estacion": estacion, "tipo_combustible": tipo,
            "precio": precio, "fecha": fecha, "tenant_id": tenant_id
        }).execute()
    else:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("INSERT INTO precios_comb (estacion,tipo_combustible,precio,fecha,tenant_id) VALUES (?,?,?,?,?)",
                    (estacion, tipo, precio, fecha, tenant_id))
        conn.commit()
        conn.close()


def get_precios(tenant_id=None):
    if tenant_id is not None:
        tenant_id = int(sanitize_number(tenant_id, 0, 9999))
    if _use_supabase:
        q = _sb.table("precios_comb").select("*").order("fecha", desc=True)
        if tenant_id is not None:
            q = q.eq("tenant_id", tenant_id)
        r = q.execute()
        return pd.DataFrame(r.data)
    conn = sqlite3.connect(DB_NAME)
    if tenant_id is not None:
        df = pd.read_sql_query("SELECT * FROM precios_comb WHERE tenant_id=? ORDER BY fecha DESC", conn, params=(tenant_id,))
    else:
        df = pd.read_sql_query("SELECT * FROM precios_comb ORDER BY fecha DESC", conn)
    conn.close()
    return df


def delete_precio(pid, tenant_id=1):
    try:
        pid = int(pid)
    except:
        return
    tenant_id = int(sanitize_number(tenant_id, 0, 9999))
    if _use_supabase:
        _sb.table("precios_comb").delete().eq("id", pid).eq("tenant_id", tenant_id).execute()
    else:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("DELETE FROM precios_comb WHERE id=? AND tenant_id=?", (pid, tenant_id))
        conn.commit()
        conn.close()


def get_audit_log(tenant_id=None, limit=200):
    if _use_supabase:
        q = _sb.table("audit_log").select("*").order("timestamp", desc=True).limit(limit)
        if tenant_id is not None:
            q = q.eq("tenant_id", tenant_id)
        r = q.execute()
        return pd.DataFrame(r.data)
    conn = sqlite3.connect(DB_NAME)
    try:
        if tenant_id is not None:
            df = pd.read_sql_query("SELECT * FROM audit_log WHERE tenant_id=? ORDER BY timestamp DESC LIMIT ?", conn, params=(tenant_id, limit))
        else:
            df = pd.read_sql_query("SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT ?", conn, params=(limit,))
    except:
        df = pd.DataFrame()
    conn.close()
    return df


def init_report_schedules():
    if _use_supabase:
        return
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "CREATE TABLE IF NOT EXISTS report_schedules ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "nombre TEXT NOT NULL, "
        "frecuencia TEXT DEFAULT 'mensual', "
        "dia_semana INTEGER DEFAULT 0, "
        "dia_mes INTEGER DEFAULT 1, "
        "hora INTEGER DEFAULT 8, "
        "formato TEXT DEFAULT 'pdf', "
        "destinatarios TEXT DEFAULT '', "
        "tipo_reporte TEXT DEFAULT 'completo', "
        "activo INTEGER DEFAULT 1, "
        "ultimo_envio TEXT DEFAULT '', "
        "tenant_id INTEGER DEFAULT 1, "
        "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
    )
    conn.commit()
    conn.close()


def insert_report_schedule(nombre, frecuencia='mensual', dia_semana=0, dia_mes=1, hora=8, formato='pdf', destinatarios='', tipo_reporte='completo', tenant_id=1):
    nombre = sanitize_text(nombre, 100)
    if not nombre:
        return None
    if frecuencia not in ('diario', 'semanal', 'mensual'):
        frecuencia = 'mensual'
    if formato not in ('pdf', 'excel', 'ambos'):
        formato = 'pdf'
    if tipo_reporte not in ('completo', 'anomalias', 'flotilla', 'presupuesto'):
        tipo_reporte = 'completo'
    destinatarios = sanitize_text(destinatarios, 500)
    hora = int(sanitize_number(hora, 0, 23))
    dia_semana = int(sanitize_number(dia_semana, 0, 6))
    dia_mes = int(sanitize_number(dia_mes, 1, 31))
    tenant_id = int(sanitize_number(tenant_id, 0, 9999))
    try:
        if _use_supabase:
            r = _sb.table("report_schedules").insert({
                "nombre": nombre, "frecuencia": frecuencia,
                "dia_semana": dia_semana, "dia_mes": dia_mes,
                "hora": hora, "formato": formato,
                "destinatarios": destinatarios, "tipo_reporte": tipo_reporte,
                "activo": 1, "ultimo_envio": "", "tenant_id": tenant_id
            }).execute()
            return r.data[0]["id"] if r.data else None
        else:
            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO report_schedules (nombre, frecuencia, dia_semana, dia_mes, hora, formato, destinatarios, tipo_reporte, activo, ultimo_envio, tenant_id) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (nombre, frecuencia, dia_semana, dia_mes, hora, formato, destinatarios, tipo_reporte, 1, '', tenant_id))
            nid = cur.lastrowid
            conn.commit()
            conn.close()
            return nid
    except Exception as e:
        print("Error inserting report schedule: " + str(e))
        return None


def get_all_report_schedules(tenant_id=None):
    if tenant_id is not None:
        tenant_id = int(sanitize_number(tenant_id, 0, 9999))
    if _use_supabase:
        q = _sb.table("report_schedules").select("*").order("nombre")
        if tenant_id is not None:
            q = q.eq("tenant_id", tenant_id)
        r = q.execute()
        return pd.DataFrame(r.data) if r.data else pd.DataFrame()
    conn = sqlite3.connect(DB_NAME)
    if tenant_id is not None:
        df = pd.read_sql_query("SELECT * FROM report_schedules WHERE tenant_id=? ORDER BY nombre", conn, params=(tenant_id,))
    else:
        df = pd.read_sql_query("SELECT * FROM report_schedules ORDER BY nombre", conn)
    conn.close()
    return df


def update_schedule_last_sent(schedule_id, timestamp, tenant_id=1):
    try:
        schedule_id = int(schedule_id)
    except:
        return
    tenant_id = int(sanitize_number(tenant_id, 0, 9999))
    if _use_supabase:
        _sb.table("report_schedules").update({"ultimo_envio": timestamp}).eq("id", schedule_id).eq("tenant_id", tenant_id).execute()
    else:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("UPDATE report_schedules SET ultimo_envio=? WHERE id=? AND tenant_id=?", (timestamp, schedule_id, tenant_id))
        conn.commit()
        conn.close()


def toggle_report_schedule(schedule_id, activo, tenant_id=1):
    try:
        schedule_id = int(schedule_id)
    except:
        return
    activo = 1 if activo else 0
    tenant_id = int(sanitize_number(tenant_id, 0, 9999))
    if _use_supabase:
        _sb.table("report_schedules").update({"activo": activo}).eq("id", schedule_id).eq("tenant_id", tenant_id).execute()
    else:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("UPDATE report_schedules SET activo=? WHERE id=? AND tenant_id=?", (activo, schedule_id, tenant_id))
        conn.commit()
        conn.close()


def delete_report_schedule(schedule_id, tenant_id=1):
    try:
        schedule_id = int(schedule_id)
    except:
        return
    tenant_id = int(sanitize_number(tenant_id, 0, 9999))
    if _use_supabase:
        _sb.table("report_schedules").delete().eq("id", schedule_id).eq("tenant_id", tenant_id).execute()
    else:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("DELETE FROM report_schedules WHERE id=? AND tenant_id=?", (schedule_id, tenant_id))
        conn.commit()
        conn.close()


def init_notification_settings():
    if _use_supabase:
        return
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "CREATE TABLE IF NOT EXISTS notification_settings ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "tipo TEXT NOT NULL, "
        "activo INTEGER DEFAULT 1, "
        "email TEXT DEFAULT '', "
        "ultimo_envio TEXT DEFAULT '', "
        "tenant_id INTEGER DEFAULT 1)"
    )
    conn.commit()
    conn.close()


def ensure_default_notifications(tenant_id=1):
    tenant_id = int(sanitize_number(tenant_id, 0, 9999))
    defaults = [
        ('anomalia', 'Alerta al detectar anomalía en rendimiento'),
        ('mantenimiento', 'Alerta de mantenimiento vencido'),
        ('presupuesto_80', 'Presupuesto al 80%'),
        ('presupuesto_100', 'Presupuesto excedido'),
    ]
    if _use_supabase:
        return
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    for tipo, desc in defaults:
        cur.execute("SELECT id FROM notification_settings WHERE tipo=? AND tenant_id=?", (tipo, tenant_id))
        if not cur.fetchone():
            cur.execute("INSERT INTO notification_settings (tipo, activo, email, tenant_id) VALUES (?,?,?,?)", (tipo, 1, '', tenant_id))
    conn.commit()
    conn.close()


def get_notification_settings(tenant_id=1):
    tenant_id = int(sanitize_number(tenant_id, 0, 9999))
    if _use_supabase:
        try:
            r = _sb.table("notification_settings").select("*").eq("tenant_id", tenant_id).execute()
            return pd.DataFrame(r.data) if r.data else pd.DataFrame()
        except:
            return pd.DataFrame()
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM notification_settings WHERE tenant_id=?", conn, params=(tenant_id,))
    conn.close()
    return df


def save_notification_setting(tipo, activo, email, tenant_id=1):
    tipo = sanitize_text(tipo, 50)
    email = sanitize_text(email, 200)
    activo = 1 if activo else 0
    tenant_id = int(sanitize_number(tenant_id, 0, 9999))
    if _use_supabase:
        try:
            existing = _sb.table("notification_settings").select("id").eq("tipo", tipo).eq("tenant_id", tenant_id).execute()
            if existing.data:
                _sb.table("notification_settings").update({"activo": activo, "email": email}).eq("id", existing.data[0]["id"]).execute()
            else:
                _sb.table("notification_settings").insert({"tipo": tipo, "activo": activo, "email": email, "tenant_id": tenant_id}).execute()
        except:
            pass
    else:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT id FROM notification_settings WHERE tipo=? AND tenant_id=?", (tipo, tenant_id))
        row = cur.fetchone()
        if row:
            cur.execute("UPDATE notification_settings SET activo=?, email=? WHERE id=?", (activo, email, row[0]))
        else:
            cur.execute("INSERT INTO notification_settings (tipo, activo, email, tenant_id) VALUES (?,?,?,?)", (tipo, activo, email, tenant_id))
        conn.commit()
        conn.close()


def update_notification_last_sent(tipo, timestamp, tenant_id=1):
    tipo = sanitize_text(tipo, 50)
    tenant_id = int(sanitize_number(tenant_id, 0, 9999))
    if _use_supabase:
        try:
            existing = _sb.table("notification_settings").select("id").eq("tipo", tipo).eq("tenant_id", tenant_id).execute()
            if existing.data:
                _sb.table("notification_settings").update({"ultimo_envio": timestamp}).eq("id", existing.data[0]["id"]).execute()
        except:
            pass
    else:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("UPDATE notification_settings SET ultimo_envio=? WHERE tipo=? AND tenant_id=?", (timestamp, tipo, tenant_id))
        conn.commit()
        conn.close()
