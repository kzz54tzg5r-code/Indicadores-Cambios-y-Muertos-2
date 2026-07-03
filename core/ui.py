from __future__ import annotations

from pathlib import Path
import streamlit as st
from config.colors import PRICE_PINK, PRICE_PURPLE, PRICE_DARK
from core.utils import formato_numero, formato_porcentaje

def aplicar_estilos():
    st.markdown(f"""
    <style>
    .block-container{{padding-top:2rem; max-width:1500px;}}
    .orion-title{{font-size:48px;line-height:.95;font-weight:900;color:{PRICE_DARK};margin:0;}}
    .orion-subtitle{{font-size:22px;color:#707789;font-weight:700;margin-top:8px;}}
    .orion-bar{{background:{PRICE_PINK};color:white;font-size:28px;font-weight:900;padding:12px 24px;margin:18px 0 26px 0;}}
    .kpi-card{{border:1px solid #E2E5EE;border-radius:14px;padding:20px;background:white;box-shadow:0 1px 6px rgba(0,0,0,.05);min-height:125px;}}
    .kpi-label{{font-weight:800;color:{PRICE_DARK};font-size:14px;}}
    .kpi-value{{font-size:32px;font-weight:900;color:{PRICE_PURPLE};margin-top:10px;}}
    </style>
    """, unsafe_allow_html=True)

def render_header():
    c1, c2, c3 = st.columns([1, 4, 5])
    with c1:
        for logo_name in ["assets/logo_price.png", "assets/logo.png"]:
            logo = Path(logo_name)
            if logo.exists():
                st.image(str(logo), width=125)
                break
    with c2:
        st.markdown('<h1 class="orion-title">Recuperación<br>Cambios y Muertos</h1>', unsafe_allow_html=True)
        st.markdown('<div class="orion-subtitle">Matriz de Operaciones</div>', unsafe_allow_html=True)
    with c3:
        st.markdown("<br><br><h3 style='color:#EC007C;'>Operaciones Ropa | Price Shoes</h3>", unsafe_allow_html=True)
    st.markdown('<div class="orion-bar">ORION Operaciones Ropa</div>', unsafe_allow_html=True)

def kpi_card(label: str, value: str, note: str = ""):
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div>{note}</div>
    </div>
    """, unsafe_allow_html=True)

def render_kpis(resumen: dict):
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: kpi_card("Piezas Ingresadas", formato_numero(resumen.get("Piezas Ingresadas", 0)))
    with c2: kpi_card("Acondicionado", formato_numero(resumen.get("Acondicionado", 0)))
    with c3: kpi_card("Ubicado", formato_numero(resumen.get("Ubicado", 0)))
    with c4: kpi_card("Pendiente Ubicar", formato_numero(resumen.get("Pendiente Ubicar", 0)))
    with c5: kpi_card("% Ubicado", formato_porcentaje(resumen.get("% Ubicado", 0)))
