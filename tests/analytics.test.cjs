const test = require('node:test');
const assert = require('node:assert/strict');
const {initAnalytics, MEASUREMENT_ID} = require('../analytics.js');
function setup(options = {}) {
  const events = {}, scripts = [], clicks = {};
  const win = {location: {hostname:'tablero.federicopellegrini.com.ar', protocol:'https:', hash:'#summary', ...options.location},
    localStorage: {getItem: () => options.optOut ? 'true' : null},
    addEventListener: (name, fn) => {events[name] = fn;}};
  const doc = {referrer:'https://example.com/private?email=test@example.com',
    head:{append:script => scripts.push(script)}, createElement:() => ({}),
    querySelector:() => options.current ? {dataset:{page:options.current}} : null,
    addEventListener:(name, fn) => {clicks[name] = fn;}};
  const api = initAnalytics(win, doc);
  const records = () => (win.dataLayer || []).map(args => Array.from(args));
  const views = () => records().filter(row => row[0] === 'event' && row[1] === 'page_view');
  return {win, doc, events, scripts, clicks, api, records, views};
}
test('loads the dedicated tag once and sends exactly one initial view', () => {
  const s = setup(); initAnalytics(s.win, s.doc);
  assert.equal(s.scripts.length, 1);
  assert.match(s.scripts[0].src, new RegExp(MEASUREMENT_ID));
  assert.equal(s.views().length, 1);
  const config = s.records().find(row => row[0] === 'config')[2];
  assert.equal(config.send_page_view, false);
  assert.equal(config.allow_google_signals, false);
  assert.equal(config.allow_ad_personalization_signals, false);
});
test('all eleven sections count once per transition; repeats and invalid values do not count', () => {
  const s = setup();
  const routes = ['summary','debt','income','federal','comparison','results','openHistory','openMap','openNation','openOperations','openGuide'];
  for (const view of routes) {
    s.events['dashboard:view']({detail:{view}});
    s.events['dashboard:view']({detail:{view}});
  }
  s.events['dashboard:view']({detail:{view:'governor'}});
  s.events['dashboard:view']({detail:{view:'__proto__'}});
  assert.equal(s.views().length, 11);
  s.api.recordView('summary');
  assert.equal(s.views().length, 12);
  assert.equal(s.views().at(-1)[2].page_referrer, 'https://tablero.federicopellegrini.com.ar/#openGuide');
});
test('direct section links and old bookmarks start in the right section', () => {
  assert.match(setup({location:{hash:'#debt'}}).views()[0][2].page_title, /^Solvencia/);
  assert.match(setup({location:{hash:'#layer2'}}).views()[0][2].page_title, /^Comparación/);
  assert.match(setup({current:'openMap'}).views()[0][2].page_title, /^Mapa/);
});
test('local development, previews and opted-out browsers send nothing', () => {
  for (const options of [{location:{hostname:'localhost'}},{location:{hostname:'federico18pellegrini-ux.github.io'}},{location:{protocol:'http:'}},{optOut:true}]) {
    const s = setup(options); assert.equal(s.api, null); assert.equal(s.records().length, 0); assert.equal(s.scripts.length, 0);
  }
});
test('page metadata excludes arbitrary URL parameters and referrer paths', () => {
  const s = setup({location:{hash:'#unknown?name=private', search:'?email=test@example.com'}});
  assert.equal(s.views()[0][2].page_referrer, 'https://example.com/');
  assert.equal(s.views()[0][2].page_location, 'https://tablero.federicopellegrini.com.ar/#summary');
  assert.doesNotMatch(JSON.stringify(s.records()), /email|private|test@example/);
});
test('opting out in another open tab stops further tracking', () => {
  const s = setup();
  s.events.storage({key:'tablero_analytics_opt_out', newValue:'true'});
  s.api.recordView('debt');
  assert.equal(s.views().length, 1);
  assert.equal(s.win['ga-disable-' + MEASUREMENT_ID], true);
});
test('PDF clicks record a sanitized download; invalid and disabled links are ignored', () => {
  const s = setup();
  function click(href, disabled = false) {
    s.clicks.click({target:{closest:() => ({href, getAttribute:() => disabled ? 'true' : null})}});
  }
  click('https://tablero.federicopellegrini.com.ar/reports/informe-buenos-aires.pdf?v=123');
  click('https://example.com/reports/informe-buenos-aires.pdf');
  click('https://tablero.federicopellegrini.com.ar/reports/informe-cordoba.pdf', true);
  const downloads = s.records().filter(row => row[1] === 'file_download');
  assert.equal(downloads.length, 1);
  assert.equal(downloads[0][2].file_name, '/reports/informe-buenos-aires.pdf');
  assert.doesNotMatch(JSON.stringify(downloads), /\?v=/);
});
