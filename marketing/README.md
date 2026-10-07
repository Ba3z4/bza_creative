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

## Comandos útiles

```
/bza-marketing-skill                     reporte y decisión de la semana
/bza-marketing-skill ¿Google o Facebook?
/bza-marketing-skill calendario          siguiente bloque de publicaciones
/bza-marketing-skill programar bloque-02
```
