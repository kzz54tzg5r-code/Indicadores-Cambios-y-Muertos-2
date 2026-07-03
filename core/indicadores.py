from __future__ import annotations

import pandas as pd
from core.utils import dividir_seguro

def resumen_ejecutivo(op: pd.DataFrame, co: pd.DataFrame) -> dict:
    dev = co["Dev_Pzs"].sum() if not co.empty and "Dev_Pzs" in co.columns else 0
    muertos = op["Muertos Piso Venta"].sum() if not op.empty and "Muertos Piso Venta" in op.columns else 0
    cajas = op["Ingresos Cajas"].sum() if not op.empty and "Ingresos Cajas" in op.columns else 0
    probador = op["Ingresos Probador"].sum() if not op.empty and "Ingresos Probador" in op.columns else 0
    acondicionado = op["Acondicionado"].sum() if not op.empty and "Acondicionado" in op.columns else 0
    ubicado = op["Ubicado"].sum() if not op.empty and "Ubicado" in op.columns else 0
    ingresos = dev + muertos + cajas + probador
    return {
        "Piezas Ingresadas": ingresos,
        "Acondicionado": acondicionado,
        "Ubicado": ubicado,
        "Pendiente Ubicar": max(ingresos - ubicado, 0),
        "% Acondicionado": dividir_seguro(acondicionado, ingresos) * 100,
        "% Ubicado": dividir_seguro(ubicado, ingresos) * 100,
    }

def resumen_por_tienda(op: pd.DataFrame, co: pd.DataFrame) -> pd.DataFrame:
    tiendas = sorted(set(
        (op["Tienda"].dropna().astype(str).tolist() if not op.empty and "Tienda" in op.columns else [])
        + (co["Tienda"].dropna().astype(str).tolist() if not co.empty and "Tienda" in co.columns else [])
    ))
    rows = []
    for tienda in tiendas:
        ot = op[op["Tienda"] == tienda] if not op.empty and "Tienda" in op.columns else pd.DataFrame()
        ct = co[co["Tienda"] == tienda] if not co.empty and "Tienda" in co.columns else pd.DataFrame()
        dev = ct["Dev_Pzs"].sum() if not ct.empty and "Dev_Pzs" in ct.columns else 0
        muertos = ot["Muertos Piso Venta"].sum() if not ot.empty and "Muertos Piso Venta" in ot.columns else 0
        cajas = ot["Ingresos Cajas"].sum() if not ot.empty and "Ingresos Cajas" in ot.columns else 0
        probador = ot["Ingresos Probador"].sum() if not ot.empty and "Ingresos Probador" in ot.columns else 0
        acondicionado = ot["Acondicionado"].sum() if not ot.empty and "Acondicionado" in ot.columns else 0
        ubicado = ot["Ubicado"].sum() if not ot.empty and "Ubicado" in ot.columns else 0
        ingresos = dev + muertos + cajas + probador
        rows.append({
            "Tienda": tienda, "Dev pzs": dev, "Muertos": muertos, "Cajas": cajas,
            "Probador": probador, "Total ingresos": ingresos, "Acondicionado": acondicionado,
            "% Acondicionado": dividir_seguro(acondicionado, ingresos) * 100,
            "Ubicado": ubicado, "% Ubicado": dividir_seguro(ubicado, ingresos) * 100,
            "Pendiente Ubicar": max(ingresos - ubicado, 0),
        })
    return pd.DataFrame(rows).sort_values("Total ingresos", ascending=False) if rows else pd.DataFrame()
