from __future__ import annotations

import numpy as np
import pandas as pd
from core.utils import buscar_columna, convertir_numero, normalizar_texto

def normalizar_operacion(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    d = df.copy()
    col_fecha = buscar_columna(d, ["Fecha Día", "Fecha Dia", "Fecha", "Timestamp", "Marca temporal"])
    col_tienda = buscar_columna(d, ["Tienda", "Sucursal"])
    col_actividad = buscar_columna(d, ["Actividad Realizada", "Actividad"])
    col_motivo = buscar_columna(d, ["Motivo de ingreso", "Ingreso", "Motivo ingreso"])
    col_piezas = buscar_columna(d, ["Número de Piezas", "Numero de Piezas", "Piezas", "Pzas", "Cantidad"])
    col_nombre = buscar_columna(d, ["Nombre", "Colaborador", "Usuario"])
    col_ocurrencia = buscar_columna(d, ["Ocurrencia", "Occurrence", "Empleado", "ID empleado"])
    col_area = buscar_columna(d, ["Área", "Area", "Tabla"])
    out = pd.DataFrame()
    out["Fecha"] = pd.to_datetime(d[col_fecha], errors="coerce") if col_fecha else pd.NaT
    out["Fecha Día"] = out["Fecha"].dt.date
    out["Semana ISO"] = out["Fecha"].dt.isocalendar().week.astype("Float64").fillna(0).astype(int)
    out["Mes"] = out["Fecha"].dt.strftime("%Y-%m").fillna("")
    out["Tienda"] = d[col_tienda].astype(str).str.strip() if col_tienda else "Sin tienda"
    out["Actividad Realizada"] = d[col_actividad].astype(str).str.strip() if col_actividad else ""
    out["Motivo de ingreso"] = d[col_motivo].astype(str).str.strip() if col_motivo else ""
    out["Número de Piezas"] = convertir_numero(d[col_piezas]) if col_piezas else 0
    out["Nombre"] = d[col_nombre].astype(str).str.strip() if col_nombre else "Sin nombre"
    out["Ocurrencia"] = d[col_ocurrencia].astype(str).str.strip() if col_ocurrencia else ""
    out["Área"] = d[col_area].astype(str).str.strip() if col_area else ""
    actividad = out["Actividad Realizada"].map(normalizar_texto)
    motivo = out["Motivo de ingreso"].map(normalizar_texto)
    piezas = out["Número de Piezas"]
    out["Recoleccion"] = np.where(actividad.str.contains("recoleccion|recolec|muerto", regex=True), piezas, 0)
    out["Acondicionado"] = np.where(actividad.str.contains("acondicionado|habilitado|habilitar", regex=True), piezas, 0)
    out["Ubicado"] = np.where(actividad.str.contains("ubicado|ubicar", regex=True), piezas, 0)
    out["Recorridos"] = np.where(actividad.str.contains("recorrido", regex=True), 1, 0)
    out["Muertos Piso Venta"] = np.where((out["Recoleccion"] > 0) & motivo.str.contains("muerto", regex=True), piezas, 0)
    out["Ingresos Cajas"] = np.where((out["Recoleccion"] > 0) & motivo.str.contains("caja", regex=True), piezas, 0)
    out["Ingresos Probador"] = np.where((out["Recoleccion"] > 0) & motivo.str.contains("probador", regex=True), piezas, 0)
    return out

def normalizar_comercial(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    d = df.copy()
    col_fecha = buscar_columna(d, ["Fecha Día", "Fecha Dia", "Fecha", "Fecha Venta", "Fecha_Venta", "Fecha Devolución", "Fecha Dev"])
    col_tienda = buscar_columna(d, ["Tienda", "Sucursal"])
    col_dev = buscar_columna(d, ["Dev_Pzs", "Dev Pzs", "Dev pzs", "Devoluciones", "Pzs Dev"])
    col_vta = buscar_columna(d, ["Vta_Pzs", "Ventas Netas Pzs", "Vta Pzs", "Venta Pzs"])
    col_imp = buscar_columna(d, ["Vta_Imp", "Venta $", "Vta Imp", "Venta Importe", "Ventas Netas $"])
    col_costo = buscar_columna(d, ["Costo_Dev", "Costo Dev", "Costo Devolución", "Valor Devolución"])
    col_modelo = buscar_columna(d, ["ID", "Id", "Modelo", "ID Modelo", "Articulo", "Artículo"])
    col_color = buscar_columna(d, ["Color"])
    col_talla = buscar_columna(d, ["Talla"])
    out = pd.DataFrame()
    out["Fecha"] = pd.to_datetime(d[col_fecha], errors="coerce") if col_fecha else pd.NaT
    out["Fecha Día"] = out["Fecha"].dt.date
    out["Semana ISO"] = out["Fecha"].dt.isocalendar().week.astype("Float64").fillna(0).astype(int)
    out["Mes"] = out["Fecha"].dt.strftime("%Y-%m").fillna("")
    out["Tienda"] = d[col_tienda].astype(str).str.strip() if col_tienda else "Sin tienda"
    out["Dev_Pzs"] = convertir_numero(d[col_dev]) if col_dev else 0
    out["Vta_Pzs"] = convertir_numero(d[col_vta]) if col_vta else 0
    out["Vta_Imp"] = convertir_numero(d[col_imp]) if col_imp else 0
    out["Costo_Dev"] = convertir_numero(d[col_costo]) if col_costo else 0
    out["ID/Modelo"] = d[col_modelo].astype(str).str.strip() if col_modelo else "Sin modelo"
    out["Color"] = d[col_color].astype(str).str.strip() if col_color else "Sin color"
    out["Talla"] = d[col_talla].astype(str).str.strip() if col_talla else "Sin talla"
    return out

def detectar_y_normalizar_hojas(hojas: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    operaciones = []
    comerciales = []
    for nombre, df in hojas.items():
        if df is None or df.empty:
            continue
        columnas = " ".join(map(str, df.columns)).lower()
        if ("actividad" in columnas and "tienda" in columnas) or "productividad" in nombre.lower():
            operaciones.append(normalizar_operacion(df))
        if any(token in columnas for token in ["dev", "vta", "venta", "devol"]):
            comercial = normalizar_comercial(df)
            if not comercial.empty and comercial[["Dev_Pzs", "Vta_Pzs", "Vta_Imp", "Costo_Dev"]].sum().sum() > 0:
                comerciales.append(comercial)
    op = pd.concat(operaciones, ignore_index=True) if operaciones else pd.DataFrame()
    co = pd.concat(comerciales, ignore_index=True) if comerciales else pd.DataFrame()
    return op, co
