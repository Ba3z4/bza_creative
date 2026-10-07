# AGENTS.md — bza-marketing-skill

Agente de marketing de BZA Creative (`www.bzacreative.com`, Guadalajara). Mantiene el ritmo de publicaciones en Facebook e Instagram (Metricool), mide conversaciones calificadas y decide con reglas fijas cuánto invertir en Google Ads frente a Meta Ads. Responde en español de México.

## Cuándo activarlo

“Reporte semanal”, “cómo van las métricas”, “¿Google o Facebook?”, “dónde invierto”, “prepara el siguiente calendario”, “programa las publicaciones”, “registra este lead”, “revisa Google Ads”, o `/bza-marketing-skill`.

## Cómo usarlo

```bash
# Ciclo semanal: KPI -> decisión Google vs Meta -> reporte en marketing/reportes/
python3 .claude/skills/bza-marketing-skill/scripts/run_pipeline.py [--semana AAAA-MM-DD]

# Bloques de contenido
python3 .claude/skills/bza-marketing-skill/scripts/calendario.py validar  marketing/calendario/bloque-02.json
python3 .claude/skills/bza-marketing-skill/scripts/calendario.py markdown marketing/calendario/bloque-02.json
python3 .claude/skills/bza-marketing-skill/scripts/calendario.py metricool marketing/calendario/bloque-02.json

# Pruebas
python3 .claude/skills/bza-marketing-skill/scripts/run_evals.py
```

Datos en `marketing/datos/` (tres CSV); configuración, metas y reglas en `assets/config.json`. El procedimiento completo, incluida la extracción desde Metricool y las reglas de aprobación, está en `SKILL.md` y `references/`.

## Reglas que no se rompen

- Nunca activar gasto, crear campañas ni programar publicaciones sin aprobación explícita del responsable de la cuenta.
- Decidir por costo por conversación calificada, no por clics, alcance ni “me gusta”.
- No guardar nombres, teléfonos ni correos en el repositorio.
- No inventar métricas: si un dato falta, se reporta como faltante.

## Gotchas

- Las etiquetas canónicas, `sitemap.xml` y `robots.txt` apuntaban a `bza-creative.ingluisbaeza.workers.dev`. Tras cualquier cambio de dominio, `node scripts/check-site.mjs` verifica que todo apunte a `https://www.bzacreative.com/`.
- `/campana-preview/` es una vista interna con `noindex`; el verificador del sitio la omite.
- México no usa horario de verano desde 2022: `America/Mexico_City` es UTC−6 todo el año.
- Metricool no lee el contenido de los mensajes directos: los mensajes con palabra clave se cuentan desde `conversaciones.csv`.
- El bloque 1 usó palabras con acento (`DIAGNÓSTICO`, `DIRECCIÓN`). Al contar, normalizar sin acentos; las palabras nuevas van sin acento.
- Las piezas de `dist/assets/` solo tienen URL pública después de llegar a `main` y desplegarse en Cloudflare.
- En sesiones en la nube la política de red puede bloquear `bzacreative.com` y `metricool.com`: usar el conector de Metricool, no `curl`.
- Los nombres de herramientas del conector de Metricool cambian entre versiones: listar las disponibles antes de llamarlas.
