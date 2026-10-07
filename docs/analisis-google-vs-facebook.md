# Google o Facebook: dónde conviene invertir primero

Fecha: 6 de octubre de 2026  
Contexto: BZA Creative tiene sitio en `bzacreative.com`, página de Facebook e Instagram nuevas, 18 publicaciones orgánicas programadas en Metricool hasta el 23 de octubre y $0 MXN en anuncios.

## Respuesta corta

**El dinero de anuncios va primero a Google Search. Facebook e Instagram se quedan como canal de credibilidad orgánica y retargeting barato.** Reparto sugerido para el primer mes con presupuesto: **80% Google / 20% Meta**. Después, el presupuesto se mueve cada semana hacia el canal con menor **costo por conversación calificada**, no hacia el de más clics o “me gusta”.

Antes de pagar un solo clic hay que terminar las bases de Google, que son gratis y hoy frenan el posicionamiento (ver sección 3).

## 1. Por qué Google primero

| Criterio | Google Search | Facebook / Instagram |
|---|---|---|
| Intención | La persona ya busca “diseño de páginas web Guadalajara” o “agencia Google Ads”: está comprando. | La persona estaba viendo otra cosa: hay que crear la necesidad. |
| Confianza que exige | Baja: un anuncio claro y una landing sólida bastan para iniciar conversación. | Alta: en frío, la gente revisa seguidores, reseñas y casos. BZA todavía no tiene casos publicados. |
| Costo | Clic más caro. | Impresión y clic más baratos (varios reportes 2026 ubican el CPM de Meta en México alrededor de USD 2–5). |
| Calidad del contacto | Alta: suele llegar con un proyecto en mente. | Variable: muchos mensajes tipo “¿precio?” o “info” sin presupuesto. |
| Encaje con la oferta | Servicios de ticket medio y alto ($12,000 MXN a seis cifras). Un solo cliente paga meses de campaña. | Mejor cuando hay prueba social y una oferta de entrada clara. |
| Prueba de capacidad | BZA vende Google Ads: operarlo bien para sí misma se vuelve caso de estudio. | Igual para Meta Ads, pero en una etapa posterior. |
| Temporada | La búsqueda de servicios B2B no depende del calendario de comercio. | De octubre a diciembre el CPM de Meta sube 30–60% por Buen Fin y fiestas. |

Conclusión: con cero casos de clientes y presupuesto limitado, **Google captura demanda que ya existe** y Facebook ayuda a que esa demanda confíe. Quien llega por Google revisa la página de Facebook e Instagram antes de escribir, así que el contenido orgánico sí importa, aunque no sea el canal que cierra.

## 2. Qué papel juega cada canal

- **Google Search (pagado):** canal principal de conversaciones. Palabras de intención comercial por servicio y ciudad, con negativas estrictas.
- **Google orgánico (gratis):** Search Console, sitemap, páginas por servicio y ciudad. Tarda semanas, pero es el canal más barato a largo plazo.
- **Facebook e Instagram orgánico (Metricool):** credibilidad, autoridad y red local. Mantener 3 publicaciones por semana y un Reel cada dos semanas.
- **Meta pagado, fase 1:** solo cuando el píxel esté activo y el sitio ya tenga visitas de Google: retargeting a visitantes y a quienes interactuaron con la página, y promoción de la publicación orgánica con mejores señales. Google sigue siendo el canal principal.
- **Meta pagado, fase 2:** campaña en frío de mensajes o clientes potenciales, como en las semanas 7–8 del plan de 90 días: solo cuando existan al menos dos creativos con señales orgánicas y un caso o testimonio.

## 3. Lo que frenaba a Google (revisado en el repositorio)

| Hallazgo | Estado |
|---|---|
| Las etiquetas canónicas, `sitemap.xml` y `robots.txt` apuntaban a `bza-creative.ingluisbaeza.workers.dev`. Le decían a Google que indexara la dirección temporal y no `bzacreative.com`. | **Corregido.** |
| La dirección `workers.dev` respondía con una copia del sitio. | **Corregido:** `src/worker.js` la redirige con 301 a `bzacreative.com`, conservando ruta y UTM para que los enlaces viejos sigan funcionando. |
| No había una página por servicio y ciudad. | **Creadas:** `/diseno-web-guadalajara/` y `/publicidad-digital-guadalajara/`, con datos estructurados para Google. |
| No había aviso de privacidad. | **Publicado** en `/privacidad/`. Falta agregar nombre legal, domicilio y correo del responsable. |
| No había GA4 ni etiqueta de Google Ads. | **Listo para activar:** pegar los IDs en `dist/campaign.js` (`MEASUREMENT`). El sitio pide consentimiento antes de cargar cualquier etiqueta. |
| Las páginas no tenían vista previa para compartir en Facebook y WhatsApp. | **Corregido:** etiquetas Open Graph e imagen `og-bza-creative.png` en todas las páginas. |
| `www.bzacreative.com` no existe en DNS; el sitio vive en `bzacreative.com`. | **Corregido:** URL canónicas, sitemap y redirecciones usan `https://bzacreative.com/`. |
| No hay Google Search Console. | Pendiente del dueño: verificar el dominio y enviar `https://bzacreative.com/sitemap.xml`. |
| Perfil de Negocio de Google | Solo si atiendes en persona o visitas clientes; en ese caso, crear perfil de área de servicio ocultando el domicilio. No usar oficina virtual. |

## 4. Plan por fases

### Fase 0 — Bases, $0 MXN (6 al 25 de octubre)

Hecho en el sitio: dominio canónico, redirección de `workers.dev`, dos landings locales, aviso de privacidad, etiquetas para compartir y medición lista para activar.

Pendiente del dueño (el reporte semanal del agente lo recuerda hasta marcarlo como hecho):

1. Conectar Metricool a Claude para que el agente lea métricas (ver `marketing/README.md`).
2. Verificar el dominio en Google Search Console y enviar el sitemap.
3. Completar nombre legal, domicilio y correo en `/privacidad/`.
4. Crear GA4, actualizar la sección 04 de `/privacidad/` y después pegar el ID en `dist/campaign.js` (orden en `docs/configuracion-campana.md`).
5. Antes del retargeting en Meta: crear el píxel y pegar `metaPixelId` de la misma forma.
6. Registrar cada conversación en `marketing/datos/conversaciones.csv`.

### Fase 1 — Validación pagada (26 de octubre al 22 de noviembre)

Requiere aprobar presupuesto. Propuesta mínima:

| Canal | Diario | 4 semanas | Uso |
|---|---:|---:|---|
| Google Search | $200–250 MXN | $5,600–7,000 MXN | 3–4 grupos: diseño web Guadalajara (→ `/diseno-web-guadalajara/`), desarrollo de apps (→ `/aplicaciones/`), agencia Google/Meta Ads (→ `/publicidad-digital-guadalajara/`), segmento elegido |
| Meta | $50 MXN | $1,400 MXN | Retargeting y promoción de la mejor publicación orgánica en Guadalajara y Zapopan |

Escenario de referencia, no pronóstico: con $6,000 MXN y un clic de $15–30 MXN se obtienen 200–400 clics. Si 5–10% escribe por WhatsApp y 30% de esas conversaciones califica, el resultado sería de 3 a 12 conversaciones calificadas. El dato real lo darán las primeras dos semanas; el Planificador de palabras clave de Google da el costo por clic estimado antes de lanzar.

### Fase 2 — Reasignación semanal (desde el 23 de noviembre)

El agente aplica las reglas de la sección 5 cada lunes y propone el nuevo reparto.

## 5. Reglas de decisión

Estas reglas también están en `.claude/skills/bza-marketing-skill/assets/config.json` y el agente las aplica cada semana.

1. **Métrica principal:** costo por conversación calificada (CPCC) = inversión ÷ conversaciones calificadas del canal.
2. **Datos mínimos:** no mover presupuesto con menos de 14 días de campaña o menos de 3 conversaciones calificadas en el canal; antes de eso solo se corrigen anuncios, palabras y landing.
3. **Tope:** CPCC máximo de **$858 MXN**, derivado del plan de 90 días: CAC máximo de $4,290 MXN × 20% de cierre. Un canal que lo supere dos semanas seguidas se pausa o se rehace.
4. **Mover presupuesto:** si un canal tiene un CPCC al menos 30% menor que el otro durante dos semanas, se le transfiere 20% del presupuesto del otro canal. Ningún canal baja de 10% mientras se prueba.
5. **Orgánico:** se repiten los temas cuya tasa de señales fuertes (guardados + compartidos + mensajes con palabra clave) ÷ alcance esté en el tercio superior. Los “me gusta” no deciden.
6. **Señal de alarma:** con 150 contactos o más **y** 6 semanas de contenido o más, pero menos de 5 conversaciones calificadas, el problema es la oferta o el segmento, no el canal. Se corrige eso antes de invertir más.

## 6. Cómo saber de dónde vino cada cliente

- Todos los enlaces llevan UTM (`utm_source=google|facebook|instagram`, `utm_medium=cpc|paid_social|organic_social`).
- `campaign.js` añade el origen al mensaje de WhatsApp, así que cada conversación llega etiquetada.
- Cada publicación usa una palabra clave distinta (`GOOGLE`, `META`, `LANDING`…) para identificar qué contenido produjo el mensaje.
- El registro `marketing/datos/conversaciones.csv` no guarda nombres ni teléfonos; solo canal, palabra clave, etapa y valor.

## Fuentes

- [Benchmarks de CPM y CPC de Meta por país, 2026 — Adamigo](https://www.adamigo.ai/blog/meta-ads-cpm-cpc-benchmarks-by-country-2026)
- [Benchmarks de Meta Ads 2026 por industria — ContentStudio](https://contentstudio.io/blog/meta-ads-benchmarks)
- [Costo por clic de búsqueda en México — Statista](https://www.statista.com/statistics/1114826/mexico-search-advertising-cpc)
- [Google Ads benchmarks 2025 — WordStream](https://www.wordstream.com/blog/2025-google-ads-benchmarks)
- [Metricool MCP: uso con Claude](https://metricool.com/how-to-use-metricool-mcp-with-claude/)
- Plan interno: `docs/plan-mercadotecnia-90-dias.md` y `docs/plan-campana-alto-valor.md`.
