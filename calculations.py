
from __future__ import annotations
import pandas as pd
import numpy as np
from .utils import *

OP_KEYS = ["ACTIVIDAD","NOMBRE","NUMERO DE PIEZAS","PIEZAS","RECORRIDOS","HABILITADO","UBICADO"]
COM_KEYS = ["DEV","VTA","VENTA","COSTO","MODELO","ID","COLOR"]

def classify_sheet(name, df):
    n = norm_text(name)
    text = " ".join([n]+[norm_text(c) for c in df.columns])
    if "PLANTILLA" in n:
        return "plantilla"
    if "RESULTADOS" in n and "PRODUCT" in n:
        return "operacion"
    if any(m in n for m in ["ENERO","FEBRERO","MARZO","ABRIL","MAYO","JUNIO","JULIO","AGOSTO","SEPTIEMBRE","OCTUBRE","NOVIEMBRE","DICIEMBRE"]):
        return "comercial"
    so = sum(k in text for k in OP_KEYS)
    sc = sum(k in text for k in COM_KEYS)
    if sc > so: return "comercial"
    if so > 0: return "operacion"
    return "otra"

def build_nombre_map(sheets):
    mp = {"ELO":"Eloisa","ELOISA":"Eloisa","IVON":"Ivonne","IVONNE":"Ivonne"}
    for name, df in sheets.items():
        if "PLANTILLA" not in norm_text(name) or df.empty:
            continue
        c_nombre = find_col(df, ["Nombre","Nombre completo","Colaborador"])
        c_alias = find_col(df, ["Alias","Usuario","Nombre corto","Registro"])
        if c_nombre is None: 
            continue
        for _, r in df.iterrows():
            nombre = str(r.get(c_nombre,"")).strip()
            if not nombre or nombre.lower()=="nan": continue
            keys = {nombre.split()[0], nombre.split()[0][:3], nombre.split()[0][:4]}
            if c_alias:
                a = str(r.get(c_alias,"")).strip()
                if a and a.lower()!="nan": keys.add(a)
            for k in keys:
                mp[norm_text(k)] = nombre
    return mp

def normalize_operation(df, sheet, nombre_map):
    out = pd.DataFrame()
    c_fecha = find_col(df, ["Fecha"])
    c_tienda = best_tienda_col(df)
    c_nombre = find_col(df, ["Nombre","Usuario","Colaborador"])
    c_act = find_col(df, ["Actividad Realizada","Actividad","Tabla"])
    c_pzs = find_col(df, ["Número de Piezas","Numero de Piezas","Piezas","Cantidad"])
    c_motivo = find_col(df, ["Motivo de ingreso","Motivo"])
    c_area = find_col(df, ["Área","Area"])
    c_rec = find_col(df, ["Recorridos","RECORRIDOS"])
    c_hab = find_col(df, ["Habilitado","Acondicionado"])
    c_ubi = find_col(df, ["Ubicado","Ubicadas"])

    out["Hoja"] = sheet
    out["Fecha"] = pd.to_datetime(df[c_fecha], errors="coerce", dayfirst=True) if c_fecha else pd.NaT
    out["Tienda"] = df[c_tienda].map(canon_tienda) if c_tienda else ""
    out["Nombre Original"] = df[c_nombre].astype(str).str.strip() if c_nombre else ""
    out["Nombre"] = out["Nombre Original"].map(lambda x: nombre_map.get(norm_text(x), x))
    out["Actividad Realizada"] = df[c_act].astype(str).str.strip() if c_act else ""
    out["Motivo de ingreso"] = df[c_motivo].astype(str).str.strip() if c_motivo else ""
    out["Área"] = df[c_area].astype(str).str.strip() if c_area else ""
    out["Número de Piezas"] = to_number(df[c_pzs]) if c_pzs else 0
    act = out["Actividad Realizada"].map(norm_text)
    pzs = out["Número de Piezas"]
    out["Acondicionado"] = to_number(df[c_hab]) if c_hab else np.where(act.str.contains("HABIL|ACONDICION", na=False), pzs, 0)
    out["Ubicado"] = to_number(df[c_ubi]) if c_ubi else np.where(act.str.contains("UBIC", na=False), pzs, 0)
    out["Recorridos"] = to_number(df[c_rec]) if c_rec else np.where(act.str.contains("RECORR", na=False), 1, 0)
    out = out[out["Tienda"].astype(str).str.len() > 0]
    out = out[~out["Tienda"].astype(str).str.isdigit()]
    out["Semana ISO"] = out["Fecha"].dt.isocalendar().week.astype("Int64")
    out["Mes"] = out["Fecha"].dt.strftime("%Y-%m")
    return out

def normalize_commercial_long(df, sheet):
    c_fecha = find_col(df, ["Fecha"])
    c_tienda = best_tienda_col(df)
    c_id = find_col(df, ["ID","Modelo","ID/Modelo"])
    c_color = find_col(df, ["Color"])
    c_dev = find_col(df, ["Dev Pzs","Dev_pzs","Devolucion Pzs","Devolución Pzs"])
    c_vta = find_col(df, ["Ventas Netas Pzs","Vta_Pzs","Venta Pzs"])
    c_imp = find_col(df, ["Venta Neta","Vta_Imp","Venta Importe","Venta Neta en $"])
    c_costo = find_col(df, ["Costo Dev","Costo_Dev","Costo"])
    if not c_dev:
        return pd.DataFrame()
    out = pd.DataFrame()
    out["Hoja"] = sheet
    out["Fecha"] = pd.to_datetime(df[c_fecha], errors="coerce", dayfirst=True) if c_fecha else pd.NaT
    out["Tienda"] = df[c_tienda].map(canon_tienda) if c_tienda else ""
    out["ID/Modelo"] = df[c_id].astype(str).str.strip() if c_id else ""
    out["Color"] = df[c_color].astype(str).str.strip() if c_color else ""
    out["Dev_Pzs"] = to_number(df[c_dev])
    out["Vta_Pzs"] = to_number(df[c_vta]) if c_vta else 0
    out["Vta_Imp"] = to_number(df[c_imp]) if c_imp else 0
    out["Costo_Dev"] = to_number(df[c_costo]) if c_costo else 0
    out["Semana ISO"] = out["Fecha"].dt.isocalendar().week.astype("Int64")
    out["Mes"] = out["Fecha"].dt.strftime("%Y-%m")
    return out

def normalize_commercial_wide(df, sheet):
    rows=[]
    for col in df.columns:
        if "DEV" not in norm_text(col) or "PZS" not in norm_text(col):
            continue
        idx = list(df.columns).index(col)
        fecha = None
        for j in range(idx, max(-1, idx-5), -1):
            f = pd.to_datetime(str(df.columns[j]), errors="coerce", dayfirst=True)
            if pd.notna(f):
                fecha = f
                break
        if fecha is None:
            continue
        tmp = pd.DataFrame({
            "Hoja": sheet, "Fecha": fecha, "Tienda": "", "ID/Modelo": "", "Color": "",
            "Dev_Pzs": to_number(df[col]), "Vta_Pzs": 0, "Vta_Imp": 0, "Costo_Dev": 0
        })
        for j in range(max(0, idx-3), min(len(df.columns), idx+4)):
            n = norm_text(df.columns[j])
            if "VENTA" in n and "PZS" in n:
                tmp["Vta_Pzs"] = to_number(df[df.columns[j]])
            if "VENTA" in n and ("$" in str(df.columns[j]) or "IMP" in n or "NETA EN" in n):
                tmp["Vta_Imp"] = to_number(df[df.columns[j]])
        rows.append(tmp[tmp["Dev_Pzs"] != 0])
    if not rows:
        return pd.DataFrame()
    out = pd.concat(rows, ignore_index=True)
    out["Semana ISO"] = out["Fecha"].dt.isocalendar().week.astype("Int64")
    out["Mes"] = out["Fecha"].dt.strftime("%Y-%m")
    return out

def load_excel(path):
    sheets = pd.read_excel(path, sheet_name=None, engine="openpyxl")
    nombre_map = build_nombre_map(sheets)
    ops, coms, diag = [], [], []
    for name, df in sheets.items():
        kind = classify_sheet(name, df)
        diag.append({
            "Hoja": name, "Tipo": kind, "Filas": len(df), "Columnas": len(df.columns),
            "Col Tienda detectada": str(best_tienda_col(df)), 
            "Candidatas Tienda": ", ".join(map(str, tienda_candidate_cols(df)))
        })
        if kind == "operacion":
            ops.append(normalize_operation(df, name, nombre_map))
        elif kind == "comercial":
            c = normalize_commercial_long(df, name)
            if c.empty:
                c = normalize_commercial_wide(df, name)
            if not c.empty: coms.append(c)
    op = pd.concat(ops, ignore_index=True) if ops else pd.DataFrame()
    co = pd.concat(coms, ignore_index=True) if coms else pd.DataFrame()
    return op, co, pd.DataFrame(diag), nombre_map
