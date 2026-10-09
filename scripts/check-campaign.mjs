// Prueba dist/campaign.js sin navegador ni dependencias: ejecuta el script en node:vm con un DOM mínimo simulado.
// Comprueba que, con los IDs vacíos, el sitio se comporta igual que antes (UTM, dataLayer y mensaje de WhatsApp,
// sin aviso ni etiquetas) y que, con IDs de prueba, el aviso de consentimiento controla GA4, Google Ads y el píxel de Meta.
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import vm from 'node:vm';

const source = await readFile(new URL('../dist/campaign.js', import.meta.url), 'utf8');
const block = source.match(/const MEASUREMENT = \{[\s\S]*?\};/);
assert.ok(block, 'campaign.js declares const MEASUREMENT = { ... }');

// 0. No se publica medición mientras el aviso de privacidad diga que no la hay.
const publishedIds = vm.runInNewContext(`(${block[0].replace(/^const MEASUREMENT = /, '').replace(/;$/, '')})`);
const configuredIds = Object.keys(publishedIds).filter(name => String(publishedIds[name] || '').trim());
if (configuredIds.length) {
  const privacy = (await readFile(new URL('../dist/privacidad/index.html', import.meta.url), 'utf8'))
    .replace(/&iacute;/g, 'í')
    .replace(/\s+/g, ' ');
  const contradiction = ['no usa herramientas de analítica', 'no hay herramientas de analítica']
    .find(phrase => privacy.toLowerCase().includes(phrase));
  if (contradiction) {
    console.error([
      `ERROR: la medición está ACTIVA en dist/campaign.js (${configuredIds.join(', ')}), pero dist/privacidad/index.html`,
      `todavía dice «${contradiction}».`,
      'Antes de publicar los IDs, actualiza la sección 04 «Este sitio y la medición» de /privacidad/: qué herramientas se usan',
      '(Google Analytics, Google Ads, píxel de Meta), para qué (medir conversaciones y remarketing) y cómo cambiar la elección.',
      'O deja los IDs vacíos en dist/campaign.js hasta que el aviso esté actualizado.'
    ].join('\n'));
    process.exit(1);
  }
}

// La sintaxis no debe ser más nueva que la del campaign.js original (replaceAll, catch sin variable, spread):
// en Safari/iOS viejos un error de sintaxis o un método inexistente rompería también el origen de WhatsApp.
const code = source.replace(/\/\/.*$/gm, '');
assert.doesNotMatch(code, /\.at\(/, 'campaign.js no usa Array.prototype.at');
assert.doesNotMatch(code, /\.replaceAll\(/, 'campaign.js no usa String.prototype.replaceAll (Safari/iOS anteriores a 13.4)');
assert.doesNotMatch(code, /\?\.(?!\d)|\?\?|\|\|=|&&=/, 'campaign.js no usa ?. ?? ||= ni &&=');

const withIds = ids => source.replace(block[0], `const MEASUREMENT = ${JSON.stringify({ ga4Id: '', googleAdsId: '', googleAdsWhatsappLabel: '', metaPixelId: '', ...ids })};`);
const plain = value => JSON.parse(JSON.stringify(value));
const isArgs = entry => Object.prototype.toString.call(entry) === '[object Arguments]';
const last = list => list[list.length - 1];

class FakeElement {
  constructor(tagName, owner) {
    Object.assign(this, { tagName: tagName.toUpperCase(), owner, children: [], parent: null, listeners: {}, attributes: {}, dataset: {}, hidden: false, textContent: '', className: '', choices: [] });
    const classes = new Set();
    this.classList = { add: name => classes.add(name), remove: name => classes.delete(name), contains: name => classes.has(name) };
    const props = {};
    this.style = { setProperty: (name, value) => { props[name] = value; }, removeProperty: name => delete props[name], getPropertyValue: name => props[name] || '' };
  }
  setAttribute(name, value) { this.attributes[name] = String(value); }
  getAttribute(name) { return this.attributes[name] ?? null; }
  addEventListener(type, listener) { (this.listeners[type] ||= []).push(listener); }
  click() { (this.listeners.click || []).forEach(listener => listener({ target: this })); }
  append(...nodes) { nodes.forEach(node => { node.parent = this; this.children.push(node); }); }
  remove() { if (this.parent) this.parent.children = this.parent.children.filter(child => child !== this); this.parent = null; }
  get isConnected() { let node = this; while (node.parent) node = node.parent; return node === this.owner.documentElement; }
  focus() { this.owner.activeElement = this; }
  contains(node) {
    if (this.choices.includes(node)) return true;
    for (let current = node; current; current = current.parent) if (current === this) return true;
    return false;
  }
  getBoundingClientRect() { return { height: 150 }; }
  set innerHTML(html) {
    this.html = html;
    this.choices = [...html.matchAll(/<button[^>]*data-consent-choice="([^"]+)"[^>]*>([^<]*)<\/button>/g)].map(([, choice, label]) => {
      const button = new FakeElement('button', this.owner);
      Object.assign(button.dataset, { consentChoice: choice });
      button.textContent = label;
      return button;
    });
  }
  get innerHTML() { return this.html || ''; }
  querySelectorAll(selector) { return selector === '[data-consent-choice]' ? this.choices : []; }
}

// Cookies por (nombre, dominio), como el navegador: una cookie con Domain solo se borra con el mismo Domain.
function cookieJar(host, seeded) {
  const entries = new Map();
  const matches = domain => !domain || host === domain || host.endsWith(`.${domain}`);
  const store = (name, value, domain) => entries.set(`${name}\n${domain}`, { name, value, domain });
  seeded.forEach(([name, value, domain = '']) => store(name, value, domain.replace(/^\./, '').toLowerCase()));
  return {
    list: () => [...entries.values()].map(({ name, domain }) => `${name}@${domain ? `.${domain}` : 'host-only'}`).sort(),
    get: () => [...entries.values()].filter(({ domain }) => matches(domain)).map(({ name, value }) => `${name}=${value}`).join('; '),
    set: text => {
      const [pair, ...attributes] = text.split(';');
      const separator = pair.indexOf('=');
      const name = pair.slice(0, separator).trim();
      let domain = '';
      let expired = false;
      attributes.forEach(attribute => {
        const [key, ...rest] = attribute.split('=');
        const setting = rest.join('=').trim();
        if (/^domain$/i.test(key.trim())) domain = setting.replace(/^\./, '').toLowerCase();
        if (/^max-age$/i.test(key.trim()) && Number(setting) <= 0) expired = true;
        if (/^expires$/i.test(key.trim()) && Date.parse(setting) <= Date.now()) expired = true;
      });
      // El navegador rechaza un Domain ajeno a la página o que sea solo un dominio de nivel superior.
      if (domain && (!domain.includes('.') || !matches(domain))) return;
      const id = `${name}\n${domain}`;
      if (expired) entries.delete(id);
      else store(name, pair.slice(separator + 1).trim(), domain);
    }
  };
}

function run({
  ids = {},
  measurementBlock = null,
  url = 'https://bzacreative.com/campana/?utm_source=google&utm_medium=cpc&utm_campaign=test',
  local = {},
  session = {},
  links = 2,
  resets = 0,
  cookies = [],
  scriptSrc = 'https://bzacreative.com/campaign.js',
  localStorageThrows = false,
  localStorageWriteThrows = false,
  createElementThrows = false
} = {}) {
  const log = [];
  // broken = true simula un almacenamiento que deja de funcionar después de cargar (datos del sitio bloqueados).
  const storage = (name, initial, writeThrows = false) => {
    const map = new Map(Object.entries(initial));
    const api = {
      map,
      broken: false,
      getItem: key => { log.push(`${name}.get:${key}`); if (api.broken) throw new Error('SecurityError'); return map.has(key) ? map.get(key) : null; },
      setItem: (key, value) => { log.push(`${name}.set:${key}`); if (writeThrows || api.broken) throw new Error('QuotaExceededError'); map.set(key, String(value)); },
      removeItem: key => { log.push(`${name}.remove:${key}`); if (writeThrows || api.broken) throw new Error('QuotaExceededError'); map.delete(key); }
    };
    return api;
  };
  const created = [];
  const location = new URL(url);
  const jar = cookieJar(location.hostname, cookies);
  const document = {
    activeElement: null,
    currentScript: scriptSrc === null ? null : { src: scriptSrc },
    createElement: tag => {
      if (createElementThrows) throw new Error('createElement roto');
      const element = new FakeElement(tag, document);
      created.push(element);
      return element;
    },
    querySelectorAll: selector => (selector === 'a[href*="wa.me/"]' ? document.links : selector === '[data-consent-reset]' ? document.resets : []),
    get cookie() { return jar.get(); },
    set cookie(value) { jar.set(value); }
  };
  document.documentElement = new FakeElement('html', document);
  document.head = new FakeElement('head', document);
  document.body = new FakeElement('body', document);
  document.documentElement.append(document.head, document.body);
  document.links = Array.from({ length: links }, (_, index) => {
    const link = new FakeElement('a', document);
    link.href = 'https://wa.me/523342781554';
    link.textContent = `  WhatsApp ${index}  `;
    if (index === 0) link.dataset.message = 'Hola, BZA Creative. Quiero solicitar el diagnóstico inicial de mi negocio.';
    return link;
  });
  document.resets = Array.from({ length: resets }, () => Object.assign(new FakeElement('button', document), { hidden: true }));
  const main = new FakeElement('main', document);
  main.append(...document.links, ...document.resets);
  document.body.append(main);
  const windowListeners = {};
  const sandbox = {
    document,
    console: { warn: (...parts) => log.push(`warn:${parts.join(' ')}`) },
    URL,
    URLSearchParams,
    addEventListener: (type, listener) => (windowListeners[type] ||= []).push(listener)
  };
  Object.assign(sandbox, { window: sandbox, location, sessionStorage: storage('sessionStorage', session) });
  const localStorage = storage('localStorage', local, localStorageWriteThrows);
  if (localStorageThrows) {
    Object.defineProperty(sandbox, 'localStorage', { get() { log.push('localStorage.blocked'); throw new Error('SecurityError'); } });
  } else {
    sandbox.localStorage = localStorage;
  }
  vm.createContext(sandbox);
  // Como Safari/iOS anteriores a 15.4: sin Array.prototype.at ni String.prototype.at.
  vm.runInContext('delete Array.prototype.at; delete String.prototype.at; delete String.prototype.replaceAll;', sandbox);
  let script = withIds(ids);
  if (ids === null) script = source;
  if (measurementBlock) script = source.replace(block[0], measurementBlock);
  vm.runInContext(script, sandbox, { filename: 'campaign.js' });
  const gtagCalls = command => plain(sandbox.dataLayer.filter(isArgs).map(entry => Array.from(entry))).filter(call => call[0] === command);
  const events = name => plain(sandbox.dataLayer.filter(entry => !isArgs(entry) && entry.event === name));
  const banner = () => document.body.children.find(child => child.className === 'bza-consent');
  const bannerText = () => banner().innerHTML.match(/<p id="bza-consent-text">([\s\S]*?)<\/p>/)[1];
  const scripts = () => document.head.children.filter(child => child.tagName === 'SCRIPT').map(child => child.src);
  const choose = label => banner().choices.find(button => button.textContent === label).click();
  const fbqQueue = () => plain((sandbox.fbq?.queue || []).map(args => Array.from(args)));
  const fire = (type, event) => (windowListeners[type] || []).forEach(listener => listener(event));
  const disabled = id => sandbox[`ga-disable-${id}`];
  // Lo que se envía a Google y Meta: eventos gtag y cola de fbq, para comparar antes y después de un clic.
  const sent = () => ({ gtag: gtagCalls('event').length, fbq: fbqQueue().filter(call => call[0] === 'track').length });
  return { sandbox, document, log, created, jar, localStorage, windowListeners, gtagCalls, events, banner, bannerText, scripts, choose, fbqQueue, fire, disabled, sent };
}

const denied = { ad_storage: 'denied', ad_user_data: 'denied', ad_personalization: 'denied', analytics_storage: 'denied' };
const granted = { ad_storage: 'granted', ad_user_data: 'granted', ad_personalization: 'granted', analytics_storage: 'granted' };
const testIds = { ga4Id: 'G-TEST123', googleAdsId: 'AW-123', googleAdsWhatsappLabel: 'abc', metaPixelId: '123' };
const origin = encodeURIComponent('Origen de la consulta: google / cpc / test');
const hrefFor = message => `https://wa.me/523342781554?text=${encodeURIComponent(message)}%0A%0A${origin}`;
const diagnosis = 'Hola, BZA Creative. Quiero solicitar el diagnóstico inicial de mi negocio.';
const general = 'Hola, BZA Creative. Quiero hablar de mi proyecto.';
const privacyLink = '<a href="https://bzacreative.com/privacidad/#sitio-web">Aviso de privacidad</a>';
const remarketing = ' y para volver a mostrar anuncios de BZA Creative a quienes visitaron el sitio (remarketing)';
const expectedText = (tools, withRemarketing, link = privacyLink) =>
  `<strong>Medición con tu permiso.</strong> Usamos ${tools} para medir qué anuncios y páginas generan conversaciones${withRemarketing ? remarketing : ''}. Si rechazas, no se cargan. ${link}`;

// Atribución completa de WhatsApp: hrefs con el origen, bza_page_view y whatsapp_click en dataLayer.
const assertAttribution = (env, label) => {
  assert.equal(env.document.links[0].href, hrefFor(diagnosis), `${label}: href con origen`);
  assert.equal(env.document.links[1].href, hrefFor(general), `${label}: href con origen`);
  assert.deepEqual(env.events('bza_page_view'), [{ event: 'bza_page_view', page_path: '/campana/', campaign_source: 'google', campaign_medium: 'cpc', campaign_name: 'test' }], `${label}: bza_page_view`);
  const before = env.events('whatsapp_click').length;
  assert.doesNotThrow(() => env.document.links[0].click(), `${label}: el clic no lanza errores`);
  assert.deepEqual(last(env.events('whatsapp_click')), { event: 'whatsapp_click', link_text: 'WhatsApp 0', page_path: '/campana/', campaign_source: 'google', campaign_medium: 'cpc', campaign_name: 'test' }, `${label}: whatsapp_click`);
  assert.equal(env.events('whatsapp_click').length, before + 1, `${label}: un whatsapp_click por clic`);
};

// 1. IDs vacíos: comportamiento original, sin aviso, sin etiquetas y sin tocar localStorage.
{
  const env = run({ resets: 1 });
  assert.equal(vm.runInContext('typeof [].at', env.sandbox), 'undefined', 'la prueba simula un navegador sin Array.prototype.at');
  assert.deepEqual(env.log.filter(entry => entry.startsWith('localStorage')), [], 'IDs vacíos: no usa localStorage');
  assert.deepEqual(env.log.filter(entry => entry.startsWith('warn:')), [], 'IDs vacíos: sin avisos en consola');
  assert.deepEqual(env.created, [], 'IDs vacíos: no crea elementos');
  assert.deepEqual(Object.keys(env.windowListeners), [], 'IDs vacíos: sin escuchas en window');
  assert.equal(env.document.body.children.length, 1, 'IDs vacíos: sin aviso');
  assert.equal(env.document.head.children.length, 0, 'IDs vacíos: sin estilos ni scripts');
  assert.equal(env.sandbox.gtag, undefined, 'IDs vacíos: sin gtag');
  assert.equal(env.sandbox.fbq, undefined, 'IDs vacíos: sin fbq');
  assert.equal(env.document.resets[0].hidden, true, 'IDs vacíos: el botón de preferencias sigue oculto');
  const saved = JSON.parse(env.sandbox.sessionStorage.map.get('bza_campaign'));
  assert.deepEqual([saved.utm_source, saved.utm_medium, saved.utm_campaign, saved.landing_path], ['google', 'cpc', 'test', '/campana/']);
  assert.deepEqual(plain(env.sandbox.dataLayer), [{ event: 'bza_page_view', page_path: '/campana/', campaign_source: 'google', campaign_medium: 'cpc', campaign_name: 'test' }]);
  assertAttribution(env, 'IDs vacíos');
  assert.equal(env.sandbox.dataLayer.filter(isArgs).length, 0, 'IDs vacíos: sin comandos gtag');
  assert.equal(env.sandbox.dataLayer.length, 2, 'IDs vacíos: solo bza_page_view y whatsapp_click');
  const direct = run({ url: 'https://bzacreative.com/servicios/' });
  assert.ok(direct.document.links[1].href.endsWith(encodeURIComponent('Origen de la consulta: directo / sitio / servicios')), 'origen directo');
  const home = run({ url: 'https://bzacreative.com/', scriptSrc: null });
  assert.ok(home.document.links[1].href.endsWith(encodeURIComponent('Origen de la consulta: directo / sitio / inicio')), 'origen en inicio');
}

// 2. Con IDs: consentimiento denegado por defecto y aviso visible; nada se carga antes de elegir.
{
  const env = run({ ids: testIds });
  assert.ok(isArgs(env.sandbox.dataLayer[0]), 'consent default es lo primero en dataLayer');
  assert.deepEqual(plain(Array.from(env.sandbox.dataLayer[0])), ['consent', 'default', { ...denied, wait_for_update: 500 }]);
  assert.equal(env.sandbox.dataLayer[1].event, 'bza_page_view', 'bza_page_view va después de consent default');
  const banner = env.banner();
  assert.ok(banner, 'aviso visible');
  assert.equal(banner.getAttribute('role'), 'region');
  assert.equal(banner.getAttribute('aria-label'), 'Preferencias de medición');
  assert.equal(env.bannerText(), expectedText('Google Analytics, Google Ads y el píxel de Meta', true));
  assert.deepEqual(banner.choices.map(button => button.textContent), ['Rechazar', 'Aceptar']);
  assert.deepEqual(env.scripts(), [], 'sin etiquetas antes de elegir');
  assertAttribution(env, 'IDs antes de elegir');
  assert.deepEqual(env.gtagCalls('event'), [], 'sin eventos antes de elegir');

  env.choose('Aceptar');
  assert.equal(env.localStorage.map.get('bza_consent'), 'granted');
  assert.equal(env.banner(), undefined, 'el aviso se cierra');
  assert.deepEqual(env.scripts(), ['https://www.googletagmanager.com/gtag/js?id=G-TEST123', 'https://connect.facebook.net/en_US/fbevents.js']);
  assert.deepEqual(last(env.gtagCalls('consent')), ['consent', 'update', granted]);
  assert.deepEqual(env.gtagCalls('config').map(call => call[1]), ['G-TEST123', 'AW-123']);
  assert.deepEqual(env.fbqQueue(), [['init', '123'], ['track', 'PageView']]);
  env.document.links[1].click();
  assert.deepEqual(env.gtagCalls('event'), [
    ['event', 'whatsapp_click', { link_text: 'WhatsApp 1', page_path: '/campana/', campaign_source: 'google', campaign_medium: 'cpc', campaign_name: 'test', send_to: 'G-TEST123' }],
    ['event', 'conversion', { send_to: 'AW-123/abc' }]
  ]);
  assert.deepEqual(last(env.fbqQueue()), ['track', 'Contact']);
  assert.equal(env.events('whatsapp_click').length, 2, 'dataLayer conserva whatsapp_click');
}

// 3. Elección guardada: aceptada carga sin aviso; rechazada no carga nada.
{
  const accepted = run({ ids: testIds, local: { bza_consent: 'granted' } });
  assert.equal(accepted.banner(), undefined);
  assert.equal(accepted.scripts().length, 2);
  const rejected = run({ ids: testIds });
  rejected.choose('Rechazar');
  assert.equal(rejected.localStorage.map.get('bza_consent'), 'denied');
  assert.deepEqual(rejected.scripts(), []);
  rejected.document.links[0].click();
  assert.deepEqual(rejected.gtagCalls('event'), []);
  const later = run({ ids: testIds, local: { bza_consent: 'denied' } });
  assert.equal(later.banner(), undefined);
  assert.deepEqual(later.scripts(), []);
}

// 4. Aceptar en otra página: Google recibe el origen de la sesión.
{
  const env = run({ ids: testIds, url: 'https://bzacreative.com/servicios/', session: { bza_campaign: JSON.stringify({ utm_source: 'google', utm_medium: 'cpc', utm_campaign: 'test', gclid: 'abc' }) } });
  env.choose('Aceptar');
  const location = new URL(env.gtagCalls('config')[0][2].page_location);
  assert.deepEqual([location.pathname, location.searchParams.get('utm_campaign'), location.searchParams.get('gclid')], ['/servicios/', 'test', 'abc']);
}

// 5. [data-consent-reset]: visible con IDs, borra la elección, vuelve a denegar, detiene gtag.js y muestra el aviso.
{
  const env = run({ ids: testIds, local: { bza_consent: 'granted' }, resets: 1, cookies: [['_ga', 'GA1.1', '.bzacreative.com'], ['_ga_TEST123', 'GS1', '.bzacreative.com'], ['_gcl_au', '1', '.bzacreative.com'], ['_fbp', 'fb', '.bzacreative.com'], ['keep', '1']] });
  const reset = env.document.resets[0];
  assert.equal(reset.hidden, false, 'botón de preferencias visible');
  assert.equal(env.disabled('G-TEST123'), undefined, 'gtag.js activo al cargar con permiso');
  reset.click();
  assert.equal(env.localStorage.map.has('bza_consent'), false);
  assert.deepEqual(last(env.gtagCalls('consent')), ['consent', 'update', denied]);
  assert.deepEqual(env.fbqQueue()[0], ['consent', 'revoke'], 'la revocación queda primero en la cola del píxel');
  assert.ok(!env.fbqQueue().some(call => /^track/.test(call[0])), 'sin eventos de Meta pendientes tras retirar');
  assert.deepEqual([env.disabled('G-TEST123'), env.disabled('AW-123')], [true, true], 'ga-disable al retirar el permiso');
  assert.deepEqual(env.jar.list(), ['keep@host-only'], 'borra cookies de medición');
  assert.ok(env.document.activeElement === env.banner(), 'el foco pasa al aviso');
  env.choose('Rechazar');
  assert.ok(env.document.activeElement === reset, 'el foco regresa al botón');
  assert.deepEqual([env.disabled('G-TEST123'), env.disabled('AW-123')], [true, true], 'ga-disable sigue al rechazar');
  reset.click();
  env.choose('Aceptar');
  assert.equal(env.scripts().length, 2, 'no duplica etiquetas');
  assert.deepEqual(last(env.fbqQueue()), ['consent', 'grant']);
  assert.deepEqual([env.disabled('G-TEST123'), env.disabled('AW-123')], [false, false], 'ga-disable se quita al volver a aceptar');
  assert.deepEqual(last(env.gtagCalls('consent')), ['consent', 'update', granted]);
}

// 6. IDs mal escritos se ignoran con aviso en consola; send_to completo como etiqueta también funciona.
{
  const env = run({ ids: { ga4Id: 'UA-1', googleAdsId: ' AW-555 ', googleAdsWhatsappLabel: 'AW-555/xYz-9' } });
  assert.ok(env.log.some(entry => entry.startsWith('warn:') && entry.includes('ga4Id')));
  env.choose('Aceptar');
  assert.deepEqual(env.scripts(), ['https://www.googletagmanager.com/gtag/js?id=AW-555']);
  env.document.links[0].click();
  assert.deepEqual(env.gtagCalls('event'), [['event', 'conversion', { send_to: 'AW-555/xYz-9' }]]);
  const labelOnly = run({ ids: { googleAdsWhatsappLabel: 'abc' } });
  assert.ok(labelOnly.log.some(entry => entry.startsWith('warn:') && entry.includes('googleAdsId')), 'etiqueta sin googleAdsId avisa');
  assert.equal(labelOnly.banner(), undefined, 'solo la etiqueta no activa la medición');
  assert.deepEqual(labelOnly.log.filter(entry => entry.startsWith('localStorage')), [], 'solo la etiqueta: no usa localStorage');
}

// 7. Aceptar concede solo lo que usan las herramientas configuradas; el aviso lo dice tal cual.
{
  const ga4 = run({ ids: { ga4Id: 'G-TEST123' } });
  assert.equal(ga4.bannerText(), expectedText('Google Analytics', false), 'solo GA4: sin remarketing en el aviso');
  ga4.choose('Aceptar');
  assert.deepEqual(last(ga4.gtagCalls('consent')), ['consent', 'update', { ...denied, analytics_storage: 'granted' }], 'solo GA4: ad_* siguen denegados');

  const ads = run({ ids: { googleAdsId: 'AW-123', googleAdsWhatsappLabel: 'abc' } });
  assert.equal(ads.bannerText(), expectedText('Google Ads', true), 'Google Ads: aviso con remarketing');
  ads.choose('Aceptar');
  assert.deepEqual(last(ads.gtagCalls('consent')), ['consent', 'update', { ...granted, analytics_storage: 'denied' }], 'solo Google Ads: analytics_storage sigue denegado');

  const pixel = run({ ids: { metaPixelId: '123' } });
  assert.equal(pixel.bannerText(), expectedText('el píxel de Meta', true), 'píxel: aviso con remarketing');
  pixel.choose('Aceptar');
  assert.deepEqual(last(pixel.gtagCalls('consent')), ['consent', 'update', denied], 'solo píxel: nada de Google se concede');
  assert.deepEqual(pixel.scripts(), ['https://connect.facebook.net/en_US/fbevents.js']);

  const ga4Ads = run({ ids: { ga4Id: 'G-TEST123', googleAdsId: 'AW-123' } });
  assert.equal(ga4Ads.bannerText(), expectedText('Google Analytics y Google Ads', true));
  ga4Ads.choose('Rechazar');
  assert.deepEqual(last(ga4Ads.gtagCalls('consent')), ['consent', 'update', denied], 'Rechazar deniega todo');
}

// 8. Enlace al aviso de privacidad: relativo a la URL de campaign.js; sin ella, la ruta del sitio.
{
  const preview = run({ ids: { ga4Id: 'G-TEST123' }, url: 'https://preview.example.dev/sitio/campana/', scriptSrc: 'https://preview.example.dev/sitio/campaign.js' });
  assert.match(preview.bannerText(), /<a href="https:\/\/preview\.example\.dev\/sitio\/privacidad\/#sitio-web">Aviso de privacidad<\/a>$/);
  for (const scriptSrc of [null, '', 'no es una url']) {
    const fallback = run({ ids: { ga4Id: 'G-TEST123' }, scriptSrc });
    assert.match(fallback.bannerText(), /<a href="\/privacidad\/#sitio-web">Aviso de privacidad<\/a>$/, `sin URL del script (${JSON.stringify(scriptSrc)})`);
  }
}

// 9. Retiro del permiso en otra página y regreso con "atrás" (bfcache): pageshow con persisted vuelve a leer la elección.
{
  const env = run({ ids: testIds, local: { bza_consent: 'granted' } });
  env.localStorage.map.set('bza_consent', 'denied');
  env.fire('pageshow', { persisted: false });
  assert.notDeepEqual(last(env.gtagCalls('consent')), ['consent', 'update', denied], 'pageshow normal no resincroniza');
  env.fire('pageshow', { persisted: true });
  assert.deepEqual(last(env.gtagCalls('consent')), ['consent', 'update', denied], 'bfcache: aplica el rechazo');
  assert.deepEqual(env.fbqQueue()[0], ['consent', 'revoke'], 'bfcache: revocación primero en la cola del píxel');
  assert.ok(!env.fbqQueue().some(call => /^track/.test(call[0])), 'bfcache: sin eventos de Meta pendientes');
  assert.deepEqual([env.disabled('G-TEST123'), env.disabled('AW-123')], [true, true], 'bfcache: ga-disable');
  assert.equal(env.banner(), undefined, 'bfcache: rechazo sin aviso');
  const before = env.sent();
  env.document.links[0].click();
  assert.deepEqual(env.sent(), before, 'bfcache: el clic de WhatsApp no envía nada a Google ni a Meta');
  assert.equal(env.events('whatsapp_click').length, 1, 'bfcache: whatsapp_click sigue en dataLayer');

  env.localStorage.map.delete('bza_consent');
  env.fire('pageshow', { persisted: true });
  assert.ok(env.banner(), 'bfcache: sin elección guardada se muestra el aviso');
  env.localStorage.map.set('bza_consent', 'granted');
  env.fire('pageshow', { persisted: true });
  assert.equal(env.banner(), undefined, 'bfcache: aceptado en otra página cierra el aviso');
  assert.deepEqual(last(env.gtagCalls('consent')), ['consent', 'update', granted]);
  assert.deepEqual([env.disabled('G-TEST123'), env.disabled('AW-123')], [false, false]);
  env.document.links[0].click();
  assert.equal(env.sent().gtag, before.gtag + 2, 'bfcache: con permiso vuelve a medir');
}

// 10. Retiro del permiso en otra pestaña: el evento storage vuelve a leer la elección.
{
  const env = run({ ids: testIds, local: { bza_consent: 'granted' } });
  const updates = env.gtagCalls('consent').length;
  env.localStorage.map.set('bza_consent', 'denied');
  env.fire('storage', { key: 'otra_clave' });
  assert.equal(env.gtagCalls('consent').length, updates, 'storage de otra clave se ignora');
  env.fire('storage', { key: 'bza_consent' });
  assert.deepEqual(last(env.gtagCalls('consent')), ['consent', 'update', denied], 'otra pestaña: aplica el rechazo');
  const before = env.sent();
  env.document.links[1].click();
  assert.deepEqual(env.sent(), before, 'otra pestaña: el clic no envía nada');

  env.localStorage.map.clear();
  env.fire('storage', { key: null });
  assert.ok(env.banner(), 'localStorage.clear() en otra pestaña: vuelve el aviso');
  env.localStorage.map.set('bza_consent', 'granted');
  env.fire('storage', { key: 'bza_consent' });
  assert.equal(env.banner(), undefined, 'aceptado en otra pestaña: se cierra el aviso');
  assert.deepEqual(last(env.gtagCalls('consent')), ['consent', 'update', granted]);
}

// 11. Sin evento (pestaña congelada, borrado de datos): el clic comprueba lo guardado antes de enviar.
{
  const env = run({ ids: testIds, local: { bza_consent: 'granted' } });
  env.localStorage.map.delete('bza_consent');
  const before = env.sent();
  env.document.links[0].click();
  assert.equal(env.sent().gtag, before.gtag, 'el clic sin permiso guardado no envía nada a Google');
  assert.ok(!env.fbqQueue().some(call => /^track/.test(call[0])), 'el clic sin permiso guardado no deja eventos de Meta en cola');
  assert.deepEqual(last(env.gtagCalls('consent')), ['consent', 'update', denied]);
  assert.ok(env.banner(), 'y vuelve a preguntar');
  assert.equal(env.events('whatsapp_click').length, 1);
}

// 12. Almacenamiento no disponible: la elección vale solo en memoria para la página.
{
  const blocked = run({ ids: testIds, localStorageThrows: true });
  assert.ok(blocked.banner(), 'sin localStorage se pregunta');
  assertAttribution(blocked, 'sin localStorage');
  blocked.choose('Aceptar');
  blocked.document.links[0].click();
  assert.equal(blocked.sent().gtag, 2, 'sin localStorage: la elección en memoria permite medir');
  blocked.fire('pageshow', { persisted: true });
  blocked.fire('storage', { key: 'bza_consent' });
  assert.deepEqual(last(blocked.gtagCalls('consent')), ['consent', 'update', granted], 'sin localStorage no se resincroniza');

  const lost = run({ ids: testIds, local: { bza_consent: 'granted' } });
  lost.localStorage.broken = true;
  lost.fire('pageshow', { persisted: true });
  lost.fire('storage', { key: 'bza_consent' });
  lost.document.links[0].click();
  assert.equal(lost.sent().gtag, 2, 'si el almacenamiento deja de leerse, se usa la elección en memoria');
  assert.equal(lost.banner(), undefined, 'y no se vuelve a preguntar');

  const readOnly = run({ ids: testIds, localStorageWriteThrows: true });
  readOnly.choose('Aceptar');
  readOnly.document.links[0].click();
  assert.equal(readOnly.sent().gtag, 2, 'si no se puede guardar, manda la elección en memoria');
}

// 13. Un fallo en el código de medición nunca rompe el origen de WhatsApp ni whatsapp_click en dataLayer.
{
  assertAttribution(run({ ids: testIds, localStorageThrows: true, createElementThrows: true }), 'createElement y localStorage fallan');
  const broken = run({ ids: testIds, createElementThrows: true });
  assertAttribution(broken, 'createElement falla');
  assert.ok(broken.log.some(entry => entry.startsWith('warn:BZA Creative: la medición no pudo iniciar')), 'el fallo se avisa en consola');

  const throwingConfig = run({ measurementBlock: "const MEASUREMENT = { get ga4Id() { throw new Error('config rota'); } };" });
  assertAttribution(throwingConfig, 'MEASUREMENT lanza un error');
  assert.ok(throwingConfig.log.some(entry => entry.startsWith('warn:BZA Creative: la medición no pudo prepararse')));

  const env = run({ ids: testIds, local: { bza_consent: 'granted' } });
  env.sandbox.fbq = () => { throw new Error('fbq roto'); };
  assertAttribution(env, 'fbq lanza al hacer clic');
  assert.ok(env.log.some(entry => entry.startsWith('warn:BZA Creative: no se pudo medir el clic de WhatsApp')));
}

// 14. Cookies de GA4, Google Ads y Meta con Domain del sitio (como las crean las etiquetas) se borran al retirar el permiso.
{
  const seeded = host => [
    ['_ga', 'GA1.1', '.bzacreative.com'],
    ['_ga_TEST123', 'GS1', '.bzacreative.com'],
    ['_gid', 'GA1.1', '.bzacreative.com'],
    ['_gcl_au', '1.1', '.bzacreative.com'],
    ['_fbp', 'fb.1', '.bzacreative.com'],
    ['_fbc', 'fb.1', '.bzacreative.com'],
    ['_ga', 'GA1.1'],
    ['_fbp', 'fb.1', `.${host}`],
    ['keep', '1', '.bzacreative.com'],
    ['keep', '2']
  ];
  for (const host of ['bzacreative.com', 'www.bzacreative.com']) {
    const env = run({ ids: testIds, url: `https://${host}/privacidad/`, local: { bza_consent: 'granted' }, resets: 1, cookies: seeded(host) });
    assert.ok(env.jar.list().includes('_ga@.bzacreative.com'), `${host}: cookies sembradas`);
    env.document.resets[0].click();
    assert.deepEqual(env.jar.list(), ['keep@.bzacreative.com', 'keep@host-only'], `${host}: se borran las cookies de medición de todos los dominios`);
  }
  const rejected = run({ ids: testIds, cookies: seeded('bzacreative.com') });
  rejected.choose('Rechazar');
  assert.deepEqual(rejected.jar.list(), ['keep@.bzacreative.com', 'keep@host-only'], 'Rechazar también borra cookies previas');
}

// 15. Los IDs publicados en dist/campaign.js tienen formato válido.
// 15. Un emoji partido en el corte de 180 caracteres no rompe el enlace de WhatsApp ni bza_page_view.
{
  const campaign = `${'x'.repeat(179)}😀`;
  for (const ids of [{}, testIds]) {
    const env = run({ ids, url: `https://bzacreative.com/campana/?utm_source=google&utm_medium=cpc&utm_campaign=${encodeURIComponent(campaign)}` });
    assert.match(env.document.links[0].href, /^https:\/\/wa\.me\/523342781554\?text=.*Origen%20de%20la%20consulta/, 'emoji en el corte: el enlace conserva el origen');
    assert.equal(env.events('bza_page_view').length, 1, 'emoji en el corte: bza_page_view');
    assert.equal(env.events('bza_page_view')[0].campaign_name, 'x'.repeat(179), 'emoji en el corte: sin medio emoji');
  }
}

// 16. Rechazo antes de que llegue fbevents.js: la cola del píxel no conserva eventos aceptados y la cookie _fbp
// que la biblioteca cree al llegar se borra.
{
  const env = run({ ids: testIds, resets: 1 });
  env.choose('Aceptar');
  env.document.links[0].click();
  assert.ok(env.fbqQueue().some(call => call[0] === 'track' && call[1] === 'Contact'), 'Contact en cola antes de retirar');
  env.document.resets[0].click();
  env.choose('Rechazar');
  assert.deepEqual(env.fbqQueue()[0], ['consent', 'revoke'], 'la revocación va primero');
  assert.ok(!env.fbqQueue().some(call => /^track/.test(call[0])), 'sin PageView ni Contact pendientes');
  env.document.cookie = '_fbp=fb.1.1; domain=.bzacreative.com; path=/';
  const fbevents = env.document.head.children.find(child => child.tagName === 'SCRIPT' && /fbevents/.test(child.src));
  (fbevents.listeners.load || []).forEach(listener => listener({}));
  assert.ok(!env.jar.list().some(name => name.startsWith('_fbp')), 'al cargar fbevents.js sin permiso se borra _fbp');
}

// 17. Si otra pestaña cierra el aviso abierto con "Cambiar mis preferencias", el foco vuelve al botón.
{
  const env = run({ ids: testIds, local: { bza_consent: 'granted' }, resets: 1 });
  const reset = env.document.resets[0];
  reset.click();
  assert.ok(env.document.activeElement === env.banner(), 'el foco pasa al aviso');
  env.localStorage.map.set('bza_consent', 'granted');
  env.fire('storage', { key: 'bza_consent' });
  assert.equal(env.banner(), undefined, 'otra pestaña aceptó: se cierra el aviso');
  assert.ok(env.document.activeElement === reset, 'el foco regresa al botón de preferencias');
}

const published = run({ ids: null, resets: 1 });
const warnings = published.log.filter(entry => entry.startsWith('warn:'));
assert.deepEqual(warnings, [], `IDs con formato incorrecto en dist/campaign.js: ${warnings.join(' | ')}`);
const active = published.banner() !== undefined;
console.log(`Verified campaign.js: original attribution intact, consent banner scoped to the configured tools, GA4/Google Ads/Meta loading only after consent, withdrawal synced across tabs and bfcache, ga-disable, cookie cleanup per domain, reset, ID validation and measurement failures isolated from WhatsApp. Measurement in dist/campaign.js: ${active ? 'ACTIVE (IDs set)' : 'off (IDs empty)'}.`);
