# Evaluación — bza-marketing-skill

Desde la raíz del repositorio:

```bash
python3 .claude/skills/bza-marketing-skill/scripts/run_evals.py             # todos los casos: todos deben decir PASA
python3 .claude/skills/bza-marketing-skill/scripts/run_evals.py ventaja     # solo los casos cuyo nombre contiene "ventaja"
python3 .claude/skills/bza-marketing-skill/scripts/run_evals.py --validate  # solo revisa que cada caso esté bien formado
```

## Comprobaciones binarias

La última columna es el filtro que se pasa a `run_evals.py`.

| # | Comprobación | Cómo se califica |
|---|---|---|
| 1 | Sin inversión pagada, el estado es `sin_inversion` y el reparto sugerido es 80/20 Google/Meta | `sin-inversion` |
| 2 | Un canal con menos de 14 días o menos de 3 calificadas nunca recibe ni pierde presupuesto | `aprendizaje` |
| 3 | Con CPCC ≥30% menor dos semanas seguidas se transfiere 20% del presupuesto del canal perdedor | `reasignar`, `ventaja` |
| 4 | Un canal arriba de $858 MXN por conversación calificada dos semanas seguidas genera alerta | `tope`, `cpcc-infinito` |
| 5 | ≥150 contactos, ≥6 semanas de contenido y <5 calificadas generan la alarma de oferta | `alarma` |
| 6 | Un bloque de contenido con errores de palabra clave, piezas, hashtags, fechas o UTM se rechaza; uno correcto se acepta y sus cargas para Metricool salen como borrador | `calendario` |
| 7 | Sin inversión, cada pendiente de `pendientes_fase0` sin `hecho` genera una acción alta “Fase 0 pendiente: …” y aparece en la sección “Pendientes de la Fase 0” del reporte; los marcados como hechos no aparecen; con inversión no se agregan esas acciones | `sin-inversion`, `aprendizaje`, `fase1-lista` |
| 8 | La vista previa de un bloque válido lleva `noindex,nofollow`, enlaza cada pieza con una ruta relativa que existe en `dist/` e incluye carrusel, Reel, pieza pendiente, texto completo y enlace UTM | `calendario-valido` |
| 9 | Un dato inválido en cualquiera de los tres CSV detiene el reporte con código 2 y un mensaje con archivo y fila | `fila` |
| 10 | El reporte en español contiene la lectura del agente y no inventa métricas | llm-judge: revisar a mano el primer reporte real |
| 11 | La vista previa se ve bien a 1440 y 390 px de ancho, sin desplazamiento horizontal y con todas las imágenes cargadas | revisión visual con captura (Playwright) después de `calendario.py preview` |

## Casos de límite

Fijan el valor exacto donde una regla cambia de resultado. La columna “Detecta” dice qué cambio en los scripts hace fallar el caso (prueba de mutación del 9 de octubre de 2026: 33 cambios, cada uno aplicado en una copia del skill; con todos, `run_evals.py` falló al menos un caso).

| Caso | Qué prueba | Detecta |
|---|---|---|
| `ventaja-30` | CPCC de Meta exactamente 30% menor ($560 contra $800) dos semanas: sí se transfiere (≥, con tolerancia de coma flotante) | Comparación estricta (`<`) sin tolerancia |
| `ventaja-25` | CPCC 25% menor ($300 contra $400) dos semanas, ambos evaluables: no se mueve presupuesto | Transferir cuando el otro canal es solo “más barato” (`a < b`) |
| `piso-transferencia` | Meta con 12% del reparto pierde dos semanas: baja solo a 10% (2 puntos), no a 9.6% | Quitar el piso de 10% en la transferencia |
| `canal-pausado` | Meta gastó la semana 1 y $0 la semana 2: reparto actual 100/0, el sugerido le deja 10% y hay acción “confirmar si la campaña está pausada o rechazada” | Quitar el piso de 10% del reparto sugerido; aprendizaje con AND |
| `aprendizaje-28-dias` | Google con 28 días y 2 calificadas; Meta con 3 calificadas y 7 días: ambos siguen en aprendizaje | Regla de aprendizaje con AND en lugar de OR |
| `cpcc-infinito` | Las dos últimas semanas ambos gastan sin calificadas: ninguno gana, no se mueve presupuesto y ambos generan alerta de tope | Tratar un CPCC infinito como ganador |
| `alarma-limite` | Exactamente 150 contactos, 6 semanas de contenido y 4 calificadas: sí hay alarma de oferta. La semana siguiente llega la quinta calificada: con 5 ya no hay alarma | `>` en lugar de `≥` en contactos o semanas; `≤` en lugar de `<` en calificadas; OR en lugar de AND |
| `sin-alarma-150` | 150 contactos y 0 calificadas, pero solo 2 semanas de contenido: no hay alarma | Alarma con OR en lugar de AND (cualquiera de las dos uniones) |
| `fase1-lista` | Sin inversión, sin pendientes de la Fase 0 y `presupuesto.fase` en `fase1`: acción alta para lanzar la campaña de validación, sin la acción genérica de la Fase 0 | Ignorar `presupuesto.fase` o dar la acción genérica de la Fase 0 sin pendientes abiertos |
| `fechas-etapa` | Una conversación de octubre llega a diagnóstico y propuesta en noviembre y se gana la semana siguiente; sin fechas de etapa se usa `fecha`; una perdida con `fecha_diagnostico` cuenta ese diagnóstico; una perdida con `fecha_cierre` y valor no cuenta como ganada | Ignorar `fecha_diagnostico`, `fecha_propuesta` y `fecha_cierre` (contar todo en la semana en que empezó la conversación) |
| `canal-escrito-distinto` | Con BOM de Excel («CSV UTF-8»): `Google Ads`, `google-ads`, `GOOGLE_ADS`, `Meta Ads` y `Prospección` se normalizan; `$1,400.50`, `350 MXN` y `1,200` se leen; `Sí` cuenta como calificada | Quitar la normalización de `canal` |
| `fila-invalida` | Fecha imposible, `1.400`, `858,50`, `nan`, `inf`, canal desconocido en métricas (`tiktok`) y en conversaciones (`WhatsApp`), canal vacío en métricas, etapa, calificada y fecha de etapa inválidas: código 2 y cada error con archivo y fila | Aceptar `1.400` como 1.4 (con más decimales permitidos o con `float()` de respaldo); quitar la validación de canal en cualquiera de los dos archivos o el error de canal vacío |
| `fila-coma-sin-comillas` | `1,400` sin comillas agrega una columna: error con archivo, fila y la pista de usar comillas | Descartar en silencio las columnas sobrantes |
| `fila-forma-y-reglas` | Errores reportados juntos con la fila de hoja de cálculo: fila larga y corta, `id` repetido, misma semana y canal (`Google Ads` otro día), número negativo, fecha de etapa anterior a la conversación, fecha de etapa sin la etapa, y numeración correcta tras una nota de varias líneas | Aceptar filas cortas (cifras en otra columna), detenerse en el primer error, contar líneas físicas, quitar cualquiera de esas reglas |
| `csv-no-utf8` | Un CSV en Windows-1252 se rechaza con la instrucción de guardarlo como CSV UTF-8 | Mostrar el error crudo de codificación |
| `tope-exacto` | CPCC exactamente de $858 tres semanas: no hay alerta (el tope es «arriba de $858») | `>=` en lugar de `>` |
| `palabras-acentos` | `DIAGNÓSTICO`, `diagnostico` y `Diagnóstico` cuentan juntas como `DIAGNOSTICO`; `DIRECCIÓN` se muestra como `DIRECCION` | Contar palabras clave sin quitar acentos |
| `calendario-metricool` | Un carrusel con una lámina `PENDIENTE:` no genera carga y stderr dice `EXCLUIDA m-02`; las demás llevan URLs absolutas `https://bzacreative.com/assets/...` | Medios con ruta relativa, ruta `/assets/...` o `dist/...`; programar publicaciones incompletas |
| `calendario-escapes` | Texto y tema con `<`, `&` y `"` se muestran escapados en la vista previa; ninguna etiqueta del texto llega al HTML | Insertar texto sin escapar en la vista previa |

## Casos dorados

Cada carpeta de `evals/casos/` tiene `caso.json` con la entrada y el resultado esperado (el formato está en el encabezado de `scripts/run_evals.py`). Un caso de tipo `pipeline` puede traer `config` para reemplazar claves de `assets/config.json` solo en ese caso (así `sin-inversion` fija sus propios `pendientes_fase0` y no falla cuando el responsable marque puntos como hechos), `otras_semanas` para revisar varias semanas con los mismos datos y `error_contiene` para esperar código 2 con esos fragmentos en stderr. El caso `reasignar` reproduce el ejemplo numérico de `references/reglas-decision.md` y se usa como prueba de liberación: si cambian las reglas, ese ejemplo y el caso deben cambiar juntos.

## Correcciones

Cuando el agente se equivoque en un reporte real, agregar un caso nuevo con esos datos (sin datos personales) y el resultado correcto, y anotar la corrección en `## Gotchas` de `SKILL.md`. Si se cambia una regla en los scripts, comprobar que algún caso falle con la regla anterior; si ninguno falla, el caso nuevo es obligatorio.
