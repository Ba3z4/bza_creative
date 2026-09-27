# Configuración de la campaña de lanzamiento

## Lo que ya está instalado

- Landing de captación en `/campana/`.
- Conservación de parámetros UTM durante la sesión.
- Etiqueta del origen dentro del mensaje de WhatsApp.
- Eventos `bza_page_view` y `whatsapp_click` preparados en `dataLayer`.
- `robots.txt` y `sitemap.xml` para buscadores.
- Mensajes diferenciados según la llamada a la acción.

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

## Datos necesarios para activar medición externa

1. Dominio definitivo comprado en Cloudflare.
2. ID de medición de Google Analytics 4 (`G-...`).
3. ID de Google Ads (`AW-...`) y etiqueta de conversión.
4. ID del píxel de Meta si se lanzará Meta Ads.
5. Nombre legal o fiscal, domicilio de privacidad y correo de contacto para publicar el aviso de privacidad.

No se deben añadir píxeles publicitarios antes de definir el aviso de privacidad y la gestión de consentimiento correspondiente.

## Conexiones de operación

- **HubSpot:** crear un pipeline con etapas `Nuevo`, `Calificado`, `Propuesta`, `Ganado` y `No viable`.
- **Metricool:** conectar Instagram y Facebook, cargar el calendario editorial y etiquetar las publicaciones de campaña.
- **WhatsApp Business:** configurar saludo, respuestas rápidas y etiquetas equivalentes al pipeline.

## Control semanal

Registrar por canal: inversión, clics, sesiones, clics a WhatsApp, conversaciones calificadas, propuestas enviadas, ventas e ingreso. Las primeras decisiones deben basarse en conversaciones calificadas y ventas, no solo en clics.
