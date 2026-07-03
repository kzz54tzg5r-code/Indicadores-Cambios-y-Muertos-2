from __future__ import annotations

from pathlib import Path
import pandas as pd
import streamlit as st
from core.storage import obtener_archivo_persistente

@st.cache_data(show_spinner=False)
def leer_excel_persistente(path_str: str) -> dict[str, pd.DataFrame]:
    xls = pd.ExcelFile(path_str)
    return {sheet: pd.read_excel(xls, sheet_name=sheet) for sheet in xls.sheet_names}

def cargar_excel_actual() -> dict[str, pd.DataFrame] | None:
    archivo = obtener_archivo_persistente()
    if archivo is None:
        return None
    return leer_excel_persistente(str(archivo))

def validar_excel(path: Path) -> tuple[bool, str]:
    if not path.exists():
        return False, "El archivo no existe."
    if path.suffix.lower() != ".xlsx":
        return False, "El archivo debe ser .xlsx."
    try:
        xls = pd.ExcelFile(path)
        if not xls.sheet_names:
            return False, "El archivo no tiene hojas."
    except Exception as exc:
        return False, f"No fue posible leer el Excel: {exc}"
    return True, "Archivo válido."
