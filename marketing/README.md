# Operación de marketing con el agente de IA

El agente de marketing es el skill `/bza-marketing-skill` (en `.claude/skills/bza-marketing-skill/`) y el subagente `bza-marketing` (en `.claude/agents/`). Cada semana:

1. Lee las métricas de Facebook e Instagram en Metricool, y las de Google Ads y Meta Ads cuando existan.
2. Calcula KPI y costo por conversación calificada.
3. Decide con reglas fijas cuánto invertir en Google frente a Meta (`docs/analisis-google-vs-facebook.md`).
4. Escribe el reporte en `marketing/reportes/<lunes>.md`.
5. Revisa que haya publicaciones programadas para las próximas tres semanas y prepara el siguiente bloque.

Nunca publica, programa ni gasta sin aprobación.

## Puesta en marcha (una vez)

1. **Conectar Metricool a Claude:** claude.ai → Configuración → Conectores → *Metricool Social Media Management* → Conectar con la cuenta donde están la página de Facebook y el Instagram de BZA Creative. Funciona con cualquier plan de Metricool.
2. **Reporte automático:** pedir en Claude Code: “crea la Routine semanal del agente de marketing con el conector de Metricool”. Se ejecuta los lunes por la mañana, hora de Guadalajara, y avisa al terminar.
3. Opcional: conectar Google Ads y Meta Ads dentro de Metricool cuando se lancen campañas, para que el agente lea la inversión.

## Lo que solo tú puedes registrar

El agente no puede leer WhatsApp. Cada vez que llegue una conversación, díctala al agente:

> /bza-marketing-skill registrar: llegó un lead de Google por WEB, constructora en Zapopan, quiere sitio de 30 mil, ya calificado

O agrega la fila en `datos/conversaciones.csv`. **No escribas nombres, teléfonos ni correos**: este repositorio no es un CRM.

> **El repositorio `Ba3z4/bza_creative` es público.** Todo lo que se guarde en `marketing/datos/` (sectores, etapas, montos de propuestas) lo puede ver cualquiera en GitHub. Si no quieres que el pipeline sea visible, cambia el repositorio a privado (GitHub → Settings → General → Danger Zone → Change visibility) o deja los montos en blanco. Cloudflare sigue publicando el sitio desde un repositorio privado.

Una vez por semana, anota los contactos de prospección enviados y respondidos (fila `prospeccion` en `datos/metricas-semanales.csv`, columnas `contactos_enviados` y `mensajes`).

## Archivos

| Archivo | Una fila por | Quién lo llena |
|---|---|---|
| `datos/metricas-semanales.csv` | semana (lunes) y canal | El agente desde Metricool; `prospeccion` a mano |
| `datos/publicaciones.csv` | publicación y red | El agente desde Metricool |
| `datos/conversaciones.csv` | conversación | Tú, o el agente cuando se lo dictas |
| `calendario/bloque-NN.json` | bloque de 4 semanas | El agente; tú apruebas |
| `reportes/AAAA-MM-DD.md` | semana | El agente |

Valores de `canal`: `facebook`, `instagram`, `google_ads`, `meta_ads`, `google_organico`, `sitio`, `prospeccion`, `referido`, `directo`.

Valores de `etapa`: `nuevo`, `calificado`, `diagnostico`, `propuesta`, `negociacion`, `ganado`, `perdido`.

## Cómo escribir los datos

### Canal

Se aceptan mayúsculas, acentos, espacios y guiones: `Google Ads`, `google-ads` y `GOOGLE_ADS` se leen como `google_ads`; `Meta Ads` como `meta_ads`; `Prospección` como `prospeccion`; `Google orgánico` como `google_organico`. Lo mismo con `calificada` (`Sí` = `si`) y `etapa` (`Diagnóstico` = `diagnostico`). Cualquier otro valor es un error: `tiktok` no es un canal y `WhatsApp` tampoco (es por dónde llegó el mensaje; el canal es dónde nos encontró la persona). En `metricas-semanales.csv` el canal es obligatorio; en `conversaciones.csv` puede quedar vacío si de verdad no se sabe el origen (sale como “Sin origen registrado”).

### Números

Coma para miles y punto para decimales, como en México: `1400`, `1,400`, `1,400.50`, `$1,400.50` o `350 MXN` (máximo dos decimales; vacío cuenta como 0). Se rechazan `1.400` (punto de miles) y `858,50` (coma decimal): el agente no adivina el formato porque leerlo mal cambiaría el valor cien o mil veces. También se rechazan `nan`, `inf` y los negativos, salvo `seguidores_nuevos`. Dentro del CSV, un número con coma de miles va entre comillas (`"1,400"`); Excel y Google Sheets lo hacen solos al exportar. Montos siempre en MXN.

### Fechas de cada etapa (opcionales)

`conversaciones.csv` tiene tres columnas después de `etapa` para anotar cuándo avanzó cada conversación:

| Columna | Qué anotar |
|---|---|
| `fecha_diagnostico` | El día de la llamada de diagnóstico. |
| `fecha_propuesta` | El día en que se envió la propuesta. |
| `fecha_cierre` | El día en que se ganó (etapa `ganado`) o se perdió (etapa `perdido`) el proyecto. |

- Formato `AAAA-MM-DD`, por ejemplo `2026-11-05`. `05/11/2026` se rechaza.
- Son opcionales. Si se dejan vacías, el reporte usa `fecha` (el día en que empezó la conversación) para cada etapa ya alcanzada. Con ellas, los diagnósticos, las propuestas y los proyectos ganados cuentan en la semana en que ocurrieron y no en la semana en que llegó el mensaje.
- Solo se anotan cuando la etapa ya ocurrió y nunca antes de `fecha`. Una fila con `fecha_propuesta` y `etapa` en `calificado` es un error: actualizar la etapa o borrar la fecha.
- En una conversación `perdido`, anotar la fecha de cada etapa a la que sí llegó: sin fecha, esas etapas no cuentan. `fecha_cierre` en una perdida es el día en que se perdió y no cuenta como ganada.
- Un `conversaciones.csv` anterior, sin estas columnas, se sigue leyendo igual.

### Errores

Si un dato no cumple, no se genera el reporte: el script termina con código 2 y dice el archivo y la fila de cada problema. La fila es la misma que muestra Excel o Google Sheets (el encabezado es la fila 1). Por ejemplo:

```
Error en los datos de …/marketing/datos (corregir y repetir):
  metricas-semanales.csv fila 3: inversion_mxn '1.400' no es un número válido (usar 1400, 1,400 o 1,400.50: coma para miles y punto para decimales)
  conversaciones.csv fila 8: canal 'WhatsApp' no es válido (usar: facebook, instagram, google_ads, meta_ads, google_organico, sitio, prospeccion, referido, directo)
```

La lista trae todos los errores de los tres archivos a la vez: hay que corregir todas las filas y repetir. También son errores una fila con más o menos valores que el encabezado (falta o sobra una coma), un `id` repetido en `conversaciones.csv`, dos filas de la misma semana y canal en `metricas-semanales.csv`, un número negativo, una fecha de etapa anterior a la conversación o anotada sin que la etapa haya ocurrido, y un archivo que no esté en UTF-8 (en Excel: *Guardar como → CSV UTF-8 (delimitado por comas)*).

Para revisar los datos y generar el reporte de una semana, desde la raíz del repositorio:

```
python3 .claude/skills/bza-marketing-skill/scripts/run_pipeline.py --semana AAAA-MM-DD
```

Escribe `marketing/reportes/<lunes>.md` y `.json`; sin `--semana` usa la última semana completa. En Windows (PowerShell) escribe `py` o `python` en lugar de `python3`; las rutas con `/` funcionan igual.

## Vista previa de cada bloque

Cada bloque de contenido tiene una vista previa para revisarlo antes de aprobarlo. Google no la indexa, pero cualquiera con el enlace puede abrirla: `https://bzacreative.com/campana-preview/bloque-02/`. El agente la regenera con `calendario.py preview`.

## Comandos útiles

```
/bza-marketing-skill                     reporte y decisión de la semana
/bza-marketing-skill ¿Google o Facebook?
/bza-marketing-skill calendario          siguiente bloque de publicaciones
/bza-marketing-skill programar bloque-02
```
