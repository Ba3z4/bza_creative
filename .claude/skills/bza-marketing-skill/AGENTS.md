# AGENTS.md — bza-marketing-skill

Agente de marketing de BZA Creative (`bzacreative.com`, Guadalajara). Mantiene el ritmo de publicaciones en Facebook e Instagram (Metricool), mide conversaciones calificadas y decide con reglas fijas cuánto invertir en Google Ads frente a Meta Ads. Responde en español de México.

## Cuándo activarlo

“Reporte semanal”, “cómo van las métricas”, “¿Google o Facebook?”, “dónde invierto”, “prepara el siguiente calendario”, “vista previa del bloque”, “programa las publicaciones”, “registra este lead”, “revisa Google Ads”, o `/bza-marketing-skill`.

## Cómo usarlo

Todos los comandos se corren desde la raíz del repositorio (en Windows/PowerShell, `py` o `python` en lugar de `python3`).

```bash
# Ciclo semanal: KPI -> decisión Google vs Meta -> reporte en marketing/reportes/
# Código 2 = datos inválidos; cada línea dice archivo y fila
python3 .claude/skills/bza-marketing-skill/scripts/run_pipeline.py [--semana AAAA-MM-DD]

# Bloques de contenido
python3 .claude/skills/bza-marketing-skill/scripts/calendario.py validar  marketing/calendario/bloque-02.json
python3 .claude/skills/bza-marketing-skill/scripts/calendario.py markdown marketing/calendario/bloque-02.json
# Cargas para Metricool (borrador; omite publicaciones con piezas PENDIENTE y lo avisa en stderr)
python3 .claude/skills/bza-marketing-skill/scripts/calendario.py metricool marketing/calendario/bloque-02.json --salida /tmp/cargas-bloque-02.json
# Vista previa visual (noindex) -> dist/campana-preview/bloque-02/index.html
#   tras desplegar en main: https://bzacreative.com/campana-preview/bloque-02/
python3 .claude/skills/bza-marketing-skill/scripts/calendario.py preview  marketing/calendario/bloque-02.json

# Pruebas
python3 .claude/skills/bza-marketing-skill/scripts/run_evals.py
python3 .claude/skills/bza-marketing-skill/scripts/run_evals.py --validate
```

Datos en `marketing/datos/` (tres CSV; reglas de llenado en `marketing/README.md`). `conversaciones.csv` acepta las columnas opcionales `fecha_diagnostico`, `fecha_propuesta` y `fecha_cierre` (`AAAA-MM-DD`) para contar cada avance en la semana en que ocurrió. Configuración, metas, reglas y pendientes de la Fase 0 en `assets/config.json`. Mientras no haya inversión, cada punto de `pendientes_fase0` con `"hecho": false` sale en el reporte como acción de prioridad alta; cuando el responsable lo confirme, cambiar `hecho` a `true`. El procedimiento completo, incluida la extracción desde Metricool y las reglas de aprobación, está en `SKILL.md` y `references/`.

## Reglas que no se rompen

- Nunca activar gasto, crear campañas ni programar publicaciones sin aprobación explícita del responsable de la cuenta.
- Decidir por costo por conversación calificada, no por clics, alcance ni “me gusta”.
- No guardar nombres, teléfonos ni correos en el repositorio.
- No inventar métricas: si un dato falta, se reporta como faltante.

## Gotchas

- Las etiquetas canónicas, `sitemap.xml` y `robots.txt` apuntaban a `bza-creative.ingluisbaeza.workers.dev`. Tras cualquier cambio de dominio, `node scripts/check-site.mjs` verifica que todo apunte a `https://bzacreative.com/`.
- `/campana-preview/` y `/campana-preview/<bloque>/` son vistas internas con `noindex`; `scripts/check-site.mjs` omite toda página con `noindex`.
- El Chromium de Playwright no reproduce H.264: en capturas automáticas los Reels de la vista previa muestran solo la portada.
- `www.bzacreative.com` no existe en DNS (NXDOMAIN en 8.8.8.8 y 1.1.1.1, 7 de octubre de 2026). El dominio canónico es `https://bzacreative.com/`, sin `www`; `src/worker.js` redirige `workers.dev` y `www` (si algún día se agrega) a ese dominio. No crear una regla de Cloudflare que redirija el dominio a `www`: haría un ciclo.
- México no usa horario de verano desde 2022: `America/Mexico_City` es UTC−6 todo el año.
- Metricool no lee el contenido de los mensajes directos: los mensajes con palabra clave se cuentan desde `conversaciones.csv`.
- El bloque 1 usó palabras con acento (`DIAGNÓSTICO`, `DIRECCIÓN`). Al contar, normalizar sin acentos; las palabras nuevas van sin acento.
- Las piezas de `dist/assets/` solo tienen URL pública después de llegar a `main` y desplegarse en Cloudflare.
- En sesiones en la nube la política de red puede bloquear `bzacreative.com` y `metricool.com`: usar el conector de Metricool, no `curl`.
- Los nombres de herramientas del conector de Metricool cambian entre versiones: listar las disponibles antes de llamarlas.
- `canal` se normaliza (`Google Ads`, `google-ads` y `GOOGLE_ADS` son `google_ads`; `Prospección` es `prospeccion`); un valor fuera de la lista (`tiktok`, `WhatsApp`) es error.
- Números con coma para miles y punto para decimales (`1,400.50`); `1.400` y `858,50` se rechazan en lugar de adivinar el formato.
- Los errores de datos dicen archivo y fila (`conversaciones.csv fila 4: …`, encabezado = fila 1) y no se escribe reporte hasta corregirlos todos.
- `calendario.py metricool` no genera carga para una publicación con alguna pieza `PENDIENTE:`; la avisa como `EXCLUIDA <id>` en stderr.
