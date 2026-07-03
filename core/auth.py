
from __future__ import annotations
import streamlit as st
from .storage import load_users


def render_access():
    st.sidebar.markdown("## 🔐 Acceso")
    role_choice = st.sidebar.radio("Rol", ["Consulta", "Administrador"], horizontal=True)

    is_admin = False
    user_name = "Consulta"
    user_nomina = ""

    if role_choice == "Administrador":
        password = st.sidebar.text_input("Contraseña administrador", type="password")
        users = load_users()
        admin_users = [u for u in users if u.get("permiso") == "Administrador" and u.get("activo", True)]
        for u in admin_users:
            if password and password == str(u.get("password", "")):
                is_admin = True
                user_name = u.get("nombre") or u.get("nomina") or "Administrador"
                user_nomina = u.get("nomina", "")
                break
        if is_admin:
            st.sidebar.success("Administrador activo")
        else:
            st.sidebar.info("Ingresa contraseña de administrador")
    else:
        st.sidebar.success("Consulta activa")

    return {"role": "Administrador" if is_admin else "Consulta", "is_admin": is_admin, "name": user_name, "nomina": user_nomina}
