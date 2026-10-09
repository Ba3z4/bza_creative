'use strict';

(() => {
  // document.currentScript solo existe mientras este archivo se ejecuta; con él se arma el enlace al aviso de privacidad.
  const scriptSrc = document.currentScript ? document.currentScript.src : '';

  // Medición con consentimiento. Pega aquí los IDs para activarla. Mientras todos estén vacíos, el sitio
  // no muestra el aviso, no usa localStorage y no carga ninguna etiqueta de Google ni de Meta.
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

  // Lee los IDs y, si hay alguno válido, fija el consentimiento denegado por defecto (debe ir antes de bza_page_view).
  // Devuelve la función que arranca el aviso y las etiquetas, o null si la medición está apagada.
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
    if (!googleIds.length && !pixelId) return null;

    const CONSENT_KEY = 'bza_consent';
    let consent = null;
    let storageReliable = true;
    let banner = null;
    let returnFocus = null;
    let spaceObserver = null;

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
    // Elecciones guardadas: 'granted' (todo), 'denied' (nada), 'analytics' (solo analítica) o 'ads' (solo publicidad).
    // Analítica = Google Analytics; publicidad = Google Ads y píxel de Meta. Solo se concede lo que está configurado.
    const CHOICES = ['granted', 'denied', 'analytics', 'ads'];
    const hasAnalytics = Boolean(ga4Id);
    const hasAds = Boolean(googleAdsId || pixelId);
    const allows = (choice, category) => choice === 'granted' || choice === category;
    const analyticsOn = choice => hasAnalytics && allows(choice, 'analytics');
    const adsOn = choice => hasAds && allows(choice, 'ads');
    const stateFor = choice => consentState(googleAdsId && adsOn(choice) ? 'granted' : 'denied', analyticsOn(choice) ? 'granted' : 'denied');

    window.gtag = gtag;
    gtag('consent', 'default', { ...deniedState, wait_for_update: 500 });

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

    // Carga gtag.js una sola vez y configura cada ID de Google la primera vez que su categoría se acepta.
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

    // Borra las cookies de cada categoría que no está aceptada.
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
      const active = [analyticsOn(choice) && ga4Id, adsOn(choice) && googleAdsId].filter(Boolean);
      if (gtagLoaded) setGoogleDisabled(active);
      gtag('consent', 'update', choice === 'denied' ? deniedState : stateFor(choice));
      if (active.length) loadGoogle(active, fromBanner ? attributedLocation() : '');
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

    const bannerStyles = `
.bza-consent{position:fixed;z-index:90;left:16px;right:16px;bottom:16px;max-width:860px;max-height:calc(100vh - 32px);overflow-y:auto;margin-inline:auto;display:flex;flex-wrap:wrap;align-items:center;gap:16px 28px;padding:18px 20px;background:#F7F7F5;color:#171717;border:1px solid #171717;border-top:4px solid #083D3A;box-shadow:0 18px 40px rgba(23,23,23,.18);font-family:var(--font,Arial,Helvetica,sans-serif);font-size:.875rem;line-height:1.55;animation:bza-consent-in .3s ease-out both}
.bza-consent:focus{outline:none}
.bza-consent p{margin:0;flex:1 1 300px}
.bza-consent-panel{flex:1 1 100%;border-top:1px solid #D6D6CF;padding-top:14px}
.bza-consent-panel fieldset{border:0;margin:0 0 12px;padding:0;display:grid;gap:10px}
.bza-consent-panel legend{font-weight:600;margin-bottom:8px}
.bza-consent-option{display:flex;gap:10px;align-items:flex-start}
.bza-consent-option input{width:20px;height:20px;margin:2px 0 0;accent-color:#083D3A;flex:none}
.bza-consent-option span{display:block}
.bza-consent strong{font-weight:600}
.bza-consent a{color:#083D3A;font-weight:600;text-decoration:underline;text-underline-offset:3px}
.bza-consent-actions{display:flex;gap:10px;flex:none}
.bza-consent button{min-height:44px;min-width:112px;padding:10px 18px;border:1px solid #083D3A;border-radius:0;font:inherit;font-weight:600;cursor:pointer;transition:background .2s,color .2s}
.bza-consent [data-consent-choice="denied"],.bza-consent [data-consent-config],.bza-consent [data-consent-save]{background:transparent;color:#083D3A}
.bza-consent [data-consent-choice="denied"]:hover,.bza-consent [data-consent-config]:hover,.bza-consent [data-consent-save]:hover{background:#E6ECEB}
.bza-consent [data-consent-choice="granted"]{background:#083D3A;color:#F7F7F5}
.bza-consent [data-consent-choice="granted"]:hover{background:#0F5550}
.bza-consent a:focus-visible,.bza-consent button:focus-visible,.bza-consent input:focus-visible{outline:3px solid #D92E22;outline-offset:3px}
html.bza-consent-open{scroll-padding-bottom:var(--bza-consent-space,0px)}
html.bza-consent-open body{padding-bottom:var(--bza-consent-space,0px)}
@keyframes bza-consent-in{from{opacity:0;transform:translateY(16px)}}
@media(max-width:640px){.bza-consent{left:0;right:0;bottom:0;flex-direction:column;align-items:stretch;gap:14px;padding:16px;border-inline:0;border-bottom:0}.bza-consent-actions{flex-wrap:wrap}.bza-consent-actions button{flex:1 1 0;min-width:96px}}
@media(prefers-reduced-motion:reduce){.bza-consent{animation:none}.bza-consent button{transition:none}}
html.motion-paused .bza-consent{animation:none}
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

    const bannerText = () => {
      const tools = [ga4Id && 'Google Analytics', googleAdsId && 'Google Ads', pixelId && 'el píxel de Meta'].filter(Boolean);
      const toolList = tools.length > 1 ? `${tools.slice(0, -1).join(', ')} y ${tools[tools.length - 1]}` : tools[0];
      const remarketing = googleAdsId || pixelId ? ' y para volver a mostrar anuncios de BZA Creative a quienes visitaron el sitio (remarketing)' : '';
      return `<strong>Cookies con tu permiso.</strong> Usamos ${toolList} para medir qué anuncios y páginas generan conversaciones${remarketing}. Nada de eso se carga si no lo aceptas: puedes aceptar todo, rechazar todo o elegir por categoría. <a href="${escapeAttribute(privacyHref())}">Aviso de privacidad</a>`;
    };

    // Casillas de las categorías configuradas; sin marcar por defecto.
    const categoryOptions = () => {
      const options = [];
      if (hasAnalytics) options.push('<label class="bza-consent-option"><input type="checkbox" data-consent-category="analytics"> <span><strong>Analítica.</strong> Google Analytics: qué páginas se visitan y cuáles generan conversaciones.</span></label>');
      if (hasAds) {
        const adTools = [googleAdsId && 'Google Ads', pixelId && 'el píxel de Meta'].filter(Boolean).join(' y ');
        options.push(`<label class="bza-consent-option"><input type="checkbox" data-consent-category="ads"> <span><strong>Publicidad.</strong> ${adTools}: medir nuestros anuncios y volver a mostrarte anuncios de BZA Creative (remarketing).</span></label>`);
      }
      return options.map(option => `\n          ${option}`).join('');
    };

    const reserveSpace = () => {
      const space = banner && banner.isConnected ? banner.getBoundingClientRect().height + 16 : 0;
      document.documentElement.style.setProperty('--bza-consent-space', `${Math.ceil(space)}px`);
    };

    const createBanner = () => {
      const style = document.createElement('style');
      style.textContent = bannerStyles;
      document.head.append(style);

      const element = document.createElement('div');
      element.className = 'bza-consent';
      element.setAttribute('role', 'region');
      element.setAttribute('aria-label', 'Preferencias de cookies');
      element.setAttribute('aria-describedby', 'bza-consent-text');
      element.tabIndex = -1;
      element.innerHTML = `
      <p id="bza-consent-text">${bannerText()}</p>
      <div class="bza-consent-actions">
        <button type="button" data-consent-choice="denied">Rechazar todo</button>
        <button type="button" data-consent-config aria-expanded="false" aria-controls="bza-consent-panel">Configurar</button>
        <button type="button" data-consent-choice="granted">Aceptar todo</button>
      </div>
      <div class="bza-consent-panel" id="bza-consent-panel" data-consent-panel hidden>
        <fieldset>
          <legend>Elige qué permites</legend>
          <label class="bza-consent-option"><input type="checkbox" checked disabled> <span><strong>Necesarias.</strong> Guardan tu elección y el origen de la visita para el mensaje de WhatsApp. Siempre activas.</span></label>${categoryOptions()}
        </fieldset>
        <button type="button" data-consent-save>Guardar selección</button>
      </div>`;
      element.querySelectorAll('[data-consent-choice]').forEach(button => {
        button.addEventListener('click', () => choose(button.dataset.consentChoice));
      });
      const panel = element.querySelector('[data-consent-panel]');
      const configButton = element.querySelector('[data-consent-config]');
      configButton.addEventListener('click', () => {
        panel.hidden = !panel.hidden;
        configButton.setAttribute('aria-expanded', String(!panel.hidden));
        const first = element.querySelector('[data-consent-category]');
        if (!panel.hidden && first) first.focus();
        reserveSpace();
      });
      element.querySelector('[data-consent-save]').addEventListener('click', () => {
        const picked = Array.prototype.filter.call(element.querySelectorAll('[data-consent-category]'), box => box.checked)
          .map(box => box.dataset.consentCategory);
        const analytics = picked.indexOf('analytics') >= 0;
        const ads = picked.indexOf('ads') >= 0;
        choose(analytics && ads ? 'granted' : analytics ? 'analytics' : ads ? 'ads' : 'denied');
      });
      if ('ResizeObserver' in window) spaceObserver = new ResizeObserver(reserveSpace);
      return element;
    };

    const showBanner = focus => {
      banner = banner || createBanner();
      const panel = banner.querySelector('[data-consent-panel]');
      if (panel && !panel.hidden) {
        panel.hidden = true;
        banner.querySelector('[data-consent-config]').setAttribute('aria-expanded', 'false');
      }
      Array.prototype.forEach.call(banner.querySelectorAll('[data-consent-category]'), box => {
        box.checked = allows(consent, box.dataset.consentCategory);
      });
      if (!banner.isConnected) document.body.append(banner);
      document.documentElement.classList.add('bza-consent-open');
      if (spaceObserver) spaceObserver.observe(banner);
      reserveSpace();
      if (focus) banner.focus();
    };

    const hideBanner = () => {
      if (!banner) return;
      const hadFocus = banner.contains(document.activeElement);
      if (spaceObserver) spaceObserver.disconnect();
      banner.remove();
      document.documentElement.classList.remove('bza-consent-open');
      document.documentElement.style.removeProperty('--bza-consent-space');
      // Si el aviso tenía el foco (también cuando lo cierra otra pestaña), vuelve al botón que lo abrió.
      if (hadFocus && returnFocus && returnFocus.isConnected) returnFocus.focus();
      if (hadFocus) returnFocus = null;
    };

    const applyChoice = (value, fromBanner) => {
      consent = value;
      if (value && value !== 'denied') {
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
      if (!consent || consent === 'denied') return;
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
      if (consent && consent !== 'denied') applyPermissions(consent, false);
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
