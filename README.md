# BZA Creative

Sitio web profesional de BZA Creative para presentar servicios de diseño web, desarrollo, Google Ads, Meta Ads, TikTok Ads y contenido digital.

## Vista local

El sitio es estático y no necesita instalar dependencias.

```powershell
node preview.mjs
```

Después abre `http://127.0.0.1:4173`.

## Publicación

El sitio está publicado en Cloudflare Workers en https://bza-creative.ingluisbaeza.workers.dev/ y conectado a la rama `main` de este repositorio.

`wrangler.jsonc` declara `dist` como carpeta de archivos estáticos. El comando de despliegue es `npx wrangler deploy`; no requiere compilación ni dependencias de ejecución. Las páginas usan carpetas con `index.html` y rutas con barra final.

El flujo de GitHub Pages se conserva como una alternativa; no es necesario para el despliegue actual en Cloudflare.

## Páginas

- `/`: presentación del estudio y resumen de las áreas.
- `/servicios/`: servicios, alcances, entregables y preguntas frecuentes.
- `/creatividad/`: conceptos creativos con intención, decisiones visuales y aplicaciones.
- `/enfoque/`: proceso de trabajo, principios y preparación del proyecto.

La navegación principal y el pie enlazan las cuatro páginas. `dist/styles.css` contiene el estilo original; `dist/pages.css`, los estilos compartidos de las páginas interiores. La preferencia de pausar las animaciones se conserva en el navegador al navegar entre páginas.

## Verificación local

```powershell
node --check dist/script.js
node scripts/check-site.mjs
```

La verificación comprueba enlaces internos, imágenes, anclas, metadatos únicos y el WhatsApp de contacto en las cuatro páginas.
