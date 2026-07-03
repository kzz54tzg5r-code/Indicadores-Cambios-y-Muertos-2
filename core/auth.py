from __future__ import annotations

import streamlit as st
from config.settings import ADMIN_PASSWORD_DEFAULT

def obtener_rol_sidebar() -> tuple[str, bool]:
    st.sidebar.header("🔐 Acceso")
    rol = st.sidebar.radio("Rol", ["Consulta", "Administrador"], horizontal=True)
    is_admin = False
    if rol == "Administrador":
        clave = st.sidebar.text_input("Clave administrador", type="password")
        password = st.secrets.get("ADMIN_PASSWORD", ADMIN_PASSWORD_DEFAULT)
        is_admin = clave == password
        if is_admin:
            st.sidebar.success("Administrador activo")
        elif clave:
            st.sidebar.warning("Clave incorrecta")
    else:
        st.sidebar.info("Modo consulta activo")
    return rol, is_admin
