# Indicadores Cambios y Muertos v8.5 Datos/UI estable

Correcciones:
- Diseño más ligero en letras y números, azul ajustado al ejemplo.
- Pestañas azul marino: texto blanco tenue y blanco intenso al seleccionar; se ocultan radios.
- Fecha del encabezado con zona horaria CDMX.
- Corrección principal de datos: normaliza tiendas por mayúsculas, acentos y variantes.
- Por Día/Semanal/Mensual ahora agrupan por tienda canonizada y ya no deben quedar en cero por diferencia de texto.
- Si una fecha no existe en el Excel, se muestra aviso con fechas disponibles.
- Hoja Resultados de productividad se fuerza como operación.
- Hoja Plantilla se detecta como plantilla y no ensucia diagnóstico operativo/comercial.

Subir sólo:
- app.py
- requirements.txt
- assets/ si usas logo
