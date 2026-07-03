from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
PERSIST_DIR = DATA_DIR / "persistencia"
CACHE_DIR = DATA_DIR / "cache"

LAST_FILE_PATH = PERSIST_DIR / "ultimo_archivo.xlsx"
METADATA_PATH = PERSIST_DIR / "metadata_archivo.json"
CONFIG_PATH = PERSIST_DIR / "configuracion.json"

def asegurar_directorios() -> None:
    for path in [DATA_DIR, UPLOADS_DIR, PERSIST_DIR, CACHE_DIR]:
        path.mkdir(parents=True, exist_ok=True)

def guardar_archivo_persistente(uploaded_file):
    asegurar_directorios()
    if uploaded_file is None:
        return None
    with open(LAST_FILE_PATH, "wb") as file:
        file.write(uploaded_file.getbuffer())
    metadata = {
        "nombre_original": uploaded_file.name,
        "fecha_carga": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ruta": str(LAST_FILE_PATH),
        "tamano_bytes": LAST_FILE_PATH.stat().st_size,
    }
    METADATA_PATH.write_text(json.dumps(metadata, ensure_ascii=False, indent=4), encoding="utf-8")
    return LAST_FILE_PATH

def existe_archivo_persistente() -> bool:
    return LAST_FILE_PATH.exists()

def obtener_archivo_persistente():
    asegurar_directorios()
    return LAST_FILE_PATH if LAST_FILE_PATH.exists() else None

def obtener_metadata_archivo() -> dict:
    if METADATA_PATH.exists():
        try:
            return json.loads(METADATA_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def borrar_archivo_persistente() -> None:
    for path in [LAST_FILE_PATH, METADATA_PATH]:
        if path.exists():
            path.unlink()
    if CACHE_DIR.exists():
        shutil.rmtree(CACHE_DIR)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

def cargar_configuracion(default: dict | None = None) -> dict:
    asegurar_directorios()
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            return default or {}
    return default or {}

def guardar_configuracion(config: dict) -> None:
    asegurar_directorios()
    CONFIG_PATH.write_text(json.dumps(config, ensure_ascii=False, indent=4), encoding="utf-8")
