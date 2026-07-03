# Indicadores Cambios y Muertos v8.3

Correcciones de ingeniería:
- Base tomada del diseño v6/interfaz ejecutiva pero estable en un solo app.py.
- Pestañas superiores azules con estructura completa.
- Usuario muestra el nombre con el que inició sesión.
- Filtros dinámicos por pestaña:
  - Dashboard/Día anterior: tienda + periodo.
  - Semanal/Conversión/Recuperación/Recorridos: tienda + Semana ISO.
  - Mensual/Macro: tienda + mes.
  - Productividad/Rankings: tienda + colaborador.
- Hoja Plantilla: homologa nombres de productividad.
  Ejemplo: Elo -> Eloisa si viene en Plantilla.
- Conversión y recuperación respetan Semana ISO:
  Agrupa por Semana ISO + Tienda + ID/Modelo + Color.
  No mezcla semanas aunque consultes mes completo.
- Corrige renderizado donde se veía HTML en pantalla.

Subir a GitHub:
- app.py
- requirements.txt
- assets/ si usas logo
Borra carpetas/archivos viejos para evitar mezclas.
