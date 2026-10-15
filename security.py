import re
import time
import hashlib

try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False


def hash_password(password):
    if not password or len(password) < 4:
        raise ValueError("Short")
    if len(password) > 128:
        password = password[:128]
    if BCRYPT_AVAILABLE:
        enc = password.encode("utf-8")
        sal = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(enc, sal).decode("utf-8")
    else:
        import secrets
        s = secrets.token_hex(16)
        h = hashlib.sha256((s + password).encode()).hexdigest()
        return "sha256$" + s + "$" + h


def verify_password(password, hashed):
    if not password or not hashed:
        return False
    if hashed.startswith("$2"):
        if not BCRYPT_AVAILABLE:
            return False
        try:
            enc_pw = password.encode("utf-8")
            enc_ha = hashed.encode("utf-8")
            return bcrypt.checkpw(enc_pw, enc_ha)
        except:
            return False
    if hashed.startswith("sha256$"):
        try:
            parts = hashed.split("$")
            s = parts[1]
            h = hashlib.sha256((s + password).encode()).hexdigest()
            return h == parts[2]
        except:
            return False
    try:
        legacy = hashlib.sha256(password.encode()).hexdigest()
        return legacy == hashed
    except:
        return False


def is_legacy_hash(hashed):
    if not hashed:
        return False
    if hashed.startswith("$2") or hashed.startswith("sha256$"):
        return False
    return True


def sanitize_text(text, max_len=100):
    if not text:
        return ""
    text = str(text).strip()
    text = re.sub(r"[\x00-\x1f\x7f]", "", text)
    text = re.sub(r"<[^>]*>", "", text)
    text = re.sub(r"(?i)(script|eval|exec|insert|delete|drop|alter|create|union)", "", text)
    return text[:max_len]


def sanitize_alphanumeric(text, max_len=50):
    if not text:
        return ""
    text = str(text).strip()
    text = re.sub(r"[^\w\s\-\.\@]", "", text)
    return text[:max_len]


def sanitize_placa(text):
    if not text:
        return ""
    text = str(text).strip().upper()
    text = re.sub(r"[^A-Z0-9]", "", text)
    return text[:10]


def sanitize_number(val, min_val=0, max_val=999999999):
    try:
        n = float(val)
        return max(min_val, min(n, max_val))
    except:
        return min_val


def sanitize_km(val):
    return sanitize_number(val, 0, 9999999)


def sanitize_litros(val):
    return sanitize_number(val, 0, 99999)


def sanitize_costo(val):
    return sanitize_number(val, 0, 9999999)


def sanitize_coords(val):
    return sanitize_number(val, -180, 180)


ALLOWED_DUPLICATE_FIELDS = {"factura", "vale"}
ALLOWED_SORT_FIELDS = {"fecha", "vehiculo", "custo", "kilometraje", "id"}


def validate_field(field, allowed_set):
    if field not in allowed_set:
        raise ValueError("Campo no permitido: " + str(field))
    return field


class RateLimiter:
    def __init__(self, max_attempts=5, base_block=60, max_block=3600):
        self.max_attempts = max_attempts
        self.base_block = base_block
        self.max_block = max_block

    def check(self, session_state, key="login"):
        ak = key + "_attempts"
        bk = key + "_blocked_until"
        if ak not in session_state:
            session_state[ak] = 0
        if bk not in session_state:
            session_state[bk] = 0
        now = time.time()
        if now < session_state[bk]:
            wait = int(session_state[bk] - now)
            return False, wait
        return True, 0

    def record_failure(self, session_state, key="login"):
        ak = key + "_attempts"
        bk = key + "_blocked_until"
        session_state[ak] = session_state.get(ak, 0) + 1
        attempts = session_state[ak]
        if attempts >= self.max_attempts:
            mult = 2 ** (attempts - self.max_attempts)
            bt = min(self.base_block * mult, self.max_block)
            session_state[bk] = time.time() + bt
            return bt
        return 0

    def reset(self, session_state, key="login"):
        session_state[key + "_attempts"] = 0
        session_state[key + "_blocked_until"] = 0


SESSION_TIMEOUT_SECONDS = 1800


def check_session_timeout(session_state):
    if "user" not in session_state:
        return False
    now = time.time()
    if "last_activity" not in session_state:
        session_state["last_activity"] = now
        return True
    elapsed = now - session_state["last_activity"]
    if elapsed > SESSION_TIMEOUT_SECONDS:
        del session_state["user"]
        session_state["session_expired"] = True
        return False
    session_state["last_activity"] = now
    return True


def password_strength(password):
    if not password:
        return 0, "Vacia"
    score = 0
    msgs = []
    if len(password) >= 8:
        score += 1
    else:
        msgs.append("min 8 chars")
    if re.search(r"[A-Z]", password):
        score += 1
    else:
        msgs.append("1 mayuscula")
    if re.search(r"[a-z]", password):
        score += 1
    else:
        msgs.append("1 minuscula")
    if re.search(r"[0-9]", password):
        score += 1
    else:
        msgs.append("1 numero")
    if re.search(r"[^A-Za-z0-9]", password):
        score += 1
    labels = {
        0: "Muy debil",
        1: "Debil",
        2: "Regular",
        3: "Buena",
        4: "Fuerte",
        5: "Muy fuerte",
    }
    label = labels.get(score, "Debil")
    if msgs:
        label = label + " (falta: " + ", ".join(msgs) + ")"
    return score, label