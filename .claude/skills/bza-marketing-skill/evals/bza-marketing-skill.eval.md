# Evaluación — bza-marketing-skill

Run: `python3 .claude/skills/bza-marketing-skill/scripts/run_evals.py` (todos deben decir `PASA`).

## Comprobaciones binarias

| # | Comprobación | Cómo se califica |
|---|---|---|
| 1 | Sin inversión pagada, el estado es `sin_inversion` y el reparto sugerido es 80/20 Google/Meta | `run_evals.py sin-inversion` |
| 2 | Un canal con menos de 14 días o menos de 3 calificadas nunca recibe ni pierde presupuesto | `run_evals.py aprendizaje` |
| 3 | Con CPCC ≥30% menor dos semanas seguidas se transfiere 20% del presupuesto del canal perdedor | `run_evals.py reasignar` |
| 4 | Un canal arriba de $858 MXN por conversación calificada dos semanas seguidas genera alerta | `run_evals.py tope` |
| 5 | ≥150 contactos, ≥6 semanas de contenido y <5 calificadas generan la alarma de oferta | `run_evals.py alarma` |
| 6 | Un bloque de contenido con errores de palabra clave, piezas, hashtags, fechas o UTM se rechaza; uno correcto se acepta y sus cargas para Metricool salen como borrador | `run_evals.py calendario` |
| 7 | El reporte en español contiene la lectura del agente y no inventa métricas | llm-judge: revisar a mano el primer reporte real |

## Casos dorados

Cada carpeta de `evals/casos/` tiene `caso.json` con la entrada y el resultado esperado. El caso `reasignar` reproduce el ejemplo numérico de `references/reglas-decision.md` y se usa como prueba de liberación: si cambian las reglas, ese ejemplo y el caso deben cambiar juntos.

## Correcciones

Cuando el agente se equivoque en un reporte real, agregar un caso nuevo con esos datos (sin datos personales) y el resultado correcto, y anotar la corrección en `## Gotchas` de `SKILL.md`.
