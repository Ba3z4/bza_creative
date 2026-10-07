// Prueba dist/campaign.js sin navegador ni dependencias: ejecuta el script en node:vm con un DOM mínimo simulado.
// Comprueba que, con los IDs vacíos, el sitio se comporta igual que antes (UTM, dataLayer y mensaje de WhatsApp,
// sin aviso ni etiquetas) y que, con IDs de prueba, el aviso de consentimiento controla GA4, Google Ads y el píxel de Meta.
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import vm from 'node:vm';

const source = await readFile(new URL('../dist/campaign.js', import.meta.url), 'utf8');
const block = source.match(/const MEASUREMENT = \{[\s\S]*?\};/);
assert.ok(block, 'campaign.js declares const MEASUREMENT = { ... }');

const withIds = ids => source.replace(block[0], `const MEASUREMENT = ${JSON.stringify({ ga4Id: '', googleAdsId: '', googleAdsWhatsappLabel: '', metaPixelId: '', ...ids })};`);
const plain = value => JSON.parse(JSON.stringify(value));
const isArgs = entry => Object.prototype.toString.call(entry) === '[object Arguments]';

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

function run({ ids = {}, url = 'https://www.bzacreative.com/campana/?utm_source=google&utm_medium=cpc&utm_campaign=test', local = {}, session = {}, links = 2, resets = 0, cookies = {} } = {}) {
  const log = [];
  const storage = (name, initial) => {
    const map = new Map(Object.entries(initial));
    return {
      map,
      getItem: key => { log.push(`${name}.get:${key}`); return map.has(key) ? map.get(key) : null; },
      setItem: (key, value) => { log.push(`${name}.set:${key}`); map.set(key, String(value)); },
      removeItem: key => { log.push(`${name}.remove:${key}`); map.delete(key); }
    };
  };
  const created = [];
  const jar = new Map(Object.entries(cookies));
  const document = {
    activeElement: null,
    createElement: tag => { const element = new FakeElement(tag, document); created.push(element); return element; },
    querySelectorAll: selector => (selector === 'a[href*="wa.me/"]' ? document.links : selector === '[data-consent-reset]' ? document.resets : []),
    get cookie() { return [...jar].map(([key, value]) => `${key}=${value}`).join('; '); },
    set cookie(value) {
      const [pair, ...attributes] = value.split(';');
      const [key, ...rest] = pair.split('=');
      if (attributes.some(attribute => /max-age=0/i.test(attribute.trim()))) jar.delete(key.trim());
      else jar.set(key.trim(), rest.join('='));
    }
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
  const location = new URL(url);
  const sandbox = { document, console: { warn: message => log.push(`warn:${message}`) }, URL, URLSearchParams };
  Object.assign(sandbox, { window: sandbox, location, sessionStorage: storage('sessionStorage', session), localStorage: storage('localStorage', local) });
  vm.createContext(sandbox);
  vm.runInContext(ids === null ? source : withIds(ids), sandbox, { filename: 'campaign.js' });
  const gtagCalls = command => plain(sandbox.dataLayer.filter(isArgs).map(entry => Array.from(entry))).filter(call => call[0] === command);
  const banner = () => document.body.children.find(child => child.className === 'bza-consent');
  const scripts = () => document.head.children.filter(child => child.tagName === 'SCRIPT').map(child => child.src);
  const choose = label => banner().choices.find(button => button.textContent === label).click();
  const fbqQueue = () => plain((sandbox.fbq?.queue || []).map(args => Array.from(args)));
  return { sandbox, document, log, created, jar, gtagCalls, banner, scripts, choose, fbqQueue };
}

const denied = { ad_storage: 'denied', ad_user_data: 'denied', ad_personalization: 'denied', analytics_storage: 'denied' };
const granted = { ad_storage: 'granted', ad_user_data: 'granted', ad_personalization: 'granted', analytics_storage: 'granted' };
const testIds = { ga4Id: 'G-TEST123', googleAdsId: 'AW-123', googleAdsWhatsappLabel: 'abc', metaPixelId: '123' };
const origin = encodeURIComponent('Origen de la consulta: google / cpc / test');

// 1. IDs vacíos: comportamiento original, sin aviso, sin etiquetas y sin tocar localStorage.
{
  const env = run({ resets: 1 });
  assert.deepEqual(env.log.filter(entry => entry.startsWith('localStorage')), [], 'IDs vacíos: no usa localStorage');
  assert.deepEqual(env.created, [], 'IDs vacíos: no crea elementos');
  assert.equal(env.document.body.children.length, 1, 'IDs vacíos: sin aviso');
  assert.equal(env.sandbox.gtag, undefined, 'IDs vacíos: sin gtag');
  assert.equal(env.sandbox.fbq, undefined, 'IDs vacíos: sin fbq');
  assert.equal(env.document.resets[0].hidden, true, 'IDs vacíos: el botón de preferencias sigue oculto');
  const saved = JSON.parse(env.sandbox.sessionStorage.map.get('bza_campaign'));
  assert.deepEqual([saved.utm_source, saved.utm_medium, saved.utm_campaign, saved.landing_path], ['google', 'cpc', 'test', '/campana/']);
  assert.deepEqual(plain(env.sandbox.dataLayer), [{ event: 'bza_page_view', page_path: '/campana/', campaign_source: 'google', campaign_medium: 'cpc', campaign_name: 'test' }]);
  assert.equal(env.document.links[0].href, `https://wa.me/523342781554?text=${encodeURIComponent('Hola, BZA Creative. Quiero solicitar el diagnóstico inicial de mi negocio.')}%0A%0A${origin}`);
  assert.equal(env.document.links[1].href, `https://wa.me/523342781554?text=${encodeURIComponent('Hola, BZA Creative. Quiero hablar de mi proyecto.')}%0A%0A${origin}`);
  env.document.links[0].click();
  assert.deepEqual(plain(env.sandbox.dataLayer.at(-1)), { event: 'whatsapp_click', link_text: 'WhatsApp 0', page_path: '/campana/', campaign_source: 'google', campaign_medium: 'cpc', campaign_name: 'test' });
  assert.equal(env.sandbox.dataLayer.filter(isArgs).length, 0, 'IDs vacíos: sin comandos gtag');
  const direct = run({ url: 'https://www.bzacreative.com/servicios/' });
  assert.ok(direct.document.links[1].href.endsWith(encodeURIComponent('Origen de la consulta: directo / sitio / servicios')), 'origen directo');
}

// 2. Con IDs: consentimiento denegado por defecto y aviso visible; nada se carga antes de elegir.
{
  const env = run({ ids: testIds });
  assert.ok(isArgs(env.sandbox.dataLayer[0]), 'consent default es lo primero en dataLayer');
  assert.deepEqual(plain(Array.from(env.sandbox.dataLayer[0])), ['consent', 'default', { ...denied, wait_for_update: 500 }]);
  const banner = env.banner();
  assert.ok(banner, 'aviso visible');
  assert.equal(banner.getAttribute('role'), 'region');
  assert.equal(banner.getAttribute('aria-label'), 'Preferencias de medición');
  assert.match(banner.innerHTML, /Google Analytics, Google Ads y el píxel de Meta/);
  assert.match(banner.innerHTML, /href="\/privacidad\//);
  assert.deepEqual(banner.choices.map(button => button.textContent), ['Rechazar', 'Aceptar']);
  assert.deepEqual(env.scripts(), [], 'sin etiquetas antes de elegir');
  env.document.links[0].click();
  assert.deepEqual(env.gtagCalls('event'), [], 'sin eventos antes de elegir');

  env.choose('Aceptar');
  assert.equal(env.sandbox.localStorage.map.get('bza_consent'), 'granted');
  assert.equal(env.banner(), undefined, 'el aviso se cierra');
  assert.deepEqual(env.scripts(), ['https://www.googletagmanager.com/gtag/js?id=G-TEST123', 'https://connect.facebook.net/en_US/fbevents.js']);
  assert.deepEqual(env.gtagCalls('consent').at(-1), ['consent', 'update', granted]);
  assert.deepEqual(env.gtagCalls('config').map(call => call[1]), ['G-TEST123', 'AW-123']);
  assert.deepEqual(env.fbqQueue(), [['init', '123'], ['track', 'PageView']]);
  env.document.links[1].click();
  assert.deepEqual(env.gtagCalls('event'), [
    ['event', 'whatsapp_click', { link_text: 'WhatsApp 1', page_path: '/campana/', campaign_source: 'google', campaign_medium: 'cpc', campaign_name: 'test', send_to: 'G-TEST123' }],
    ['event', 'conversion', { send_to: 'AW-123/abc' }]
  ]);
  assert.deepEqual(env.fbqQueue().at(-1), ['track', 'Contact']);
  assert.equal(plain(env.sandbox.dataLayer).filter(entry => entry.event === 'whatsapp_click').length, 2, 'dataLayer conserva whatsapp_click');
}

// 3. Elección guardada: aceptada carga sin aviso; rechazada no carga nada.
{
  const accepted = run({ ids: testIds, local: { bza_consent: 'granted' } });
  assert.equal(accepted.banner(), undefined);
  assert.equal(accepted.scripts().length, 2);
  const rejected = run({ ids: testIds });
  rejected.choose('Rechazar');
  assert.equal(rejected.sandbox.localStorage.map.get('bza_consent'), 'denied');
  assert.deepEqual(rejected.scripts(), []);
  rejected.document.links[0].click();
  assert.deepEqual(rejected.gtagCalls('event'), []);
  const later = run({ ids: testIds, local: { bza_consent: 'denied' } });
  assert.equal(later.banner(), undefined);
  assert.deepEqual(later.scripts(), []);
}

// 4. Aceptar en otra página: Google recibe el origen de la sesión.
{
  const env = run({ ids: testIds, url: 'https://www.bzacreative.com/servicios/', session: { bza_campaign: JSON.stringify({ utm_source: 'google', utm_medium: 'cpc', utm_campaign: 'test', gclid: 'abc' }) } });
  env.choose('Aceptar');
  const location = new URL(env.gtagCalls('config')[0][2].page_location);
  assert.deepEqual([location.pathname, location.searchParams.get('utm_campaign'), location.searchParams.get('gclid')], ['/servicios/', 'test', 'abc']);
}

// 5. [data-consent-reset]: visible con IDs, borra la elección, vuelve a denegar y muestra el aviso.
{
  const env = run({ ids: testIds, local: { bza_consent: 'granted' }, resets: 1, cookies: { _ga: 'GA1.1', _ga_TEST123: 'GS1', _gcl_au: '1', _fbp: 'fb', keep: '1' } });
  const reset = env.document.resets[0];
  assert.equal(reset.hidden, false, 'botón de preferencias visible');
  reset.click();
  assert.equal(env.sandbox.localStorage.map.has('bza_consent'), false);
  assert.deepEqual(env.gtagCalls('consent').at(-1), ['consent', 'update', denied]);
  assert.deepEqual(env.fbqQueue().at(-1), ['consent', 'revoke']);
  assert.equal(env.document.cookie, 'keep=1', 'borra cookies de medición');
  assert.ok(env.document.activeElement === env.banner(), 'el foco pasa al aviso');
  env.choose('Rechazar');
  assert.ok(env.document.activeElement === reset, 'el foco regresa al botón');
  reset.click();
  env.choose('Aceptar');
  assert.equal(env.scripts().length, 2, 'no duplica etiquetas');
  assert.deepEqual(env.fbqQueue().at(-1), ['consent', 'grant']);
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
}

// 7. Los IDs publicados en dist/campaign.js tienen formato válido.
const published = run({ ids: null, resets: 1 });
const warnings = published.log.filter(entry => entry.startsWith('warn:'));
assert.deepEqual(warnings, [], `IDs con formato incorrecto en dist/campaign.js: ${warnings.join(' | ')}`);
const active = published.banner() !== undefined;
console.log(`Verified campaign.js: original attribution intact, consent banner, GA4/Google Ads/Meta loading only after consent, reset and ID validation. Measurement in dist/campaign.js: ${active ? 'ACTIVE (IDs set)' : 'off (IDs empty)'}.`);
