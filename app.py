
from __future__ import annotations

from pathlib import Path
from datetime import datetime
import sqlite3
import json
import io
import base64
import re
import unicodedata

import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go


# ============================================================
# CONFIG
# ============================================================

st.set_page_config(
    page_title="Indicadores Cambios y Muertos",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

PRICE_BLUE = "#1D2E6E"
PRICE_BLUE_2 = "#2563EB"
PRICE_PINK = "#EC007C"
PRICE_DARK = "#15172F"
PRICE_GREEN = "#00B050"
PRICE_ORANGE = "#FF8C00"
PRICE_PURPLE = "#6D28D9"
PRICE_CYAN = "#06B6D4"
PRICE_RED = "#E11D48"
PRICE_GRAY = "#6B7280"

DATA_DIR = Path("data")
UPLOAD_DIR = DATA_DIR / "uploads"
CONFIG_DIR = DATA_DIR / "config"
ACTIVE_FILE = UPLOAD_DIR / "base_activa.xlsx"
META_FILE = CONFIG_DIR / "metadata.json"
DB_FILE = CONFIG_DIR / "app_config.db"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# STORAGE / DB
# ============================================================

def db_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            nomina TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            permiso TEXT NOT NULL,
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

    total = cur.execute("SELECT COUNT(*) AS total FROM users").fetchone()["total"]
    if total == 0:
        cur.execute(
            "INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)",
            ("admin", "Administrador", "Administrador", "admin123", 1, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )

    for k, v in {
        "productividad_diaria": "784",
        "recorridos_semanal": "47",
        "conversion_meta": "90.0",
    }.items():
        cur.execute("INSERT OR IGNORE INTO goals VALUES (?, ?)", (k, v))
    conn.commit()
    conn.close()


def load_users():
    init_db()
    conn = db_conn()
    rows = conn.execute("SELECT * FROM users ORDER BY permiso DESC, nombre").fetchall()
    conn.close()
    return [dict(r) | {"activo": bool(r["activo"])} for r in rows]


def upsert_user(nomina, nombre, permiso, password=None, activo=True):
    init_db()
    conn = db_conn()
    cur = conn.cursor()
    exists = cur.execute("SELECT nomina, password FROM users WHERE nomina=?", (nomina,)).fetchone()
    if exists:
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
            raise ValueError("Contraseña requerida")
        cur.execute(
            "INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)",
            (nomina, nombre, permiso, password, int(activo), datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
    conn.commit()
    conn.close()


def delete_user(nomina):
    conn = db_conn()
    conn.execute("DELETE FROM users WHERE nomina=?", (nomina,))
    conn.commit()
    conn.close()


def load_goals():
    init_db()
    conn = db_conn()
    rows = conn.execute("SELECT key, value FROM goals").fetchall()
    conn.close()
    d = {r["key"]: r["value"] for r in rows}
    return {
        "productividad_diaria": int(float(d.get("productividad_diaria", 784))),
        "recorridos_semanal": int(float(d.get("recorridos_semanal", 47))),
        "conversion_meta": float(d.get("conversion_meta", 90.0)),
    }


def save_goals(goals):
    conn = db_conn()
    for k, v in goals.items():
        conn.execute("INSERT OR REPLACE INTO goals VALUES (?, ?)", (k, str(v)))
    conn.commit()
    conn.close()


def save_uploaded_file(uploaded_file):
    with open(ACTIVE_FILE, "wb") as f:
        f.write(uploaded_file.getbuffer())
    META_FILE.write_text(json.dumps({
        "nombre_original": uploaded_file.name,
        "fecha_carga": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }, ensure_ascii=False, indent=2), encoding="utf-8")


def get_metadata():
    if META_FILE.exists():
        try:
            return json.loads(META_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def delete_active_file():
    if ACTIVE_FILE.exists():
        ACTIVE_FILE.unlink()
    if META_FILE.exists():
        META_FILE.unlink()
    st.cache_data.clear()


# ============================================================
# UTILIDADES
# ============================================================

def norm_text(x):
    s = "" if x is None else str(x).strip()
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"\s+", " ", s)
    return s.upper()


def find_col(df, candidates):
    norm_cols = {norm_text(c): c for c in df.columns}
    for cand in candidates:
        n = norm_text(cand)
        if n in norm_cols:
            return norm_cols[n]
    for c in df.columns:
        nc = norm_text(c)
        if any(norm_text(cand) in nc for cand in candidates):
            return c
    return None


def to_number(s):
    try:
        return pd.to_numeric(s, errors="coerce").fillna(0)
    except Exception:
        return 0


def fmt_num(v):
    try:
        return f"{float(v):,.0f}"
    except Exception:
        return "0"


def fmt_pct(v):
    try:
        return f"{float(v):,.1f}%"
    except Exception:
        return "0.0%"


def fmt_money(v):
    try:
        return f"${float(v):,.0f}"
    except Exception:
        return "$0"


def safe_div(a, b):
    try:
        return (float(a) / float(b) * 100) if float(b) else 0
    except Exception:
        return 0


def pct_clip(v):
    try:
        return max(0, min(100, float(v)))
    except Exception:
        return 0


# ============================================================
# CSS / UI
# ============================================================

def apply_styles():
    st.markdown(f"""
    <style>
    .stApp {{ background:#F3F6FA; }}
    .block-container {{ max-width:100% !important; padding:0 1.6rem 2rem 1.6rem !important; }}
    section[data-testid="stSidebar"] {{ background:#FFFFFF; border-right:1px solid #DDE3EE; }}
    section[data-testid="stSidebar"] > div {{ padding-top:1rem; }}

    .top-header {{
        background:#FFFFFF; border-bottom:4px solid {PRICE_PINK};
        padding:18px 24px; display:grid; grid-template-columns:160px 1fr 430px;
        gap:24px; align-items:center; margin:0 -1.6rem 0 -1.6rem;
    }}
    .logo-fallback {{ font-weight:950; color:{PRICE_BLUE}; font-size:25px; line-height:.9; text-align:center; }}
    .header-title {{ border-left:4px solid {PRICE_PINK}; padding-left:22px; }}
    .header-title .small {{ color:{PRICE_PINK}; font-weight:900; letter-spacing:5px; font-size:13px; text-transform:uppercase; }}
    .header-title .big {{ color:{PRICE_BLUE}; font-weight:950; font-size:32px; line-height:1; letter-spacing:-.5px; }}
    .header-title .sub {{ color:#596174; font-weight:650; font-size:14px; margin-top:4px; }}
    .header-controls {{ display:grid; grid-template-columns:1fr 1fr; gap:14px; }}
    .header-card {{ background:#F8FAFC; border:1px solid #DCE3EF; border-radius:14px; padding:12px 14px; }}
    .header-card label {{ display:block; color:{PRICE_GRAY}; font-size:11px; font-weight:800; text-transform:uppercase; letter-spacing:1.4px; }}
    .header-card div {{ color:{PRICE_BLUE}; font-size:17px; font-weight:950; margin-top:3px; }}

    div[data-testid="stSegmentedControl"] {{
        background:{PRICE_BLUE}; border-top:4px solid {PRICE_PINK}; padding:0;
        margin:0 -1.6rem 22px -1.6rem; overflow-x:auto; white-space:nowrap; display:block;
        box-shadow:0 10px 22px rgba(29,46,110,.18);
    }}
    div[data-testid="stSegmentedControl"] button {{
        border-radius:0 !important; border:none !important; background:{PRICE_BLUE} !important;
        color:#DDE8FF !important; padding:15px 23px !important; font-weight:900 !important;
        font-size:15px !important; border-bottom:4px solid transparent !important; white-space:nowrap !important;
    }}
    div[data-testid="stSegmentedControl"] button[aria-pressed="true"] {{
        color:white !important; background:#233B86 !important; border-bottom-color:{PRICE_PINK} !important;
    }}

    .section-title {{ color:{PRICE_DARK}; font-size:31px; line-height:1.05; font-weight:950; margin:10px 0 6px 0; }}
    .section-subtitle {{ color:{PRICE_GRAY}; font-size:15px; font-weight:550; margin-bottom:18px; }}
    .filter-card {{ background:#FFFFFF; border:1px solid #E1E7F0; border-radius:18px; padding:16px; margin-bottom:20px; box-shadow:0 8px 18px rgba(17,24,39,.04); }}
    .hero-blue {{ background:linear-gradient(135deg, {PRICE_BLUE} 0%, #2546A8 70%, {PRICE_PINK} 160%); border-radius:22px; padding:24px; color:#FFFFFF; margin-bottom:20px; box-shadow:0 18px 38px rgba(29,46,110,.25); }}
    .hero-blue h2 {{ margin:0; font-size:28px; font-weight:950; color:#FFFFFF; }}
    .hero-blue p {{ margin:6px 0 0 0; color:#E7ECFF; font-weight:650; }}
    .hero-grid {{ display:grid; grid-template-columns:repeat(5, 1fr); gap:12px; margin-top:18px; }}
    .hero-mini {{ background:rgba(255,255,255,.12); border:1px solid rgba(255,255,255,.20); border-radius:15px; padding:12px; }}
    .hero-mini-label {{ opacity:.78; font-size:12px; font-weight:850; }}
    .hero-mini-value {{ font-size:20px; font-weight:950; margin-top:3px; }}

    .kpi-grid {{ display:grid; grid-template-columns:repeat(5, 1fr); gap:16px; margin-bottom:20px; }}
    .kpi-card {{ background:#FFFFFF; border:1px solid #E1E7F0; border-radius:20px; padding:18px; box-shadow:0 10px 24px rgba(17,24,39,.06); min-height:165px; position:relative; overflow:hidden; }}
    .kpi-card:after {{ content:""; position:absolute; right:-35px; top:-35px; width:100px; height:100px; border-radius:50%; background:var(--soft); }}
    .kpi-top {{ display:flex; align-items:center; gap:12px; position:relative; z-index:1; }}
    .kpi-icon {{ width:52px; height:52px; border-radius:16px; display:flex; align-items:center; justify-content:center; background:var(--accent); color:#FFFFFF; font-size:23px; font-weight:950; box-shadow:0 10px 22px var(--shadow); }}
    .kpi-label {{ color:var(--accent); font-size:14px; line-height:1.1; font-weight:950; }}
    .kpi-value {{ color:{PRICE_DARK}; font-size:28px; font-weight:950; margin-top:16px; letter-spacing:-.5px; position:relative; z-index:1; }}
    .kpi-note {{ color:{PRICE_GRAY}; font-size:13px; font-weight:650; margin-top:5px; }}
    .progress {{ height:9px; background:#EDF2F7; border-radius:99px; margin-top:14px; overflow:hidden; }}
    .progress > div {{ height:100%; background:var(--accent); width:var(--pct); border-radius:99px; }}
    .delta {{ display:inline-block; margin-top:10px; padding:5px 9px; border-radius:10px; background:var(--soft); color:var(--accent); font-size:12px; font-weight:950; }}

    .panel {{ background:#FFFFFF; border:1px solid #E1E7F0; border-radius:20px; padding:20px; box-shadow:0 10px 24px rgba(17,24,39,.05); margin-bottom:18px; }}
    .panel-title {{ color:{PRICE_DARK}; font-size:18px; font-weight:950; margin-bottom:14px; }}

    .week-grid {{ display:grid; grid-template-columns:repeat(4, 1fr); gap:16px; margin-bottom:20px; }}
    .week-card {{ background:#FFFFFF; border:1px solid #E1E7F0; border-radius:18px; overflow:hidden; box-shadow:0 10px 22px rgba(17,24,39,.06); }}
    .week-head {{ background:#3F3F91; color:#FFFFFF; padding:13px 16px; text-align:center; font-weight:950; }}
    .week-line {{ display:grid; grid-template-columns:1fr auto auto; gap:10px; align-items:center; padding:12px 16px; border-bottom:1px solid #EDF2F7; }}
    .week-label {{ color:#666; font-size:12px; font-weight:900; text-transform:uppercase; }}
    .week-value {{ color:#3F3F91; font-size:17px; font-weight:950; }}
    .week-delta {{ font-size:11px; font-weight:950; }}

    .rank-row {{ display:grid; grid-template-columns:150px 1fr 72px; gap:12px; align-items:center; padding:10px 0; border-bottom:1px solid #EDF2F7; }}
    .rank-name {{ color:{PRICE_DARK}; font-weight:850; font-size:13px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
    .rankbar {{ height:10px; background:#EDF2F7; border-radius:99px; overflow:hidden; }}
    .rankbar-fill {{ height:100%; background:var(--accent); width:var(--w); border-radius:99px; }}
    .rank-value {{ text-align:right; color:{PRICE_DARK}; font-weight:950; font-size:13px; }}

    .login-wrap {{ min-height:72vh; display:flex; align-items:center; justify-content:center; }}
    .login-card {{ width:min(680px, 92vw); background:white; border:1px solid #DDE3EE; border-radius:26px; padding:34px; box-shadow:0 18px 45px rgba(17,24,39,.10); }}
    .login-title {{ color:{PRICE_BLUE}; font-size:34px; font-weight:950; line-height:1.05; margin-bottom:8px; }}
    .login-sub {{ color:#6B7280; font-size:16px; font-weight:600; margin-bottom:20px; }}
    .login-alert {{ background:#EEF5FF; border:1px solid #DBEAFE; color:{PRICE_BLUE}; border-radius:16px; padding:16px; font-weight:750; margin-bottom:18px; }}
    @media (max-width:1200px) {{
        .top-header {{ grid-template-columns:110px 1fr; }}
        .header-controls {{ display:none; }}
        .kpi-grid {{ grid-template-columns:repeat(2, 1fr); }}
        .hero-grid {{ grid-template-columns:repeat(2, 1fr); }}
        .week-grid {{ grid-template-columns:repeat(2, 1fr); }}
    }}
    </style>
    """, unsafe_allow_html=True)


def logo_html():
    for name in ["assets/logo_price.png", "assets/logo.png"]:
        p = Path(name)
        if p.exists():
            ext = p.suffix.replace(".", "") or "png"
            data = base64.b64encode(p.read_bytes()).decode()
            return f'<img src="data:image/{ext};base64,{data}" style="max-width:135px;max-height:82px;">'
    return '<div class="logo-fallback">Price<br>Shoes</div>'


def header(user):
    now = datetime.now()
    st.markdown(f"""
    <div class="top-header">
        <div>{logo_html()}</div>
        <div class="header-title">
            <div class="small">Operaciones Ropa</div>
            <div class="big">Indicadores Cambios y Muertos</div>
            <div class="sub">Recuperación · Productividad · Conversión</div>
        </div>
        <div class="header-controls">
            <div class="header-card"><label>Fecha</label><div>📅 {now.strftime("%d/%m/%Y")}</div></div>
            <div class="header-card"><label>Usuario</label><div>{'👑' if user['is_admin'] else '👤'} {user['role']}</div></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def login_screen():
    st.markdown("""
    <div class="login-wrap">
      <div class="login-card">
        <div class="login-title">Acceso al Sistema</div>
        <div class="login-sub">Indicadores Operaciones Ropa</div>
        <div class="login-alert">
          Para visualizar la información, inicia sesión con un usuario autorizado.
          Si aún no cuentas con acceso, solicita al Administrador del sistema la creación de tu usuario.
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)


def nav_bar():
    items = ["Resumen", "Día Anterior", "Reporte Semanal", "Reporte Mensual", "Conversión", "Recuperación Económica",
             "Productividad", "Recorridos", "Ranking", "Macro", "Criterios", "Configuración", "Usuarios"]
    if "page" not in st.session_state:
        st.session_state.page = "Resumen"
    current = st.session_state.page if st.session_state.page in items else "Resumen"
    selected = st.segmented_control("Navegación", items, default=current, label_visibility="collapsed", key="page_selector")
    st.session_state.page = selected or current
    return st.session_state.page


def section(title, subtitle=""):
    st.markdown(f'<div class="section-title">{title}</div><div class="section-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def kpi_card(label, value, icon, color, note="", pct=0, delta=""):
    st.markdown(f"""
    <div class="kpi-card" style="--accent:{color};--soft:{color}18;--shadow:{color}38;">
        <div class="kpi-top"><div class="kpi-icon">{icon}</div><div class="kpi-label">{label}</div></div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-note">{note}</div>
        <div class="progress"><div style="--pct:{pct_clip(pct)}%;"></div></div>
        {f'<div class="delta">{delta}</div>' if delta else ''}
    </div>
    """, unsafe_allow_html=True)


def kpis(resumen):
    st.markdown('<div class="kpi-grid">', unsafe_allow_html=True)
    kpi_card("Piezas Ingresadas", fmt_num(resumen.get("Ingresos", 0)), "↻", PRICE_PINK, "Dev + muertos + cajas + probador", 100)
    kpi_card("Piezas Acondicionadas", fmt_num(resumen.get("Acondicionado", 0)), "✓", PRICE_BLUE, fmt_pct(resumen.get("% Acondicionado", 0)) + " vs ingresos", resumen.get("% Acondicionado", 0))
    kpi_card("Piezas Ubicadas", fmt_num(resumen.get("Ubicado", 0)), "⌖", PRICE_ORANGE, fmt_pct(resumen.get("% Ubicado", 0)) + " vs ingresos", resumen.get("% Ubicado", 0))
    kpi_card("Pendientes por Ubicar", fmt_num(resumen.get("Pendiente", 0)), "⌛", PRICE_GREEN, "Ingreso - ubicado", 100 - resumen.get("% Ubicado", 0))
    kpi_card("% Procesado", fmt_pct(resumen.get("% Ubicado", 0)), "%", PRICE_PURPLE, "Ubicado / ingresadas", resumen.get("% Ubicado", 0))
    st.markdown('</div>', unsafe_allow_html=True)


def hero(resumen, tiendas_count=0):
    st.markdown(f"""
    <div class="hero-blue">
        <h2>Dashboard Ejecutivo</h2>
        <p>Vista ejecutiva de recuperación, productividad, conversión y operación.</p>
        <div class="hero-grid">
            <div class="hero-mini"><div class="hero-mini-label">Tiendas con registro</div><div class="hero-mini-value">{tiendas_count}</div></div>
            <div class="hero-mini"><div class="hero-mini-label">Ingresos</div><div class="hero-mini-value">{fmt_num(resumen.get("Ingresos", 0))}</div></div>
            <div class="hero-mini"><div class="hero-mini-label">Habilitado</div><div class="hero-mini-value">{fmt_pct(resumen.get("% Acondicionado", 0))}</div></div>
            <div class="hero-mini"><div class="hero-mini-label">Ubicado</div><div class="hero-mini-value">{fmt_pct(resumen.get("% Ubicado", 0))}</div></div>
            <div class="hero-mini"><div class="hero-mini-label">Estado</div><div class="hero-mini-value">Activo</div></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def safe_df(df, height=360, editable=False):
    if df is None or df.empty:
        st.info("Sin información con los filtros seleccionados.")
        return df
    view = df.head(500)
    if editable:
        return st.data_editor(view, width="stretch", hide_index=True, height=height, num_rows="dynamic")
    st.dataframe(view, width="stretch", hide_index=True, height=height)
    if len(df) > 500:
        st.caption(f"Vista previa de 500 filas de {len(df):,}. Descarga Excel para ver todo.")
    return df


def panel(title, df=None, height=360, editable=False):
    st.markdown(f'<div class="panel"><div class="panel-title">{title}</div>', unsafe_allow_html=True)
    out = None
    if df is not None:
        out = safe_df(df, height=height, editable=editable)
    st.markdown("</div>", unsafe_allow_html=True)
    return out


def excel_button(df, filename, label="Descargar Excel"):
    if df is None or df.empty:
        return
    b = io.BytesIO()
    with pd.ExcelWriter(b, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Detalle")
    st.download_button(label, b.getvalue(), filename, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


def week_cards(sem_df):
    if sem_df is None or sem_df.empty:
        st.info("Sin información semanal.")
        return
    df = sem_df.tail(4).copy()
    html = '<div class="week-grid">'
    prev = None
    for _, r in df.iterrows():
        ingresos = float(r.get("Ingresos", 0) or 0)
        hab = float(r.get("Acondicionado", 0) or 0)
        ubi = float(r.get("Ubicado", 0) or 0)
        rec = float(r.get("Recorridos", 0) or 0)
        semana = r.get("Semana ISO", 0)
        if prev is None or prev == 0:
            delta = '<span class="week-delta" style="color:#777;">—</span>'
        else:
            d = (ingresos - prev) / prev * 100
            arrow = "▲" if d >= 0 else "▼"
            color = PRICE_GREEN if d >= 0 else PRICE_RED
            delta = f'<span class="week-delta" style="color:{color};">{arrow} {abs(d):.1f}%</span>'
        prev = ingresos
        p_hab = hab / ingresos * 100 if ingresos else 0
        p_ubi = ubi / ingresos * 100 if ingresos else 0
        html += f"""
        <div class="week-card">
            <div class="week-head">Sem {semana}</div>
            <div class="week-line"><div class="week-label">Ingresos</div><div class="week-value">{fmt_num(ingresos)}</div>{delta}</div>
            <div class="week-line"><div class="week-label">% Hab / Ing</div><div class="week-value">{p_hab:.1f}%</div><span></span></div>
            <div class="week-line"><div class="week-label">% Ubic / Ing</div><div class="week-value">{p_ubi:.1f}%</div><span></span></div>
            <div class="week-line"><div class="week-label">Recorridos</div><div class="week-value">{fmt_num(rec)}</div><span></span></div>
        </div>
        """
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def rank_panel(title, df, value_col, name_col="Tienda", color=PRICE_PINK):
    st.markdown(f'<div class="panel"><div class="panel-title">{title}</div>', unsafe_allow_html=True)
    if df is None or df.empty or value_col not in df.columns:
        st.info("Sin información.")
    else:
        show = df.copy()
        if name_col not in show:
            show[name_col] = show.index.astype(str)
        show = show.sort_values(value_col, ascending=False).head(12)
        mx = float(show[value_col].max()) if len(show) else 1
        for _, row in show.iterrows():
            val = float(row[value_col]) if pd.notna(row[value_col]) else 0
            w = val / mx * 100 if mx else 0
            st.markdown(f"""
            <div class="rank-row">
                <div class="rank-name">{row[name_col]}</div>
                <div class="rankbar"><div class="rankbar-fill" style="--accent:{color};--w:{w}%;"></div></div>
                <div class="rank-value">{fmt_num(val)}</div>
            </div>
            """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# EXCEL NORMALIZACIÓN
# ============================================================

OP_KEYS = ["ACTIVIDAD", "NOMBRE", "OCURRENCIA", "NUMERO DE PIEZAS", "PIEZAS", "RECORRIDOS", "HABILITADO", "UBICADO"]
COM_KEYS = ["DEV", "VTA", "VENTA", "COSTO", "MODELO", "ID", "TALLA", "COLOR"]


def classify_sheet(name, df):
    text = " ".join([norm_text(name)] + [norm_text(c) for c in df.columns])
    score_op = sum(k in text for k in OP_KEYS)
    score_co = sum(k in text for k in COM_KEYS)
    if score_co > score_op:
        return "comercial"
    if score_op > 0:
        return "operacion"
    return "otra"


def normalize_operation(df, sheet_name):
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

    out["Fecha"] = pd.to_datetime(df[c_fecha], errors="coerce") if c_fecha else pd.NaT
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


def normalize_commercial(df, sheet_name):
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

    out["Fecha"] = pd.to_datetime(df[c_fecha], errors="coerce") if c_fecha else pd.NaT
    out["Tienda"] = df[c_tienda].astype(str).str.strip() if c_tienda else ""
    out["ID/Modelo"] = df[c_id].astype(str).str.strip() if c_id else ""
    out["Color"] = df[c_color].astype(str).str.strip() if c_color else ""
    out["Talla"] = df[c_talla].astype(str).str.strip() if c_talla else ""
    out["Dev_Pzs"] = to_number(df[c_dev]) if c_dev else 0
    out["Costo_Dev"] = to_number(df[c_costo]) if c_costo else 0
    out["Vta_Pzs"] = to_number(df[c_vta_pzs]) if c_vta_pzs else 0
    out["Vta_Imp"] = to_number(df[c_vta_imp]) if c_vta_imp else 0
    if out["Fecha"].notna().any():
        out["Semana ISO"] = out["Fecha"].dt.isocalendar().week.astype("Int64")
        out["Año ISO"] = out["Fecha"].dt.isocalendar().year.astype("Int64")
        out["Mes"] = out["Fecha"].dt.strftime("%Y-%m")
    else:
        out["Semana ISO"] = 0
        out["Año ISO"] = 0
        out["Mes"] = ""
    return out


@st.cache_data(show_spinner=False)
def load_normalized(file_path, mtime):
    sheets = pd.read_excel(file_path, sheet_name=None, engine="openpyxl")
    ops, coms, diagnostics = [], [], []
    for name, df in sheets.items():
        kind = classify_sheet(name, df)
        diagnostics.append({"Hoja": name, "Tipo detectado": kind, "Filas": len(df), "Columnas": len(df.columns)})
        if kind == "operacion":
            ops.append(normalize_operation(df, name))
        elif kind == "comercial":
            coms.append(normalize_commercial(df, name))
    op = pd.concat(ops, ignore_index=True) if ops else pd.DataFrame()
    co = pd.concat(coms, ignore_index=True) if coms else pd.DataFrame()
    return op, co, pd.DataFrame(diagnostics), list(sheets.keys())


def filter_period(op, co, period):
    if period == "Todo el archivo":
        return op, co
    today = pd.Timestamp.today()
    op2, co2 = op.copy(), co.copy()
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
        "Ingresos": ingresos, "Acondicionado": acondicionado, "Ubicado": ubicado,
        "Pendiente": pendiente, "Recorridos": recorridos,
        "% Acondicionado": safe_div(acondicionado, ingresos), "% Ubicado": safe_div(ubicado, ingresos),
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
        return pd.DataFrame(), {"Dev Pzs": 0, "Conversión Pzs": 0, "Conversión $": 0, "Pendiente Pzs": 0, "% Conversión": 0, "No Convertido $": 0}
    df = co.copy()
    for c in ["Dev_Pzs", "Vta_Pzs", "Vta_Imp", "Costo_Dev"]:
        if c not in df:
            df[c] = 0
    group_cols = [c for c in ["Semana ISO", "Tienda", "ID/Modelo", "Color", "Talla"] if c in df.columns]
    if not group_cols:
        group_cols = ["Tienda"] if "Tienda" in df.columns else []
    if group_cols:
        g = df.groupby(group_cols, dropna=False).agg(**{
            "Dev Pzs": ("Dev_Pzs", "sum"), "Venta Pzs": ("Vta_Pzs", "sum"),
            "Venta $": ("Vta_Imp", "sum"), "Costo Dev": ("Costo_Dev", "sum")
        }).reset_index()
    else:
        g = pd.DataFrame([{"Dev Pzs": df["Dev_Pzs"].sum(), "Venta Pzs": df["Vta_Pzs"].sum(), "Venta $": df["Vta_Imp"].sum(), "Costo Dev": df["Costo_Dev"].sum()}])
    g["Conversión Pzs"] = g[["Dev Pzs", "Venta Pzs"]].min(axis=1)
    ratio = g["Conversión Pzs"] / g["Venta Pzs"].replace(0, pd.NA)
    g["Conversión $"] = (g["Venta $"] * ratio.fillna(0)).fillna(0)
    g["Pendiente Pzs"] = (g["Dev Pzs"] - g["Conversión Pzs"]).clip(lower=0)
    g["No Convertido $"] = (g["Costo Dev"] - g["Conversión $"]).clip(lower=0)
    g["% Conversión"] = (g["Conversión Pzs"] / g["Dev Pzs"].replace(0, pd.NA) * 100).fillna(0)
    k = {
        "Dev Pzs": g["Dev Pzs"].sum(), "Conversión Pzs": g["Conversión Pzs"].sum(),
        "Conversión $": g["Conversión $"].sum(), "Pendiente Pzs": g["Pendiente Pzs"].sum(),
        "No Convertido $": g["No Convertido $"].sum()
    }
    k["% Conversión"] = safe_div(k["Conversión Pzs"], k["Dev Pzs"])
    return g, k


# ============================================================
# LOGIN Y APP
# ============================================================

apply_styles()
init_db()

st.sidebar.markdown("## 🔐 Acceso")
if st.session_state.get("auth_user"):
    user = st.session_state.auth_user
    st.sidebar.success(f"Sesión activa: {user.get('nombre') or user.get('nomina')}")
    st.sidebar.caption(f"Permiso: {user.get('permiso')}")
    if st.sidebar.button("Cerrar sesión"):
        st.session_state.pop("auth_user", None)
        st.rerun()
else:
    st.sidebar.info("Para visualizar, inicia sesión.")
    nomina = st.sidebar.text_input("Nómina / Usuario")
    password = st.sidebar.text_input("Contraseña", type="password")
    if st.sidebar.button("Iniciar sesión", type="primary", use_container_width=True):
        ok = None
        for u in load_users():
            if u.get("activo", True) and str(u.get("nomina", "")).strip() == str(nomina).strip() and str(u.get("password", "")) == str(password):
                ok = u
                break
        if ok:
            st.session_state.auth_user = ok
            st.rerun()
        else:
            st.sidebar.error("Usuario o contraseña incorrectos.")

if not st.session_state.get("auth_user"):
    login_screen()
    st.stop()

user = st.session_state.auth_user
is_admin = user.get("permiso") == "Administrador"

st.sidebar.divider()
st.sidebar.markdown("## 📁 Fuente de datos")
meta = get_metadata()
if ACTIVE_FILE.exists():
    st.sidebar.success("Archivo cargado")
    st.sidebar.write(meta.get("nombre_original", "Archivo activo"))
    st.sidebar.caption(meta.get("fecha_carga", ""))
else:
    st.sidebar.warning("No hay archivo cargado")

if is_admin:
    up = st.sidebar.file_uploader("Cargar/Reemplazar Excel", type=["xlsx"])
    if up is not None and st.sidebar.button("Procesar archivo", type="primary"):
        save_uploaded_file(up)
        st.cache_data.clear()
        st.sidebar.success("Archivo guardado")
        st.rerun()

    if ACTIVE_FILE.exists() and st.sidebar.button("Borrar archivo persistido"):
        delete_active_file()
        st.sidebar.success("Archivo eliminado")
        st.rerun()

st.sidebar.markdown('<div style="background:#EEF5FF;border-radius:14px;padding:14px;margin-top:24px;color:#1D2E6E;font-weight:900;">🛡️ CONFIDENCIAL<br><span style="font-weight:500;color:#6B7280;">Price Shoes | Operaciones Ropa</span></div>', unsafe_allow_html=True)

header({"role": user.get("permiso", "Consulta"), "is_admin": is_admin})

if not ACTIVE_FILE.exists():
    st.warning("Carga un archivo Excel desde el panel lateral para iniciar.")
    st.stop()

page = nav_bar()

try:
    op_all, co_all, diag_df, sheet_names = load_normalized(str(ACTIVE_FILE), ACTIVE_FILE.stat().st_mtime)
except Exception as e:
    st.error("No fue posible procesar el Excel. Valida que el archivo no esté dañado y que tenga hojas operativas/comerciales.")
    st.exception(e)
    st.stop()

tiendas = sorted(set(
    (op_all["Tienda"].dropna().astype(str).tolist() if not op_all.empty and "Tienda" in op_all else [])
    + (co_all["Tienda"].dropna().astype(str).tolist() if not co_all.empty and "Tienda" in co_all else [])
))

st.markdown('<div class="filter-card">', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns([2.1, 1.5, 1.2, .8])
with c1:
    f_tienda = st.multiselect("Tienda", tiendas, placeholder="Todas las tiendas")
with c2:
    periodo = st.selectbox("Periodo", ["Todo el archivo", "Semana actual", "Mes actual"], index=0)
with c3:
    vista = st.selectbox("Vista", ["Ejecutiva", "Detalle"], index=0)
with c4:
    st.write("")
    st.button("Actualizar", type="primary", use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

op_base, co_base = op_all.copy(), co_all.copy()
if f_tienda:
    if not op_base.empty and "Tienda" in op_base:
        op_base = op_base[op_base["Tienda"].isin(f_tienda)]
    if not co_base.empty and "Tienda" in co_base:
        co_base = co_base[co_base["Tienda"].isin(f_tienda)]

op, co = filter_period(op_base, co_base, periodo)
resumen = resumen_ejecutivo(op, co)
detalle = resumen_tienda(op, co)
sem_df = resumen_semana(op_base, co_base)
mes_df = resumen_mes(op_base, co_base)
prod_df = productividad(op)
conv_df, conv_kpis = conversion(co)
goals = load_goals()


# ============================================================
# PÁGINAS
# ============================================================

def dashboard():
    hero(resumen, len(detalle) if detalle is not None else 0)
    kpis(resumen)
    section("Últimas 4 semanas", "Ingresos vs semana anterior, % habilitado y % ubicado sobre ingresos.")
    week_cards(sem_df)
    a, b, c = st.columns(3)
    with a:
        rank_panel("Top tiendas por ingresos", detalle, "Ingresos", "Tienda", PRICE_BLUE)
    with b:
        rank_panel("Top tiendas por ubicado", detalle, "Ubicado", "Tienda", PRICE_PURPLE)
    with c:
        rank_panel("Top colaboradores", prod_df, "Productividad", "Nombre" if not prod_df.empty and "Nombre" in prod_df else "Tienda", PRICE_GREEN)


def dia_anterior():
    section("Día Anterior | Ingresos y Pendiente por Procesar", "Detalle operativo por tienda y registros cargados.")
    kpis(resumen)
    a, b = st.columns([1.1, .9])
    with a:
        panel("Detalle por tienda", detalle, height=390, editable=is_admin)
    with b:
        st.markdown('<div class="panel"><div class="panel-title">Ingreso vs Habilitado vs Ubicado</div>', unsafe_allow_html=True)
        if not detalle.empty:
            p = detalle.head(12)
            fig = px.bar(p, x="Tienda", y=["Ingresos", "Acondicionado", "Ubicado"], barmode="group")
            fig.update_layout(height=390, margin=dict(l=10, r=10, t=10, b=75))
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("Sin información.")
        st.markdown("</div>", unsafe_allow_html=True)

    section("Detalle de registros subidos", "No entra al PDF; sirve para auditar lo cargado.")
    tienda_det = st.selectbox("Filtrar tienda para detalle", ["Todas"] + tiendas)
    reg = op.copy()
    if tienda_det != "Todas" and "Tienda" in reg:
        reg = reg[reg["Tienda"] == tienda_det]
    cols = [c for c in ["Fecha", "Tienda", "Nombre", "Actividad Realizada", "Número de Piezas", "Área", "Motivo de ingreso", "Ocurrencia"] if c in reg.columns]
    show = reg[cols] if cols else reg
    safe_df(show, height=360, editable=is_admin)
    excel_button(show, "detalle_registros_dia_anterior.xlsx", "Descargar detalle completo")


def reporte_semanal():
    section("Reporte Semanal", "Indicadores por Semana ISO.")
    kpis(resumen)
    week_cards(sem_df)
    a, b = st.columns([.9, 1.1])
    with a:
        panel("Resumen por semana", sem_df, height=410, editable=is_admin)
    with b:
        st.markdown('<div class="panel"><div class="panel-title">Tendencia semanal</div>', unsafe_allow_html=True)
        if not sem_df.empty:
            p = sem_df.tail(12)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=p["Semana ISO"], y=p["Ingresos"], mode="lines+markers", name="Ingresos"))
            fig.add_trace(go.Scatter(x=p["Semana ISO"], y=p["Acondicionado"], mode="lines+markers", name="Habilitado"))
            fig.add_trace(go.Scatter(x=p["Semana ISO"], y=p["Ubicado"], mode="lines+markers", name="Ubicado"))
            fig.update_layout(height=410, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("Sin información.")
        st.markdown("</div>", unsafe_allow_html=True)
    excel_button(sem_df, "reporte_semanal.xlsx")


def reporte_mensual():
    section("Reporte Mensual", "Indicadores acumulados por mes.")
    kpis(resumen)
    a, b = st.columns([.9, 1.1])
    with a:
        panel("Resumen por mes", mes_df, height=420, editable=is_admin)
    with b:
        st.markdown('<div class="panel"><div class="panel-title">Evolución mensual</div>', unsafe_allow_html=True)
        if not mes_df.empty:
            fig = px.bar(mes_df, x="Mes", y=["Ingresos", "Acondicionado", "Ubicado"], barmode="group")
            fig.update_layout(height=420, margin=dict(l=10, r=10, t=10, b=65))
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("Sin información.")
        st.markdown("</div>", unsafe_allow_html=True)
    excel_button(mes_df, "reporte_mensual.xlsx")


def conversion_page():
    section("Conversión Semanal Dev → Venta", "La venta sólo cuenta si ocurre en la misma Semana ISO de la devolución.")
    st.info("Si el archivo comercial no contiene fecha válida, se muestra acumulado como Semana 0. Para calcular Semana ISO automáticamente, valida una columna de fecha.")
    st.markdown('<div class="kpi-grid">', unsafe_allow_html=True)
    kpi_card("Dev Pzs Semana", fmt_num(conv_kpis.get("Dev Pzs", 0)), "↩", PRICE_BLUE, "Devolución", 100)
    kpi_card("Conversión Pzs", fmt_num(conv_kpis.get("Conversión Pzs", 0)), "🔄", PRICE_GREEN, "Misma semana", conv_kpis.get("% Conversión", 0))
    kpi_card("Conversión $", fmt_money(conv_kpis.get("Conversión $", 0)), "$", PRICE_PURPLE, "Venta recuperada", 100)
    kpi_card("% Conversión", fmt_pct(conv_kpis.get("% Conversión", 0)), "%", PRICE_CYAN, "Dev → Venta", conv_kpis.get("% Conversión", 0))
    kpi_card("Pendiente Pzs", fmt_num(conv_kpis.get("Pendiente Pzs", 0)), "⏱", PRICE_ORANGE, "Por convertir", 100 - conv_kpis.get("% Conversión", 0))
    st.markdown('</div>', unsafe_allow_html=True)
    panel("Detalle de conversión", conv_df, height=430, editable=is_admin)
    excel_button(conv_df, "conversion_semanal_dev_venta.xlsx")


def recuperacion():
    section("Recuperación Económica", "Importe recuperado y pendiente.")
    st.markdown('<div class="kpi-grid">', unsafe_allow_html=True)
    kpi_card("Recuperación $", fmt_money(conv_kpis.get("Conversión $", 0)), "$", PRICE_GREEN, "Venta recuperada", 100)
    kpi_card("No Convertido $", fmt_money(conv_kpis.get("No Convertido $", 0)), "⏱", PRICE_ORANGE, "Pendiente", 100)
    kpi_card("% Conversión", fmt_pct(conv_kpis.get("% Conversión", 0)), "%", PRICE_CYAN, "Piezas", conv_kpis.get("% Conversión", 0))
    st.markdown('</div>', unsafe_allow_html=True)
    panel("Detalle económico", conv_df, height=430, editable=is_admin)


def productividad_page():
    section("Productividad", "Productividad por colaborador.")
    a, b = st.columns([.9, 1.1])
    with a:
        panel("Productividad por colaborador", prod_df, height=430, editable=is_admin)
    with b:
        st.markdown('<div class="panel"><div class="panel-title">Top colaboradores</div>', unsafe_allow_html=True)
        if not prod_df.empty:
            name_col = "Nombre" if "Nombre" in prod_df else "Tienda"
            p = prod_df.head(15).sort_values("Productividad")
            fig = px.bar(p, x="Productividad", y=name_col, orientation="h", text="Productividad")
            fig.update_layout(height=430)
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("Sin información.")
        st.markdown("</div>", unsafe_allow_html=True)


def recorridos_page():
    section("Recorridos", "Meta vs real.")
    if not op.empty and "Tienda" in op:
        rec = op.groupby("Tienda", dropna=False).agg(Recorridos=("Recorridos", "sum")).reset_index()
        rec["Meta"] = goals.get("recorridos_semanal", 47)
        rec["% Cumplimiento"] = rec["Recorridos"] / rec["Meta"].replace(0, pd.NA) * 100
    else:
        rec = pd.DataFrame()
    a, b = st.columns([.9, 1.1])
    with a:
        panel("Cumplimiento por tienda", rec, height=430, editable=is_admin)
    with b:
        st.markdown('<div class="panel"><div class="panel-title">Recorridos por tienda</div>', unsafe_allow_html=True)
        if not rec.empty:
            fig = px.bar(rec.sort_values("Recorridos"), x="Recorridos", y="Tienda", orientation="h", text="Recorridos")
            fig.update_layout(height=430)
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("Sin información.")
        st.markdown("</div>", unsafe_allow_html=True)


def ranking_page():
    section("Ranking", "Top y bottom tiendas / colaboradores.")
    a, b = st.columns(2)
    with a:
        rank_panel("Top tiendas por ingresos", detalle, "Ingresos", "Tienda", PRICE_BLUE)
    with b:
        rank_panel("Top colaboradores", prod_df, "Productividad", "Nombre" if not prod_df.empty and "Nombre" in prod_df else "Tienda", PRICE_GREEN)
    panel("Detalle ranking tiendas", detalle, height=320, editable=is_admin)


def macro_page():
    section("Macro", "Últimas 4 semanas y últimos 3 meses.")
    week_cards(sem_df)
    panel("Últimos 3 meses", mes_df.tail(3) if not mes_df.empty else mes_df, height=260)


def criterios_page():
    section("Criterios", "Diagnóstico y validación del archivo.")
    panel("Hojas detectadas", diag_df, height=320)
    with st.expander("Ver columnas normalizadas"):
        st.write("Operación:", list(op_all.columns))
        st.write("Comercial:", list(co_all.columns))
        st.write("Hojas:", sheet_names)


def configuracion_page():
    section("Configuración", "Metas, tiendas y parámetros.")
    if not is_admin:
        st.warning("Sólo administrador puede modificar configuración.")
        return
    with st.form("goals_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            prod_goal = st.number_input("Meta Productividad Diaria", min_value=0, value=int(goals.get("productividad_diaria", 784)))
        with c2:
            rec_goal = st.number_input("Meta Recorridos Semanal", min_value=0, value=int(goals.get("recorridos_semanal", 47)))
        with c3:
            conv_goal = st.number_input("Meta Conversión %", min_value=0.0, value=float(goals.get("conversion_meta", 90.0)))
        if st.form_submit_button("Guardar metas"):
            save_goals({"productividad_diaria": prod_goal, "recorridos_semanal": rec_goal, "conversion_meta": conv_goal})
            st.success("Metas guardadas.")
    st.multiselect("Tiendas del proyecto", tiendas, default=tiendas)


def usuarios_page():
    section("Usuarios", "Asignación de accesos: sólo los usuarios creados pueden entrar al reporte.")
    if not is_admin:
        st.warning("Sólo administrador puede crear, editar o eliminar usuarios.")
        return

    users = load_users()
    st.markdown('<div class="panel"><div class="panel-title">Crear nuevo usuario</div>', unsafe_allow_html=True)
    with st.form("user_form"):
        c1, c2, c3, c4, c5 = st.columns([1, 1.5, 1.2, 1.2, .8])
        with c1:
            nomina = st.text_input("Nómina / Usuario")
        with c2:
            nombre = st.text_input("Nombre")
        with c3:
            permiso = st.selectbox("Tipo de permiso", ["Consulta", "Administrador"])
        with c4:
            password = st.text_input("Contraseña", type="password")
        with c5:
            activo = st.checkbox("Activo", value=True)
        if st.form_submit_button("Crear usuario"):
            if not nomina or not password:
                st.error("Nómina/Usuario y contraseña son obligatorios.")
            elif any(str(u.get("nomina", "")).strip() == str(nomina).strip() for u in users):
                st.error("Ese usuario/nómina ya existe.")
            else:
                upsert_user(str(nomina).strip(), str(nombre).strip() or str(nomina).strip(), permiso, str(password), bool(activo))
                st.success("Usuario creado. Ya podrá ingresar con su usuario y contraseña.")
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("### Usuarios existentes")
    users = load_users()
    users_df = pd.DataFrame([{"nomina": u.get("nomina", ""), "nombre": u.get("nombre", ""), "permiso": u.get("permiso", "Consulta"), "activo": bool(u.get("activo", True))} for u in users])
    edited = st.data_editor(
        users_df, width="stretch", hide_index=True, height=300, num_rows="fixed",
        column_config={"permiso": st.column_config.SelectboxColumn("permiso", options=["Consulta", "Administrador"]), "activo": st.column_config.CheckboxColumn("activo")},
    )

    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("Guardar cambios", type="primary"):
            for _, r in edited.iterrows():
                nom = str(r.get("nomina", "")).strip()
                if not nom:
                    continue
                existing = next((u for u in users if u.get("nomina") == nom), {})
                upsert_user(nom, str(r.get("nombre", "")).strip() or nom, str(r.get("permiso", "Consulta")), existing.get("password", None), bool(r.get("activo", True)))
            st.success("Cambios guardados.")
            st.rerun()
    with c2:
        eliminar = st.selectbox("Eliminar usuario", [""] + [u.get("nomina", "") for u in users], key="delete_user")
        if st.button("Eliminar seleccionado"):
            if not eliminar:
                st.warning("Selecciona un usuario.")
            elif eliminar == user.get("nomina"):
                st.error("No puedes eliminar el usuario con el que estás conectado.")
            else:
                delete_user(eliminar)
                st.success("Usuario eliminado.")
                st.rerun()

    st.markdown("### Cambiar contraseña")
    with st.form("change_pass_form"):
        c1, c2 = st.columns([1, 1])
        with c1:
            usr = st.selectbox("Usuario", [u.get("nomina", "") for u in users], key="pass_user")
        with c2:
            new_pass = st.text_input("Nueva contraseña", type="password")
        if st.form_submit_button("Actualizar contraseña"):
            if not new_pass:
                st.error("Captura una contraseña.")
            else:
                existing = next((u for u in users if u.get("nomina") == usr), None)
                if existing:
                    upsert_user(existing.get("nomina"), existing.get("nombre"), existing.get("permiso"), new_pass, existing.get("activo", True))
                    st.success("Contraseña actualizada.")
                    st.rerun()


ROUTES = {
    "Resumen": dashboard,
    "Día Anterior": dia_anterior,
    "Reporte Semanal": reporte_semanal,
    "Reporte Mensual": reporte_mensual,
    "Conversión": conversion_page,
    "Recuperación Económica": recuperacion,
    "Productividad": productividad_page,
    "Recorridos": recorridos_page,
    "Ranking": ranking_page,
    "Macro": macro_page,
    "Criterios": criterios_page,
    "Configuración": configuracion_page,
    "Usuarios": usuarios_page,
}

ROUTES.get(page, dashboard)()

st.markdown("---")
st.caption("CONFIDENCIAL | Price Shoes | Operaciones Ropa")
