
from __future__ import annotations
import streamlit as st
from .storage import load_users, init_db


def render_login_screen():
    st.markdown(
        """
        <style>
        .login-wrap {
            min-height: 72vh;
            display:flex;
            align-items:center;
            justify-content:center;
        }
        .login-card {
            width: min(680px, 92vw);
            background:white;
            border:1px solid #DDE3EE;
            border-radius:26px;
            padding:34px;
            box-shadow:0 18px 45px rgba(17,24,39,.10);
        }
        .login-title {
            color:#1D2E6E;
            font-size:34px;
            font-weight:950;
            line-height:1.05;
            margin-bottom:8px;
        }
        .login-sub {
            color:#6B7280;
            font-size:16px;
            font-weight:600;
            margin-bottom:20px;
        }
        .login-alert {
            background:#EEF5FF;
            border:1px solid #DBEAFE;
            color:#1D2E6E;
            border-radius:16px;
            padding:16px;
            font-weight:750;
            margin-bottom:18px;
        }
        </style>
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
        """,
        unsafe_allow_html=True,
    )


def render_access():
    init_db()
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

    st.sidebar.info("Para visualizar, inicia sesión.")
    nomina = st.sidebar.text_input("Nómina / Usuario")
    password = st.sidebar.text_input("Contraseña", type="password")

    if st.sidebar.button("Iniciar sesión", type="primary", use_container_width=True):
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
