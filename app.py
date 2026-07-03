
from __future__ import annotations
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from core.styles import apply_styles, PRICE_BLUE, PRICE_PINK, PRICE_GREEN, PRICE_ORANGE, PRICE_PURPLE, PRICE_CYAN
from core.auth import render_access
from core.storage import (
    save_uploaded_file, active_file_exists, get_active_file_path,
    delete_active_file, get_metadata, load_users, save_users,
    load_goals, save_goals
)
from core.data import (
    load_normalized, filter_period, resumen_ejecutivo, resumen_tienda,
    resumen_semana, resumen_mes, productividad, conversion
)
from core.ui import (
    header, nav_bar, section, kpis, hero, panel, safe_df,
    excel_button, week_cards, rank_panel
)
from core.utils import fmt_num, fmt_pct, fmt_money

st.set_page_config(page_title="Indicadores Cambios y Muertos", page_icon="📊", layout="wide", initial_sidebar_state="expanded")
apply_styles()

user = render_access()

if not user.get("authenticated"):
    st.warning("Debes ingresar con un usuario autorizado para ver la información.")
    st.info("Usuario inicial: admin / Contraseña inicial: admin123")
    st.stop()

st.sidebar.divider()
st.sidebar.markdown("## 📁 Fuente de datos")
meta = get_metadata()
if active_file_exists():
    st.sidebar.success("Archivo cargado")
    st.sidebar.write(meta.get("nombre_original", "Archivo activo"))
    st.sidebar.caption(meta.get("fecha_carga", ""))
else:
    st.sidebar.warning("No hay archivo cargado")

if user["is_admin"]:
    up = st.sidebar.file_uploader("Cargar/Reemplazar Excel", type=["xlsx"])
    if up is not None and st.sidebar.button("Procesar archivo", type="primary"):
        save_uploaded_file(up)
        st.sidebar.success("Archivo guardado")
        st.rerun()

    if active_file_exists() and st.sidebar.button("Borrar archivo persistido"):
        delete_active_file()
        st.sidebar.success("Archivo eliminado")
        st.rerun()

st.sidebar.markdown(
    """
    <div style="background:#EEF5FF;border-radius:14px;padding:14px;margin-top:24px;color:#1D2E6E;font-weight:900;">
        🛡️ CONFIDENCIAL<br>
        <span style="font-weight:500;color:#6B7280;">Price Shoes | Operaciones Ropa</span>
    </div>
    """,
    unsafe_allow_html=True
)

header(user)
page = nav_bar()

if not active_file_exists():
    st.warning("Carga un archivo Excel desde el panel lateral para iniciar.")
    st.stop()

@st.cache_data(show_spinner=False)
def cached_load(path_str):
    return load_normalized(get_active_file_path())

with st.spinner("Normalizando archivo..."):
    op_all, co_all, diag_df, sheets = load_normalized(get_active_file_path())

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

op_base = op_all.copy()
co_base = co_all.copy()
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


def dashboard():
    hero(resumen, len(detalle) if detalle is not None else 0)
    kpis(resumen)
    section("Últimas 4 semanas", "Ingresos vs semana anterior, % habilitado e % ubicado sobre ingresos.")
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
        panel("Detalle por tienda", detalle, height=390, editable=user["is_admin"])
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
    safe_df(show, height=360, editable=user["is_admin"])
    excel_button(show, "detalle_registros_dia_anterior.xlsx", "Descargar detalle completo")


def reporte_semanal():
    section("Reporte Semanal", "Indicadores por Semana ISO.")
    kpis(resumen)
    week_cards(sem_df)
    a, b = st.columns([.9, 1.1])
    with a:
        panel("Resumen por semana", sem_df, height=410, editable=user["is_admin"])
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
        panel("Resumen por mes", mes_df, height=420, editable=user["is_admin"])
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
    from core.ui import kpi_card
    kpi_card("Dev Pzs Semana", fmt_num(conv_kpis.get("Dev Pzs", 0)), "↩", PRICE_BLUE, "Devolución", 100)
    kpi_card("Conversión Pzs", fmt_num(conv_kpis.get("Conversión Pzs", 0)), "🔄", PRICE_GREEN, "Misma semana", conv_kpis.get("% Conversión", 0))
    kpi_card("Conversión $", fmt_money(conv_kpis.get("Conversión $", 0)), "$", PRICE_PURPLE, "Venta recuperada", 100)
    kpi_card("% Conversión", fmt_pct(conv_kpis.get("% Conversión", 0)), "%", PRICE_CYAN, "Dev → Venta", conv_kpis.get("% Conversión", 0))
    kpi_card("Pendiente Pzs", fmt_num(conv_kpis.get("Pendiente Pzs", 0)), "⏱", PRICE_ORANGE, "Por convertir", 100-conv_kpis.get("% Conversión", 0))
    st.markdown('</div>', unsafe_allow_html=True)
    panel("Detalle de conversión", conv_df, height=430, editable=user["is_admin"])
    excel_button(conv_df, "conversion_semanal_dev_venta.xlsx")


def recuperacion():
    section("Recuperación Económica", "Importe recuperado y pendiente.")
    st.markdown('<div class="kpi-grid">', unsafe_allow_html=True)
    from core.ui import kpi_card
    kpi_card("Recuperación $", fmt_money(conv_kpis.get("Conversión $", 0)), "$", PRICE_GREEN, "Venta recuperada", 100)
    kpi_card("No Convertido $", fmt_money(conv_kpis.get("No Convertido $", 0)), "⏱", PRICE_ORANGE, "Pendiente", 100)
    kpi_card("% Conversión", fmt_pct(conv_kpis.get("% Conversión", 0)), "%", PRICE_CYAN, "Piezas", conv_kpis.get("% Conversión", 0))
    st.markdown('</div>', unsafe_allow_html=True)
    panel("Detalle económico", conv_df, height=430, editable=user["is_admin"])


def productividad_page():
    section("Productividad", "Productividad por colaborador.")
    a, b = st.columns([.9, 1.1])
    with a:
        panel("Productividad por colaborador", prod_df, height=430, editable=user["is_admin"])
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
        panel("Cumplimiento por tienda", rec, height=430, editable=user["is_admin"])
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
    panel("Detalle ranking tiendas", detalle, height=320, editable=user["is_admin"])


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


def configuracion_page():
    section("Configuración", "Metas, tiendas y parámetros.")
    if not user["is_admin"]:
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
    if not user["is_admin"]:
        st.warning("Sólo administrador puede crear, editar o eliminar usuarios.")
        return

    users = load_users()

    st.markdown('<div class="user-card">', unsafe_allow_html=True)
    st.markdown("### Crear nuevo usuario")
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
                users.append({
                    "nomina": str(nomina).strip(),
                    "nombre": str(nombre).strip(),
                    "permiso": permiso,
                    "password": str(password),
                    "activo": bool(activo),
                })
                save_users(users)
                st.success("Usuario creado. Ya podrá ingresar con su nómina/usuario y contraseña.")
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("### Usuarios existentes")
    if not users:
        st.info("No hay usuarios.")
        return

    users_df = pd.DataFrame([
        {
            "nomina": u.get("nomina", ""),
            "nombre": u.get("nombre", ""),
            "permiso": u.get("permiso", "Consulta"),
            "activo": bool(u.get("activo", True)),
        }
        for u in users
    ])

    edited = st.data_editor(
        users_df,
        width="stretch",
        hide_index=True,
        height=300,
        num_rows="fixed",
        column_config={
            "permiso": st.column_config.SelectboxColumn("permiso", options=["Consulta", "Administrador"]),
            "activo": st.column_config.CheckboxColumn("activo"),
        },
    )

    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("Guardar cambios", type="primary"):
            old = {str(u.get("nomina", "")): u for u in users}
            new_users = []
            for _, r in edited.iterrows():
                nom = str(r.get("nomina", "")).strip()
                if not nom:
                    continue
                prev = old.get(nom, {})
                new_users.append({
                    "nomina": nom,
                    "nombre": str(r.get("nombre", "")).strip(),
                    "permiso": str(r.get("permiso", "Consulta")),
                    "password": prev.get("password", ""),
                    "activo": bool(r.get("activo", True)),
                })
            save_users(new_users)
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
                users = [u for u in users if u.get("nomina", "") != eliminar]
                save_users(users)
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
                for u in users:
                    if u.get("nomina", "") == usr:
                        u["password"] = new_pass
                save_users(users)
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
