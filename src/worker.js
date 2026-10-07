// Redirige la dirección temporal de workers.dev al dominio para que Google no indexe dos copias del sitio.
// Solo este host exacto redirige; el dominio, sus versiones de vista previa y localhost se sirven desde dist.
const OLD_HOST = 'bza-creative.ingluisbaeza.workers.dev';
const SITE_ORIGIN = 'https://www.bzacreative.com';

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.hostname === OLD_HOST) {
      // 301 permanente que conserva la ruta y los parámetros UTM de enlaces ya publicados.
      return Response.redirect(SITE_ORIGIN + url.pathname + url.search, 301);
    }
    return env.ASSETS.fetch(request);
  },
};
