# Guía de contenido orgánico

Leer este archivo antes de escribir o modificar un bloque de contenido.

## Ritmo

- Lunes, miércoles y viernes a las 10:00: publicación de imagen o carrusel (4:5, 1080×1350).
- Un Reel vertical (9:16, 1080×1920) cada dos semanas, sábado a las 18:00.
- Una historia el mismo día de cada publicación, entre 17:00 y 18:00, con la pieza y una pregunta o encuesta.
- Si el lunes es día de descanso oficial (por ejemplo, el tercer lunes de noviembre), mover la publicación al martes.

## Pilares y proporción por bloque de 4 semanas

| Pilar | Piezas | Ejemplos |
|---|---:|---|
| Educar sobre canales y medición | 4 | Google vs Facebook, qué medir, retargeting, presupuesto inicial |
| Autoridad web y conversión | 3 | landing, errores del sitio, búsqueda local |
| Aplicaciones y sistemas | 2 | operación digital, integraciones |
| Oferta y temporada | 3 | diagnóstico, Buen Fin, planeación del siguiente año |
| Reels de descubrimiento | 2 | resumen visual de un tema educativo del bloque |

## Estructura de cada texto

1. **Gancho** en la primera línea: un problema reconocible por el dueño del negocio. Sin “¿Sabías que…?”.
2. **Desarrollo** de 2 a 4 líneas cortas con una idea concreta, no una lista de servicios.
3. **Postura de BZA**: qué hacemos distinto, en una línea.
4. **Llamada a la acción** con palabra clave: “Escríbenos **PALABRA** por mensaje y te respondemos con…”. Decir qué recibe la persona.
5. Máximo 5 hashtags: 2 de tema, 1 de ciudad (`#Guadalajara` o `#Zapopan`), 1 de segmento y `#BZACreative`.

Tono: cercano, claro y profesional; tú (no usted); sin promesas de ventas garantizadas, sin cifras inventadas ni casos de clientes que no existan.

## Palabras clave

- MAYÚSCULAS, sin acentos ni espacios, de 3 a 15 caracteres (`GOOGLE`, `LANDING`, `2027`). Las personas escriben sin acentos; una palabra con acento divide los conteos.
- Una palabra distinta por tema; no repetirla en menos de 14 días.
- Al registrar una conversación, guardar la palabra recibida en `conversaciones.csv` → `palabra_clave`.

## Enlaces

Instagram no vuelve clicables los enlaces en el texto: la llamada a la acción remite al mensaje directo o al enlace del perfil. Las historias usan el sticker de enlace con el UTM que genera `calendario.py markdown` (`utm_medium=organic_social`, `utm_content` del tema).

## Producción de piezas

- Paleta: verde `#083D3A`, rojo `#D92E22`, papel `#F7F7F5`, tinta `#171717`.
- Las piezas se generan con scripts del repositorio (`scripts/create-*.py`) para mantener el estilo; las nuevas van en `dist/assets/brand-kit/<bloque>/`.
- Toda pieza necesita texto alternativo en la publicación cuando la red lo permita.

## Temporada (México)

| Momento | Ajuste |
|---|---|
| Finales de octubre y Día de Muertos | Menor atención B2B el 1 y 2 de noviembre: evitar piezas de oferta esos días. |
| Buen Fin (mediados de noviembre) | El costo de Meta sube; contenido sobre no improvisar anuncios y preparar el sitio antes de invertir. |
| Diciembre | Decisiones B2B más lentas: contenido de planeación del siguiente año y diagnóstico para enero. |
| Enero | Presupuestos nuevos: oferta de arranque y casos o procesos documentados. |

## Revisión con datos

Cada lunes, el reporte marca los temas con más **señales fuertes** (guardados + compartidos + mensajes con palabra clave ÷ alcance). El siguiente bloque repite el ángulo de los temas del tercio superior con una pieza nueva y cambia gancho o formato de los del tercio inferior.
