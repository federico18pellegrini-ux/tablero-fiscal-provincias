/* GA4: one page view per visible section. Enhanced measurement is off in GA. */
(function (root) {
  'use strict';
  const MEASUREMENT_ID = 'G-H3P727GYS0';
  const HOST = 'tablero.federicopellegrini.com.ar';
  const OPT_OUT_KEY = 'tablero_analytics_opt_out';
  const VIEWS = Object.freeze({
    summary: 'Resumen provincial', debt: 'Solvencia y deuda',
    income: 'Ingresos y gasto', federal: 'Relación con Nación',
    comparison: 'Comparación provincial', results: 'Resultados de gobierno',
    openHistory: 'Historia fiscal', openMap: 'Mapa de Argentina',
    openNation: 'Economía nacional', openOperations: 'Caja y vencimientos',
    openGuide: 'Cómo leer los datos'
  });
  const ALIASES = {governorRoom:'summary', layer3:'debt', structuralIndicators:'income',
    layer1:'federal', layer2:'comparison', comparisonSection:'comparison'};

  function initAnalytics(win, doc) {
    if (win.location.hostname !== HOST || win.location.protocol !== 'https:') return null;
    try { if (win.localStorage.getItem(OPT_OUT_KEY) === 'true') return null; } catch (_) {}
    if (win.tableroAnalytics) return win.tableroAnalytics;
    win.dataLayer = win.dataLayer || [];
    win.gtag = function () { win.dataLayer.push(arguments); };
    const origin = 'https://' + HOST;
    let previousLocation = '';
    try { previousLocation = doc.referrer ? new URL(doc.referrer).origin + '/' : ''; } catch (_) {}
    let lastView = null;
    const disabledKey = 'ga-disable-' + MEASUREMENT_ID;
    win.addEventListener('storage', event => {
      if (event.key === OPT_OUT_KEY) win[disabledKey] = event.newValue === 'true';
    });
    win.gtag('consent', 'default', {
      ad_storage: 'denied', ad_user_data: 'denied', ad_personalization: 'denied'
    });
    win.gtag('js', new Date());
    win.gtag('config', MEASUREMENT_ID, {
      send_page_view: false,
      allow_google_signals: false,
      allow_ad_personalization_signals: false,
      cookie_domain: HOST,
      cookie_prefix: 'tablero',
      page_location: origin + '/',
      page_referrer: previousLocation
    });

    function recordView(view) {
      if (win[disabledKey] || !Object.hasOwn(VIEWS, view) || view === lastView) return;
      const pageLocation = origin + '/#' + view;
      const params = {page_title: VIEWS[view] + ' · Tablero Fiscal',
        page_location: pageLocation, page_referrer: previousLocation};
      win.gtag('set', params);
      win.gtag('event', 'page_view', params);
      previousLocation = pageLocation;
      lastView = view;
    }

    win.addEventListener('dashboard:view', event => recordView(event.detail?.view));
    // The selected role, simulations and free text are never collected.
    doc.addEventListener('click', event => {
      if (win[disabledKey]) return;
      const link = event.target?.closest?.('#downloadPdf');
      if (!link || link.getAttribute('aria-disabled') === 'true') return;
      let url;
      try { url = new URL(link.href); } catch (_) { return; }
      if (url.origin !== origin || !/^\/reports\/informe-[a-z-]+\.pdf$/.test(url.pathname)) return;
      win.gtag('event', 'file_download', {file_extension: 'pdf',
        file_name: url.pathname, link_url: origin + url.pathname,
        link_text: 'PDF de la provincia'});
    });
    const current = doc.querySelector('.visible-navigation button[aria-current="page"]')?.dataset.page;
    const hash = win.location.hash.slice(1);
    recordView(current || (Object.hasOwn(VIEWS, hash) ? hash : Object.hasOwn(ALIASES, hash) ? ALIASES[hash] : 'summary'));
    const script = doc.createElement('script');
    script.async = true;
    script.src = 'https://www.googletagmanager.com/gtag/js?id=' + MEASUREMENT_ID;
    doc.head.append(script);
    win.tableroAnalytics = {recordView};
    return win.tableroAnalytics;
  }
  if (typeof module !== 'undefined' && module.exports) module.exports = {initAnalytics, MEASUREMENT_ID};
  else initAnalytics(root, root.document);
})(typeof window === 'undefined' ? null : window);
