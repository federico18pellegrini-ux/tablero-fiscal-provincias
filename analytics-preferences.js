/* This page does not load Google Analytics. */
(function () {
  'use strict';
  const key = 'tablero_analytics_opt_out';
  const status = document.getElementById('analyticsPreference');
  const button = document.getElementById('toggleAnalytics');
  function update() {
    try {
      const disabled = localStorage.getItem(key) === 'true';
      status.textContent = disabled ? 'Las estadísticas están desactivadas en este navegador.' : 'Las estadísticas están activadas en este navegador.';
      button.textContent = (disabled ? 'Activar' : 'Desactivar') + ' estadísticas en este navegador';
    } catch (_) {
      status.textContent = 'El navegador no permite guardar esta preferencia. Podés bloquear Google Analytics desde la configuración de privacidad del navegador.';
      button.disabled = true;
    }
  }
  button.addEventListener('click', () => {
    try {
      const disabled = localStorage.getItem(key) !== 'true';
      localStorage.setItem(key, String(disabled));
      if (disabled) {
        for (const cookie of document.cookie.split(';')) {
          const name = cookie.split('=')[0].trim();
          if (!name.startsWith('tablero_ga')) continue;
          document.cookie = name + '=; Max-Age=0; Path=/; SameSite=Lax';
          document.cookie = name + '=; Max-Age=0; Path=/; Domain=tablero.federicopellegrini.com.ar; SameSite=Lax';
        }
      }
      update();
    } catch (_) { status.textContent = 'No se pudo guardar la preferencia. Revisá los permisos de almacenamiento del navegador.'; }
  });
  update();
})();
