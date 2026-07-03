
from __future__ import annotations
import streamlit as st
from .storage import load_users


def render_access():
    st.sidebar.markdown("## 🔐 Acceso")

    if st.session_state.get("auth_user"):
        user = st.session_state["auth_user"]
        st.sidebar.success(f"Sesión activa: {user.get('nombre') or user.get('nomina')}")
        st.sidebar.caption(f"Permiso: {user.get('permiso')}")
        if st.sidebar.button("Cerrar sesión"):
            st.session_state.pop("auth_user", None)
            st.rerun()

        return {
            "role": user.get("permiso", "Consulta"),
            "is_admin": user.get("permiso") == "Administrador",
            "name": user.get("nombre") or user.get("nomina"),
            "nomina": user.get("nomina", ""),
            "authenticated": True,
        }

    st.sidebar.info("Ingresa con usuario autorizado.")
    nomina = st.sidebar.text_input("Nómina / Usuario")
    password = st.sidebar.text_input("Contraseña", type="password")

    if st.sidebar.button("Entrar", type="primary", use_container_width=True):
        for u in load_users():
            if not u.get("activo", True):
                continue
            if str(u.get("nomina", "")).strip() == str(nomina).strip() and str(u.get("password", "")) == str(password):
                st.session_state["auth_user"] = dict(u)
                st.rerun()
        st.sidebar.error("Usuario o contraseña incorrectos.")

    return {
        "role": "Sin acceso",
        "is_admin": False,
        "name": "",
        "nomina": "",
        "authenticated": False,
    }
