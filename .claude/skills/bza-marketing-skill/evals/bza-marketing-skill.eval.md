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
| 7 | Sin inversión, cada pendiente de `pendientes_fase0` sin `hecho` genera una acción alta “Fase 0 pendiente: …” y aparece en la sección “Pendientes de la Fase 0” del reporte; los marcados como hechos no aparecen; con inversión no se agregan esas acciones | `run_evals.py sin-inversion` y `run_evals.py aprendizaje` |
| 8 | La vista previa de un bloque válido lleva `noindex,nofollow`, enlaza cada pieza con una ruta relativa que existe en `dist/` e incluye carrusel, Reel, pieza pendiente, texto completo y enlace UTM | `run_evals.py calendario-valido` |
| 9 | El reporte en español contiene la lectura del agente y no inventa métricas | llm-judge: revisar a mano el primer reporte real |
| 10 | La vista previa se ve bien a 1440 y 390 px de ancho, sin desplazamiento horizontal y con todas las imágenes cargadas | revisión visual con captura (Playwright) después de `calendario.py preview` |

## Casos dorados

Cada carpeta de `evals/casos/` tiene `caso.json` con la entrada y el resultado esperado. Un caso de tipo `pipeline` puede traer `config` para reemplazar claves de `assets/config.json` solo en ese caso (así `sin-inversion` fija sus propios `pendientes_fase0` y no falla cuando el responsable marque puntos como hechos). El caso `reasignar` reproduce el ejemplo numérico de `references/reglas-decision.md` y se usa como prueba de liberación: si cambian las reglas, ese ejemplo y el caso deben cambiar juntos.

## Correcciones

Cuando el agente se equivoque en un reporte real, agregar un caso nuevo con esos datos (sin datos personales) y el resultado correcto, y anotar la corrección en `## Gotchas` de `SKILL.md`.
