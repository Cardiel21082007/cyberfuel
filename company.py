import json
import base64
from pathlib import Path

CONFIG_DIR = Path(__file__).parent

DEFAULT_CONFIG = {
    "empresa": "Mi Empresa S.A. de C.V.",
    "razon_social": "",
    "rfc": "",
    "direccion": "",
    "ciudad": "",
    "telefono": "",
    "email": "",
    "website": "",
    "logo_b64": "",
    "color_primario": "#00ff88",
    "color_secundario": "#0e1117",
    "pie_reporte": "Reporte generado automáticamente — {empresa} — {fecha}",
    "formato_hoja": "Letter",
    "orientacion": "portrait"
}

def _config_file(tenant_id):
    if tenant_id and tenant_id > 0:
        return CONFIG_DIR / f"company_config_{tenant_id}.json"
    return CONFIG_DIR / "company_config_global.json"

def load_config(tenant_id=1):
    fpath = _config_file(tenant_id)
    if fpath.exists():
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                saved = json.load(f)
            cfg = DEFAULT_CONFIG.copy()
            cfg.update(saved)
            return cfg
        except:
            pass
    # Fallback: intentar leer datos de la org desde la BD
    try:
        from db import get_org_info
        org = get_org_info(tenant_id)
        if org:
            cfg = DEFAULT_CONFIG.copy()
            cfg["empresa"] = org.get("nombre", cfg["empresa"])
            cfg["rfc"] = org.get("rfc", "")
            cfg["direccion"] = org.get("direccion", "")
            cfg["telefono"] = org.get("telefono", "")
            cfg["email"] = org.get("email", "")
            cfg["color_primario"] = org.get("color_primario", "#00ff88")
            cfg["logo_b64"] = org.get("logo_b64", "")
            return cfg
    except:
        pass
    return DEFAULT_CONFIG.copy()

def save_config(cfg, tenant_id=1):
    fpath = _config_file(tenant_id)
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    # También guardar en la org de la BD
    try:
        from db import update_organization
        update_organization(tenant_id,
            nombre=cfg.get("empresa",""),
            rfc=cfg.get("rfc",""),
            direccion=cfg.get("direccion",""),
            telefono=cfg.get("telefono",""),
            email=cfg.get("email",""),
            color_primario=cfg.get("color_primario","#00ff88"),
            logo_b64=cfg.get("logo_b64",""))
    except:
        pass

def get_logo_bytes(tenant_id=1):
    cfg = load_config(tenant_id)
    if cfg.get("logo_b64"):
        try:
            return base64.b64decode(cfg["logo_b64"])
        except:
            pass
    return None