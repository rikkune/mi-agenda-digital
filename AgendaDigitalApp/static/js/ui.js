/* Mejoras de interfaz: menú "Nuevo", selector de fondo, atajos de teclado
   y comportamiento del menú lateral en móvil. Se carga después de app.js
   y usa sus funciones globales (openTaskForm, openEventForm, ...). */
(function () {
  'use strict';

  const FONDO_KEY = 'agenda-fondo';
  const byId = (id) => document.getElementById(id);

  /* ---------- Popovers (menú Nuevo y selector de fondo) ---------- */
  const popovers = [
    { button: byId('quickAddBtn'), panel: byId('quickAddMenu') },
    { button: byId('fondoBtn'), panel: byId('fondoMenu') }
  ].filter((p) => p.button && p.panel);

  function closePopovers(except) {
    popovers.forEach((p) => {
      if (p === except) return;
      p.panel.hidden = true;
      p.button.setAttribute('aria-expanded', 'false');
    });
  }

  function togglePopover(pop) {
    const willOpen = pop.panel.hidden;
    closePopovers(pop);
    pop.panel.hidden = !willOpen;
    pop.button.setAttribute('aria-expanded', String(willOpen));
    if (willOpen) {
      const first = pop.panel.querySelector('[aria-checked="true"], button');
      if (first) first.focus();
    }
  }

  popovers.forEach((pop) => {
    pop.button.addEventListener('click', (event) => {
      event.stopPropagation();
      togglePopover(pop);
    });
  });

  document.addEventListener('click', (event) => {
    if (!event.target.closest('.pop-wrap')) closePopovers();
  });

  /* ---------- Crear nuevo ---------- */
  const QUICK_ACTIONS = {
    task: () => typeof openTaskForm === 'function' && openTaskForm(),
    event: () => typeof openEventForm === 'function' && openEventForm(),
    note: () => typeof openNoteForm === 'function' && openNoteForm(),
    reminder: () => typeof openReminderForm === 'function' && openReminderForm(),
    tutoring: () => typeof openTutoringForm === 'function' && openTutoringForm()
  };

  const quickMenu = byId('quickAddMenu');
  if (quickMenu) {
    quickMenu.addEventListener('click', (event) => {
      const item = event.target.closest('[data-quick]');
      if (!item) return;
      closePopovers();
      const action = QUICK_ACTIONS[item.dataset.quick];
      if (action) action();
    });
  }

  /* ---------- Fondo ---------- */
  function currentFondo() {
    return document.documentElement.getAttribute('data-fondo') || 'crema';
  }

  function markFondo() {
    const active = currentFondo();
    document.querySelectorAll('[data-fondo-opt]').forEach((opt) => {
      opt.setAttribute('aria-checked', String(opt.dataset.fondoOpt === active));
    });
  }

  function setFondo(name) {
    document.documentElement.setAttribute('data-fondo', name);
    try { window.localStorage.setItem(FONDO_KEY, name); } catch (error) { /* sin almacenamiento */ }
    markFondo();
  }

  const fondoMenu = byId('fondoMenu');
  if (fondoMenu) {
    fondoMenu.addEventListener('click', (event) => {
      const opt = event.target.closest('[data-fondo-opt]');
      if (opt) setFondo(opt.dataset.fondoOpt);
    });
    // Flechas para moverse entre las opciones (patrón radiogroup)
    fondoMenu.addEventListener('keydown', (event) => {
      const options = Array.from(fondoMenu.querySelectorAll('[data-fondo-opt]'));
      const index = options.indexOf(document.activeElement);
      if (index < 0) return;
      const step = { ArrowRight: 1, ArrowDown: 2, ArrowLeft: -1, ArrowUp: -2 }[event.key];
      if (!step) return;
      event.preventDefault();
      const next = options[(index + step + options.length) % options.length];
      next.focus();
      setFondo(next.dataset.fondoOpt);
    });
  }
  markFondo();

  /* ---------- Menú lateral en móvil ---------- */
  const sidebar = byId('sidebar');
  const backdrop = byId('backdrop');
  const menuButton = byId('menu');
  if (sidebar && backdrop) {
    const sync = () => {
      const open = sidebar.classList.contains('open');
      backdrop.hidden = !open;
      if (menuButton) menuButton.setAttribute('aria-expanded', String(open));
    };
    new MutationObserver(sync).observe(sidebar, { attributes: true, attributeFilter: ['class'] });
    backdrop.addEventListener('click', () => sidebar.classList.remove('open'));
    sync();
  }

  /* ---------- Tarjetas clicables accesibles con teclado ---------- */
  document.addEventListener('keydown', (event) => {
    const card = event.target.closest && event.target.closest('[role="button"][data-go]');
    if (card && (event.key === 'Enter' || event.key === ' ')) {
      event.preventDefault();
      card.click();
    }
  });

  /* ---------- Atajos de teclado ---------- */
  function isTyping(target) {
    if (!target) return false;
    const tag = target.tagName;
    return tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || target.isContentEditable;
  }

  function dialogOpen() {
    const modal = byId('modal');
    const confirm = byId('confirm');
    return (modal && !modal.hidden) || (confirm && !confirm.hidden);
  }

  function focusSearch() {
    const active = document.querySelector('.view.active');
    let input = active && active.querySelector('input[type="search"]');
    if (!input && typeof navigate === 'function') {
      navigate('tareas');
      input = byId('taskSearch');
    }
    if (input) {
      input.focus();
      input.select();
    }
  }

  const SHORTCUTS = {
    t: QUICK_ACTIONS.task,
    e: QUICK_ACTIONS.event,
    n: QUICK_ACTIONS.note,
    r: QUICK_ACTIONS.reminder,
    s: QUICK_ACTIONS.tutoring,
    '/': focusSearch
  };

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      closePopovers();
      if (sidebar) sidebar.classList.remove('open');
      return;
    }
    if (event.ctrlKey || event.metaKey || event.altKey) return;
    if (isTyping(event.target) || dialogOpen()) return;
    const action = SHORTCUTS[event.key.toLowerCase()];
    if (!action) return;
    event.preventDefault();
    closePopovers();
    action();
  });
})();
