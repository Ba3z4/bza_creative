'use strict';

(() => {
  // document.currentScript solo existe mientras este archivo se ejecuta; con él se arma el enlace al aviso de privacidad.
  const scriptSrc = document.currentScript ? document.currentScript.src : '';

  // Medición con consentimiento. Pega aquí los IDs para activarla. El aviso de cookies aparece siempre en la primera
  // visita y bloquea el sitio hasta elegir; con los IDs vacíos no se carga ninguna etiqueta de Google ni de Meta.
  // Antes de pegarlos, actualiza la sección 04 de /privacidad/ (node scripts/check-campaign.mjs lo exige).
  // - ga4Id: Google Analytics > Administrar > Flujos de datos > tu flujo web > "ID de medición" (G-XXXXXXXXXX).
  // - googleAdsId: Google Ads > Objetivos > Conversiones > tu conversión de WhatsApp > Configuración de la etiqueta >
  //   instalarla tú mismo: en el fragmento de evento, send_to: 'AW-XXXXXXXXXX/etiqueta'; aquí va la parte antes de la diagonal.
  // - googleAdsWhatsappLabel: la parte de send_to después de la diagonal (la etiqueta de conversión).
  // - metaPixelId: Meta > Administrador de eventos > tu píxel (conjunto de datos) > ID de solo números.
  const MEASUREMENT = {
    ga4Id: '',
    googleAdsId: '',
    googleAdsWhatsappLabel: '',
    metaPixelId: ''
  };

  const params = new URLSearchParams(window.location.search);
  const trackedKeys = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term', 'gclid', 'fbclid'];
  // Recorta a 180 caracteres sin dejar medio emoji, que haría fallar encodeURIComponent.
  const clean = value => {
    const text = String(value || '').trim().slice(0, 180);
    return /[\uD800-\uDBFF]$/.test(text) ? text.slice(0, -1) : text;
  };
  let attribution = {};

  try {
    attribution = JSON.parse(sessionStorage.getItem('bza_campaign') || '{}');
  } catch {
    attribution = {};
  }

  const incoming = Object.fromEntries(
    trackedKeys
      .filter(key => params.has(key))
      .map(key => [key, clean(params.get(key))])
      .filter(([, value]) => value)
  );

  if (Object.keys(incoming).length) {
    attribution = {
      ...incoming,
      landing_path: window.location.pathname,
      first_seen_at: new Date().toISOString()
    };
    try {
      sessionStorage.setItem('bza_campaign', JSON.stringify(attribution));
    } catch {
      // Attribution still works for the current page when storage is unavailable.
    }
  }

  window.dataLayer = window.dataLayer || [];
  const pushEvent = (event, details = {}) => window.dataLayer.push({ event, ...details });

  // El origen en el mensaje de WhatsApp va antes que cualquier código de medición. La medición reemplaza esta
  // función solo si arranca; si falla, el enlace y el evento whatsapp_click de dataLayer siguen funcionando.
  let measureWhatsappClick = () => {};

  document.querySelectorAll('a[href*="wa.me/"]').forEach(link => {
    const source = attribution.utm_source || 'directo';
    const medium = attribution.utm_medium || 'sitio';
    const campaign = attribution.utm_campaign || window.location.pathname.replace(/\//g, '') || 'inicio';
    const baseMessage = link.dataset.message || 'Hola, BZA Creative. Quiero hablar de mi proyecto.';
    const origin = `Origen de la consulta: ${source} / ${medium} / ${campaign}`;

    try {
      link.href = `https://wa.me/523342781554?text=${encodeURIComponent(`${baseMessage}\n\n${origin}`)}`;
    } catch (error) {
      console.warn('BZA Creative: no se pudo agregar el origen al enlace de WhatsApp.', error);
    }
    link.addEventListener('click', () => {
      const details = {
        link_text: clean(link.textContent),
        page_path: window.location.pathname,
        campaign_source: source,
        campaign_medium: medium,
        campaign_name: campaign
      };
      pushEvent('whatsapp_click', details);
      try {
        measureWhatsappClick(details);
      } catch (error) {
        console.warn('BZA Creative: no se pudo medir el clic de WhatsApp.', error);
      }
    });
  });

  // Lee los IDs y prepara el aviso de cookies. Con Google configurado, fija el consentimiento denegado por defecto
  // (debe ir antes de bza_page_view). Devuelve la función que muestra el aviso y aplica la elección guardada.
  const prepareMeasurement = () => {
    // IDs válidos de MEASUREMENT; un valor con formato incorrecto se ignora y se avisa en la consola.
    const readId = (name, pattern, pick = value => value) => {
      const value = pick(String(MEASUREMENT[name] || '').trim());
      if (value && !pattern.test(value)) {
        console.warn(`BZA Creative: ${name} "${value}" no tiene el formato esperado; no se usará.`);
        return '';
      }
      return value;
    };
    const ga4Id = readId('ga4Id', /^G-[A-Z0-9]+$/);
    const googleAdsId = readId('googleAdsId', /^AW-\d+$/, value => value.split('/')[0]);
    const adsLabel = readId('googleAdsWhatsappLabel', /^[\w-]+$/, value => value.split('/').pop());
    const pixelId = readId('metaPixelId', /^\d+$/);
    if (adsLabel && !googleAdsId) console.warn('BZA Creative: googleAdsWhatsappLabel necesita googleAdsId para medir conversiones.');
    const googleIds = [ga4Id, googleAdsId].filter(Boolean);

    const CONSENT_KEY = 'bza_consent';
    let consent = null;
    let storageReliable = true;
    let banner = null;
    let returnFocus = null;
    let inerted = [];

    function gtag() {
      window.dataLayer.push(arguments);
    }
    const consentState = (ads, analytics) => ({
      ad_storage: ads,
      ad_user_data: ads,
      ad_personalization: ads,
      analytics_storage: analytics
    });
    const deniedState = consentState('denied', 'denied');
    // Dos categorías: necesarias (siempre activas) y publicidad y medición (Google Analytics, Google Ads y píxel de Meta).
    // Elecciones guardadas: 'granted' (aceptar todas) o 'denied' (solo necesarias). Solo se concede lo configurado.
    const CHOICES = ['granted', 'denied'];
    const analyticsOn = choice => Boolean(ga4Id) && choice === 'granted';
    const adsOn = choice => Boolean(googleAdsId || pixelId) && choice === 'granted';
    const stateFor = choice => consentState(googleAdsId && adsOn(choice) ? 'granted' : 'denied', analyticsOn(choice) ? 'granted' : 'denied');

    if (googleIds.length) {
      window.gtag = gtag;
      gtag('consent', 'default', { ...deniedState, wait_for_update: 500 });
    }

    // undefined: no se puede leer el almacenamiento; null: todavía no hay elección.
    const readChoice = () => {
      if (!storageReliable) return undefined;
      try {
        const value = localStorage.getItem(CONSENT_KEY);
        return CHOICES.indexOf(value) >= 0 ? value : null;
      } catch {
        return undefined;
      }
    };
    const saveChoice = value => {
      try {
        if (value) localStorage.setItem(CONSENT_KEY, value);
        else localStorage.removeItem(CONSENT_KEY);
      } catch {
        // Sin almacenamiento, la elección vale solo para esta página y manda sobre lo que quedara guardado.
        storageReliable = false;
      }
    };

    const loadScript = src => {
      const script = document.createElement('script');
      script.async = true;
      script.src = src;
      document.head.append(script);
      return script;
    };

    // Si la visita llegó desde un anuncio y acepta en otra página, se le pasa a Google el origen guardado en la sesión.
    const attributedLocation = () => {
      const keys = trackedKeys.filter(key => attribution[key]);
      if (!keys.length || trackedKeys.some(key => params.has(key))) return '';
      const url = new URL(window.location.href);
      keys.forEach(key => url.searchParams.set(key, attribution[key]));
      return url.href;
    };

    let gtagLoaded = false;
    let pixelLoaded = false;
    const configured = [];

    const loadMetaPixel = () => {
      pixelLoaded = true;
      if (!window.fbq) {
        const fbq = function fbq() {
          if (fbq.callMethod) fbq.callMethod.apply(fbq, arguments);
          else fbq.queue.push(arguments);
        };
        Object.assign(fbq, { push: fbq, loaded: true, version: '2.0', queue: [] });
        window.fbq = fbq;
        if (!window._fbq) window._fbq = fbq;
        // Si la visita rechazó mientras la biblioteca cargaba, se borra la cookie que pudiera crear al llegar.
        loadScript('https://connect.facebook.net/en_US/fbevents.js').addEventListener('load', () => {
          clearMeasurementCookies(analyticsOn(consent), adsOn(consent));
        });
      }
      window.fbq('init', pixelId);
      window.fbq('track', 'PageView');
    };

    // Carga gtag.js una sola vez y configura cada ID de Google la primera vez que se acepta.
    const loadGoogle = (ids, pageLocation) => {
      if (!gtagLoaded) {
        gtagLoaded = true;
        loadScript(`https://www.googletagmanager.com/gtag/js?id=${encodeURIComponent(ids[0])}`);
        gtag('js', new Date());
      }
      ids.filter(id => configured.indexOf(id) < 0).forEach(id => {
        configured.push(id);
        gtag('config', id, pageLocation ? { page_location: pageLocation } : {});
      });
    };

    // Con gtag.js ya cargado, ga-disable detiene también los envíos sin cookies del modo de consentimiento.
    const setGoogleDisabled = active => googleIds.forEach(id => {
      window[`ga-disable-${id}`] = active.indexOf(id) < 0;
    });

    // Borra las cookies de medición que no están aceptadas.
    const clearMeasurementCookies = (keepAnalytics, keepAds) => {
      const names = document.cookie
        .split(';')
        .map(cookie => cookie.split('=')[0].trim())
        .filter(name => (!keepAnalytics && /^(_ga|_gid|_gat)/.test(name)) || (!keepAds && /^(_gcl_|_fbp|_fbc)/.test(name)));
      if (!names.length) return;
      const parts = window.location.hostname.split('.');
      const domains = [''];
      for (let index = 0; index < parts.length - 1; index++) domains.push(`; domain=.${parts.slice(index).join('.')}`);
      names.forEach(name => domains.forEach(domain => {
        document.cookie = `${name}=; Max-Age=0; path=/${domain}`;
      }));
    };

    // Antes de que llegue fbevents.js, los eventos esperan en fbq.queue: al rechazar se descartan y la revocación va
    // primero, para que la biblioteca no envíe nada aceptado antes de procesarla.
    const revokeMetaPixel = () => {
      const fbq = window.fbq;
      if (!fbq) return;
      if (!fbq.callMethod && Array.isArray(fbq.queue)) {
        fbq.queue = fbq.queue.filter(args => !/^track/.test(String(args[0])));
        fbq.queue.unshift(['consent', 'revoke']);
        return;
      }
      fbq('consent', 'revoke');
    };

    // Aplica una elección: actualiza el modo de consentimiento, carga solo lo aceptado y apaga y limpia lo demás.
    const applyPermissions = (choice, fromBanner) => {
      if (googleIds.length) {
        const active = [analyticsOn(choice) && ga4Id, adsOn(choice) && googleAdsId].filter(Boolean);
        if (gtagLoaded) setGoogleDisabled(active);
        gtag('consent', 'update', choice === 'granted' ? stateFor(choice) : deniedState);
        if (active.length) loadGoogle(active, fromBanner ? attributedLocation() : '');
      }
      if (pixelId) {
        if (adsOn(choice)) {
          if (pixelLoaded) window.fbq('consent', 'grant');
          else loadMetaPixel();
        } else if (pixelLoaded) {
          revokeMetaPixel();
        }
      }
      clearMeasurementCookies(analyticsOn(choice), adsOn(choice));
    };

    const deny = () => applyPermissions('denied', false);

    // En el aviso de privacidad (<body data-consent-readable>) el aviso no bloquea: hay que poder leerlo antes de decidir.
    const blocking = !(document.body && document.body.hasAttribute && document.body.hasAttribute('data-consent-readable'));

    const bannerStyles = `
.bza-consent{position:fixed;z-index:1000;inset:0;display:flex;align-items:center;justify-content:center;padding:16px;overflow-y:auto;background:rgba(23,23,23,.62);font-family:var(--font,Arial,Helvetica,sans-serif);font-size:.9375rem;line-height:1.55;color:#171717;animation:bza-consent-fade .25s ease-out both}
.bza-consent.is-readable{inset:auto 0 0;align-items:flex-end;background:transparent;pointer-events:none}
.bza-consent-box{position:relative;width:100%;max-width:560px;max-height:calc(100vh - 32px);overflow-y:auto;margin:auto;padding:28px;background:#F7F7F5;border:1px solid #171717;border-top:4px solid #083D3A;box-shadow:0 24px 60px rgba(23,23,23,.3);pointer-events:auto;animation:bza-consent-in .3s ease-out both}
.bza-consent.is-readable .bza-consent-box{max-width:860px;margin:0 auto}
.bza-consent-box:focus{outline:none}
.bza-consent h2{margin:0 0 12px;font-size:1.375rem;font-weight:600;line-height:1.25;letter-spacing:-.02em}
.bza-consent p{margin:0 0 12px}
.bza-consent ul{margin:0 0 16px;padding:0;list-style:none;display:grid;gap:10px}
.bza-consent li{padding-left:14px;border-left:3px solid #083D3A}
.bza-consent strong{font-weight:600}
.bza-consent a{color:#083D3A;font-weight:600;text-decoration:underline;text-underline-offset:3px}
.bza-consent-actions{display:flex;flex-wrap:wrap;gap:10px;margin-top:20px}
.bza-consent button{flex:1 1 180px;min-height:48px;padding:12px 18px;border:1px solid #083D3A;border-radius:0;font:inherit;font-weight:600;cursor:pointer;transition:background .2s,color .2s}
.bza-consent [data-consent-choice="denied"]{background:transparent;color:#083D3A}
.bza-consent [data-consent-choice="denied"]:hover{background:#E6ECEB}
.bza-consent [data-consent-choice="granted"]{background:#083D3A;color:#F7F7F5}
.bza-consent [data-consent-choice="granted"]:hover{background:#0F5550}
.bza-consent a:focus-visible,.bza-consent button:focus-visible{outline:3px solid #D92E22;outline-offset:3px}
html.bza-consent-lock,html.bza-consent-lock body{overflow:hidden}
html.bza-consent-open{scroll-padding-bottom:var(--bza-consent-space,0px)}
html.bza-consent-open body{padding-bottom:var(--bza-consent-space,0px)}
@keyframes bza-consent-fade{from{opacity:0}}
@keyframes bza-consent-in{from{opacity:0;transform:translateY(16px)}}
@media(max-width:640px){.bza-consent{padding:12px}.bza-consent-box{padding:22px 18px}.bza-consent.is-readable{padding:0}.bza-consent.is-readable .bza-consent-box{border-inline:0;border-bottom:0}}
@media(prefers-reduced-motion:reduce){.bza-consent,.bza-consent-box{animation:none}.bza-consent button{transition:none}}
html.motion-paused .bza-consent,html.motion-paused .bza-consent-box{animation:none}
@media print{.bza-consent{display:none}}`;

    // Enlace relativo a la ubicación de campaign.js (raíz del sitio), igual que los demás enlaces del sitio.
    const privacyHref = () => {
      try {
        if (scriptSrc) return new URL('privacidad/#sitio-web', scriptSrc).href;
      } catch {
        // Sin una URL válida del script se usa la ruta del sitio publicado.
      }
      return '/privacidad/#sitio-web';
    };
    const escapeAttribute = value => value.replace(/&/g, '&amp;').replace(/"/g, '&quot;');

    // Nombra las herramientas configuradas; si todavía no hay ninguna, las que el sitio podrá activar.
    const adTools = () => {
      const configuredTools = [ga4Id && 'Google Analytics', googleAdsId && 'Google Ads', pixelId && 'el píxel de Meta'].filter(Boolean);
      const tools = configuredTools.length ? configuredTools : ['Google Analytics', 'Google Ads', 'el píxel de Meta'];
      return tools.length > 1 ? `${tools.slice(0, -1).join(', ')} y ${tools[tools.length - 1]}` : tools[0];
    };

    const bannerMarkup = () => `
      <div class="bza-consent-box" role="dialog" aria-modal="${blocking}" aria-labelledby="bza-consent-title" aria-describedby="bza-consent-text" tabindex="-1">
        <h2 id="bza-consent-title">Antes de continuar, elige tus cookies</h2>
        <p id="bza-consent-text">Este sitio solo usa dos tipos de cookies y almacenamiento:</p>
        <ul>
          <li><strong>Necesarias (siempre activas).</strong> Hacen que el sitio funcione: guardan tu elección y el origen de tu visita para el mensaje de WhatsApp.</li>
          <li><strong>Publicidad y medición (solo si aceptas).</strong> ${adTools()}: medir qué anuncios generan conversaciones y volver a mostrarte anuncios de BZA Creative (remarketing).</li>
        </ul>
        <p>Puedes cambiar tu elección cuando quieras en «Preferencias de cookies», al pie de cada página. <a href="${escapeAttribute(privacyHref())}">Aviso de privacidad</a></p>
        <div class="bza-consent-actions">
          <button type="button" data-consent-choice="denied">Solo necesarias</button>
          <button type="button" data-consent-choice="granted">Aceptar todas</button>
        </div>
      </div>`;

    // Mantiene el foco dentro del aviso mientras bloquea el sitio; Escape no lo cierra porque hay que elegir.
    const trapFocus = event => {
      if (!blocking || !banner) return;
      if (event.key === 'Escape') {
        event.preventDefault();
        return;
      }
      if (event.key !== 'Tab') return;
      const focusable = Array.prototype.slice.call(banner.querySelectorAll('a[href], button'));
      if (!focusable.length) return;
      const first = focusable[0];
      const lastItem = focusable[focusable.length - 1];
      const current = document.activeElement;
      if (event.shiftKey && (current === first || !banner.contains(current) || current === dialog())) {
        event.preventDefault();
        lastItem.focus();
      } else if (!event.shiftKey && (current === lastItem || !banner.contains(current))) {
        event.preventDefault();
        first.focus();
      }
    };

    const dialog = () => (banner ? banner.querySelector('[role="dialog"]') : null);

    const reserveSpace = () => {
      const box = dialog();
      const space = !blocking && banner && banner.isConnected && box ? box.getBoundingClientRect().height : 0;
      document.documentElement.style.setProperty('--bza-consent-space', `${Math.ceil(space)}px`);
    };

    const createBanner = () => {
      const style = document.createElement('style');
      style.textContent = bannerStyles;
      document.head.append(style);

      const element = document.createElement('div');
      element.className = blocking ? 'bza-consent' : 'bza-consent is-readable';
      element.innerHTML = bannerMarkup();
      element.querySelectorAll('[data-consent-choice]').forEach(button => {
        button.addEventListener('click', () => choose(button.dataset.consentChoice));
      });
      element.addEventListener('keydown', trapFocus);
      return element;
    };

    // Con el aviso abierto, el resto de la página queda inerte: no se puede hacer clic, enfocar ni desplazar.
    const lockPage = () => {
      if (!blocking) return;
      document.documentElement.classList.add('bza-consent-lock');
      Array.prototype.forEach.call(document.body.children, child => {
        if (child === banner || child.inert) return;
        child.inert = true;
        inerted.push(child);
      });
    };
    const unlockPage = () => {
      document.documentElement.classList.remove('bza-consent-lock');
      inerted.forEach(child => {
        child.inert = false;
      });
      inerted = [];
    };

    const showBanner = focus => {
      banner = banner || createBanner();
      if (!banner.isConnected) document.body.append(banner);
      lockPage();
      document.documentElement.classList.add('bza-consent-open');
      reserveSpace();
      const box = dialog();
      if ((focus || blocking) && box) box.focus();
    };

    const hideBanner = () => {
      if (!banner) return;
      const hadFocus = banner.contains(document.activeElement);
      banner.remove();
      unlockPage();
      document.documentElement.classList.remove('bza-consent-open');
      document.documentElement.style.removeProperty('--bza-consent-space');
      // Si el aviso tenía el foco (también cuando lo cierra otra pestaña), vuelve al botón que lo abrió.
      if (hadFocus && returnFocus && returnFocus.isConnected) returnFocus.focus();
      if (hadFocus) returnFocus = null;
    };

    const applyChoice = (value, fromBanner) => {
      consent = value;
      if (value === 'granted') {
        hideBanner();
        applyPermissions(value, fromBanner);
      } else if (value === 'denied') {
        deny();
        hideBanner();
      } else {
        deny();
        showBanner(false);
      }
    };

    const choose = value => {
      const choice = CHOICES.indexOf(value) >= 0 ? value : 'denied';
      saveChoice(choice);
      applyChoice(choice, true);
      if (returnFocus && returnFocus.isConnected) returnFocus.focus();
      returnFocus = null;
    };

    // Aplica lo guardado si cambió en otra pestaña o mientras la página estaba en la caché de ir atrás/adelante.
    const syncChoice = () => {
      const stored = readChoice();
      if (stored === undefined || stored === consent) return;
      applyChoice(stored, false);
    };

    const trackWhatsapp = details => {
      if (consent !== 'granted') return;
      const stored = readChoice();
      if (stored !== undefined && stored !== consent) {
        syncChoice();
        return;
      }
      if (analyticsOn(consent)) gtag('event', 'whatsapp_click', { ...details, send_to: ga4Id });
      if (googleAdsId && adsLabel && adsOn(consent)) gtag('event', 'conversion', { send_to: `${googleAdsId}/${adsLabel}` });
      if (pixelId && adsOn(consent)) window.fbq('track', 'Contact');
    };

    return () => {
      measureWhatsappClick = trackWhatsapp;
      window.addEventListener('pageshow', event => {
        if (event.persisted) syncChoice();
      });
      window.addEventListener('storage', event => {
        if (event.key === CONSENT_KEY || event.key === null) syncChoice();
      });

      document.querySelectorAll('[data-consent-reset]').forEach(button => {
        button.hidden = false;
        button.addEventListener('click', () => {
          consent = null;
          saveChoice(null);
          deny();
          returnFocus = button;
          showBanner(true);
        });
      });

      const stored = readChoice();
      consent = stored === undefined ? null : stored;
      if (consent === 'granted') applyPermissions(consent, false);
      else if (!consent) showBanner(false);
    };
  };

  let startMeasurement = null;
  try {
    startMeasurement = prepareMeasurement();
  } catch (error) {
    console.warn('BZA Creative: la medición no pudo prepararse.', error);
  }

  pushEvent('bza_page_view', {
    page_path: window.location.pathname,
    campaign_source: attribution.utm_source || 'direct',
    campaign_medium: attribution.utm_medium || 'none',
    campaign_name: attribution.utm_campaign || 'none'
  });

  if (startMeasurement) {
    try {
      startMeasurement();
    } catch (error) {
      console.warn('BZA Creative: la medición no pudo iniciar.', error);
    }
  }
})();
