# BZA Creative

Sitio web profesional de BZA Creative para presentar servicios de diseño web, aplicaciones para Android, Windows y macOS, Google Ads, Meta Ads, TikTok Ads y contenido digital.

## Vista local

El sitio es estático y no necesita instalar dependencias.

```powershell
node preview.mjs
```

Después abre `http://127.0.0.1:4173`.

## Publicación

El sitio está publicado en Cloudflare Workers con el dominio https://www.bzacreative.com/ y conectado a la rama `main` de este repositorio. Los enlaces canónicos, `sitemap.xml` y `robots.txt` usan ese dominio; la dirección temporal `bza-creative.ingluisbaeza.workers.dev` redirige con 301 al dominio, conservando ruta y parámetros UTM, mediante `src/worker.js` (el Worker se ejecuta antes de servir `dist`).

`wrangler.jsonc` declara `src/worker.js` como Worker y `dist` como carpeta de archivos estáticos (binding `ASSETS`). El comando de despliegue es `npx wrangler deploy`; no requiere compilación ni dependencias de ejecución. Las páginas usan carpetas con `index.html` y rutas con barra final.

El flujo de GitHub Pages se conserva como una alternativa; no es necesario para el despliegue actual en Cloudflare.

## Páginas

- `/`: presentación del estudio y resumen de las áreas.
- `/servicios/`: servicios, alcances, entregables y preguntas frecuentes.
- `/aplicaciones/`: estrategia, UX/UI y desarrollo de aplicaciones multiplataforma.
- `/creatividad/`: conceptos creativos con intención, decisiones visuales y aplicaciones.
- `/enfoque/`: proceso de trabajo, principios y preparación del proyecto.
- `/campana/`: página de captación para anuncios y diagnóstico inicial.
- `/diseno-web-guadalajara/`: landing local para búsquedas y anuncios de diseño web en Guadalajara.
- `/publicidad-digital-guadalajara/`: landing local para búsquedas y anuncios de Google Ads y Meta Ads.
- `/privacidad/`: aviso de privacidad integral.
- `/campana-preview/`: vistas previas internas de los bloques de contenido (`noindex`).

La navegación principal enlaza las cuatro páginas institucionales; el pie agrega las landings locales y el aviso de privacidad. `/campana/` y las landings locales funcionan como destinos para anuncios. Todas las páginas públicas tienen etiquetas Open Graph con `assets/og-bza-creative.png` (generada con `scripts/create-og-image.py`). `dist/styles.css` contiene el estilo original; `dist/pages.css`, los estilos compartidos de las páginas interiores. La preferencia de pausar las animaciones se conserva en el navegador al navegar entre páginas.

`dist/campaign.js` conserva parámetros UTM durante la sesión, prepara eventos en `dataLayer` y añade el origen de la visita al mensaje de WhatsApp. La guía de activación está en `docs/configuracion-campana.md` y el plan de lanzamiento en `docs/plan-mercadotecnia-90-dias.md`.

La primera secuencia editorial y la preparación para Meta Ads están en `docs/campana-instagram-lanzamiento.md`.

## Agente de marketing

El análisis de canales está en `docs/analisis-google-vs-facebook.md`. El agente de IA que mide, decide y prepara publicaciones es el skill `/bza-marketing-skill` (`.claude/skills/bza-marketing-skill/`); su operación semanal y la conexión con Metricool se explican en `marketing/README.md`. El bloque 2 de contenido está en `marketing/calendario/bloque-02.json` (versión legible en `docs/calendario-bloque-02.md`) y sus piezas se generan con `python scripts/create-block-02.py`.

## Verificación local

```powershell
node --check dist/script.js
node --check dist/campaign.js
node --check src/worker.js
node scripts/check-site.mjs
node scripts/check-worker.mjs
```

La verificación comprueba enlaces internos, imágenes, anclas, metadatos únicos, dominio canónico, Open Graph, datos estructurados, sitemap, atribución y el WhatsApp de contacto en las nueve páginas públicas; `check-worker.mjs` prueba la redirección de `workers.dev`. Las páginas internas marcadas con `noindex`, como `/campana-preview/`, se omiten.
