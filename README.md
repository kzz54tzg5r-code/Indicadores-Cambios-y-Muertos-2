# v8.6.8 Fix navegación única

Corrección definitiva:
- Elimina llamadas duplicadas a nav_bar().
- Sustituye st.radio por st.pills, y fallback a selectbox.
- Usa una sola key de navegación.
- El reporte se carga automáticamente al seleccionar pestaña.
