// Lleva las direcciones alternas al dominio para que Google no indexe copias del sitio.
// Solo estos hosts exactos redirigen; el dominio, las vistas previas de versión y localhost se sirven desde dist.
// www.bzacreative.com no existe hoy en DNS; si se agrega, también llegará al dominio sin www.
const SITE_ORIGIN = 'https://bzacreative.com';
const REDIRECT_HOSTS = new Set(['bza-creative.ingluisbaeza.workers.dev', 'www.bzacreative.com']);

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (REDIRECT_HOSTS.has(url.hostname)) {
      // 301 permanente que conserva la ruta y los parámetros UTM de enlaces ya publicados.
      return Response.redirect(SITE_ORIGIN + url.pathname + url.search, 301);
    }
    return env.ASSETS.fetch(request);
  },
};
