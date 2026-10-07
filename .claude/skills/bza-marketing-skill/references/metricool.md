# Metricool: lectura de métricas y programación

Leer este archivo antes de llamar cualquier herramienta de Metricool.

## Conexión

- Conector oficial **Metricool Social Management** en claude.ai → Configuración → Conectores. Funciona con cualquier plan de Metricool; los límites del plan siguen aplicando (historial disponible, número de marcas, anuncios).
- En una Routine de Claude Code, el conector debe estar conectado en claude.ai **y** concedido a la Routine; si no aparece ninguna herramienta de Metricool en la sesión, no inventar datos: generar el reporte con lo que haya en los CSV y anotarlo en “Datos faltantes”.

## Herramientas

Los nombres cambian entre versiones del conector. **Primero listar las herramientas disponibles y leer su esquema**; usar los nombres reales. Las conocidas al 6 de octubre de 2026:

| Herramienta | Uso en este skill |
|---|---|
| `getBrandSettings` | Obtener el `blogId` de la marca “BZA Creative”, redes conectadas y zona horaria. |
| `getAnalyticsAvailableMetrics` | Ver qué métricas existen por red antes de pedirlas. |
| `getAnalyticsDataByMetrics` | Traer métricas de Facebook, Instagram y, si están conectados, anuncios, por rango de fechas. |
| `getBestTimeToPostByNetwork` | Revisar una vez al mes si 10:00 y 18:00 siguen siendo las mejores ventanas. |
| `getScheduledPosts` | Ver qué está programado en los próximos 21 días. |
| `createScheduledPost` | Programar una publicación del bloque aprobado. |
| `updateScheduledPost` | Corregir texto, fecha o medios de una publicación ya programada. |
| Herramientas de campañas (`…facebookads…`, `…googleads…`) | Inversión, impresiones, clics y resultados de Meta Ads y Google Ads cuando están conectados a Metricool. |

## Extracción semanal → `marketing/datos/`

1. `getBrandSettings` → `blogId`.
2. Para cada red (`facebook`, `instagram`) pedir el rango lunes 00:00 a domingo 23:59 de las **últimas 6 semanas**. Reconstruir esas filas cada vez: Metricool es la fuente de verdad y el CSV es una copia.
3. Escribir una fila por `semana_inicio` + `canal` en `metricas-semanales.csv`. **Reemplazar** la fila si ya existe; nunca duplicar.

| Columna | Facebook (página) | Instagram (cuenta) |
|---|---|---|
| `alcance` | alcance de la página / publicaciones | cuentas alcanzadas |
| `impresiones` | impresiones | impresiones o visualizaciones |
| `interacciones` | reacciones + comentarios + compartidos | me gusta + comentarios + guardados + compartidos |
| `guardados` | — (dejar 0) | guardados |
| `compartidos` | compartidos | compartidos |
| `visitas_perfil` | vistas de página | visitas al perfil |
| `seguidores_nuevos` | nuevos seguidores netos | nuevos seguidores netos |
| `clics` | clics en enlaces | toques en el enlace del perfil |
| `mensajes` | conversaciones nuevas (si existe la métrica) | conversaciones nuevas (si existe la métrica) |

Los nombres exactos de métricas salen de `getAnalyticsAvailableMetrics`. Si una métrica no existe, dejar 0 y anotarlo en “Datos faltantes” del reporte, nunca estimarla.

4. **Por publicación** (`publicaciones.csv`): una fila por publicación y red con alcance, interacciones, guardados, compartidos y clics. `tema` y `palabra_clave` se obtienen comparando fecha y texto con el bloque de contenido (`marketing/calendario/*.json`) o con `docs/calendario-feed-inicial.md`.
5. `mensajes_palabra_clave`: Metricool no lee el contenido de los mensajes directos. Contar las filas de `conversaciones.csv` con esa palabra clave en los 7 días posteriores a la publicación.
6. **Anuncios**: si hay campañas, escribir filas `google_ads` y `meta_ads` con `tipo=pagado`, `inversion_mxn`, `impresiones`, `clics` y `clics_whatsapp` (conversión `whatsapp_click`).
7. `prospeccion` (contactos personalizados enviados y respuestas) y `conversaciones.csv` los captura el responsable de la cuenta o se agregan cuando los dicta en la conversación; no vienen de Metricool.

## Programación

1. `getScheduledPosts` para los próximos 21 días. Si hay menos de 3 publicaciones por semana, falta contenido.
2. Generar las cargas: `python3 scripts/calendario.py metricool marketing/calendario/<bloque>.json --salida /tmp/cargas.json`. Solo se generan si el bloque es válido.
3. Ajustar cada carga al esquema real de `createScheduledPost` (fecha ISO con zona `America/Mexico_City`, `providers` con cada red, `media` con URLs públicas, texto).
4. **Aprobación:** con `aprobacion_requerida: true` en la configuración, mostrar la lista (fecha, tema, palabra, pieza) y esperar un “sí” explícito antes de crear publicaciones. En una Routine sin persona presente, no programar: dejar la propuesta en el reporte.
5. Después de crear, volver a llamar `getScheduledPosts` y confirmar fecha, redes y medios de cada una.
6. Nunca borrar ni reemplazar publicaciones existentes sin aprobación.

## Medios públicos

`createScheduledPost` necesita URLs accesibles. Las piezas viven en `dist/assets/...` y se publican en `https://www.bzacreative.com/assets/...` **solo después de que el cambio llegue a `main` y Cloudflare despliegue**. Antes de programar, comprobar que la URL responde; si no, subir la pieza manualmente en Metricool.
