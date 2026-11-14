/* Página de inicio de sesión: mostrar contraseña y estado de envío. */
(function () {
  var form = document.getElementById('loginForm');
  var password = document.getElementById('password');
  var toggle = document.getElementById('togglePassword');
  var submit = document.getElementById('loginSubmit');

  toggle.addEventListener('click', function () {
    var show = password.type === 'password';
    password.type = show ? 'text' : 'password';
    toggle.textContent = show ? 'Ocultar' : 'Mostrar';
    toggle.setAttribute('aria-pressed', String(show));
    password.focus();
  });

  form.addEventListener('submit', function (event) {
    var user = document.getElementById('username');
    if (!user.value.trim()) { event.preventDefault(); user.focus(); return; }
    if (!password.value) { event.preventDefault(); password.focus(); return; }
    // La comprobación con MEDAC tarda unos segundos.
    submit.disabled = true;
    submit.setAttribute('aria-busy', 'true');
    submit.textContent = 'Comprobando con MEDAC…';
  });

  // Al volver con «Atrás» el botón no debe quedarse bloqueado.
  window.addEventListener('pageshow', function () {
    submit.disabled = false;
    submit.removeAttribute('aria-busy');
    submit.textContent = 'Entrar';
  });
})();
