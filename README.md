# v8.7 Fix columna Tienda real

El Excel trae dos columnas llamadas Tienda:
- La primera realmente es el folio/Occurrence numérico.
- La segunda es la tienda real.

Esta versión:
- Busca todas las columnas Tienda/Tienda.1.
- Elige la que contiene nombres reales de tiendas.
- Descarta filas donde Tienda sea numérica.
- En Diagnóstico muestra las columnas candidatas y la columna seleccionada.
