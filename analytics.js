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
  const MUNICIPAL_VIEWS = Object.freeze({panorama:'Panorama municipal',rankings:'Rankings municipales',recursos:'Recursos municipales',empleo:'Empleo municipal',simular:'Escenario de coparticipación',informe:'Preparar informe municipal'});
  const NATIONAL_VIEWS = Object.freeze({prioridades:'Prioridades y efectos',normas:'Normas y partidas',carteras:'Ministerios y poderes','politica-jubilaciones':'Jubilaciones y pensiones','politica-alimentacion':'Asistencia alimentaria','politica-medicamentos':'Medicamentos','politica-seguridad-federal':'Seguridad federal',inicio:'Presupuesto Nacional',distribucion:'Distribución',obras:'Obras',programas:'Programas',escala:'Escala',comparacion:'Comparación',finalidades:'Finalidades',cambios:'Subas y bajas',recursos:'Recursos',macro:'Supuestos macro',financiamiento:'Cierre y financiamiento',escenarios:'Escenarios','obra-ra10':'Obra RA-10','politica-inmunizaciones':'Política de inmunizaciones','politica-educacion-superior':'Política universitaria',historia:'Historia',ejecucion:'Ejecución',modificaciones:'Modificaciones 2026',caja:'Caja nacional','deuda-nacional':'Deuda nacional','provincias-nacion':'Recursos a provincias',metas:'Prestaciones','obras-ejecucion':'Obras ejecutadas','historia-ejecucion':'Historia de ejecución',metodo:'Método'});

  function initAnalytics(win, doc) {
    if (win.tableroRedirecting) return null;
    if (win.location.hostname !== HOST || win.location.protocol !== 'https:') return null;
    try { if (win.localStorage.getItem(OPT_OUT_KEY) === 'true') return null; } catch (_) {}
    if (win.tableroAnalytics) return win.tableroAnalytics;
    win.dataLayer = win.dataLayer || [];
    win.gtag = function () { win.dataLayer.push(arguments); };
    const origin = 'https://' + HOST;
    const municipal = /^\/municipios(?:\/|$)/.test(win.location.pathname || '');
    const national = /^\/nacion(?:\/|$)/.test(win.location.pathname || '');
    const views = national ? NATIONAL_VIEWS : municipal ? MUNICIPAL_VIEWS : VIEWS;
    const basePath = national ? '/nacion/' : municipal ? '/municipios/' : '/';
    const contentGroup = national ? 'Nación' : municipal ? 'Municipios' : 'Provincias';
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
      content_group: contentGroup,
      page_location: origin + basePath,
      page_referrer: previousLocation
    });

    function recordView(view) {
      if (win[disabledKey] || !Object.hasOwn(views, view) || view === lastView) return;
      const pageLocation = origin + basePath + '#' + view;
      const params = {page_title: views[view] + (national ? ' · Presupuesto Nacional' : municipal ? ' · Municipios' : ' · Tablero Fiscal'),
        page_location: pageLocation, page_referrer: previousLocation, content_group: contentGroup};
      win.gtag('set', params);
      win.gtag('event', 'page_view', params);
      previousLocation = pageLocation;
      lastView = view;
    }

    win.addEventListener('dashboard:view', event => recordView(event.detail?.view));
    // The selected role, simulations and free text are never collected.
    doc.addEventListener('click', event => {
      if (win[disabledKey]) return;
      const link = event.target?.closest?.('#downloadPdf, #download-national-report');
      if (!link || link.getAttribute('aria-disabled') === 'true') return;
      let url;
      try { url = new URL(link.href); } catch (_) { return; }
      const provincePdf = /^\/reports\/informe-[a-z-]+\.pdf$/.test(url.pathname);
      const nationalPdf = /^\/nacion\/reports\/(informe-nacional-(nominal|real)-(current|law|closing)(-anexo)?|ficha-nacional-(inmunizaciones|educacion-superior|jubilaciones|alimentacion|medicamentos|seguridad-federal|reactor-ra10|cartera-(1|5|10|20|25|30|35|40|41|45|50|80|88|89|90|91)|provincia-(2|6|10|14|18|22|26|30|34|38|42|46|50|54|58|62|66|70|74|78|82|86|90|94)))\.pdf$/.test(url.pathname);
      if (url.origin !== origin || (!provincePdf && !nationalPdf)) return;
      win.gtag('event', 'file_download', {file_extension: 'pdf',
        file_name: url.pathname, link_url: origin + url.pathname,
        link_text: nationalPdf ? 'Informe del Presupuesto Nacional' : 'PDF de la provincia'});
    });
    const current = doc.querySelector(municipal ? '.main-nav button[aria-current="page"]' : '.visible-navigation button[aria-current="page"]')?.dataset;
    const hash = municipal ? new URLSearchParams(win.location.search || '').get('vista') : win.location.hash.slice(1);
    recordView(national ? (Object.hasOwn(views, hash) ? hash : 'inicio') : municipal ? (Object.hasOwn(views, hash) ? hash : 'panorama') : (current?.page || (Object.hasOwn(VIEWS, hash) ? hash : Object.hasOwn(ALIASES, hash) ? ALIASES[hash] : 'summary')));
    if(national)win.addEventListener('hashchange',()=>recordView(win.location.hash.slice(1)));
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
