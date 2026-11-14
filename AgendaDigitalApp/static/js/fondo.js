/* Aplica el fondo elegido antes de pintar la página (evita el parpadeo). */
(function () {
  var valid = { crema: 1, rosa: 1, turquesa: 1, liso: 1 };
  var fondo = 'crema';
  try {
    var saved = window.localStorage.getItem('agenda-fondo');
    if (saved && valid[saved]) fondo = saved;
  } catch (error) { /* almacenamiento no disponible: se usa el fondo por defecto */ }
  document.documentElement.setAttribute('data-fondo', fondo);
})();
