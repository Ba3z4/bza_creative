# Configuración de la campaña de lanzamiento

## Lo que ya está instalado

- Landing de captación en `/campana/`.
- Conservación de parámetros UTM durante la sesión.
- Etiqueta del origen dentro del mensaje de WhatsApp.
- Eventos `bza_page_view` y `whatsapp_click` preparados en `dataLayer`.
- `robots.txt` y `sitemap.xml` para buscadores.
- Mensajes diferenciados según la llamada a la acción.
- Landings locales `/diseno-web-guadalajara/` y `/publicidad-digital-guadalajara/` para los grupos de Google Ads.
- Aviso de privacidad en `/privacidad/`.
- Aviso de consentimiento y carga de GA4, Google Ads y píxel de Meta, listos para activarse con sus IDs.
- Redirección 301 de `bza-creative.ingluisbaeza.workers.dev` a `bzacreative.com`.

## Convención para enlaces de anuncios

Usar parámetros en minúsculas y sin espacios. Ejemplo:

```text
https://DOMINIO/campana/?utm_source=google&utm_medium=cpc&utm_campaign=lanzamiento_servicios&utm_content=busqueda_diseno_web
```

Valores recomendados:

| Campo | Google Ads | Meta Ads |
| --- | --- | --- |
| `utm_source` | `google` | `facebook` o `instagram` |
| `utm_medium` | `cpc` | `paid_social` |
| `utm_campaign` | `lanzamiento_servicios` | `lanzamiento_servicios` |
| `utm_content` | grupo o anuncio | concepto creativo |

## Activar la medición externa

Orden obligatorio:

1. Completar en `/privacidad/` el nombre legal, domicilio y correo del responsable.
2. Actualizar la sección 04 de `/privacidad/` («Este sitio y la medición») para decir qué herramientas quedan activas, y cambiar la fecha de actualización en sus tres lugares. Google Ads y el píxel de Meta se usan para medir anuncios y para remarketing; el aviso de consentimiento del sitio ya lo dice.
3. Pegar los IDs en el objeto `MEASUREMENT` al inicio de `dist/campaign.js` y ejecutar `node scripts/check-campaign.mjs`. Debe decir `ACTIVE`; falla si `/privacidad/` todavía dice que el sitio no usa herramientas de analítica.
4. Publicar en `main`.

Cada ID funciona por separado.

| Campo | Dónde se obtiene |
|---|---|
| `ga4Id` | Google Analytics → Administrar → Recopilación y modificación de datos → Flujos de datos → Web (`https://bzacreative.com`) → “ID de medición” (`G-…`). |
| `googleAdsId` y `googleAdsWhatsappLabel` | Google Ads → Objetivos → Conversiones → Crear acción de conversión → Sitio web → configurarla manualmente con código, categoría Contacto, nombre “Clic WhatsApp”, contar “Una”. En el fragmento de evento, `send_to: 'AW-123456789/AbCdEf'`: la parte antes de la diagonal va en `googleAdsId` y la etiqueta en `googleAdsWhatsappLabel`. No pegar el fragmento en el HTML. |
| `metaPixelId` | Meta Business → Administrador de eventos → Orígenes de datos → píxel de BZA Creative → ID numérico. No instalar el código base: `campaign.js` lo carga tras el consentimiento y envía `PageView` y `Contact`. |

Después de publicar:

1. Marcar `whatsapp_click` como evento clave en GA4 y vincular GA4 con Google Ads.
2. Mantener activo el etiquetado automático (`gclid`) en Google Ads.

## Conexiones de operación

- **HubSpot:** crear un pipeline con etapas `Nuevo`, `Calificado`, `Propuesta`, `Ganado` y `No viable`.
- **Metricool:** conectar Instagram y Facebook, cargar el calendario editorial y etiquetar las publicaciones de campaña.
- **WhatsApp Business:** configurar saludo, respuestas rápidas y etiquetas equivalentes al pipeline.

## Control semanal

Registrar por canal: inversión, clics, sesiones, clics a WhatsApp, conversaciones calificadas, propuestas enviadas, ventas e ingreso. Las primeras decisiones deben basarse en conversaciones calificadas y ventas, no solo en clics.
