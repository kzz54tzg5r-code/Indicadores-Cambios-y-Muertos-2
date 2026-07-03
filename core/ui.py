
from __future__ import annotations
from pathlib import Path
from datetime import datetime
import base64
import io
import pandas as pd
import streamlit as st
import plotly.express as px

from .styles import PRICE_BLUE, PRICE_BLUE_2, PRICE_PINK, PRICE_DARK, PRICE_GREEN, PRICE_ORANGE, PRICE_PURPLE, PRICE_CYAN, PRICE_RED, PRICE_GRAY
from .utils import fmt_num, fmt_pct, fmt_money


MAX_PREVIEW_ROWS = 500


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
    st.markdown(
        f"""
        <div class="top-header">
            <div>{logo_html()}</div>
            <div class="header-title">
                <div class="small">Operaciones Ropa</div>
                <div class="big">Indicadores Cambios y Muertos</div>
                <div class="sub">Recuperación · Productividad · Conversión</div>
            </div>
            <div class="header-controls">
                <div class="header-card">
                    <label>Fecha</label>
                    <div>📅 {now.strftime("%d/%m/%Y")}</div>
                </div>
                <div class="header-card">
                    <label>Usuario</label>
                    <div>{'👑' if user['is_admin'] else '👤'} {user['role']}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def nav_bar():
    items = [
        "Resumen",
        "Día Anterior",
        "Reporte Semanal",
        "Reporte Mensual",
        "Conversión",
        "Recuperación Económica",
        "Productividad",
        "Recorridos",
        "Ranking",
        "Macro",
        "Criterios",
        "Configuración",
        "Usuarios",
    ]

    if "page" not in st.session_state:
        st.session_state["page"] = "Resumen"

    current = st.session_state.get("page", "Resumen")
    if current not in items:
        current = "Resumen"

    try:
        selected = st.segmented_control(
            "Navegación",
            options=items,
            default=current,
            label_visibility="collapsed",
            key="page_selector",
        )
    except Exception:
        selected = st.radio(
            "Navegación",
            options=items,
            index=items.index(current),
            horizontal=True,
            label_visibility="collapsed",
            key="page_selector_radio",
        )

    st.session_state["page"] = selected or current

    st.markdown(
        """
        <style>
        div[data-testid="stSegmentedControl"] {
            background:#1D2E6E;
            border-top:4px solid #EC007C;
            padding:0;
            margin:0 -1.6rem 22px -1.6rem;
            overflow-x:auto;
            white-space:nowrap;
            display:block;
            box-shadow:0 10px 22px rgba(29,46,110,.18);
        }
        div[data-testid="stSegmentedControl"] button {
            border-radius:0 !important;
            border:none !important;
            background:#1D2E6E !important;
            color:#DDE8FF !important;
            padding:15px 23px !important;
            font-weight:900 !important;
            font-size:15px !important;
            border-bottom:4px solid transparent !important;
            white-space:nowrap !important;
        }
        div[data-testid="stSegmentedControl"] button[aria-pressed="true"] {
            color:white !important;
            background:#233B86 !important;
            border-bottom-color:#EC007C !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    return st.session_state["page"]


def section(title, subtitle=""):
    st.markdown(f'<div class="section-title">{title}</div><div class="section-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def pct_clip(v):
    try:
        return max(0, min(100, float(v)))
    except Exception:
        return 0


def kpi_card(label, value, icon, color, note="", pct=0, delta=""):
    st.markdown(
        f"""
        <div class="kpi-card" style="--accent:{color};--soft:{color}18;--shadow:{color}38;">
            <div class="kpi-top">
                <div class="kpi-icon">{icon}</div>
                <div class="kpi-label">{label}</div>
            </div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-note">{note}</div>
            <div class="progress"><div style="--pct:{pct_clip(pct)}%;"></div></div>
            {f'<div class="delta">{delta}</div>' if delta else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpis(resumen):
    st.markdown('<div class="kpi-grid">', unsafe_allow_html=True)
    kpi_card("Piezas Ingresadas", fmt_num(resumen.get("Ingresos", 0)), "↻", PRICE_PINK, "Dev + muertos + cajas + probador", 100)
    kpi_card("Piezas Acondicionadas", fmt_num(resumen.get("Acondicionado", 0)), "✓", PRICE_BLUE, fmt_pct(resumen.get("% Acondicionado", 0)) + " vs ingresos", resumen.get("% Acondicionado", 0))
    kpi_card("Piezas Ubicadas", fmt_num(resumen.get("Ubicado", 0)), "⌖", PRICE_ORANGE, fmt_pct(resumen.get("% Ubicado", 0)) + " vs ingresos", resumen.get("% Ubicado", 0))
    kpi_card("Pendientes por Ubicar", fmt_num(resumen.get("Pendiente", 0)), "⌛", PRICE_GREEN, "Ingreso - ubicado", 100-resumen.get("% Ubicado", 0))
    kpi_card("% Procesado", fmt_pct(resumen.get("% Ubicado", 0)), "%", PRICE_PURPLE, "Ubicado / ingresadas", resumen.get("% Ubicado", 0))
    st.markdown('</div>', unsafe_allow_html=True)


def hero(resumen, tiendas_count=0):
    st.markdown(
        f"""
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
        """,
        unsafe_allow_html=True,
    )


def safe_df(df: pd.DataFrame, height=360, editable=False):
    if df is None or df.empty:
        st.info("Sin información con los filtros seleccionados.")
        return df
    view = df.head(MAX_PREVIEW_ROWS)
    if editable:
        edited = st.data_editor(view, width="stretch", hide_index=True, height=height, num_rows="dynamic")
        return edited
    st.dataframe(view, width="stretch", hide_index=True, height=height)
    if len(df) > MAX_PREVIEW_ROWS:
        st.caption(f"Vista previa de {MAX_PREVIEW_ROWS:,} filas de {len(df):,}. Descarga Excel para ver todo.")
    return df


def panel(title, df=None, height=360, editable=False):
    st.markdown(f'<div class="panel"><div class="panel-title">{title}</div>', unsafe_allow_html=True)
    out = None
    if df is not None:
        out = safe_df(df, height=height, editable=editable)
    st.markdown("</div>", unsafe_allow_html=True)
    return out


def excel_button(df: pd.DataFrame, filename: str, label="Descargar Excel"):
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
            st.markdown(
                f"""
                <div class="rank-row">
                    <div class="rank-name">{row[name_col]}</div>
                    <div class="rankbar"><div class="rankbar-fill" style="--accent:{color};--w:{w}%;"></div></div>
                    <div class="rank-value">{fmt_num(val)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    st.markdown("</div>", unsafe_allow_html=True)


def plot_bar(df, x, y, title="", orientation=None):
    if df is None or df.empty:
        st.info("Sin información.")
        return
    fig = px.bar(df, x=x, y=y, title=title, orientation=orientation)
    fig.update_layout(height=390, margin=dict(l=10, r=10, t=40, b=70))
    st.plotly_chart(fig, width="stretch")
