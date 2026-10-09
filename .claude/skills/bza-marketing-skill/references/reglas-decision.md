# Reglas de inversión Google vs Meta

Leer este archivo cuando haya que explicar o ajustar una recomendación de presupuesto. Los valores viven en `.claude/skills/bza-marketing-skill/assets/config.json` → `reglas`; `.claude/skills/bza-marketing-skill/scripts/decidir.py` los aplica.

## Métrica principal

**CPCC — costo por conversación calificada** = inversión del canal en la semana ÷ conversaciones calificadas atribuidas a ese canal en la misma semana.

Una conversación es **calificada** cuando responde las cinco preguntas del plan: qué ofrece el negocio, qué quiere lanzar o mejorar, qué hace hoy para conseguir clientes, cuándo quiere empezar y qué rango de inversión contempla, y el proyecto encaja con la oferta. Un “info”, “precio” o un estudiante no califica.

La atribución sale de `conversaciones.csv` → `canal`. El origen llega escrito en el mensaje de WhatsApp gracias a `dist/campaign.js` (UTM); si el mensaje no lo trae, preguntar “¿dónde nos encontraste?”.

## Reglas

| # | Regla | Valor | Por qué |
|---|---|---|---|
| 1 | Datos mínimos por canal | 14 días y 3 calificadas | Con menos, una sola conversación cambia el CPCC 50% o más. Si falta cualquiera de los dos, el canal sigue en aprendizaje. |
| 2 | CPCC máximo | $858 MXN | Plan de 90 días: contribución de un sitio de $22,000 con costo directo de 35% = $14,300; 30% para adquirir = CAC $4,290; con 20% de cierre, $858 por conversación calificada. |
| 3 | Tope sostenido | 2 semanas seguidas arriba de $858 | Pausar o rehacer anuncios, palabras clave y landing. |
| 4 | Reasignación | CPCC ≥30% menor 2 semanas seguidas | Se transfiere 20% del presupuesto del canal perdedor al ganador. Exactamente 30% sí cuenta; 25% no. Una semana con gasto y sin calificadas (CPCC infinito) nunca gana. |
| 5 | Piso por canal | 10% | Mantener aprendizaje y retargeting mientras se prueba. Una transferencia nunca deja a un canal por debajo de 10%, y un canal que ya invirtió conserva 10% del reparto sugerido aunque esta semana no haya gastado (el reporte pide confirmar si está pausado o rechazado). |
| 6 | Alarma de oferta | ≥150 contactos, ≥6 semanas de contenido y <5 calificadas | El problema es la oferta o el segmento, no el canal. Se necesitan las tres condiciones. |

## Ejemplo

| Semana | Google: inversión / calificadas / CPCC | Meta: inversión / calificadas / CPCC |
|---|---|---|
| 1 | $1,400 / 2 / $700 | $350 / 0 / sin conversaciones |
| 2 | $1,400 / 3 / $467 | $350 / 1 / $350 |
| 3 | $1,400 / 2 / $700 | $350 / 1 / $350 |
| 4 | $1,400 / 2 / $700 | $350 / 1 / $350 |

Al cierre de la semana 4 ambos canales llevan más de 14 días y al menos 3 calificadas. En las semanas 3 y 4 Meta tuvo un CPCC al menos 30% menor que Google ($350 frente a $700 en ambas): se mueven 20% del 80% de Google = 16 puntos. Reparto nuevo: Google 64%, Meta 36%.

Si cambia una regla, actualizar este ejemplo y los casos de `evals/casos/` que la fijan, y correr desde la raíz del repositorio:

```bash
python3 .claude/skills/bza-marketing-skill/scripts/run_evals.py
```

## Lo que el agente nunca hace

- Decidir por clics, alcance, seguidores o “me gusta”.
- Mover presupuesto en un canal en aprendizaje.
- Activar gasto, cambiar presupuestos en las plataformas o crear campañas sin aprobación explícita del responsable de la cuenta.
- Comparar con benchmarks de otros países como si fueran metas.
