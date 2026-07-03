
from __future__ import annotations

from pathlib import Path
from datetime import datetime
import json
import sqlite3

UPLOAD_DIR = Path("data/uploads")
CONFIG_DIR = Path("data/config")
ACTIVE_FILE = UPLOAD_DIR / "base_activa.xlsx"
META_FILE = CONFIG_DIR / "metadata.json"
DB_FILE = CONFIG_DIR / "app_config.db"

for p in [UPLOAD_DIR, CONFIG_DIR]:
    p.mkdir(parents=True, exist_ok=True)


def get_conn():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            nomina TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            permiso TEXT NOT NULL DEFAULT 'Consulta',
            password TEXT NOT NULL,
            activo INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS goals (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    conn.commit()

    cur.execute("SELECT COUNT(*) AS total FROM users")
    total = cur.fetchone()["total"]
    if total == 0:
        cur.execute(
            "INSERT INTO users (nomina, nombre, permiso, password, activo, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            ("admin", "Administrador", "Administrador", "admin123", 1, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
        conn.commit()

    default_goals = {
        "productividad_diaria": "784",
        "recorridos_semanal": "47",
        "conversion_meta": "90.0",
    }
    for k, v in default_goals.items():
        cur.execute("INSERT OR IGNORE INTO goals (key, value) VALUES (?, ?)", (k, v))
    conn.commit()
    conn.close()


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
    init_db()
    conn = get_conn()
    rows = conn.execute("SELECT nomina, nombre, permiso, password, activo, created_at FROM users ORDER BY permiso DESC, nombre").fetchall()
    conn.close()
    return [
        {
            "nomina": r["nomina"],
            "nombre": r["nombre"],
            "permiso": r["permiso"],
            "password": r["password"],
            "activo": bool(r["activo"]),
            "created_at": r["created_at"],
        }
        for r in rows
    ]


def upsert_user(nomina: str, nombre: str, permiso: str, password: str | None = None, activo: bool = True):
    init_db()
    conn = get_conn()
    cur = conn.cursor()
    existing = cur.execute("SELECT nomina FROM users WHERE nomina = ?", (nomina,)).fetchone()
    if existing:
        if password:
            cur.execute(
                "UPDATE users SET nombre=?, permiso=?, password=?, activo=? WHERE nomina=?",
                (nombre, permiso, password, int(activo), nomina),
            )
        else:
            cur.execute(
                "UPDATE users SET nombre=?, permiso=?, activo=? WHERE nomina=?",
                (nombre, permiso, int(activo), nomina),
            )
    else:
        if not password:
            raise ValueError("La contraseña es obligatoria para usuarios nuevos.")
        cur.execute(
            "INSERT INTO users (nomina, nombre, permiso, password, activo, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (nomina, nombre, permiso, password, int(activo), datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
    conn.commit()
    conn.close()


def delete_user(nomina: str):
    init_db()
    conn = get_conn()
    conn.execute("DELETE FROM users WHERE nomina = ?", (nomina,))
    conn.commit()
    conn.close()


def save_users(users: list[dict]):
    init_db()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM users")
    for u in users:
        cur.execute(
            "INSERT INTO users (nomina, nombre, permiso, password, activo, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (
                u.get("nomina", ""),
                u.get("nombre", ""),
                u.get("permiso", "Consulta"),
                u.get("password", ""),
                int(bool(u.get("activo", True))),
                u.get("created_at") or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )
    conn.commit()
    conn.close()


def load_goals() -> dict:
    init_db()
    conn = get_conn()
    rows = conn.execute("SELECT key, value FROM goals").fetchall()
    conn.close()
    data = {r["key"]: r["value"] for r in rows}
    return {
        "productividad_diaria": int(float(data.get("productividad_diaria", 784))),
        "recorridos_semanal": int(float(data.get("recorridos_semanal", 47))),
        "conversion_meta": float(data.get("conversion_meta", 90.0)),
    }


def save_goals(goals: dict):
    init_db()
    conn = get_conn()
    cur = conn.cursor()
    for k, v in goals.items():
        cur.execute("INSERT OR REPLACE INTO goals (key, value) VALUES (?, ?)", (k, str(v)))
    conn.commit()
    conn.close()
