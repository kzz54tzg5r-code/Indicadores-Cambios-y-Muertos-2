from __future__ import annotations

from pathlib import Path
from datetime import datetime
import base64
import io

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from core.auth import obtener_rol_sidebar
from core.indicadores import resumen_ejecutivo, resumen_por_tienda
from core.loader import cargar_excel_actual
from core.normalizador import detectar_y_normalizar_hojas
from core.storage import (
    borrar_archivo_persistente,
    existe_archivo_persistente,
    guardar_archivo_persistente,
    obtener_metadata_archivo,
)
from core.utils import formato_numero, formato_porcentaje, formato_pesos

PRICE_BLUE = "#2563EB"
PRICE_PINK = "#EC007C"
PRICE_PURPLE = "#7C3AED"
PRICE_DARK = "#15172F"
PRICE_GREEN = "#16A34A"
PRICE_ORANGE = "#F97316"
PRICE_CYAN = "#06B6D4"
PRICE_RED = "#E11D48"
PRICE_GRAY = "#6B7280"
LIGHT = "#F7F8FB"

st.set_page_config(
    page_title="Indicadores Cambios y Muertos",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# ESTILO EJECUTIVO
# ============================================================

def aplicar_estilos():
    st.markdown(
        f"""
        <style>
        .stApp {{
            background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
        }}

        .block-container {{
            max-width: 100% !important;
            padding-top: 1rem !important;
            padding-left: 1.7rem !important;
            padding-right: 1.7rem !important;
            padding-bottom: 2rem !important;
        }}

        section[data-testid="stSidebar"] {{
            background: #FFFFFF;
            border-right: 1px solid #E5EAF3;
            box-shadow: 8px 0 25px rgba(17,24,39,.04);
        }}

        section[data-testid="stSidebar"] > div {{
            padding-top: 1.1rem;
        }}

        .sidebar-title {{
            color: {PRICE_DARK};
            font-weight: 950;
            font-size: 22px;
            line-height: 1.05;
            margin-bottom: 2px;
        }}

        .sidebar-subtitle {{
            color: {PRICE_GRAY};
            font-size: 13px;
            font-weight: 650;
            margin-bottom: 14px;
        }}

        .side-chip {{
            background: #EEF5FF;
            color: {PRICE_BLUE};
            border-radius: 14px;
            padding: 12px 14px;
            font-size: 13px;
            font-weight: 850;
            border: 1px solid #DBEAFE;
            margin: 8px 0 14px;
        }}

        .source-card {{
            background: #F8FAFC;
            border: 1px solid #E5EAF3;
            border-radius: 16px;
            padding: 14px;
            margin: 10px 0 18px;
            color: {PRICE_DARK};
        }}

        .status-dot {{
            display:inline-block;
            width:10px;
            height:10px;
            border-radius:50%;
            background:{PRICE_GREEN};
            margin-right:8px;
        }}

        .topbar {{
            background: #FFFFFF;
            border: 1px solid #E6EAF2;
            border-radius: 22px;
            padding: 18px 22px;
            display: grid;
            grid-template-columns: 170px 1fr 420px;
            gap: 20px;
            align-items: center;
            box-shadow: 0 10px 28px rgba(17,24,39,.07);
            margin-bottom: 18px;
        }}

        .logo-box {{
            display:flex;
            align-items:center;
            justify-content:center;
            min-height: 72px;
        }}

        .logo-fallback {{
            font-weight:950;
            color:{PRICE_BLUE};
            font-size: 25px;
            line-height: .88;
            text-align:center;
        }}

        .headline {{
            border-left: 4px solid {PRICE_PINK};
            padding-left: 22px;
        }}

        .headline-title {{
            color: {PRICE_DARK};
            font-weight: 950;
            font-size: 34px;
            line-height: 1.02;
            letter-spacing: -0.6px;
        }}

        .headline-sub {{
            color: {PRICE_GRAY};
            font-weight: 750;
            font-size: 15px;
            margin-top: 7px;
        }}

        .top-meta {{
            display:grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
        }}

        .meta-card {{
            background:#F8FAFC;
            border:1px solid #E5EAF3;
            border-radius:16px;
            padding: 12px 14px;
            min-height:70px;
        }}

        .meta-label {{
            color:{PRICE_GRAY};
            font-size: 12px;
            font-weight: 750;
        }}

        .meta-value {{
            color:{PRICE_DARK};
            font-size: 17px;
            font-weight: 950;
            margin-top: 4px;
        }}

        .hero {{
            background: linear-gradient(135deg, #1D2E6E 0%, #2563EB 72%, #EC007C 170%);
            border-radius: 24px;
            padding: 24px;
            color: white;
            box-shadow: 0 18px 35px rgba(21,23,47,.22);
            margin-bottom: 22px;
        }}

        .hero-title {{
            font-size: 28px;
            font-weight: 950;
            line-height: 1.05;
        }}

        .hero-sub {{
            opacity: .82;
            font-size: 14px;
            font-weight: 650;
            margin-top: 6px;
        }}

        .status-row {{
            display:grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 12px;
            margin-top: 18px;
        }}

        .status-mini {{
            background: rgba(255,255,255,.11);
            border: 1px solid rgba(255,255,255,.18);
            border-radius: 16px;
            padding: 12px;
        }}

        .status-mini-label {{
            opacity:.75;
            font-size:12px;
            font-weight:750;
        }}

        .status-mini-value {{
            margin-top:3px;
            font-size:17px;
            font-weight:950;
        }}

        .section-title {{
            color:{PRICE_DARK};
            font-size: 25px;
            font-weight: 950;
            margin: 8px 0 4px;
        }}

        .section-sub {{
            color:{PRICE_GRAY};
            font-size: 14px;
            margin-bottom: 16px;
        }}

        .metric-grid {{
            display:grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-bottom: 22px;
        }}

        .metric-card {{
            background:white;
            border:1px solid #E6EAF2;
            border-radius:22px;
            padding:18px;
            min-height: 170px;
            box-shadow:0 12px 28px rgba(17,24,39,.07);
            position:relative;
            overflow:hidden;
        }}

        .metric-card:after {{
            content:"";
            position:absolute;
            right:-35px;
            top:-35px;
            width:95px;
            height:95px;
            border-radius:50%;
            background: var(--accent-soft);
        }}

        .metric-top {{
            display:flex;
            align-items:center;
            gap:12px;
            position:relative;
            z-index:1;
        }}

        .metric-icon {{
            width:50px;
            height:50px;
            border-radius:16px;
            background: var(--accent);
            color:white;
            display:flex;
            align-items:center;
            justify-content:center;
            font-size:22px;
            font-weight:950;
            box-shadow:0 10px 22px var(--accent-shadow);
        }}

        .metric-label {{
            color:var(--accent);
            font-weight:950;
            font-size:14px;
            line-height:1.1;
        }}

        .metric-value {{
            color:{PRICE_DARK};
            font-size:30px;
            font-weight:950;
            margin-top:18px;
            letter-spacing:-.5px;
            position:relative;
            z-index:1;
        }}

        .metric-note {{
            color:{PRICE_GRAY};
            font-size:13px;
            font-weight:650;
            margin-top:5px;
        }}

        .progress-wrap {{
            height:9px;
            width:100%;
            background:#EEF2F7;
            border-radius:99px;
            overflow:hidden;
            margin-top:16px;
        }}

        .progress-bar {{
            height:100%;
            width:var(--pct);
            background:var(--accent);
            border-radius:99px;
        }}

        .delta {{
            display:inline-block;
            margin-top:12px;
            padding:6px 9px;
            border-radius:10px;
            font-size:12px;
            font-weight:900;
            color:var(--accent);
            background:var(--accent-soft);
        }}

        .panel {{
            background:white;
            border:1px solid #E6EAF2;
            border-radius:22px;
            padding:20px;
            box-shadow:0 12px 28px rgba(17,24,39,.06);
            min-height:360px;
        }}

        .panel-title {{
            color:{PRICE_DARK};
            font-size:18px;
            font-weight:950;
            margin-bottom:12px;
        }}

        .rank-row {{
            display:grid;
            grid-template-columns: 140px 1fr 70px;
            gap: 12px;
            align-items:center;
            padding:10px 0;
            border-bottom:1px solid #EEF2F7;
        }}

        .rank-name {{
            color:{PRICE_DARK};
            font-weight:850;
            font-size:13px;
            white-space:nowrap;
            overflow:hidden;
            text-overflow:ellipsis;
        }}

        .rankbar {{
            height:10px;
            background:#EEF2F7;
            border-radius:99px;
            overflow:hidden;
        }}

        .rankbar-fill {{
            height:100%;
            border-radius:99px;
            background:{PRICE_PINK};
            width:var(--w);
        }}

        .rank-value {{
            color:{PRICE_DARK};
            font-weight:950;
            font-size:13px;
            text-align:right;
        }}

        .week-grid {{
            display:grid;
            grid-template-columns: repeat(4, 1fr);
            gap:16px;
            margin-bottom:22px;
        }}

        .week-card {{
            background:white;
            border:1px solid #E6EAF2;
            border-radius:20px;
            overflow:hidden;
            box-shadow:0 10px 22px rgba(17,24,39,.06);
        }}

        .week-head {{
            background:#3F3F91;
            color:white;
            padding:13px 15px;
            font-weight:950;
            text-align:center;
            font-size:15px;
        }}

        .week-line {{
            display:grid;
            grid-template-columns: 1fr auto auto;
            gap:10px;
            padding:12px 16px;
            border-bottom:1px solid #EEF2F7;
            align-items:center;
        }}

        .week-label {{
            color:#666;
            font-size:12px;
            font-weight:900;
            text-transform:uppercase;
        }}

        .week-value {{
            color:#3F3F91;
            font-size:17px;
            font-weight:950;
        }}

        .week-delta {{
            font-size:11px;
            font-weight:900;
        }}

        .module-tabs {{
            display:flex;
            gap:8px;
            overflow-x:auto;
            padding:4px 0 10px;
            margin-bottom:12px;
            border-bottom:1px solid #E5EAF3;
        }}

        .module-tab {{
            padding:10px 14px;
            border-radius:14px 14px 0 0;
            color:{PRICE_DARK};
            background:white;
            border:1px solid #E6EAF2;
            font-weight:850;
            white-space:nowrap;
            min-width:max-content;
        }}

        div[data-testid="stDataFrame"] {{
            border-radius:14px;
            overflow:hidden;
        }}

        .admin-box {{
            background:#FFF7ED;
            border:1px solid #FED7AA;
            border-radius:18px;
            padding:16px;
            margin:14px 0;
        }}


        .top-nav {
            background:#1D2E6E;
            border-top:4px solid #EC007C;
            display:flex;
            gap:0;
            overflow-x:auto;
            margin:4px 0 24px 0;
            box-shadow:0 8px 20px rgba(29,46,110,.12);
        }
        div[data-testid="stSegmentedControl"] {
            background:#1D2E6E;
            border-top:4px solid #EC007C;
            padding:0;
            margin-bottom:24px;
            overflow-x:auto;
            display:block;
            white-space:nowrap;
        }
        div[data-testid="stSegmentedControl"] button {
            border-radius:0 !important;
            border:none !important;
            background:#1D2E6E !important;
            color:white !important;
            padding:15px 22px !important;
            font-weight:900 !important;
            border-bottom:4px solid transparent !important;
        }
        div[data-testid="stSegmentedControl"] button[aria-pressed="true"] {
            border-bottom-color:#EC007C !important;
            background:#243A82 !important;
        }

        @media (max-width: 1200px) {{
            .topbar {{ grid-template-columns: 120px 1fr; }}
            .top-meta {{ display:none; }}
            .metric-grid {{ grid-template-columns: repeat(2, 1fr); }}
            .week-grid {{ grid-template-columns: repeat(2, 1fr); }}
            .status-row {{ grid-template-columns: repeat(2, 1fr); }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def logo_html():
    for logo_name in ["assets/logo_price.png", "assets/logo.png"]:
        logo = Path(logo_name)
        if logo.exists():
            ext = logo.suffix.replace(".", "") or "png"
            data = base64.b64encode(logo.read_bytes()).decode()
            return f'<img src="data:image/{ext};base64,{data}" style="max-width:145px;max-height:80px;">'
    return '<div class="logo-fallback">Price<br>Shoes</div>'


def render_topbar(is_admin: bool):
    now = datetime.now()
    role = "Administrador" if is_admin else "Consulta"
    st.markdown(
        f"""
        <div class="topbar">
            <div class="logo-box">{logo_html()}</div>
            <div class="headline">
                <div class="headline-title">Indicadores Cambios y Muertos</div>
                <div class="headline-sub">Operaciones Ropa | Recuperación | Productividad | Conversión</div>
            </div>
            <div class="top-meta">
                <div class="meta-card">
                    <div class="meta-label">Fecha de consulta</div>
                    <div class="meta-value">📅 {now.strftime('%d/%m/%Y')}</div>
                </div>
                <div class="meta-card">
                    <div class="meta-label">Usuario activo</div>
                    <div class="meta-value">{'👑' if is_admin else '👤'} {role}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def sidebar_access():
    rol, is_admin = obtener_rol_sidebar()

    st.sidebar.markdown(
        """
        <div class="sidebar-title">Indicadores<br>Cambios y Muertos</div>
        <div class="sidebar-subtitle">Operaciones Ropa | Price Shoes</div>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.markdown(
        f"""
        <div class="side-chip">
            <span class="status-dot"></span>Rol activo: {"Administrador" if is_admin else "Consulta"}
        </div>
        """,
        unsafe_allow_html=True,
    )
    return rol, is_admin


def source_sidebar(is_admin: bool):
    st.sidebar.divider()
    st.sidebar.markdown("### 📁 Fuente de datos")
    metadata = obtener_metadata_archivo()

    if existe_archivo_persistente():
        st.sidebar.success("Archivo cargado")
        st.sidebar.markdown(
            f"""
            <div class="source-card">
                <b>📗 Archivo activo</b><br>
                {metadata.get('nombre_original', 'Sin nombre')}<br><br>
                <span style="color:#6B7280;font-size:12px;">Actualizado: {metadata.get('fecha_carga', 'Sin fecha')}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.sidebar.warning("No hay archivo cargado")

    if is_admin:
        uploaded_file = st.sidebar.file_uploader("Cargar/Reemplazar Excel", type=["xlsx"], key="excel_uploader")
        if uploaded_file is not None and st.sidebar.button("Procesar y guardar archivo", type="primary"):
            guardar_archivo_persistente(uploaded_file)
            st.sidebar.success("Archivo guardado correctamente")
            st.rerun()

        if existe_archivo_persistente() and st.sidebar.button("Borrar archivo persistido"):
            borrar_archivo_persistente()
            st.sidebar.success("Archivo eliminado")
            st.rerun()


def top_navigation():
    labels = [
        "Dashboard",
        "Día Anterior",
        "Reporte Semanal",
        "Reporte Mensual",
        "Conversión",
        "Recuperación Económica",
        "Productividad",
        "Recorridos",
        "Rankings",
        "Macro",
        "Diagnóstico",
        "Configuración",
        "Usuarios",
    ]
    default_label = st.session_state.get("nav_label", "Dashboard")
    if default_label not in labels:
        default_label = "Dashboard"

    try:
        selected = st.segmented_control(
            "Navegación",
            labels,
            default=default_label,
            label_visibility="collapsed",
            key="nav_label",
        )
    except Exception:
        selected = st.radio(
            "Navegación",
            labels,
            index=labels.index(default_label),
            horizontal=True,
            label_visibility="collapsed",
            key="nav_label_radio",
        )

    mapping = {
        "Dashboard": "🏠 Dashboard Ejecutivo",
        "Día Anterior": "📅 Día Anterior",
        "Reporte Semanal": "📈 Reporte Semanal",
        "Reporte Mensual": "📆 Reporte Mensual",
        "Conversión": "🔄 Conversión",
        "Recuperación Económica": "💲 Recuperación Económica",
        "Productividad": "👥 Productividad",
        "Recorridos": "🚶 Recorridos",
        "Rankings": "🏆 Rankings",
        "Macro": "📊 Macro",
        "Diagnóstico": "🩺 Diagnóstico",
        "Configuración": "⚙️ Configuración",
        "Usuarios": "👤 Usuarios",
    }
    return mapping.get(selected, "🏠 Dashboard Ejecutivo")


def sidebar_menu():
    st.sidebar.markdown("### 🧭 Navegación")
    st.sidebar.info("La navegación principal ahora está en la barra superior azul, como el tablero de referencia.")
    return None


def sidebar_footer():
    st.sidebar.markdown(
        '<div class="side-chip">🛡️ CONFIDENCIAL<br><span style="font-weight:500;color:#6B7280;">Price Shoes | Operaciones Ropa</span></div>',
        unsafe_allow_html=True,
    )


# ============================================================
# HELPERS VISUALES
# ============================================================

def css_color(hex_color: str):
    return hex_color


def pct_width(value):
    try:
        v = float(value)
    except Exception:
        v = 0
    return max(0, min(100, v))


def metric_card(label, value, icon, color, note="", pct=0, delta=""):
    st.markdown(
        f"""
        <div class="metric-card" style="--accent:{color};--accent-soft:{color}18;--accent-shadow:{color}38;">
            <div class="metric-top">
                <div class="metric-icon">{icon}</div>
                <div class="metric-label">{label}</div>
            </div>
            <div class="metric-value">{value}</div>
            <div class="metric-note">{note}</div>
            <div class="progress-wrap"><div class="progress-bar" style="--pct:{pct_width(pct)}%;"></div></div>
            {f'<div class="delta">{delta}</div>' if delta else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi_grid(resumen):
    ingresos = resumen.get("Piezas Ingresadas", 0)
    habilitado = resumen.get("Acondicionado", 0)
    ubicado = resumen.get("Ubicado", 0)
    pendiente = resumen.get("Pendiente Ubicar", 0)
    p_hab = resumen.get("% Acondicionado", 0)
    p_ubic = resumen.get("% Ubicado", 0)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Ingresos", formato_numero(ingresos), "📦", PRICE_BLUE, "Total de piezas ingresadas", 100, "+8.6% vs semana anterior")
    with c2:
        metric_card("Habilitado", formato_numero(habilitado), "✓", PRICE_GREEN, f"{formato_porcentaje(p_hab)} del total", p_hab, "Meta diaria: 784")
    with c3:
        metric_card("Ubicado", formato_numero(ubicado), "📍", PRICE_PURPLE, f"{formato_porcentaje(p_ubic)} del total", p_ubic, "Ubicado / ingreso")
    with c4:
        metric_card("Pendiente", formato_numero(pendiente), "⏱", PRICE_ORANGE, "Pendiente por ubicar", 100 - pct_width(p_ubic), "Prioridad operativa")


def section_title(title, subtitle=""):
    st.markdown(f'<div class="section-title">{title}</div><div class="section-sub">{subtitle}</div>', unsafe_allow_html=True)


def excel_download(df: pd.DataFrame, filename: str, label: str):
    if df is None or df.empty:
        return
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Detalle")
    st.download_button(label, data=buf.getvalue(), file_name=filename, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


MAX_PREVIEW_ROWS = 500

def safe_dataframe(df: pd.DataFrame, height: int = 360):
    if df is None or df.empty:
        st.info("Sin información con los filtros seleccionados.")
        return
    view = df.head(MAX_PREVIEW_ROWS)
    st.dataframe(view, width="stretch", hide_index=True, height=height)
    if len(df) > MAX_PREVIEW_ROWS:
        st.caption(f"Vista previa de {MAX_PREVIEW_ROWS:,} filas de {len(df):,}. Descarga Excel para ver todo.")


def panel_table(title, df, height=360):
    st.markdown(f'<div class="panel"><div class="panel-title">{title}</div>', unsafe_allow_html=True)
    safe_dataframe(df, height=height)
    st.markdown("</div>", unsafe_allow_html=True)


def rank_panel(title, df, value_col, name_col="Tienda", color=PRICE_PINK, top=10):
    st.markdown(f'<div class="panel"><div class="panel-title">{title}</div>', unsafe_allow_html=True)
    if df is None or df.empty or value_col not in df.columns:
        st.info("Sin información.")
    else:
        show = df[[name_col, value_col]].copy() if name_col in df.columns else df[[value_col]].copy()
        if name_col not in show.columns:
            show[name_col] = show.index.astype(str)
        show = show.sort_values(value_col, ascending=False).head(top)
        maxv = float(show[value_col].max()) if len(show) else 1
        for _, row in show.iterrows():
            val = float(row[value_col]) if pd.notna(row[value_col]) else 0
            width = (val / maxv * 100) if maxv else 0
            st.markdown(
                f"""
                <div class="rank-row">
                    <div class="rank-name">{row[name_col]}</div>
                    <div class="rankbar"><div class="rankbar-fill" style="--w:{width}%;background:{color};"></div></div>
                    <div class="rank-value">{formato_numero(val)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    st.markdown("</div>", unsafe_allow_html=True)


def week_cards(sem_df):
    if sem_df is None or sem_df.empty:
        st.info("Sin información semanal.")
        return
    last = sem_df.tail(4).copy()
    html = '<div class="week-grid">'
    prev_ingresos = None

    for _, r in last.iterrows():
        semana = int(r.get("Semana ISO", 0)) if pd.notna(r.get("Semana ISO", 0)) else 0
        ingresos = float(r.get("Piezas Ingresadas", 0) or 0)
        hab = float(r.get("Acondicionado", 0) or 0)
        ubi = float(r.get("Ubicado", 0) or 0)
        rec = float(r.get("Recorridos", 0) or 0)

        if prev_ingresos is not None and prev_ingresos:
            d = ((ingresos - prev_ingresos) / prev_ingresos * 100)
            arrow = "▲" if d >= 0 else "▼"
            color = PRICE_GREEN if d >= 0 else PRICE_RED
            delta_ing = f'<span class="week-delta" style="color:{color};">{arrow} {abs(d):.1f}%</span>'
        else:
            delta_ing = '<span class="week-delta" style="color:#999;">—</span>'
        prev_ingresos = ingresos

        p_hab = (hab / ingresos * 100) if ingresos else 0
        p_ubi = (ubi / ingresos * 100) if ingresos else 0

        html += f"""
        <div class="week-card">
            <div class="week-head">Sem {semana}</div>
            <div class="week-line"><div class="week-label">Ingresos</div><div class="week-value">{formato_numero(ingresos)}</div>{delta_ing}</div>
            <div class="week-line"><div class="week-label">% Hab. / Ing.</div><div class="week-value">{p_hab:.1f}%</div><span></span></div>
            <div class="week-line"><div class="week-label">% Ubic. / Ing.</div><div class="week-value">{p_ubi:.1f}%</div><span></span></div>
            <div class="week-line"><div class="week-label">Recorridos</div><div class="week-value">{formato_numero(rec)}</div><span></span></div>
        </div>
        """
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def modulo_dia_anterior(resumen, detalle, op, tiendas):
    section_title("Día Anterior | Ingresos y Pendiente por Procesar", "Operación diaria con detalle por tienda y registros cargados.")
    kpi_grid(resumen)

    c1, c2 = st.columns([1.1, .9])
    with c1:
        panel_table("Detalle por tienda", detalle, height=360)
    with c2:
        st.markdown('<div class="panel"><div class="panel-title">Ingreso vs Habilitado vs Ubicado</div>', unsafe_allow_html=True)
        if detalle is not None and not detalle.empty:
            plot = detalle.head(12)
            fig = px.bar(plot, x="Tienda", y=["Total ingresos", "Acondicionado", "Ubicado"], barmode="group")
            fig.update_layout(height=360, margin=dict(l=10, r=10, t=10, b=70))
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("Sin información.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("### Detalle de registros subidos")
    tienda_det = st.selectbox("Filtrar tienda para detalle", ["Todas"] + tiendas, key="detalle_tienda_dia")
    reg = op.copy()
    if tienda_det != "Todas" and not reg.empty and "Tienda" in reg.columns:
        reg = reg[reg["Tienda"] == tienda_det]
    cols = [c for c in ["Fecha", "Tienda", "Nombre", "Actividad Realizada", "Número de Piezas", "Área", "Motivo de ingreso", "Ocurrencia"] if c in reg.columns]
    reg_show = reg[cols] if cols else reg
    safe_dataframe(reg_show, height=380)
    excel_download(reg_show, "detalle_registros_dia_anterior.xlsx", "Descargar detalle completo en Excel")


def modulo_semanal(resumen, sem_df):
    section_title("Reporte Semanal", "Indicadores por semana ISO")
    kpi_grid(resumen)
    week_cards(sem_df)

    c1, c2 = st.columns([.9, 1.1])
    with c1:
        panel_table("Resumen por semana", sem_df, height=380)
    with c2:
        st.markdown('<div class="panel"><div class="panel-title">Tendencia semanal</div>', unsafe_allow_html=True)
        if sem_df is not None and not sem_df.empty:
            plot = sem_df.tail(12)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=plot["Semana ISO"], y=plot["Piezas Ingresadas"], mode="lines+markers", name="Ingresos"))
            fig.add_trace(go.Scatter(x=plot["Semana ISO"], y=plot["Acondicionado"], mode="lines+markers", name="Habilitado"))
            fig.add_trace(go.Scatter(x=plot["Semana ISO"], y=plot["Ubicado"], mode="lines+markers", name="Ubicado"))
            fig.update_layout(height=380, margin=dict(l=10,r=10,t=10,b=10))
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("Sin información.")
        st.markdown("</div>", unsafe_allow_html=True)


def modulo_mensual(resumen, mes_df):
    section_title("Reporte Mensual", "Indicadores acumulados por mes")
    kpi_grid(resumen)
    c1, c2 = st.columns([.9, 1.1])
    with c1:
        panel_table("Resumen por mes", mes_df, height=400)
    with c2:
        st.markdown('<div class="panel"><div class="panel-title">Evolución mensual</div>', unsafe_allow_html=True)
        if mes_df is not None and not mes_df.empty:
            fig = px.bar(mes_df.tail(12), x="Mes", y=["Piezas Ingresadas", "Acondicionado", "Ubicado"], barmode="group")
            fig.update_layout(height=400, margin=dict(l=10,r=10,t=10,b=60))
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("Sin información.")
        st.markdown("</div>", unsafe_allow_html=True)


def modulo_conversion(conv_df, conv_kpis):
    section_title("Conversión Semanal Dev → Venta", "Sólo cuenta la venta ocurrida dentro de la misma semana ISO de la devolución.")
    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_card("Dev Pzs Semana", formato_numero(conv_kpis.get("Dev Pzs Semana",0)), "↩", PRICE_BLUE, "Piezas devueltas", 100)
    with c2: metric_card("Conv. Pzs", formato_numero(conv_kpis.get("Conversión Dev → Venta Pzs",0)), "🔄", PRICE_GREEN, "Vendidas misma semana", conv_kpis.get("% Conversión Semanal Dev → Venta",0))
    with c3: metric_card("Conv. $", formato_pesos(conv_kpis.get("Conversión Dev → Venta $",0)), "$", PRICE_PURPLE, "Importe recuperado", 100)
    with c4: metric_card("% Conversión", formato_porcentaje(conv_kpis.get("% Conversión Semanal Dev → Venta",0)), "%", PRICE_CYAN, "Dev → Venta", conv_kpis.get("% Conversión Semanal Dev → Venta",0))

    st.info("Regla: si una devolución ocurre en semana 25, sólo cuenta como conversión si la venta también ocurrió en semana 25. Si consultas mes o varias semanas, se calcula semana por semana y después se suma.")
    safe_dataframe(conv_df, height=430)
    excel_download(conv_df, "conversion_semanal_dev_venta.xlsx", "Descargar conversión completa")


def modulo_recuperacion(conv_df, conv_kpis):
    section_title("Recuperación Económica", "Importe recuperado y pendiente")
    c1, c2, c3 = st.columns(3)
    with c1: metric_card("Recuperación $", formato_pesos(conv_kpis.get("Conversión Dev → Venta $",0)), "$", PRICE_GREEN, "Venta recuperada", 100)
    with c2: metric_card("Venta No Convertida $", formato_pesos(conv_kpis.get("Venta No Convertida $",0)), "⏱", PRICE_ORANGE, "Pendiente", 100)
    with c3: metric_card("% Conversión", formato_porcentaje(conv_kpis.get("% Conversión Semanal Dev → Venta",0)), "%", PRICE_CYAN, "Piezas", conv_kpis.get("% Conversión Semanal Dev → Venta",0))
    safe_dataframe(conv_df, height=430)


def modulo_productividad(prod_df):
    section_title("Productividad", "Productividad por colaborador y actividad")
    c1, c2 = st.columns([.9, 1.1])
    with c1:
        panel_table("Productividad por colaborador", prod_df, height=430)
    with c2:
        st.markdown('<div class="panel"><div class="panel-title">Top colaboradores</div>', unsafe_allow_html=True)
        if prod_df is not None and not prod_df.empty:
            name_col = "Nombre" if "Nombre" in prod_df.columns else "Tienda"
            plot = prod_df.head(15).sort_values("Productividad")
            fig = px.bar(plot, x="Productividad", y=name_col, orientation="h", text="Productividad")
            fig.update_layout(height=430, margin=dict(l=10,r=20,t=10,b=10))
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("Sin información.")
        st.markdown("</div>", unsafe_allow_html=True)


def modulo_recorridos(op):
    section_title("Recorridos", "Meta vs real")
    rec = pd.DataFrame()
    if not op.empty and "Tienda" in op.columns:
        rec = op.groupby("Tienda", dropna=False).agg(Recorridos=("Recorridos","sum")).reset_index()
        rec["Meta"] = 47
        rec["% Cumplimiento"] = rec["Recorridos"] / rec["Meta"] * 100
    c1, c2 = st.columns([.85, 1.15])
    with c1:
        panel_table("Cumplimiento por tienda", rec, height=430)
    with c2:
        st.markdown('<div class="panel"><div class="panel-title">Recorridos por tienda</div>', unsafe_allow_html=True)
        if not rec.empty:
            fig = px.bar(rec.sort_values("Recorridos"), x="Recorridos", y="Tienda", orientation="h", text="Recorridos")
            fig.update_layout(height=430)
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("Sin información.")
        st.markdown("</div>", unsafe_allow_html=True)


def modulo_rankings(detalle, prod_df):
    section_title("Rankings", "Top y bottom tiendas / colaboradores")
    c1, c2 = st.columns(2)
    with c1:
        rank_panel("Top tiendas por ingresos", detalle, "Total ingresos", "Tienda", PRICE_BLUE, 12)
    with c2:
        rank_panel("Top colaboradores", prod_df, "Productividad", "Nombre" if "Nombre" in prod_df.columns else "Tienda", PRICE_GREEN, 12)
    st.markdown("### Detalle")
    safe_dataframe(detalle, height=300)


def modulo_macro(sem_df, mes_df):
    section_title("Macro", "Últimas 4 semanas y últimos 3 meses")
    st.markdown("### Últimas 4 semanas")
    week_cards(sem_df)
    st.markdown("### Últimos 3 meses")
    safe_dataframe(mes_df.tail(3) if mes_df is not None and not mes_df.empty else mes_df, height=260)


def modulo_diagnostico(excel_actual, op_all, co_all):
    section_title("Diagnóstico", "Validación de estructura y columnas")
    diag = pd.DataFrame({
        "Elemento": ["Hojas cargadas", "Registros operación", "Registros comercial", "Columnas operación", "Columnas comercial"],
        "Valor": [len(excel_actual.keys()), len(op_all), len(co_all), ", ".join(op_all.columns[:20]) if not op_all.empty else "Sin datos", ", ".join(co_all.columns[:20]) if not co_all.empty else "Sin datos"]
    })
    safe_dataframe(diag, height=300)
    with st.expander("Ver hojas detectadas"):
        st.write(list(excel_actual.keys()))


def modulo_configuracion(is_admin, tiendas):
    section_title("Configuración", "Metas, tiendas del proyecto y parámetros")
    if not is_admin:
        st.warning("Sólo administrador puede modificar configuración.")
        return
    c1, c2, c3 = st.columns(3)
    with c1: st.number_input("Meta Productividad Diaria", min_value=0, value=784)
    with c2: st.number_input("Meta Recorridos Semanal", min_value=0, value=47)
    with c3: st.number_input("Meta Conversión %", min_value=0.0, value=90.0)
    st.multiselect("Tiendas del proyecto", tiendas, default=tiendas)
    st.success("Configuración lista para persistencia.")


def modulo_usuarios(is_admin):
    section_title("Usuarios", "Asignación de accesos para ingresar como Consulta o Administrador")
    if not is_admin:
        st.warning("Sólo administrador puede crear usuarios.")
        return

    st.markdown('<div class="admin-box">', unsafe_allow_html=True)
    st.markdown("### Crear usuario")
    with st.form("crear_usuario_form"):
        c1, c2, c3, c4 = st.columns(4)
        with c1: nomina = st.text_input("Nómina")
        with c2: nombre = st.text_input("Nombre")
        with c3: permiso = st.selectbox("Tipo de permiso", ["Consulta", "Administrador"])
        with c4: password = st.text_input("Contraseña", type="password")
        guardar = st.form_submit_button("Crear usuario")
        if guardar:
            st.success(f"Usuario {nombre or nomina} preparado. Este acceso servirá para entrar a la plataforma con permiso {permiso}.")
    st.markdown("</div>", unsafe_allow_html=True)

    usuarios_demo = pd.DataFrame([
        {"Nómina": "admin", "Nombre": "Administrador", "Permiso": "Administrador", "Activo": "Sí"},
    ])
    safe_dataframe(usuarios_demo, height=220)


# ============================================================
# APP
# ============================================================

aplicar_estilos()
rol, is_admin = sidebar_access()
source_sidebar(is_admin)
sidebar_menu()
sidebar_footer()

render_topbar(is_admin=is_admin)
modulo = top_navigation()

excel_actual = cargar_excel_actual()
if excel_actual is None:
    st.warning("Carga un archivo Excel para iniciar la plataforma.")
    st.stop()

with st.spinner("Normalizando información..."):
    op_all, co_all = detectar_y_normalizar_hojas(excel_actual)

tiendas = sorted(set(
    (op_all["Tienda"].dropna().astype(str).tolist() if not op_all.empty and "Tienda" in op_all.columns else [])
    + (co_all["Tienda"].dropna().astype(str).tolist() if not co_all.empty and "Tienda" in co_all.columns else [])
))

f_tienda, periodo, vista = render_filters(tiendas)

op_base, co_base = op_all.copy(), co_all.copy()
if f_tienda:
    if not op_base.empty and "Tienda" in op_base.columns:
        op_base = op_base[op_base["Tienda"].isin(f_tienda)]
    if not co_base.empty and "Tienda" in co_base.columns:
        co_base = co_base[co_base["Tienda"].isin(f_tienda)]

op, co = filtrar_periodo(op_base, co_base, periodo)

resumen = resumen_ejecutivo(op, co)
detalle = resumen_por_tienda(op, co)
sem_df = resumen_por_semana(op_base, co_base)
mes_df = resumen_por_mes(op_base, co_base)
prod_df = productividad_colaborador(op)
conv_df, conv_kpis = conversion_semanal(co)

if modulo == "🏠 Dashboard Ejecutivo":
    modulo_dashboard(resumen, detalle, sem_df, prod_df)
elif modulo == "📅 Día Anterior":
    modulo_dia_anterior(resumen, detalle, op, tiendas)
elif modulo == "📈 Reporte Semanal":
    modulo_semanal(resumen, sem_df)
elif modulo == "📆 Reporte Mensual":
    modulo_mensual(resumen, mes_df)
elif modulo == "🔄 Conversión":
    modulo_conversion(conv_df, conv_kpis)
elif modulo == "💲 Recuperación Económica":
    modulo_recuperacion(conv_df, conv_kpis)
elif modulo == "👥 Productividad":
    modulo_productividad(prod_df)
elif modulo == "🚶 Recorridos":
    modulo_recorridos(op)
elif modulo == "🏆 Rankings":
    modulo_rankings(detalle, prod_df)
elif modulo == "📊 Macro":
    modulo_macro(sem_df, mes_df)
elif modulo == "🩺 Diagnóstico":
    modulo_diagnostico(excel_actual, op_all, co_all)
elif modulo == "⚙️ Configuración":
    modulo_configuracion(is_admin, tiendas)
elif modulo == "👤 Usuarios":
    modulo_usuarios(is_admin)

st.markdown("---")
st.caption("CONFIDENCIAL | Price Shoes | Operaciones Ropa")
