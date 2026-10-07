'use strict';

(() => {
  // Medición con consentimiento. Pega aquí los IDs para activarla. Mientras todos estén vacíos, el sitio
  // no muestra el aviso, no usa localStorage y no carga ninguna etiqueta de Google ni de Meta.
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
  const clean = value => String(value || '').trim().slice(0, 180);
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
  const measuring = googleIds.length > 0 || Boolean(pixelId);

  const CONSENT_KEY = 'bza_consent';
  let consent = null;
  let tagsLoaded = false;
  let banner = null;
  let returnFocus = null;

  function gtag() {
    window.dataLayer.push(arguments);
  }
  const consentState = value => ({
    ad_storage: value,
    ad_user_data: value,
    ad_personalization: value,
    analytics_storage: value
  });

  if (measuring) {
    window.gtag = gtag;
    gtag('consent', 'default', { ...consentState('denied'), wait_for_update: 500 });
  }

  pushEvent('bza_page_view', {
    page_path: window.location.pathname,
    campaign_source: attribution.utm_source || 'direct',
    campaign_medium: attribution.utm_medium || 'none',
    campaign_name: attribution.utm_campaign || 'none'
  });

  const readChoice = () => {
    try {
      const value = localStorage.getItem(CONSENT_KEY);
      return value === 'granted' || value === 'denied' ? value : null;
    } catch {
      return null;
    }
  };
  const saveChoice = value => {
    try {
      if (value) localStorage.setItem(CONSENT_KEY, value);
      else localStorage.removeItem(CONSENT_KEY);
    } catch {
      // Sin almacenamiento, la elección vale solo para esta página.
    }
  };

  const loadScript = src => {
    const script = document.createElement('script');
    script.async = true;
    script.src = src;
    document.head.append(script);
  };

  // Si la visita llegó desde un anuncio y acepta en otra página, se le pasa a Google el origen guardado en la sesión.
  const attributedLocation = () => {
    const keys = trackedKeys.filter(key => attribution[key]);
    if (!keys.length || trackedKeys.some(key => params.has(key))) return '';
    const url = new URL(window.location.href);
    keys.forEach(key => url.searchParams.set(key, attribution[key]));
    return url.href;
  };

  const loadMetaPixel = () => {
    if (!window.fbq) {
      const fbq = function fbq() {
        if (fbq.callMethod) fbq.callMethod.apply(fbq, arguments);
        else fbq.queue.push(arguments);
      };
      Object.assign(fbq, { push: fbq, loaded: true, version: '2.0', queue: [] });
      window.fbq = fbq;
      if (!window._fbq) window._fbq = fbq;
      loadScript('https://connect.facebook.net/en_US/fbevents.js');
    }
    window.fbq('init', pixelId);
    window.fbq('track', 'PageView');
  };

  const loadTags = pageLocation => {
    if (tagsLoaded) return;
    tagsLoaded = true;
    if (googleIds.length) {
      loadScript(`https://www.googletagmanager.com/gtag/js?id=${encodeURIComponent(googleIds[0])}`);
      gtag('js', new Date());
      googleIds.forEach(id => gtag('config', id, pageLocation ? { page_location: pageLocation } : {}));
    }
    if (pixelId) loadMetaPixel();
  };

  const clearMeasurementCookies = () => {
    const names = document.cookie
      .split(';')
      .map(cookie => cookie.split('=')[0].trim())
      .filter(name => /^(_ga|_gid|_gat|_gcl_|_fbp|_fbc)/.test(name));
    if (!names.length) return;
    const parts = window.location.hostname.split('.');
    const domains = [''];
    for (let index = 0; index < parts.length - 1; index++) domains.push(`; domain=.${parts.slice(index).join('.')}`);
    names.forEach(name => domains.forEach(domain => {
      document.cookie = `${name}=; Max-Age=0; path=/${domain}`;
    }));
  };

  const grant = fromBanner => {
    gtag('consent', 'update', consentState('granted'));
    if (tagsLoaded) {
      if (pixelId) window.fbq('consent', 'grant');
      return;
    }
    loadTags(fromBanner ? attributedLocation() : '');
  };

  const deny = () => {
    gtag('consent', 'update', consentState('denied'));
    if (tagsLoaded && pixelId) window.fbq('consent', 'revoke');
    clearMeasurementCookies();
  };

  const bannerStyles = `
.bza-consent{position:fixed;z-index:90;left:16px;right:16px;bottom:16px;max-width:780px;margin-inline:auto;display:flex;align-items:center;gap:16px 28px;padding:18px 20px;background:#F7F7F5;color:#171717;border:1px solid #171717;border-top:4px solid #083D3A;box-shadow:0 18px 40px rgba(23,23,23,.18);font-family:var(--font,Arial,Helvetica,sans-serif);font-size:.875rem;line-height:1.55;animation:bza-consent-in .3s ease-out both}
.bza-consent:focus{outline:none}
.bza-consent p{margin:0;flex:1 1 auto}
.bza-consent strong{font-weight:600}
.bza-consent a{color:#083D3A;font-weight:600;text-decoration:underline;text-underline-offset:3px}
.bza-consent-actions{display:flex;gap:10px;flex:none}
.bza-consent button{min-height:44px;min-width:112px;padding:10px 18px;border:1px solid #083D3A;border-radius:0;font:inherit;font-weight:600;cursor:pointer;transition:background .2s,color .2s}
.bza-consent [data-consent-choice="denied"]{background:transparent;color:#083D3A}
.bza-consent [data-consent-choice="denied"]:hover{background:#E6ECEB}
.bza-consent [data-consent-choice="granted"]{background:#083D3A;color:#F7F7F5}
.bza-consent [data-consent-choice="granted"]:hover{background:#0F5550}
.bza-consent a:focus-visible,.bza-consent button:focus-visible{outline:3px solid #D92E22;outline-offset:3px}
html.bza-consent-open{scroll-padding-bottom:var(--bza-consent-space,0px)}
html.bza-consent-open body{padding-bottom:var(--bza-consent-space,0px)}
@keyframes bza-consent-in{from{opacity:0;transform:translateY(16px)}}
@media(max-width:640px){.bza-consent{left:0;right:0;bottom:0;flex-direction:column;align-items:stretch;gap:14px;padding:16px;border-inline:0;border-bottom:0}.bza-consent-actions button{flex:1 1 0;min-width:0}}
@media(prefers-reduced-motion:reduce){.bza-consent{animation:none}.bza-consent button{transition:none}}
html.motion-paused .bza-consent{animation:none}
@media print{.bza-consent{display:none}}`;

  const toolNames = [ga4Id && 'Google Analytics', googleAdsId && 'Google Ads', pixelId && 'el píxel de Meta'].filter(Boolean);
  const toolList = toolNames.length > 1 ? `${toolNames.slice(0, -1).join(', ')} y ${toolNames.at(-1)}` : toolNames[0];

  let spaceObserver = null;
  const reserveSpace = () => {
    const space = banner?.isConnected ? banner.getBoundingClientRect().height + 16 : 0;
    document.documentElement.style.setProperty('--bza-consent-space', `${Math.ceil(space)}px`);
  };

  const createBanner = () => {
    const style = document.createElement('style');
    style.textContent = bannerStyles;
    document.head.append(style);

    const element = document.createElement('div');
    element.className = 'bza-consent';
    element.setAttribute('role', 'region');
    element.setAttribute('aria-label', 'Preferencias de medición');
    element.setAttribute('aria-describedby', 'bza-consent-text');
    element.tabIndex = -1;
    element.innerHTML = `
      <p id="bza-consent-text"><strong>Medición con tu permiso.</strong> Usamos ${toolList} solo para medir qué anuncios y páginas generan conversaciones. Si rechazas, no se cargan. <a href="/privacidad/#sitio-web">Aviso de privacidad</a></p>
      <div class="bza-consent-actions">
        <button type="button" data-consent-choice="denied">Rechazar</button>
        <button type="button" data-consent-choice="granted">Aceptar</button>
      </div>`;
    element.querySelectorAll('[data-consent-choice]').forEach(button => {
      button.addEventListener('click', () => choose(button.dataset.consentChoice));
    });
    if ('ResizeObserver' in window) spaceObserver = new ResizeObserver(reserveSpace);
    return element;
  };

  const showBanner = focus => {
    banner = banner || createBanner();
    if (!banner.isConnected) document.body.append(banner);
    document.documentElement.classList.add('bza-consent-open');
    spaceObserver?.observe(banner);
    reserveSpace();
    if (focus) banner.focus();
  };

  const hideBanner = () => {
    if (!banner) return;
    spaceObserver?.disconnect();
    banner.remove();
    document.documentElement.classList.remove('bza-consent-open');
    document.documentElement.style.removeProperty('--bza-consent-space');
  };

  const choose = value => {
    consent = value === 'granted' ? 'granted' : 'denied';
    saveChoice(consent);
    hideBanner();
    if (consent === 'granted') grant(true);
    else deny();
    if (returnFocus?.isConnected) returnFocus.focus();
    returnFocus = null;
  };

  const trackWhatsapp = details => {
    if (consent !== 'granted') return;
    if (ga4Id) gtag('event', 'whatsapp_click', { ...details, send_to: ga4Id });
    if (googleAdsId && adsLabel) gtag('event', 'conversion', { send_to: `${googleAdsId}/${adsLabel}` });
    if (pixelId) window.fbq('track', 'Contact');
  };

  document.querySelectorAll('a[href*="wa.me/"]').forEach(link => {
    const source = attribution.utm_source || 'directo';
    const medium = attribution.utm_medium || 'sitio';
    const campaign = attribution.utm_campaign || window.location.pathname.replaceAll('/', '') || 'inicio';
    const baseMessage = link.dataset.message || 'Hola, BZA Creative. Quiero hablar de mi proyecto.';
    const origin = `Origen de la consulta: ${source} / ${medium} / ${campaign}`;

    link.href = `https://wa.me/523342781554?text=${encodeURIComponent(`${baseMessage}\n\n${origin}`)}`;
    link.addEventListener('click', () => {
      const details = {
        link_text: clean(link.textContent),
        page_path: window.location.pathname,
        campaign_source: source,
        campaign_medium: medium,
        campaign_name: campaign
      };
      pushEvent('whatsapp_click', details);
      trackWhatsapp(details);
    });
  });

  if (!measuring) return;

  consent = readChoice();
  if (consent === 'granted') grant(false);
  else if (!consent) showBanner(false);

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
})();
