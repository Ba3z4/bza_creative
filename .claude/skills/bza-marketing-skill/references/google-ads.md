# Google Ads y retargeting en Meta — configuración de validación

Leer este archivo cuando se apruebe presupuesto o se revise una campaña pagada. El agente prepara la configuración; **no crea campañas ni activa gasto sin aprobación explícita**.

## Requisitos antes de lanzar

- Search Console verificado y sitemap enviado.
- GA4 instalado y evento `whatsapp_click` marcado como conversión principal en Google Ads.
- Aviso de privacidad publicado.
- Landing específica por grupo de anuncios (al menos la de diseño web en Guadalajara).

## Campaña de búsqueda

| Ajuste | Valor |
|---|---|
| Tipo | Solo red de búsqueda (sin Display ni socios) |
| Ubicación | Guadalajara y Zapopan, “presencia: personas que están en la ubicación” |
| Idioma | Español |
| Horario | Lunes a sábado, 8:00–20:00 |
| Puja | “Maximizar clics” con CPC máximo durante las 2 primeras semanas; pasar a “Maximizar conversiones” cuando haya conversiones medidas cada semana |
| Presupuesto | Lo aprobado; referencia $200–250 MXN diarios |
| Sufijo de URL final | `utm_source=google&utm_medium=cpc&utm_campaign=validacion_bza_2026&utm_content={adgroupid}&utm_term={keyword}` |
| Performance Max | No en el primer mes |

### Grupos y palabras (frase o exacta)

1. **Diseño web Guadalajara** → `/campana/` o landing de diseño web
   - "diseño de páginas web guadalajara", [diseño web guadalajara], "agencia de diseño web guadalajara", "páginas web para empresas guadalajara"
2. **Desarrollo de aplicaciones** → `/aplicaciones/`
   - "desarrollo de aplicaciones guadalajara", "desarrollo de apps para empresas", "crear una aplicación para mi negocio"
3. **Agencia de anuncios** → `/servicios/`
   - "agencia google ads guadalajara", "agencia de publicidad digital guadalajara", "agencia de marketing digital guadalajara", "agencia meta ads"
4. **Segmento elegido** (cuando se defina): "diseño web para arquitectos", "páginas web para constructoras"…

### Negativas iniciales

gratis, empleo, trabajo, vacante, sueldo, curso, carrera, tutorial, plantilla, plantillas, pdf, definición, “qué es”, ejemplos, wix, software, udg, iteso, tec de monterrey.

### Anuncio de búsqueda adaptable (grupo 1)

Títulos (≤30 caracteres):

1. Diseño Web en Guadalajara
2. Sitios que Generan Contactos
3. Diagnóstico Inicial sin Costo
4. Web + Google Ads + Medición
5. Habla por WhatsApp Hoy
6. Propuesta en Menos de 24 h
7. Estudio Web en Guadalajara
8. Diseño y Campañas Conectados
9. Apps Android, Windows y macOS
10. BZA Creative

Descripciones (≤90 caracteres):

1. Diseñamos sitios claros y campañas medibles para negocios de servicios en Guadalajara.
2. Revisamos tu oferta, tu sitio y tu recorrido al contacto. Escríbenos por WhatsApp.
3. Un solo equipo para web, anuncios y contenido. Medimos conversaciones, no solo clics.
4. Cuéntanos tu proyecto y recibe una propuesta con alcance, fechas y entregables.

## Revisión semanal (lunes)

1. Informe de términos de búsqueda: agregar como negativa todo término informativo, de empleo o de servicios gratuitos.
2. Pausar palabras con gasto mayor a 2 × $858 MXN y cero conversaciones calificadas.
3. Revisar cuota de impresiones perdida por presupuesto: si es alta y el CPCC está bajo el máximo, proponer más presupuesto.
4. Registrar en `metricas-semanales.csv` la fila `google_ads` (inversión, impresiones, clics, `clics_whatsapp`).

## Meta: retargeting (20% inicial)

| Ajuste | Valor |
|---|---|
| Objetivo | Mensajes (WhatsApp) o Clientes potenciales |
| Públicos | Visitantes del sitio 30 días (requiere píxel y aviso de privacidad) + personas que interactuaron con la página o Instagram en 90 días |
| Ubicación | Guadalajara y Zapopan |
| Creativo | La publicación orgánica con mejor tasa de señal del último reporte, en 4:5 y 9:16 |
| UTM | `utm_source=facebook` o `instagram`, `utm_medium=paid_social`, `utm_campaign=validacion_bza_2026`, `utm_content=<concepto>` |
| Presupuesto | Referencia $50 MXN diarios |

La campaña en frío de Meta se prueba solo cuando existan dos creativos con señales orgánicas y al menos un caso o testimonio.
