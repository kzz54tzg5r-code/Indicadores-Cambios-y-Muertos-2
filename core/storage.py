
from __future__ import annotations

from pathlib import Path
from datetime import datetime
import json
import shutil

UPLOAD_DIR = Path("data/uploads")
CONFIG_DIR = Path("data/config")
PERSIST_DIR = Path("data/persistencia")
ACTIVE_FILE = UPLOAD_DIR / "base_activa.xlsx"
META_FILE = CONFIG_DIR / "metadata.json"
USERS_FILE = CONFIG_DIR / "usuarios.json"
GOALS_FILE = CONFIG_DIR / "metas.json"

for p in [UPLOAD_DIR, CONFIG_DIR, PERSIST_DIR]:
    p.mkdir(parents=True, exist_ok=True)


def save_uploaded_file(uploaded_file):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    with open(ACTIVE_FILE, "wb") as f:
        f.write(uploaded_file.getbuffer())
    meta = {
        "nombre_original": uploaded_file.name,
        "fecha_carga": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    META_FILE.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def active_file_exists() -> bool:
    return ACTIVE_FILE.exists()


def get_active_file_path() -> Path | None:
    return ACTIVE_FILE if ACTIVE_FILE.exists() else None


def delete_active_file():
    if ACTIVE_FILE.exists():
        ACTIVE_FILE.unlink()
    if META_FILE.exists():
        META_FILE.unlink()


def get_metadata() -> dict:
    if META_FILE.exists():
        try:
            return json.loads(META_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def load_users() -> list[dict]:
    if USERS_FILE.exists():
        try:
            data = json.loads(USERS_FILE.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except Exception:
            return []
    default = [
        {"nomina": "admin", "nombre": "Administrador", "permiso": "Administrador", "password": "admin123", "activo": True},
    ]
    save_users(default)
    return default


def save_users(users: list[dict]):
    USERS_FILE.write_text(json.dumps(users, ensure_ascii=False, indent=2), encoding="utf-8")


def load_goals() -> dict:
    default = {"productividad_diaria": 784, "recorridos_semanal": 47, "conversion_meta": 90.0}
    if GOALS_FILE.exists():
        try:
            data = json.loads(GOALS_FILE.read_text(encoding="utf-8"))
            default.update(data)
        except Exception:
            pass
    return default


def save_goals(goals: dict):
    GOALS_FILE.write_text(json.dumps(goals, ensure_ascii=False, indent=2), encoding="utf-8")
