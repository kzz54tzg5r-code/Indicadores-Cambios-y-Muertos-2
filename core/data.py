
from __future__ import annotations
from pathlib import Path
import pandas as pd
import numpy as np
from .utils import norm_text, to_number, safe_div


OP_KEYS = ["ACTIVIDAD", "NOMBRE", "OCURRENCIA", "NUMERO DE PIEZAS", "PIEZAS", "RECORRIDOS", "HABILITADO", "UBICADO"]
COM_KEYS = ["DEV", "VTA", "VENTA", "COSTO", "MODELO", "ID", "TALLA", "COLOR"]


def read_excel(path: Path) -> dict[str, pd.DataFrame]:
    return pd.read_excel(path, sheet_name=None, engine="openpyxl")


def find_col(df: pd.DataFrame, candidates: list[str]):
    normalized = {norm_text(c): c for c in df.columns}
    for cand in candidates:
        n = norm_text(cand)
        if n in normalized:
            return normalized[n]
    for c in df.columns:
        nc = norm_text(c)
        if any(norm_text(cand) in nc for cand in candidates):
            return c
    return None


def normalize_date(s):
    return pd.to_datetime(s, errors="coerce", dayfirst=False)


def classify_sheet(name: str, df: pd.DataFrame) -> str:
    text = " ".join([norm_text(name)] + [norm_text(c) for c in df.columns])
    score_op = sum(k in text for k in OP_KEYS)
    score_co = sum(k in text for k in COM_KEYS)
    if score_co > score_op:
        return "comercial"
    if score_op > 0:
        return "operacion"
    return "otra"


def normalize_operation_sheet(df: pd.DataFrame, sheet_name="") -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    out = pd.DataFrame()
    out["Hoja"] = sheet_name

    c_fecha = find_col(df, ["Fecha", "Fecha captura", "Día", "Dia"])
    c_tienda = find_col(df, ["Tienda", "Sucursal"])
    c_nombre = find_col(df, ["Nombre", "Usuario", "Colaborador"])
    c_actividad = find_col(df, ["Actividad Realizada", "Actividad", "Tabla"])
    c_piezas = find_col(df, ["Número de Piezas", "Numero de Piezas", "Piezas", "Cantidad"])
    c_recorridos = find_col(df, ["Recorridos", "RECORRIDOS"])
    c_hab = find_col(df, ["Habilitado", "Acondicionado", "Acondicionadas", "Piezas Habilitadas"])
    c_ubi = find_col(df, ["Ubicado", "Ubicadas", "Piezas Ubicadas"])
    c_ocurrencia = find_col(df, ["Ocurrencia", "Occurrence", "Ba"])
    c_area = find_col(df, ["Área", "Area"])
    c_motivo = find_col(df, ["Motivo de ingreso", "Motivo"])

    out["Fecha"] = normalize_date(df[c_fecha]) if c_fecha else pd.NaT
    out["Tienda"] = df[c_tienda].astype(str).str.strip() if c_tienda else ""
    out["Nombre"] = df[c_nombre].astype(str).str.strip() if c_nombre else ""
    out["Actividad Realizada"] = df[c_actividad].astype(str).str.strip() if c_actividad else ""
    out["Número de Piezas"] = to_number(df[c_piezas]) if c_piezas else 0
    out["Recorridos"] = to_number(df[c_recorridos]) if c_recorridos else 0
    out["Acondicionado"] = to_number(df[c_hab]) if c_hab else 0
    out["Ubicado"] = to_number(df[c_ubi]) if c_ubi else 0
    out["Ocurrencia"] = df[c_ocurrencia].astype(str).str.strip() if c_ocurrencia else ""
    out["Área"] = df[c_area].astype(str).str.strip() if c_area else ""
    out["Motivo de ingreso"] = df[c_motivo].astype(str).str.strip() if c_motivo else ""

    # Si no hay columnas explícitas de habilitado/ubicado, inferir desde actividad y piezas.
    act_norm = out["Actividad Realizada"].map(norm_text)
    pzs = out["Número de Piezas"]
    if out["Acondicionado"].sum() == 0:
        out["Acondicionado"] = np.where(act_norm.str.contains("HABIL|ACOND"), pzs, 0)
    if out["Ubicado"].sum() == 0:
        out["Ubicado"] = np.where(act_norm.str.contains("UBIC"), pzs, 0)
    if out["Recorridos"].sum() == 0:
        out["Recorridos"] = np.where(act_norm.str.contains("RECORR"), 1, 0)

    out["Semana ISO"] = out["Fecha"].dt.isocalendar().week.astype("Int64")
    out["Año ISO"] = out["Fecha"].dt.isocalendar().year.astype("Int64")
    out["Mes"] = out["Fecha"].dt.strftime("%Y-%m")

    return out


def normalize_commercial_sheet(df: pd.DataFrame, sheet_name="") -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    out = pd.DataFrame()
    out["Hoja"] = sheet_name

    c_fecha = find_col(df, ["Fecha", "Fecha venta", "Fecha devolución", "Dia", "Día"])
    c_tienda = find_col(df, ["Tienda", "Sucursal"])
    c_id = find_col(df, ["ID/Modelo", "Id", "Modelo", "Artículo", "Articulo"])
    c_color = find_col(df, ["Color"])
    c_talla = find_col(df, ["Talla"])
    c_dev = find_col(df, ["Dev_pzs", "Dev Pzs", "Devolución Pzs", "Devolucion Pzs", "Dev"])
    c_costo = find_col(df, ["Costo_Dev", "Costo Dev", "Costo"])
    c_vta_pzs = find_col(df, ["Vta_Pzs", "Ventas Netas Pzs", "Venta Pzs", "Vta Pzs"])
    c_vta_imp = find_col(df, ["Vta_Imp", "Venta Importe", "Ventas Netas Imp", "Vta Imp"])

    out["Fecha"] = normalize_date(df[c_fecha]) if c_fecha else pd.NaT
    out["Tienda"] = df[c_tienda].astype(str).str.strip() if c_tienda else ""
    out["ID/Modelo"] = df[c_id].astype(str).str.strip() if c_id else ""
    out["Color"] = df[c_color].astype(str).str.strip() if c_color else ""
    out["Talla"] = df[c_talla].astype(str).str.strip() if c_talla else ""
    out["Dev_Pzs"] = to_number(df[c_dev]) if c_dev else 0
    out["Costo_Dev"] = to_number(df[c_costo]) if c_costo else 0
    out["Vta_Pzs"] = to_number(df[c_vta_pzs]) if c_vta_pzs else 0
    out["Vta_Imp"] = to_number(df[c_vta_imp]) if c_vta_imp else 0
    out["Semana ISO"] = out["Fecha"].dt.isocalendar().week.astype("Int64") if out["Fecha"].notna().any() else 0
    out["Año ISO"] = out["Fecha"].dt.isocalendar().year.astype("Int64") if out["Fecha"].notna().any() else 0
    out["Mes"] = out["Fecha"].dt.strftime("%Y-%m") if out["Fecha"].notna().any() else ""
    return out


def load_normalized(path: Path):
    sheets = read_excel(path)
    ops = []
    coms = []
    diagnostics = []

    for name, df in sheets.items():
        kind = classify_sheet(name, df)
        diagnostics.append({"Hoja": name, "Tipo detectado": kind, "Filas": len(df), "Columnas": len(df.columns)})
        if kind == "operacion":
            ops.append(normalize_operation_sheet(df, name))
        elif kind == "comercial":
            coms.append(normalize_commercial_sheet(df, name))

    op = pd.concat(ops, ignore_index=True) if ops else pd.DataFrame()
    co = pd.concat(coms, ignore_index=True) if coms else pd.DataFrame()
    diag = pd.DataFrame(diagnostics)
    return op, co, diag, sheets


def filter_period(op, co, period):
    if period == "Todo el archivo":
        return op, co
    today = pd.Timestamp.today()
    op2 = op.copy()
    co2 = co.copy()

    if period == "Semana actual":
        sem = int(today.isocalendar().week)
        if not op2.empty and "Semana ISO" in op2:
            op2 = op2[op2["Semana ISO"] == sem]
        if not co2.empty and "Semana ISO" in co2:
            co2 = co2[co2["Semana ISO"] == sem]

    if period == "Mes actual":
        mes = today.strftime("%Y-%m")
        if not op2.empty and "Mes" in op2:
            op2 = op2[op2["Mes"] == mes]
        if not co2.empty and "Mes" in co2:
            co2 = co2[co2["Mes"] == mes]

    return op2, co2


def resumen_ejecutivo(op, co):
    ingresos_op = float(op["Número de Piezas"].sum()) if not op.empty and "Número de Piezas" in op else 0
    dev = float(co["Dev_Pzs"].sum()) if not co.empty and "Dev_Pzs" in co else 0
    ingresos = dev if dev > 0 else ingresos_op
    acondicionado = float(op["Acondicionado"].sum()) if not op.empty and "Acondicionado" in op else 0
    ubicado = float(op["Ubicado"].sum()) if not op.empty and "Ubicado" in op else 0
    recorridos = float(op["Recorridos"].sum()) if not op.empty and "Recorridos" in op else 0
    pendiente = max(ingresos - ubicado, 0)
    return {
        "Ingresos": ingresos,
        "Acondicionado": acondicionado,
        "Ubicado": ubicado,
        "Pendiente": pendiente,
        "Recorridos": recorridos,
        "% Acondicionado": safe_div(acondicionado, ingresos),
        "% Ubicado": safe_div(ubicado, ingresos),
    }


def resumen_tienda(op, co):
    tiendas = sorted(set(
        (op["Tienda"].dropna().astype(str).tolist() if not op.empty and "Tienda" in op else [])
        + (co["Tienda"].dropna().astype(str).tolist() if not co.empty and "Tienda" in co else [])
    ))
    rows = []
    for t in tiendas:
        ot = op[op["Tienda"] == t] if not op.empty and "Tienda" in op else pd.DataFrame()
        ct = co[co["Tienda"] == t] if not co.empty and "Tienda" in co else pd.DataFrame()
        r = resumen_ejecutivo(ot, ct)
        r["Tienda"] = t
        rows.append(r)
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df[["Tienda", "Ingresos", "Acondicionado", "Ubicado", "Pendiente", "Recorridos", "% Acondicionado", "% Ubicado"]]
        df = df.sort_values("Ingresos", ascending=False)
    return df


def resumen_semana(op, co):
    semanas = sorted(set(
        (op["Semana ISO"].dropna().astype(int).tolist() if not op.empty and "Semana ISO" in op else [])
        + (co["Semana ISO"].dropna().astype(int).tolist() if not co.empty and "Semana ISO" in co else [])
    ))
    rows = []
    for s in semanas:
        ot = op[op["Semana ISO"] == s] if not op.empty and "Semana ISO" in op else pd.DataFrame()
        ct = co[co["Semana ISO"] == s] if not co.empty and "Semana ISO" in co else pd.DataFrame()
        r = resumen_ejecutivo(ot, ct)
        r["Semana ISO"] = s
        rows.append(r)
    return pd.DataFrame(rows)


def resumen_mes(op, co):
    meses = sorted(set(
        (op["Mes"].dropna().astype(str).tolist() if not op.empty and "Mes" in op else [])
        + (co["Mes"].dropna().astype(str).tolist() if not co.empty and "Mes" in co else [])
    ))
    rows = []
    for m in meses:
        ot = op[op["Mes"] == m] if not op.empty and "Mes" in op else pd.DataFrame()
        ct = co[co["Mes"] == m] if not co.empty and "Mes" in co else pd.DataFrame()
        r = resumen_ejecutivo(ot, ct)
        r["Mes"] = m
        rows.append(r)
    return pd.DataFrame(rows)


def productividad(op):
    if op.empty:
        return pd.DataFrame()
    group_cols = ["Tienda", "Nombre"] if "Nombre" in op else ["Tienda"]
    df = op.groupby(group_cols, dropna=False).agg(
        Piezas=("Número de Piezas", "sum"),
        Acondicionado=("Acondicionado", "sum"),
        Ubicado=("Ubicado", "sum"),
        Recorridos=("Recorridos", "sum"),
    ).reset_index()
    df["Productividad"] = df["Acondicionado"] + df["Ubicado"]
    return df.sort_values("Productividad", ascending=False)


def conversion(co):
    if co.empty:
        return pd.DataFrame(), {"Dev Pzs": 0, "Conversión Pzs": 0, "Conversión $": 0, "Pendiente Pzs": 0, "% Conversión": 0}
    df = co.copy()
    for c in ["Dev_Pzs", "Vta_Pzs", "Vta_Imp", "Costo_Dev"]:
        if c not in df:
            df[c] = 0
    group_cols = [c for c in ["Semana ISO", "Tienda", "ID/Modelo", "Color", "Talla"] if c in df.columns]
    if not group_cols:
        group_cols = ["Tienda"] if "Tienda" in df.columns else []
    if group_cols:
        g = df.groupby(group_cols, dropna=False).agg(
            **{
                "Dev Pzs": ("Dev_Pzs", "sum"),
                "Venta Pzs": ("Vta_Pzs", "sum"),
                "Venta $": ("Vta_Imp", "sum"),
                "Costo Dev": ("Costo_Dev", "sum"),
            }
        ).reset_index()
    else:
        g = pd.DataFrame([{
            "Dev Pzs": df["Dev_Pzs"].sum(),
            "Venta Pzs": df["Vta_Pzs"].sum(),
            "Venta $": df["Vta_Imp"].sum(),
            "Costo Dev": df["Costo_Dev"].sum(),
        }])
    g["Conversión Pzs"] = g[["Dev Pzs", "Venta Pzs"]].min(axis=1)
    ratio = g["Conversión Pzs"] / g["Venta Pzs"].replace(0, pd.NA)
    g["Conversión $"] = (g["Venta $"] * ratio.fillna(0)).fillna(0)
    g["Pendiente Pzs"] = (g["Dev Pzs"] - g["Conversión Pzs"]).clip(lower=0)
    g["No Convertido $"] = (g["Costo Dev"] - g["Conversión $"]).clip(lower=0)
    g["% Conversión"] = (g["Conversión Pzs"] / g["Dev Pzs"].replace(0, pd.NA) * 100).fillna(0)
    k = {
        "Dev Pzs": g["Dev Pzs"].sum(),
        "Conversión Pzs": g["Conversión Pzs"].sum(),
        "Conversión $": g["Conversión $"].sum(),
        "Pendiente Pzs": g["Pendiente Pzs"].sum(),
        "No Convertido $": g["No Convertido $"].sum(),
    }
    k["% Conversión"] = safe_div(k["Conversión Pzs"], k["Dev Pzs"])
    return g, k
