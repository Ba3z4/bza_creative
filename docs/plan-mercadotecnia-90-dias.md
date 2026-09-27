# Plan de mercadotecnia de BZA Creative

Fecha: 27 de septiembre de 2026  
Horizonte: primeros 90 días  
Mercado inicial: Guadalajara y Zapopan, con posibilidad de atender clientes en todo México  

## 1. Decisión estratégica

BZA Creative debe iniciar como un estudio especializado en **sitios web y campañas para negocios de servicios de ticket medio o alto**, no como una agencia que ofrece todo para todos.

El primer segmento de prueba será:

- arquitectura, interiorismo y mobiliario;
- construcción, remodelación y servicios para inmuebles;
- consultores y servicios B2B especializados.

Estos negocios tienen tres ventajas: su trabajo se puede mostrar visualmente, una sola venta nueva puede justificar la inversión en marketing y normalmente necesitan conectar sitio, portafolio, Google y WhatsApp.

La promesa inicial será:

> Diseñamos una presencia digital clara y campañas que convierten búsquedas e interés en conversaciones calificadas.

No prometeremos ventas garantizadas. La propuesta será crear el sistema, medirlo y mejorarlo.

## 2. Viabilidad

### Evidencia de mercado

INEGI reporta más de seis millones de establecimientos en DENUE. En los Censos Económicos 2024, las ventas por internet representaron 20.2% del ingreso de las unidades económicas; entre quienes vendieron por internet, 61.1% utilizó su propia página web y 24.3% utilizó redes sociales. Esto confirma que sitio y redes cumplen funciones complementarias, que coincide con la oferta de BZA Creative.

Fuentes:

- [DENUE de INEGI](https://www.inegi.org.mx/app/mapa/denue/)
- [Resultados definitivos de los Censos Económicos 2024](https://www.inegi.org.mx/contenidos/saladeprensa/boletines/2025/ce/CE2024_def_RR.pdf)

### Diagnóstico actual

| Área | Situación actual | Evaluación |
|---|---|---|
| Oferta | Web, Google Ads, Meta Ads y creatividad conectados | Fuerte |
| Sitio | Profesional, rápido y orientado a WhatsApp | Fuerte |
| Portafolio | Buenos conceptos, todavía sin casos y resultados de clientes | Débil |
| Nicho | Oferta todavía general | Débil |
| Medición | UTM, origen en WhatsApp y eventos en `dataLayer` listos; faltan IDs de GA4 y plataformas publicitarias | Parcialmente lista |
| Ventas | WhatsApp funciona, pero falta proceso de calificación y CRM | Pendiente |
| Formalización | Falta confirmar régimen fiscal, contrato y aviso de privacidad | Pendiente |

Conclusión: **viabilidad moderada-alta**, condicionada a validar el segmento y conseguir dos o tres casos reales. El principal riesgo no es la capacidad de diseño; es conseguir clientes de manera repetible y demostrar resultados.

## 3. Oferta comercial inicial

Los precios son hipótesis para validar, no tarifas definitivas.

| Oferta | Alcance inicial | Precio de prueba sugerido |
|---|---|---:|
| Presencia esencial | Landing page, copy básico, WhatsApp, medición | $12,000–$18,000 MXN |
| Sitio de servicios | 4–6 páginas, portafolio, SEO básico, medición | $22,000–$38,000 MXN |
| Arranque de anuncios | Estrategia, configuración, creativos y medición | $6,000–$10,000 MXN más inversión publicitaria |
| Gestión mensual | Optimización, creativos, reporte y reunión mensual | $6,000–$12,000 MXN mensuales |
| Identidad para campaña | Dirección visual y paquete inicial de piezas | $8,000–$16,000 MXN |

Reglas comerciales:

- 50% de anticipo, 30% con aprobación de diseño y 20% antes de publicar.
- La inversión en medios se paga directamente desde la cuenta publicitaria del cliente.
- Dominio, herramientas, fotografías y servicios de terceros se cotizan por separado.
- Cada propuesta define entregables, revisiones, fechas, responsabilidades y exclusiones.
- El cliente conserva la propiedad de sus cuentas de Google, Meta, dominio y analítica.

## 4. Embudo de adquisición

```text
Contenido / búsqueda / prospección
                ↓
Página específica del servicio
                ↓
Conversación por WhatsApp
                ↓
Calificación de 5 preguntas
                ↓
Diagnóstico de 30 minutos
                ↓
Propuesta en menos de 24 horas
                ↓
Seguimiento a 2, 5 y 10 días
                ↓
Anticipo y onboarding
```

Preguntas de calificación:

1. ¿Qué ofrece el negocio y en qué ciudad trabaja?
2. ¿Qué quiere lanzar o mejorar?
3. ¿Qué está haciendo hoy para conseguir clientes?
4. ¿Cuándo quiere comenzar?
5. ¿Qué rango de inversión tiene contemplado para el proyecto y, en su caso, para anuncios?

Etapas del CRM: nuevo contacto, calificado, diagnóstico agendado, propuesta enviada, negociación, ganado, perdido y seguimiento futuro.

## 5. Preparación antes de invertir en anuncios — semanas 1 y 2

### Sitio y dominio

- Conectar el dominio nuevo a Cloudflare.
- Cambiar enlaces canónicos y metadatos del dominio temporal al dominio definitivo.
- Crear una página específica para el segmento inicial, por ejemplo `/soluciones/arquitectura-construccion/`.
- Agregar aviso de privacidad y, si se usan cookies de medición o publicidad, el mecanismo de consentimiento correspondiente.
- Añadir una página breve con proceso, rangos de inversión y preguntas de calificación.

### Medición

- Instalar GA4 y Google Search Console.
- Crear los eventos `whatsapp_click`, `service_view`, `qualified_lead`, `proposal_sent` y `sale_closed`.
- Instalar Google Ads Tag y, cuando comience Meta, Meta Pixel/Conversions API conforme al consentimiento aplicable.
- Usar UTM en todos los enlaces: `utm_source`, `utm_medium` y `utm_campaign`.
- Crear un mensaje de WhatsApp diferente por campaña para identificar el origen incluso si falla la analítica.

Google recomienda medir acciones valiosas y distinguir conversiones primarias de las secundarias. Los UTM permiten identificar las campañas que envían tráfico.

- [Medición de conversiones de Google Ads](https://support.google.com/google-ads/answer/1722022)
- [Parámetros UTM de Google Analytics](https://support.google.com/analytics/answer/10917952)

### Activos comerciales

- Plantilla de diagnóstico.
- Propuesta comercial de una página.
- Contrato de servicios y documento de alcance.
- Formato de reporte mensual.
- Dos auditorías de ejemplo sobre negocios reales, sin publicar información privada.
- Un proyecto piloto real a precio de introducción a cambio de testimonio y autorización para documentar el caso.

## 6. Validación sin publicidad — semanas 3 y 4

Construir una lista manual de 100 empresas del segmento usando DENUE, directorios profesionales, asociaciones y búsquedas locales. No comprar bases ni enviar mensajes masivos.

Clasificar cada empresa:

- A: buen negocio, sitio inexistente o claramente mejorable, oferta de ticket alto;
- B: sitio aceptable, pero campaña y seguimiento débiles;
- C: no encaja, no contactar.

Ritmo semanal:

- 25 contactos personalizados;
- 3 publicaciones educativas;
- 1 auditoría visual corta;
- 5 conversaciones con aliados como fotógrafos, arquitectos, desarrolladores o consultores;
- 1 revisión de métricas y objeciones.

Mensaje de prospección:

> Hola, [nombre]. Revisé la presencia digital de [negocio] y vi dos oportunidades concretas para que sus proyectos se entiendan mejor y sea más fácil solicitar una cotización. Preparé una revisión breve de tres minutos. ¿Te la envío?

El diagnóstico inicial será gratuito; no se diseñará un sitio completo sin anticipo.

### Lo que aportaron los foros

Las conversaciones revisadas son evidencia anecdótica, no estadísticas, pero repiten patrones útiles:

- funciona mejor señalar un problema específico que enviar un discurso genérico;
- la red personal, aliados y referidos suelen producir los primeros clientes;
- los primeros casos bajan la barrera de confianza;
- definir alcance, comunicación y entrega es tan importante como vender;
- regalar un sitio completo crea riesgo de trabajo no pagado; una microauditoría demuestra capacidad con menor costo.

Referencias:

- [Experiencias sobre primeros clientes de diseño web](https://www.reddit.com/r/smallbusiness/comments/1tu1s6o/how_did_you_get_your_first_clients_for_a_web/)
- [Prospección basada en problemas concretos](https://www.reddit.com/r/agencynewbies/comments/1tu1v3u/how_did_you_get_your_first_clients_for_a_web/)
- [Red profesional, alianzas y especialización](https://www.reddit.com/r/freelanceuk/comments/1mk362v)
- [Dos o tres ciclos de adquisición repetibles](https://www.indiehackers.com/post/advice-for-ramping-up-marketing-for-a-digital-agency-1c48b33ba4)

## 7. Campaña piloto — semanas 5 a 8

No dividir un presupuesto pequeño entre demasiados canales. Comenzar con Google Search, porque captura demanda existente. Meta funcionará primero como contenido orgánico y se probará después.

### Google Search

Presupuesto de prueba: **$6,000 a $8,000 MXN durante 30 días**.

Grupos iniciales:

1. diseño de páginas web en Guadalajara;
2. agencia Google Ads en Guadalajara;
3. agencia Meta Ads / publicidad digital en Guadalajara;
4. diseño web para arquitectos, constructoras o interioristas.

Negativas iniciales: gratis, empleo, curso, carrera, sueldo, definición, plantilla, tutorial y software.

Destino: página específica del segmento, no la portada general. Conversión primaria: conversación calificada por WhatsApp. Clic sin conversación será una métrica de diagnóstico, no una venta.

Durante el primer mes no lanzar Performance Max. Google indica que la automatización necesita medición confiable, una conversión claramente definida y tiempo de aprendizaje. Primero reuniremos datos de búsqueda y calidad de prospectos.

- [Generación de clientes potenciales con Google Ads](https://support.google.com/google-ads/answer/15795510)
- [Uso de datos para optimizar Search](https://support.google.com/google-ads/answer/9451527)

### Meta, semanas 7 y 8

Si ya existen al menos dos creativos que generaron interacción orgánica, probar **$3,000 a $4,500 MXN** durante 14–21 días.

Objetivo: clientes potenciales o conversación por WhatsApp. Creativos:

- auditoría: “Tu trabajo se ve mejor que tu sitio”;
- proceso: antes/después de reorganizar una oferta;
- oferta: diagnóstico de presencia digital para negocios del segmento.

Preparar versiones 4:5 y video vertical 9:16 con mensaje dentro de la zona segura. Meta recomienda creativos verticales con audio para Reels y pruebas A/B.

- [Buenas prácticas de anuncios en Reels](https://www.facebook.com/business/ads/facebook-instagram-reels-ads)

## 8. Optimización y expansión — semanas 9 a 12

- Pausar palabras, anuncios y audiencias que atraigan estudiantes, empleo o servicios gratuitos.
- Revisar llamadas y conversaciones, no solamente clics.
- Crear el primer caso de estudio con situación inicial, proceso, entrega y resultado observable.
- Solicitar testimonio y dos referidos a cada cliente satisfecho.
- Convertir el servicio vendido en un proceso repetible.
- Probar Meta pagado solo si Google o la prospección ya demuestran qué mensaje y oferta convierten.
- Explorar un segundo segmento únicamente después de cerrar dos clientes del primero.

## 9. Tablero semanal

| Indicador | Meta inicial |
|---|---:|
| Empresas investigadas | 25 por semana |
| Contactos personalizados | 20–25 por semana |
| Respuestas | 8% o más |
| Diagnósticos realizados | 4 por semana al final del segundo mes |
| Propuestas enviadas | 2 por semana |
| Cierre de propuestas | 25% o más |
| Tiempo de respuesta en horario laboral | menos de 15 minutos |
| CAC máximo | 30% del margen bruto del primer contrato |

Estas metas son umbrales internos para aprender, no promedios garantizados del mercado.

### Fórmula de viabilidad

Si un sitio se vende en $22,000 MXN y el costo directo de producirlo es 35%, deja una contribución aproximada de $14,300 MXN antes de gastos generales. Si se acepta invertir hasta 30% de esa contribución en adquirir al cliente, el CAC máximo sería $4,290 MXN.

Si se cierra uno de cada cinco prospectos calificados, el costo máximo por prospecto calificado sería:

`$4,290 × 20% = $858 MXN`

No escalaremos una campaña que supere ese costo durante dos ciclos de venta sin mostrar mejora en calidad.

## 10. Criterios de decisión al día 90

Continuar y aumentar inversión si se cumplen al menos cuatro de cinco condiciones:

1. dos o más clientes pagados;
2. un caso de estudio publicable;
3. tasa de cierre de propuestas igual o superior a 25%;
4. CAC menor a 30% de la contribución del primer contrato;
5. al menos una fuente repetible: referidos, prospección, Google o contenido.

Reposicionar oferta o segmento antes de invertir más si, después de 150 contactos personalizados y seis semanas de contenido, hay menos de cinco conversaciones calificadas. El problema podría estar en el segmento, la oferta o la prueba, no necesariamente en el canal.

## 11. Formalización de la empresa en México

La ruta más ligera suele ser comenzar como persona física con actividad empresarial o profesional y evaluar RESICO si se cumplen sus requisitos. El SAT señala un límite de $3.5 millones de pesos de ingresos anuales para personas físicas elegibles en RESICO. La elección concreta debe revisarse con un contador según ingresos, otras actividades, deducciones y socios.

Pasos:

1. Obtener o actualizar RFC, contraseña y e.firma.
2. Elegir régimen fiscal con un contador.
3. Habilitar facturación y una cuenta bancaria separada para el negocio.
4. Usar contrato, alcance y política de anticipos en cada proyecto.
5. Publicar aviso de privacidad antes de almacenar formularios, analítica identificable o datos de prospectos.
6. Buscar “BZA Creative” en las herramientas del IMPI y solicitar la marca si está disponible.
7. Crear una SAS únicamente si se necesita persona moral, socios, separación patrimonial o contratos que la requieran.

Una SAS puede constituirse en línea y sin costo ante la Secretaría de Economía; requiere e.firma y autorización de denominación. No es obligatorio crearla para validar el negocio como persona física.

Fuentes oficiales:

- [Orientación del SAT para emprendedores](https://wwwmat.sat.gob.mx/consulta/09788/emprendedor%2C-conoce-los-regimenes-fiscales-de-las-personas-fisicas)
- [Artículo 113-E, límite de RESICO](https://wwwmat.sat.gob.mx/articulo/58780/articulo-113-e)
- [Constitución en línea de una SAS](https://www.gob.mx/tramites/ficha/constitucion-de-sociedad-por-acciones-simplificada-sas/SE2568)
- [Registro de marca ante el IMPI](https://www.gob.mx/impi/documentos/registro-de-marcas)
- [Ley de protección de datos personales](https://www.ordenjuridico.gob.mx/Documentos/Federal/html/wo125102.html)

Nota: si BZA Creative es exclusivamente online, no debe crear un Perfil de Negocio de Google con una oficina virtual. Google limita ese perfil a negocios con contacto presencial o que visitan a sus clientes.

## 12. Herramientas recomendadas

- HubSpot: registrar prospectos, etapas y seguimiento. La versión gratuita es suficiente para comenzar.
- Metricool: programar contenido y revisar rendimiento de redes.
- Supermetrics: útil cuando existan varias cuentas y suficiente volumen para consolidar Google, Meta y GA4; no es necesario en el primer mes.
- GA4, Search Console y hojas de cálculo: medición inicial.
- WhatsApp Business: respuestas rápidas, etiquetas y horario de atención.

La prioridad no es acumular herramientas. Primero se debe demostrar un proceso semanal capaz de producir conversaciones, propuestas y ventas.

## 13. Próximas cinco acciones

1. Confirmar el dominio comprado y conectarlo al Worker.
2. Elegir el primer segmento entre arquitectura/interiores, construcción/remodelación o consultoría B2B.
3. Definir tres paquetes y aprobar sus rangos de inversión.
4. Implementar medición y aviso de privacidad en el sitio.
5. Preparar la primera lista de 25 empresas y comenzar la validación antes de pagar anuncios.
