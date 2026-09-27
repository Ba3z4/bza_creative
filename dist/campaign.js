'use strict';

(() => {
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

  pushEvent('bza_page_view', {
    page_path: window.location.pathname,
    campaign_source: attribution.utm_source || 'direct',
    campaign_medium: attribution.utm_medium || 'none',
    campaign_name: attribution.utm_campaign || 'none'
  });

  document.querySelectorAll('a[href*="wa.me/"]').forEach(link => {
    const source = attribution.utm_source || 'directo';
    const medium = attribution.utm_medium || 'sitio';
    const campaign = attribution.utm_campaign || window.location.pathname.replaceAll('/', '') || 'inicio';
    const baseMessage = link.dataset.message || 'Hola, BZA Creative. Quiero hablar de mi proyecto.';
    const origin = `Origen de la consulta: ${source} / ${medium} / ${campaign}`;

    link.href = `https://wa.me/523342781554?text=${encodeURIComponent(`${baseMessage}\n\n${origin}`)}`;
    link.addEventListener('click', () => {
      pushEvent('whatsapp_click', {
        link_text: clean(link.textContent),
        page_path: window.location.pathname,
        campaign_source: source,
        campaign_medium: medium,
        campaign_name: campaign
      });
    });
  });
})();
