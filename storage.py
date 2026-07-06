
from __future__ import annotations
import re, unicodedata
import pandas as pd
import numpy as np

PROJECT_TIENDAS = [
    "Iztapalapa","Vallejo","Ecatepec","Toluca","Arco Norte","Ixtapaluca",
    "Querétaro","Centro","Olivar","León","Puebla","Puebla Sur",
    "Aguascalientes","Veracruz","Naucalpan","Miravalle","Atemajac"
]

def norm_text(x) -> str:
    s = "" if x is None else str(x).strip()
    s = unicodedata.normalize("NFKD", s).encode("ascii","ignore").decode("ascii")
    s = re.sub(r"\s+", " ", s)
    return s.upper()

TIENDA_MAP = {norm_text(t): t for t in PROJECT_TIENDAS}
TIENDA_MAP.update({"QUERETARO":"Querétaro","LEON":"León","PUEBLA SUR":"Puebla Sur","ARCO NORTE":"Arco Norte"})

def canon_tienda(x) -> str:
    s = "" if x is None else str(x).strip()
    if not s or s.upper() == "NAN" or s.isdigit():
        return ""
    n = norm_text(s)
    if n in TIENDA_MAP:
        return TIENDA_MAP[n]
    for k,v in TIENDA_MAP.items():
        if k in n:
            return v
    return s.title()

def exact_col(df, name):
    target = norm_text(name)
    for c in df.columns:
        if norm_text(c) == target:
            return c
    return None

def find_col(df, candidates):
    # exact first
    for cand in candidates:
        c = exact_col(df, cand)
        if c is not None:
            return c
    # contains later
    for c in df.columns:
        nc = norm_text(c)
        if any(norm_text(x) in nc for x in candidates):
            return c
    return None

def tienda_candidate_cols(df):
    return [c for c in df.columns if norm_text(c) == "TIENDA" or norm_text(c).startswith("TIENDA.")]

def best_tienda_col(df):
    cand = tienda_candidate_cols(df)
    if not cand:
        return find_col(df, ["Tienda","Sucursal"])
    valid = [norm_text(t) for t in PROJECT_TIENDAS]
    best, best_score = cand[0], -10**9
    for c in cand:
        s = df[c].astype(str).fillna("").str.strip()
        n = s.map(norm_text)
        num_ratio = pd.to_numeric(s, errors="coerce").notna().mean() if len(s) else 1
        hits = sum(n.str.contains(v, na=False).sum() for v in valid)
        score = hits*100 + (s!="").sum() - num_ratio*len(s)*50
        if score > best_score:
            best, best_score = c, score
    return best

def to_number(s):
    return pd.to_numeric(pd.Series(s).astype(str).str.replace("$","",regex=False).str.replace(",","",regex=False).replace({"-":"0","nan":"0"}), errors="coerce").fillna(0)

def safe_div(a,b):
    try:
        return float(a)/float(b)*100 if float(b) else 0
    except Exception:
        return 0

def fmt_num(x):
    try: return f"{float(x):,.0f}"
    except Exception: return "0"

def fmt_pct(x):
    try: return f"{float(x):,.1f}%"
    except Exception: return "0.0%"

def fmt_money(x):
    try: return f"${float(x):,.0f}"
    except Exception: return "$0"

def format_table(df):
    if df is None or df.empty:
        return df
    out = df.copy()
    for c in out.columns:
        if str(c).startswith("%"):
            out[c] = out[c].apply(fmt_pct)
        elif pd.api.types.is_numeric_dtype(out[c]) and any(k in str(c).lower() for k in ["pzs","piezas","total","pend","muertos","cajas","probador","recolect","habil","ubic","dev","ingreso"]):
            out[c] = out[c].apply(fmt_num)
    return out
