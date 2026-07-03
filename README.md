# Indicadores Cambios y Muertos v8

Cambios principales:
- Login profesional sin mostrar credenciales por defecto.
- Leyenda de acceso: "Para visualizar, inicia sesión con un usuario autorizado".
- Usuarios y metas guardados en SQLite.
- El Excel se normaliza una sola vez por versión de archivo usando `st.cache_data`.
- Al cambiar de pestaña ya no debe quedarse en "Normalizando archivo...".
- Administrador puede crear, editar, eliminar usuarios y cambiar contraseñas.
- Sólo usuarios existentes pueden visualizar la información.

Nota: usuario inicial de arranque técnico: `admin` / `admin123`. Se recomienda entrar como administrador y crear usuarios reales.
