from __future__ import annotations

import re
import unicodedata
import pandas as pd

def normalizar_texto(valor) -> str:
    texto = str(valor).strip().lower()
    texto = unicodedata.normalize("NFKD", texto)
    texto = texto.encode("ascii", errors="ignore").decode("utf-8")
    return re.sub(r"[^a-z0-9]+", "", texto)

def buscar_columna(df: pd.DataFrame, aliases: list[str]) -> str | None:
    if df is None or df.empty:
        return None
    mapa = {normalizar_texto(col): col for col in df.columns}
    for alias in aliases:
        clave = normalizar_texto(alias)
        if clave in mapa:
            return mapa[clave]
    for col in df.columns:
        col_norm = normalizar_texto(col)
        for alias in aliases:
            if normalizar_texto(alias) in col_norm:
                return col
    return None

def convertir_numero(serie) -> pd.Series:
    return pd.to_numeric(serie, errors="coerce").fillna(0)

def dividir_seguro(a, b) -> float:
    try:
        a = float(a or 0)
        b = float(b or 0)
        return a / b if b else 0
    except Exception:
        return 0

def formato_numero(valor) -> str:
    try:
        return f"{float(valor):,.0f}"
    except Exception:
        return "0"

def formato_pesos(valor) -> str:
    try:
        return f"${float(valor):,.0f}"
    except Exception:
        return "$0"

def formato_porcentaje(valor) -> str:
    try:
        return f"{float(valor):,.1f}%"
    except Exception:
        return "0.0%"
