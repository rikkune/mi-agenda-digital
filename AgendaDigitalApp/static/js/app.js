'use strict';

/* ============================================================
   Mi Agenda Digital 2026–2027 · interfaz conectada a Flask
   ============================================================ */

const MONTHS = [
  'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
  'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'
];
const MONTHS_SHORT = [
  'ene', 'feb', 'mar', 'abr', 'may', 'jun',
  'jul', 'ago', 'sep', 'oct', 'nov', 'dic'
];
const WEEKDAYS_SHORT = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'];

const TASK_KIND_LABELS = {
  tarea: 'Tarea', entrega: 'Entrega', examen: 'Examen',
  reunion: 'Reunión', otro: 'Otro'
};
const TASK_TARGET_LABELS = {
  docente: 'La hago yo', alumno: 'Entregan alumnos'
};
// Iconos propios: manzana = lo hago yo (docente); birrete = lo entrega el alumnado
const TARGET_SVG = {
  docente: '<svg class="target-svg" viewBox="0 0 24 24" aria-hidden="true"><path fill="#E0475B" d="M12 7.6c-1.6-1.3-4.2-1.6-5.9-.2C4.2 8.9 3.8 11.8 4.6 14.6 5.5 17.8 7.6 21 10 21c1 0 1.3-.5 2-.5s1 .5 2 .5c2.4 0 4.5-3.2 5.4-6.4.8-2.8.4-5.7-1.5-7.2-1.7-1.4-4.3-1.1-5.9.2z"/><path d="M12 7.6c0-2 .9-3.6 2.6-4.4" fill="none" stroke="#7a4b2a" stroke-width="1.6" stroke-linecap="round"/><path fill="#4CAF6A" d="M13.2 5.6c.4-1.9 2.2-2.9 4.3-2.5-.4 1.9-2.2 2.9-4.3 2.5z"/><path fill="#fff" opacity=".55" d="M7.4 10.2c.6-1 1.7-1.4 2.6-1.2-.9.6-1.5 1.5-1.7 2.6-.5-.2-.9-.8-.9-1.4z"/></svg>',
  alumno: '<svg class="target-svg" viewBox="0 0 24 24" aria-hidden="true"><path fill="#2F3A5C" d="M12 3.5 1.5 8.6 12 13.7l10.5-5.1L12 3.5z"/><path fill="#46557f" d="M6 11.2v4.3c0 1.6 2.7 3.2 6 3.2s6-1.6 6-3.2v-4.3l-6 2.9-6-2.9z"/><path d="M20.6 9.3v5.2" fill="none" stroke="#F2B233" stroke-width="1.6" stroke-linecap="round"/><circle cx="20.6" cy="15.3" r="1.3" fill="#F2B233"/></svg>'
};
const TASK_TARGET_ICONS = {
  docente: TARGET_SVG.docente, alumno: TARGET_SVG.alumno
};
const TASK_PRIORITY_LABELS = { alta: 'Alta', media: 'Media', baja: 'Baja' };
const TASK_STATUS_LABELS = { pendiente: 'Pendiente', en_curso: 'En curso', completada: 'Completada' };
const EVENT_CATEGORY_LABELS = {
  evento: 'Evento', entrega: 'Entrega', reunion: 'Reunión',
  examen: 'Examen', otro: 'Otro'
};
const TUTORING_KIND_LABELS = { seguimiento: 'Seguimiento', visita: 'Visita', reunion: 'Reunión' };
const TUTORING_STATUS_LABELS = { pendiente: 'Pendiente', realizado: 'Realizado', cancelado: 'Cancelado' };
const HOLIDAY_SCOPE_LABELS = {
  nacional: 'Festivo nacional', autonomico: 'Festivo autonómico',
  local: 'Festivo local', vacaciones: 'Vacaciones', no_lectivo: 'Día no lectivo'
};
const SUBJECT_CSS = {
  juego: 'juego', habilidades: 'habilidades', saac: 'saac',
  mediacion: 'mediacion', apoyo: 'apoyo', practicas: 'practicas'
};
// Color con el que se diseñó cada clase CSS: si la asignatura cambia de color,
// se usa el color elegido en lugar del estilo fijo.
const SUBJECT_CSS_COLORS = {
  juego: '#4295E8', habilidades: '#59B77B', saac: '#F29A43',
  mediacion: '#A77AD8', apoyo: '#E989B4', practicas: '#8C929B'
};
const SUBJECT_ICONS = ['◇', '✿', '♡', '✧', '◌', '✦', '★', '☼', '♪', '✎'];

function subjectCss(slug) {
  const css = SUBJECT_CSS[slug];
  if (!css) return '';
  const subject = (state.subjects || []).find((item) => item.slug === slug);
  if (subject && String(subject.color || '').toUpperCase() !== SUBJECT_CSS_COLORS[slug]) return '';
  return css;
}

// Colores disponibles para eventos y tareas (paleta de la app)
const TASK_COLORS = [
  { value: '', label: 'Automático (por asignatura)', class: 'pencil-gray' },
  { value: '#4295E8', label: 'Azul', class: 'pencil-blue' },
  { value: '#59B77B', label: 'Verde', class: 'pencil-green' },
  { value: '#F29A43', label: 'Naranja', class: 'pencil-orange' },
  { value: '#A77AD8', label: 'Morado', class: 'pencil-purple' },
  { value: '#E989B4', label: 'Rosa', class: 'pencil-pink' },
  { value: '#FF7F7F', label: 'Coral', class: 'pencil-red' },
  { value: '#FFB88C', label: 'Melocotón', class: 'pencil-orange' },
  { value: '#E6D72A', label: 'Amarillo', class: 'pencil-yellow' },
  { value: '#8C929B', label: 'Gris', class: 'pencil-gray' },
  { value: 'gradient-pink-blue', label: 'Kinesis', class: 'pencil-gradient-pink-blue' }
];

const EVENT_COLORS = [
  { value: '', label: 'Automático (por asignatura)', class: 'pencil-gray' },
  { value: '#4295E8', label: 'Azul', class: 'pencil-blue' },
  { value: '#59B77B', label: 'Verde', class: 'pencil-green' },
  { value: '#F29A43', label: 'Naranja', class: 'pencil-orange' },
  { value: '#A77AD8', label: 'Morado', class: 'pencil-purple' },
  { value: '#E989B4', label: 'Rosa', class: 'pencil-pink' },
  { value: '#FF7F7F', label: 'Coral', class: 'pencil-red' },
  { value: '#FFB88C', label: 'Melocotón', class: 'pencil-orange' },
  { value: '#E6D72A', label: 'Amarillo', class: 'pencil-yellow' },
  { value: '#8C929B', label: 'Gris', class: 'pencil-gray' },
  { value: 'gradient-pink-blue', label: 'Kinesis', class: 'pencil-gradient-pink-blue' }
];

const state = {
  subjects: [],
  currentView: 'inicio',
  subject: null,
  subjectData: null,
  tasks: [],
  taskFilter: { status: 'todas', q: '', priority: '' },
  calendar: { view: 'month', anchor: null, data: null },
  schedule: null,
  scheduleTimes: [],
  scheduleOriginal: '',
  evaluationCourse: '1LFP',
  tutoring: [],
  notes: [],
  reminders: { view: 'week', anchor: null, status: 'pending', category: '', items: [], currentWeek: null, today: null },
  data: null
};

/* ---------- Utilidades ---------- */

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, (character) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[character]));
}

function pad2(value) {
  return String(value).padStart(2, '0');
}

function parseISO(iso) {
  if (!iso) return null;
  const [year, month, day] = iso.slice(0, 10).split('-').map(Number);
  return new Date(year, month - 1, day || 1);
}

function todayISO() {
  const now = new Date();
  return `${now.getFullYear()}-${pad2(now.getMonth() + 1)}-${pad2(now.getDate())}`;
}

function formatShort(iso) {
  const date = parseISO(iso);
  if (!date) return '';
  return `${pad2(date.getDate())} ${MONTHS_SHORT[date.getMonth()]}`;
}

function formatLong(iso) {
  const date = parseISO(iso);
  if (!date) return '';
  return new Intl.DateTimeFormat('es-ES', {
    weekday: 'long', day: 'numeric', month: 'long', year: 'numeric'
  }).format(date);
}

function formatDateTime(value) {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat('es-ES', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
  }).format(date);
}

function humanSize(size) {
  const value = Number(size) || 0;
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

function slugById(id) {
  const subject = state.subjects.find((item) => item.id === Number(id));
  return subject ? subject.slug : '';
}

function subjectColorById(id) {
  const subject = state.subjects.find((item) => item.id === Number(id));
  return subject ? subject.color : '#8C929B';
}

function subjectDot(slug, color) {
  const css = subjectCss(slug);
  if (css) return `<i class="dot ${css}"></i>`;
  return `<i class="dot" style="background:${esc(color || '#8C929B')}"></i>`;
}

/* ---------- API ---------- */

async function api(url, options = {}) {
  const config = Object.assign({}, options);
  config.headers = Object.assign({ 'Content-Type': 'application/json' }, options.headers || {});
  if (config.body && typeof config.body !== 'string') {
    config.body = JSON.stringify(config.body);
  }
  let response;
  try {
    response = await fetch(url, config);
  } catch (error) {
    throw new Error('No se ha podido conectar con el servidor. Comprueba que la agenda sigue abierta.');
  }
  if (!response.ok) {
    let message = 'No se ha podido completar la operación.';
    let payload = null;
    try {
      payload = await response.json();
      if (payload && payload.error) message = payload.error;
    } catch (error) {
      /* Respuesta sin cuerpo JSON. */
    }
    if (response.status === 401 && payload && payload.login_required) {
      // Sesión cerrada o contraseña de MEDAC cambiada: de vuelta al inicio de sesión.
      toast(message, 'error');
      setTimeout(() => { window.location.href = '/login'; }, 1500);
    }
    throw new Error(message);
  }
  if (response.status === 204) return {};
  const type = response.headers.get('content-type') || '';
  if (!type.includes('application/json')) return response.text();
  return response.json();
}

/* ---------- Avisos y confirmaciones ---------- */

let toastTimer = null;

function toast(message, tone = '') {
  const element = $('#toast');
  element.textContent = message;
  element.className = `toast ${tone}`.trim();
  element.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { element.hidden = true; }, 4200);
}

let confirmResolve = null;

function askConfirm({ title, message, accept = 'Continuar', danger = false }) {
  $('#confirmTitle').textContent = title;
  $('#confirmMessage').textContent = message;
  const button = $('#confirmAccept');
  button.textContent = accept;
  button.className = `primary${danger ? ' danger' : ''}`;
  $('#confirm').hidden = false;
  document.body.style.overflow = 'hidden';
  return new Promise((resolve) => { confirmResolve = resolve; });
}

function closeConfirm(answer) {
  $('#confirm').hidden = true;
  document.body.style.overflow = '';
  if (confirmResolve) {
    const resolve = confirmResolve;
    confirmResolve = null;
    resolve(answer);
  }
}

/* ---------- Formularios modales ---------- */

let modalSubmitHandler = null;

function fieldHTML(field, values) {
  const value = values[field.name] ?? field.value ?? '';
  const id = `field_${field.name}`;
  const full = field.full ? ' full' : '';

  if (field.type === 'checkbox') {
    return `<div class="field check${full}">
      <input type="checkbox" id="${id}" name="${esc(field.name)}" ${value ? 'checked' : ''}>
      <label for="${id}">${esc(field.label)}</label>
    </div>`;
  }

  if (field.type === 'colorpicker') {
    return renderColorPicker(field, value);
  }

  // Usar custom select para asignaturas (subject_id) - muestran lápices de colores
  if (field.type === 'select' && field.name === 'subject_id') {
    return renderCustomSelect(field, value, values);
  }

  let control;
  if (field.type === 'select') {
    const options = (field.options || []).map((option) => {
      const optionValue = typeof option === 'object' ? option.value : option;
      const optionLabel = typeof option === 'object' ? option.label : option;
      const selected = String(optionValue) === String(value) ? ' selected' : '';
      return `<option value="${esc(optionValue)}"${selected}>${esc(optionLabel)}</option>`;
    }).join('');
    control = `<select id="${id}" name="${esc(field.name)}">${options}</select>`;
  } else if (field.type === 'textarea') {
    control = `<textarea id="${id}" name="${esc(field.name)}" placeholder="${esc(field.placeholder || '')}" rows="${field.rows || 4}">${esc(value)}</textarea>`;
  } else {
    control = `<input id="${id}" name="${esc(field.name)}" type="${field.type || 'text'}" value="${esc(value)}" placeholder="${esc(field.placeholder || '')}"${field.min ? ` min="${esc(field.min)}"` : ''}${field.max ? ` max="${esc(field.max)}"` : ''}>`;
  }

  const required = field.required ? ' *' : '';
  return `<div class="field${full}">
    <label for="${id}">${esc(field.label)}${required}</label>
    ${control}
  </div>`;
}

function openModal({ title, eyebrow = 'FORMULARIO', fields = [], values = {}, submitLabel = 'Guardar', onSubmit }) {
  $('#modalTitle').textContent = title;
  $('#modalEyebrow').textContent = eyebrow;
  $('#modalFields').innerHTML = fields.map((field) => fieldHTML(field, values)).join('');
  // Quitar botones añadidos por formularios anteriores (p. ej. «Eliminar»)
  $$('#modal .modal-extra').forEach((button) => button.remove());
  $('#modalError').hidden = true;
  $('#modalError').textContent = '';
  const submit = $('#modalSubmit');
  submit.hidden = false;
  submit.disabled = false;
  submit.dataset.label = submitLabel;
  submit.textContent = submitLabel;
  $('#modalCancel').textContent = 'Cancelar';
  modalSubmitHandler = onSubmit;
  $('#modal').hidden = false;
  document.body.style.overflow = 'hidden';
  // Inicializar custom selects después de renderizar
  setTimeout(() => {
    initCustomSelects();
    initColorPickers();
    const first = $('#modalFields input:not([type=checkbox]), #modalFields textarea, #modalFields select, #modalFields .custom-select-trigger');
    if (first) first.focus();
  }, 10);
}

function closeModal() {
  $('#modal').hidden = true;
  modalSubmitHandler = null;
  // Quitar botones extra (p. ej. «Eliminar») para que no aparezcan en el siguiente diálogo
  $$('#modal .modal-extra').forEach((button) => button.remove());
  document.body.style.overflow = '';
}

function readModalFields() {
  const values = {};
  $$('#modalFields [name]').forEach((element) => {
    if (element.type === 'checkbox') {
      values[element.name] = element.checked;
    } else if (element.tagName === 'INPUT' && element.type === 'hidden' && element.closest('.custom-select')) {
      // Custom select - leer del hidden input
      values[element.name] = element.value;
    } else {
      values[element.name] = element.value.trim();
    }
  });
  return values;
}

function showModalError(message) {
  const element = $('#modalError');
  element.textContent = message;
  element.hidden = false;
}

$('#modalForm').addEventListener('submit', async (event) => {
  event.preventDefault();
  if (!modalSubmitHandler) return;
  const submit = $('#modalSubmit');
  submit.disabled = true;
  submit.textContent = 'Guardando…';
  try {
    await modalSubmitHandler(readModalFields());
    closeModal();
  } catch (error) {
    showModalError(error.message || 'No se ha podido guardar.');
  } finally {
    submit.disabled = false;
    submit.textContent = submit.dataset.label || 'Guardar';
  }
});

/* ---------- Selector de color libre ---------- */

const GRADIENT_PINK_BLUE = 'linear-gradient(135deg,#E83E9C 0%,#EC6FB0 45%,#4295E8 100%)';

// Devuelve el valor CSS de fondo para un color guardado (hex o degradado)
function colorBackground(color) {
  if (color === 'gradient-pink-blue') return GRADIENT_PINK_BLUE;
  return color || '#8C929B';
}

// Color efectivo de un elemento: el personalizado manda sobre el de la asignatura
function itemColor(item) {
  return (item && (item.color || item.subject_color)) || '#8C929B';
}

function colorDot(item) {
  return `<i class="dot" style="background:${esc(colorBackground(itemColor(item)))}"></i>${kinesisIcon(itemColor(item))}`;
}

// Icono de patín que acompaña automáticamente al color «Kinesis»
function kinesisIcon(color) {
  return color === 'gradient-pink-blue'
    ? '<span class="kinesis-icon" role="img" aria-label="Kinesis" title="Kinesis">🛼</span>'
    : '';
}

function renderColorPicker(field, value) {
  const current = value || '';
  const presets = (field.options || []).filter((option) => option.value);
  const isPreset = !current || presets.some((option) => option.value === current);
  const customValue = /^#[0-9a-f]{6}$/i.test(current) ? current : '#4295E8';
  const swatches = presets.map((option) => `
    <button type="button" class="swatch${option.value === current ? ' selected' : ''}" data-color="${esc(option.value)}"
      title="${esc(option.label)}" aria-label="${esc(option.label)}" style="background:${esc(colorBackground(option.value))}"></button>
  `).join('');
  return `<div class="field full">
    <label>${esc(field.label)}</label>
    <div class="color-picker">
      <input type="hidden" name="${esc(field.name)}" value="${esc(current)}">
      <button type="button" class="swatch auto${current ? '' : ' selected'}" data-color="" title="Automático (color de la asignatura)" aria-label="Automático">A</button>
      ${swatches}
      <label class="swatch custom${isPreset ? '' : ' selected'}" title="Elegir cualquier color" style="${isPreset ? '' : `background:${esc(current)}`}">
        <input type="color" value="${esc(customValue)}" aria-label="Elegir cualquier color">
        <span>＋</span>
      </label>
    </div>
  </div>`;
}

function initColorPickers() {
  $$('#modalFields .color-picker').forEach((picker) => {
    const hidden = picker.querySelector('input[type=hidden]');
    const custom = picker.querySelector('.swatch.custom');
    const colorInput = custom.querySelector('input[type=color]');
    const select = (element, color) => {
      hidden.value = color;
      picker.querySelectorAll('.swatch').forEach((swatch) => swatch.classList.toggle('selected', swatch === element));
    };
    picker.querySelectorAll('button.swatch').forEach((button) => {
      button.addEventListener('click', () => {
        custom.style.background = '';
        select(button, button.dataset.color);
      });
    });
    colorInput.addEventListener('input', () => {
      custom.style.background = colorInput.value;
      select(custom, colorInput.value.toUpperCase());
    });
  });
}

/* ---------- Opciones de asignaturas ---------- */

function subjectOptions(selected, includeEmpty = true) {
  const options = [];
  if (includeEmpty) options.push({ value: '', label: 'Sin asignatura', slug: '', color: '' });
  state.subjects.forEach((subject) => {
    options.push({
      value: subject.id,
      label: `${subject.name}${subject.course ? ` · ${subject.course}` : ''}`,
      slug: subject.slug,
      color: subject.color
    });
  });
  if (selected && !options.some((option) => String(option.value) === String(selected))) {
    options.push({ value: selected, label: 'Asignatura actual', slug: '', color: '' });
  }
  return options;
}

/* ---------- Custom Select (Lápices) ---------- */

function pencilClassForSubject(slug) {
  if (!slug) return 'pencil-gray';
  return `pencil-${slug}`;
}

function pencilClassForValue(value, type) {
  // Para selects genéricos (prioridad, estado, tipo, etc.)
  const colorMap = {
    // Prioridad
    alta: 'pencil-red', media: 'pencil-orange', baja: 'pencil-green',
    // Estado tarea
    pendiente: 'pencil-orange', en_curso: 'pencil-blue', completada: 'pencil-green',
    // Tipo tarea
    tarea: 'pencil-blue', entrega: 'pencil-orange', examen: 'pencil-red', reunion: 'pencil-purple', otro: 'pencil-gray',
    // Categoría evento
    evento: 'pencil-blue', entrega: 'pencil-orange', reunion: 'pencil-purple', examen: 'pencil-red', otro: 'pencil-gray',
    // Tipo horario
    class: 'pencil-blue', break: 'pencil-orange', free: 'pencil-green',
    // Tutoría tipo
    seguimiento: 'pencil-blue', visita: 'pencil-green', reunion: 'pencil-purple',
    // Tutoría estado
    pendiente: 'pencil-orange', realizado: 'pencil-green', cancelado: 'pencil-gray',
    // Evaluaciones curso
    '1LFP': 'pencil-blue', '2LFP': 'pencil-purple'
  };
  return colorMap[value] || 'pencil-gray';
}

function renderCustomSelect(field, value, values) {
  const id = `cs_${field.name}`;
  const full = field.full ? ' full' : '';
  const isSubject = field.name === 'subject_id';
  const options = field.options || [];
  const selectedOpt = options.find((o) => String(o.value) === String(value)) || options[0] || { value: '', label: '', slug: '', color: '' };
  const selectedLabel = selectedOpt.label || (isSubject ? 'Sin asignatura' : 'Seleccionar…');
  const selectedSlug = selectedOpt.slug || '';
  const selectedColor = selectedOpt.color || '';
  const pencilClass = isSubject ? pencilClassForSubject(selectedSlug) : pencilClassForValue(value, field.name);

  let optionsHtml = '';
  options.forEach((opt) => {
    const optValue = typeof opt === 'object' ? opt.value : opt;
    const optLabel = typeof opt === 'object' ? opt.label : opt;
    const optSlug = typeof opt === 'object' ? (opt.slug || '') : '';
    const optColor = typeof opt === 'object' ? (opt.color || '') : '';
    const isSel = String(optValue) === String(value);
    const pc = isSubject ? pencilClassForSubject(optSlug) : pencilClassForValue(optValue, field.name);
    const subLabel = typeof opt === 'object' && opt.slug ? ` · ${opt.course || ''}` : '';
    optionsHtml += `
      <div class="custom-select-option${isSel ? ' selected' : ''}" data-value="${esc(optValue)}" tabindex="0" role="option" aria-selected="${isSel}">
        <div class="pencil ${pc}"></div>
        <span class="option-label">${esc(optLabel)}${subLabel}</span>
      </div>
    `;
  });

  return `
    <div class="field${full}">
      <label for="${id}_trigger">${esc(field.label)}${field.required ? ' *' : ''}</label>
      <div class="custom-select" id="${id}">
        <input type="hidden" name="${esc(field.name)}" id="${id}_hidden" value="${esc(value)}">
        <button type="button" class="custom-select-trigger" id="${id}_trigger" aria-haspopup="listbox" aria-expanded="false" aria-controls="${id}_options">
          <div class="pencil ${pencilClass}"></div>
          <span class="cs-label${value ? '' : ' placeholder'}">${esc(selectedLabel)}</span>
          <span class="chevron">▾</span>
        </button>
        <div class="custom-select-options" id="${id}_options" role="listbox">
          ${optionsHtml}
        </div>
      </div>
    </div>
  `;
}

function closeCustomSelects(except = null) {
  $$('.custom-select').forEach((sel) => {
    if (sel === except) return;
    sel.classList.remove('open');
    sel.querySelector('.custom-select-trigger').setAttribute('aria-expanded', 'false');
    sel.querySelector('.custom-select-options').classList.remove('open');
  });
}

// Un único listener global (antes se añadía uno nuevo cada vez que se abría un formulario)
document.addEventListener('click', (e) => {
  if (!e.target.closest('.custom-select')) closeCustomSelects();
});

function initCustomSelects() {
  $$('#modalFields .custom-select').forEach((selectEl) => {
    const trigger = selectEl.querySelector('.custom-select-trigger');
    const optionsEl = selectEl.querySelector('.custom-select-options');
    const hidden = selectEl.querySelector('input[type=hidden]');
    const name = hidden.name;

    // Cerrar otros selects al abrir uno
    trigger.addEventListener('click', (e) => {
      e.stopPropagation();
      const isOpen = selectEl.classList.toggle('open');
      trigger.setAttribute('aria-expanded', String(isOpen));
      optionsEl.classList.toggle('open', isOpen);
      closeCustomSelects(selectEl);
    });

    // Seleccionar opción
    optionsEl.querySelectorAll('.custom-select-option').forEach((opt) => {
      opt.addEventListener('click', () => {
        const val = opt.dataset.value;
        hidden.value = val;
        trigger.querySelector('.pencil').className = 'pencil ' + (opt.querySelector('.pencil').className.replace('pencil ', ''));
        const label = trigger.querySelector('.cs-label');
        label.textContent = opt.querySelector('.option-label').textContent;
        label.classList.toggle('placeholder', !val);
        optionsEl.querySelectorAll('.custom-select-option').forEach((o) => o.classList.toggle('selected', o === opt));
        selectEl.classList.remove('open');
        optionsEl.classList.remove('open');
        trigger.setAttribute('aria-expanded', 'false');
        // Disparar change event
        hidden.dispatchEvent(new Event('change', { bubbles: true }));
      });

      opt.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          opt.click();
        }
      });
    });
  });

}

/* ---------- Navegación ---------- */

const VIEW_TITLES = {
  inicio: 'Inicio',
  calendario: 'Calendario',
  tareas: 'Tareas y entregas',
  recordatorios: 'Recordatorios',
  horario: 'Mi horario',
  evaluaciones: 'Evaluaciones',
  tutoria: 'Prácticas y tutoría',
  notas: 'Notas',
  datos: 'Copias y datos',
  asignatura: 'Asignatura'
};

function setActiveNav(view) {
  $$('.nav').forEach((button) => button.classList.remove('active'));
  const direct = document.querySelector(`.nav[data-view="${view}"]`);
  if (direct) {
    direct.classList.add('active');
  } else if (view === 'asignatura' && state.subject) {
    const subjectButton = document.querySelector(`.nav[data-subject="${state.subject}"]`);
    if (subjectButton) subjectButton.classList.add('active');
  }
}

function scheduleIsDirty() {
  return Boolean(state.schedule) && (
    JSON.stringify(state.schedule) !== state.scheduleOriginal
    || JSON.stringify(state.scheduleTimes) !== state.scheduleTimesOriginal
  );
}

async function navigate(view) {
  if (view === 'asignatura' && !state.subject) return;
  // Al salir del horario (o recargarlo) con cambios sin guardar, se perderían
  if (state.currentView === 'horario' && scheduleIsDirty()) {
    const leave = await askConfirm({
      title: '¿Descartar los cambios del horario?',
      message: 'Tienes cambios en el horario sin guardar. Si continúas, se perderán.',
      accept: 'Descartar cambios',
      danger: true
    });
    if (!leave) return;
    state.schedule = null;
  }
  if (view !== 'asignatura') clearSubjectTheme();
  state.currentView = view;
  $$('.view').forEach((section) => section.classList.toggle('active', section.id === view));
  document.title = `${VIEW_TITLES[view] || 'Inicio'} · Mi agenda`;
  setActiveNav(view);
  $('#sidebar').classList.remove('open');
  window.scrollTo({ top: 0, behavior: 'smooth' });
  loadView(view).catch((error) => toast(error.message, 'error'));
}

function loadView(view) {
  if (view === 'inicio') return loadDashboard();
  if (view === 'calendario') return loadCalendar();
  if (view === 'tareas') return loadTasks();
  if (view === 'horario') return loadSchedule();
  if (view === 'evaluaciones') return loadEvaluations();
  if (view === 'tutoria') return loadTutoring();
  if (view === 'notas') return loadNotes();
  if (view === 'recordatorios') return loadReminders();
  if (view === 'datos') return loadData();
  if (view === 'asignatura' && state.subject) return loadSubject(state.subject);
  return Promise.resolve();
}

async function refreshCurrent() {
  await loadView(state.currentView);
}

/* ---------- Tema de color por asignatura ---------- */

function hexToRgb(hex) {
  const match = /^#?([0-9a-f]{6})$/i.exec(hex || '');
  if (!match) return null;
  const value = parseInt(match[1], 16);
  return [(value >> 16) & 255, (value >> 8) & 255, value & 255];
}

// Mezcla un color con otro (t = 0 → original, t = 1 → destino)
function mixRgb(rgb, target, t) {
  return rgb.map((channel, index) => Math.round(channel + (target[index] - channel) * t));
}

function rgbCss(rgb) {
  return `rgb(${rgb.join(',')})`;
}

function applySubjectTheme(color) {
  const root = document.documentElement;
  const rgb = hexToRgb(color);
  if (!rgb) {
    clearSubjectTheme();
    return;
  }
  root.style.setProperty('--subj', rgbCss(rgb));
  root.style.setProperty('--subj-rgb', rgb.join(','));
  // Versión oscura para textos (legible sobre blanco) y clara para degradados
  root.style.setProperty('--subj-strong', rgbCss(mixRgb(rgb, [0, 0, 0], 0.32)));
  root.style.setProperty('--subj-light', rgbCss(mixRgb(rgb, [255, 255, 255], 0.35)));
  root.dataset.subjectTheme = '';
}

function clearSubjectTheme() {
  const root = document.documentElement;
  delete root.dataset.subjectTheme;
  ['--subj', '--subj-rgb', '--subj-strong', '--subj-light'].forEach((name) => root.style.removeProperty(name));
}

function openSubject(slug) {
  state.subject = slug;
  const subject = state.subjects.find((item) => item.slug === slug);
  navigate('asignatura');
  // Se aplica ya (sin esperar a la carga) para que el cambio de color sea inmediato
  if (subject && state.currentView === 'asignatura') applySubjectTheme(subject.color);
}

/* ---------- Datos de asignaturas ---------- */

async function loadSubjects() {
  const data = await api('/api/subjects');
  state.subjects = data.subjects || [];
  renderSubjectNav();
}

function renderSubjectNav() {
  const nav = $('#subjectNav');
  if (!nav) return;
  const items = state.subjects.map((subject) => `
    <button class="nav" data-subject="${esc(subject.slug)}">${subjectDot(subject.slug, subject.color)} ${esc(subject.short_name || subject.name)}</button>
  `).join('');
  nav.innerHTML = items + `<button class="nav nav-add" type="button" data-action="manage-subjects">
    <svg class="ico"><use href="#i-plus"/></svg>${state.subjects.length ? 'Gestionar asignaturas' : 'Añadir asignaturas'}</button>`;
  if (state.currentView) setActiveNav(state.currentView);
  const legend = $('#calendarLegend');
  if (legend) {
    legend.innerHTML = state.subjects.map((subject) =>
      `<span>${subjectDot(subject.slug, subject.color)} ${esc(subject.short_name || subject.name)}</span>`).join('');
  }
}

function tileClass(slug) {
  const css = subjectCss(slug);
  return css ? `${css}-bg` : 'custom-subject';
}

/* ---------- Panel de inicio ---------- */

async function loadDashboard() {
  const data = await api('/api/dashboard');
  const firstName = (data.display_name || '').split(/\s+/)[0];
  $('#greeting').textContent = firstName ? `¡Hola, ${firstName}!` : '¡Hola!';
  $('#today').textContent = formatLong(data.date);

  $('#statPending').textContent = pad2(data.stats.pending);
  $('#statPendingNote').textContent = data.stats.due_soon
    ? `${data.stats.due_soon} próxima${data.stats.due_soon === 1 ? '' : 's'} a vencer`
    : 'Sin vencimientos cercanos';

  $('#statUpcoming').textContent = pad2(data.stats.upcoming);
  $('#statUpcomingNote').textContent = data.stats.upcoming
    ? 'Entregas y exámenes · 7 días'
    : 'Nada urgente esta semana';

  $('#statClasses').textContent = pad2(data.stats.classes_week);
  $('#statClassesNote').textContent = `${data.stats.subjects} asignatura${data.stats.subjects === 1 ? '' : 's'}`;

  renderTodaySchedule(data);
  renderUpcoming(data.upcoming);
  renderSubjectGrid(data.subjects);
  loadFichaje();
}

/* ---------- Fichaje en Factorial ---------- */

const FICHAJE_STATES = {
  out: { label: 'Sin fichar', css: 'out' },
  working: { label: 'Trabajando', css: 'working' },
  break: { label: 'En descanso', css: 'break' },
};
const FICHAJE_ACTIONS = {
  clock_in: { label: 'Fichar entrada', css: 'primary' },
  break_start: { label: 'Iniciar descanso', css: 'ghost' },
  break_end: { label: 'Volver del descanso', css: 'primary' },
  clock_out: { label: 'Fichar salida', css: 'primary danger' },
};
const fichaje = { data: null, poll: null, tick: null, busy: false, loadedAt: 0 };

function hhmm(iso) {
  return iso ? iso.slice(11, 16) : '';
}

function durationLabel(seconds) {
  const minutes = Math.max(0, Math.floor(seconds / 60));
  return `${Math.floor(minutes / 60)} h ${pad2(minutes % 60)} min`;
}

async function loadFichaje() {
  try {
    fichaje.data = await api('/api/factorial/status');
  } catch (error) {
    fichaje.data = { connected: false, login: { state: 'idle' }, error: error.message };
  }
  fichaje.loadedAt = Date.now();
  renderFichaje();
}

function fichajeWorkedSeconds() {
  const clock = fichaje.data && fichaje.data.clock;
  if (!clock) return 0;
  const extra = clock.state === 'working' ? (Date.now() - fichaje.loadedAt) / 1000 : 0;
  return clock.worked_seconds + extra;
}

function renderFichaje() {
  const body = $('#fichajeBody');
  if (!body) return;
  const data = fichaje.data || {};
  const login = data.login || {};
  clearTimeout(fichaje.poll);
  clearInterval(fichaje.tick);
  $('#fichajeRefresh').hidden = !data.connected;
  $('#fichajeDisconnect').hidden = !data.connected;

  if (login.state === 'waiting') {
    body.innerHTML = `<div class="fichaje-wait"><span class="fichaje-spinner" aria-hidden="true"></span>
      <p><strong>Se ha abierto una ventana de Microsoft Edge.</strong><br>
      Inicia sesión en Factorial con tu cuenta de Microsoft y marca «Mantener la sesión iniciada».
      La ventana se cerrará sola cuando termines.</p></div>`;
    fichaje.poll = setTimeout(loadFichaje, 2000);
    return;
  }

  if (!data.connected) {
    const message = login.state === 'error' ? login.error : data.error;
    body.innerHTML = `<div class="fichaje-connect">
      <p class="muted">Conecta tu cuenta de Factorial para fichar la entrada, los descansos y la salida desde aquí.
      Solo tendrás que iniciar sesión con Microsoft de vez en cuando.</p>
      ${message ? `<p class="fichaje-error">${esc(message)}</p>` : ''}
      <button type="button" class="primary" data-fichaje="connect">Conectar con Factorial</button>
    </div>`;
    return;
  }

  const clock = data.clock;
  if (!clock) {
    body.innerHTML = `<p class="fichaje-error">${esc(data.error || 'No se ha podido leer tu fichaje en Factorial.')}</p>
      <button type="button" class="ghost small" data-fichaje="refresh">Reintentar</button>`;
    return;
  }

  const info = FICHAJE_STATES[clock.state] || FICHAJE_STATES.out;
  const since = clock.since ? ` desde las ${hhmm(clock.since)}` : '';
  const buttons = clock.actions.map((action) => {
    const config = FICHAJE_ACTIONS[action];
    return `<button type="button" class="${config.css}" data-fichaje-action="${action}" ${fichaje.busy ? 'disabled' : ''}>${config.label}</button>`;
  }).join('');
  body.innerHTML = `<div class="fichaje-status">
      <span class="fichaje-pill ${info.css}">${info.label}${esc(since)}</span>
      <span class="fichaje-worked">Trabajado hoy: <b id="fichajeWorked">${durationLabel(fichajeWorkedSeconds())}</b></span>
      ${clock.first_in ? `<small class="muted">Primera entrada: ${hhmm(clock.first_in)}</small>` : ''}
    </div>
    <div class="fichaje-actions">${buttons}</div>
    ${data.error ? `<p class="fichaje-error">${esc(data.error)}</p>` : ''}`;
  if (clock.state === 'working') {
    fichaje.tick = setInterval(() => {
      const element = $('#fichajeWorked');
      if (element) element.textContent = durationLabel(fichajeWorkedSeconds());
    }, 30000);
  }
}

async function fichajeConnect() {
  try {
    fichaje.data = await api('/api/factorial/connect', { method: 'POST' });
  } catch (error) {
    toast(`Factorial: ${error.message}`, 'error');
    return;
  }
  renderFichaje();
}

async function fichajeAction(action) {
  const config = FICHAJE_ACTIONS[action];
  if (action === 'clock_out') {
    const ok = await askConfirm({
      title: 'Fichar salida',
      message: 'Se registrará en Factorial el final de tu jornada de hoy.',
      accept: 'Fichar salida',
    });
    if (!ok) return;
  }
  fichaje.busy = true;
  renderFichaje();
  try {
    const result = await api(`/api/factorial/clock/${action}`, { method: 'POST' });
    toast(`${result.label}: registrado en Factorial a las ${hhmm(result.clock.checked_at)}.`, 'success');
  } catch (error) {
    toast(`${config.label}: ${error.message}`, 'error');
  } finally {
    fichaje.busy = false;
    await loadFichaje();
  }
}

async function fichajeDisconnect() {
  const ok = await askConfirm({
    title: 'Desconectar Factorial',
    message: 'La agenda olvidará tu sesión de Factorial y de Microsoft en este equipo. Para volver a fichar desde aquí tendrás que conectar de nuevo.',
    accept: 'Desconectar',
    danger: true,
  });
  if (!ok) return;
  try {
    await api('/api/factorial/disconnect', { method: 'POST' });
  } catch (error) {
    toast(error.message, 'error');
  }
  loadFichaje();
}

function bindFichajeEvents() {
  $('#fichaje').addEventListener('click', (event) => {
    const action = event.target.closest('[data-fichaje-action]');
    if (action && !fichaje.busy) {
      fichajeAction(action.dataset.fichajeAction);
      return;
    }
    const command = event.target.closest('[data-fichaje]');
    if (command && command.dataset.fichaje === 'connect') fichajeConnect();
    if (command && command.dataset.fichaje === 'refresh') loadFichaje();
  });
  $('#fichajeRefresh').addEventListener('click', loadFichaje);
  $('#fichajeDisconnect').addEventListener('click', fichajeDisconnect);
}

function renderTodaySchedule(data) {
  const container = $('#todaySchedule');
  if (data.holiday_today && data.holiday_today.length) {
    container.innerHTML = data.holiday_today
      .map((holiday) => `<p class="panel-empty">${esc(holiday.name)} · ${esc(HOLIDAY_SCOPE_LABELS[holiday.scope] || holiday.scope)}</p>`)
      .join('');
    return;
  }
  if (!data.schedule.length) {
    container.innerHTML = '<p class="panel-empty">Hoy no hay clases programadas.</p>';
    return;
  }
  container.innerHTML = data.schedule.map((slot) => {
    const slug = slugById(slot.subject_id);
    const name = slot.kind === 'class'
      ? (slot.subject_short || slot.subject_name || 'Clase')
      : (slot.label || (slot.kind === 'break' ? 'Descanso' : 'Libre'));
    const detail = slot.kind === 'class' ? (slot.subject_course || '') : slot.start_time;
    return `<div class="upcoming" data-go="horario">
      <b>${esc(slot.start_time)}<small>${esc(slot.end_time)}</small></b>
      <span><strong>${esc(name)}</strong><small>${esc(detail || 'Sin curso')}</small></span>
      ${slot.kind === 'class' ? subjectDot(slug, slot.subject_color) : '<i class="dot practicas"></i>'}
    </div>`;
  }).join('');
}

function renderUpcoming(items) {
  const container = $('#upcoming');
  if (!items.length) {
    container.innerHTML = '<p class="panel-empty">No hay novedades para los próximos días.</p>';
    return;
  }
  container.innerHTML = items.map((item) => {
    const dot = item.kind === 'holiday'
      ? '<i class="holiday"></i>'
      : colorDot(item);
    return `<div class="upcoming" data-upcoming-kind="${esc(item.kind)}" data-upcoming-id="${item.id}">
      <b>${esc(formatShort(item.date).split(' ')[0])}<small>${esc((MONTHS_SHORT[parseISO(item.date).getMonth()] || '').toUpperCase())}</small></b>
      <span><strong>${esc(item.title)}</strong><small>${esc(item.subject_name || item.label || '')}</small></span>
      ${dot}
    </div>`;
  }).join('');
}

function renderSubjectGrid(subjects) {
  const container = $('#subjectGrid');
  if (!subjects.length) {
    container.innerHTML = `<div class="setup-card">
      <strong>Configura tu agenda</strong>
      <p>Pulsa <b>Sincronizar</b> para traer tus cursos del Aula Virtual, o añade tus asignaturas a mano. Después rellena «Mi horario».</p>
      <div class="setup-actions">
        <button type="button" class="primary" data-action="sync-canvas">Sincronizar con el Aula Virtual</button>
        <button type="button" class="ghost" data-action="manage-subjects">Añadir asignaturas</button>
      </div>
    </div>`;
    return;
  }
  container.innerHTML = subjects.map((subject) => `
    <button data-subject="${esc(subject.slug)}" class="tile ${tileClass(subject.slug)}" style="--sc:${esc(subject.color || '#8C929B')}">
      ${esc(subject.icon)}
      <strong>${esc(subject.name)}</strong>
      <small>${esc(subject.course || 'Sin curso')}</small>
    </button>
  `).join('');
}

/* ---------- Calendario ---------- */

async function loadCalendar() {
  const params = new URLSearchParams({ view: state.calendar.view });
  if (state.calendar.anchor) params.set('anchor', state.calendar.anchor);
  const data = await api(`/api/calendar?${params.toString()}`);
  state.calendar.data = data;
  state.calendar.anchor = data.anchor;
  renderCalendar(data);
}

function calendarItemHTML(item) {
  const typeClass = item.kind === 'evaluation' ? 'evaluation' : item.kind;
  const done = item.status === 'completada' ? ' done' : '';
  const time = item.time ? `<span class="event-time">${esc(item.time)}</span>` : '';
  // Las tareas son siempre entregas del alumnado: ya no se marca quién la hace
  const targetTitle = '';
  const targetMark = '';
  const targetClass = '';
  let eventColor = item.color || item.subject_color || '#8C929B';
  let style = '';
  if (eventColor === 'gradient-pink-blue') {
    style = 'style="background:linear-gradient(135deg,#E83E9C 0%,#EC6FB0 45%,#4295E8 100%)"';
  } else {
    style = `style="--c:${esc(eventColor)}"`;
  }
  const mark = item.kind === 'task' && item.marked ? MARK_DOT : '';
  return `<div class="event ${typeClass}${done}${targetClass}" ${style} data-kind="${esc(item.kind)}" data-id="${item.id}" title="${esc(item.title + targetTitle)}">${targetMark}<span class="event-body">${time}<span class="event-title">${kinesisIcon(eventColor)}${esc(item.title)}</span></span>${mark}</div>`;
}

// Círculo degradado turquesa-rosa para las tareas marcadas
const MARK_DOT = '<i class="mark-dot" title="Tarea marcada" aria-label="Tarea marcada"></i>';

// Estado de un recuadro de nota: 'open' (abierto), 'collapsed' (minimizado)
// o 'hidden' (cerrado). Si no hay estado guardado, los días ya pasados se
// muestran minimizados para que no ocupen tanto espacio.
function resolveNoteState(day, entry, autoCollapse = true) {
  if (entry.state === 'collapsed' || entry.state === 'hidden') return entry.state;
  if (entry.state === 'open') return 'open';
  return autoCollapse && day.date < todayKey() ? 'collapsed' : 'open';
}

// El día de hoy según el servidor (evita desfases de zona horaria).
function todayKey() {
  return (state.calendar.data && state.calendar.data.today) || todayISO();
}

// Notas del día: un recuadro por cada asignatura que se imparte ese día
// (según «Mi horario») y otro para notas generales.
function dayNoteEditor(day, rows = 3, prefix = '', autoCollapse = true) {
  const hidden = (day.hidden_notes || []).map((entry) => `
    <button type="button" class="note-hidden-chip" data-note-action="restore" data-date="${esc(day.date)}" data-note-subject-id="${entry.subject_id}"
      title="Volver a mostrar la nota de ${esc(entry.subject_short || entry.subject_name)}">${esc(entry.subject_short || entry.subject_name)}</button>`).join('');

  const classes = (day.class_notes || []).map((entry) => {
    const name = entry.subject_short || entry.subject_name;
    const time = entry.times.length ? esc(entry.times[0].split('–')[0]) : '';
    const state = resolveNoteState(day, entry, autoCollapse);
    const color = esc(entry.subject_color || '#8C929B');
    if (state === 'collapsed') {
      const preview = (entry.body || '').trim();
      return `
      <div class="day-note class-note is-collapsed" data-note-date="${esc(day.date)}" data-note-subject-id="${entry.subject_id}" style="--c:${color}">
        <button type="button" class="note-expand" data-note-action="expand" data-date="${esc(day.date)}" data-note-subject-id="${entry.subject_id}"
          title="Ampliar la nota de ${esc(name)}">
          <strong>${esc(name)}</strong>
          ${time ? `<small>${time}</small>` : ''}
          ${preview ? `<em>${esc(preview.slice(0, 60))}${preview.length > 60 ? '…' : ''}</em>` : '<em class="is-empty">Sin notas</em>'}
        </button>
        <button type="button" class="note-tool note-tool-close" data-note-action="hide" data-date="${esc(day.date)}" data-note-subject-id="${entry.subject_id}"
          title="Cerrar: esta asignatura no se imparte este día" aria-label="Cerrar la nota de ${esc(name)}">✕</button>
      </div>`;
    }
    return `
    <div class="day-note class-note" data-note-date="${esc(day.date)}" data-note-subject-id="${entry.subject_id}" style="--c:${color}">
      <div class="class-note-bar">
        <label class="class-note-label" for="${prefix}cn_${esc(day.date)}_${entry.subject_id}">
          <i class="dot" style="background:${color}"></i>
          <strong>${esc(name)}</strong>
          ${time ? `<small>${time}</small>` : ''}
        </label>
        <span class="class-note-tools">
          <button type="button" class="note-tool" data-note-action="collapse" data-date="${esc(day.date)}" data-note-subject-id="${entry.subject_id}"
            title="Minimizar este recuadro" aria-label="Minimizar la nota de ${esc(name)}">⌃</button>
          <button type="button" class="note-tool note-tool-close" data-note-action="hide" data-date="${esc(day.date)}" data-note-subject-id="${entry.subject_id}"
            title="Cerrar: esta asignatura no se imparte este día" aria-label="Cerrar la nota de ${esc(name)}">✕</button>
        </span>
      </div>
      <textarea class="day-note-text" id="${prefix}cn_${esc(day.date)}_${entry.subject_id}" data-note-date="${esc(day.date)}" data-subject-id="${entry.subject_id}"
        rows="${Math.max(2, rows - 1)}" maxlength="5000" placeholder="¿Qué vas a hacer en ${esc(name)}?"
        title="${esc(entry.subject_name)}${entry.times.length ? ` · ${esc(entry.times.join(', '))}` : ''}">${esc(entry.body || '')}</textarea>
      <small class="day-note-status" aria-live="polite"></small>
    </div>`;
  }).join('');

  // Con dos o más asignaturas, un botón para minimizar o abrir todas a la vez
  const entries = day.class_notes || [];
  const anyOpen = entries.some((entry) => resolveNoteState(day, entry, autoCollapse) === 'open');
  const bulk = entries.length >= 2
    ? `<button type="button" class="notes-bulk" data-note-action="${anyOpen ? 'collapse-all' : 'expand-all'}" data-date="${esc(day.date)}"
        title="${anyOpen ? 'Minimizar todas las notas de este día' : 'Abrir todas las notas de este día'}">${anyOpen ? '⌃ Minimizar todas' : '⌄ Abrir todas'}</button>`
    : '';
  // En días ya pasados, si «Otras notas» está vacía, se queda en una sola línea
  const slim = autoCollapse && day.date < todayKey() && !day.day_note;

  return `<div class="day-notes" data-notes-day="${esc(day.date)}" data-notes-rows="${rows}" data-notes-prefix="${esc(prefix)}" data-notes-auto="${autoCollapse ? '1' : '0'}">
    ${bulk}
    ${classes}
    <div class="day-note${slim ? ' is-slim' : ''}">
      <label class="class-note-head" for="${prefix}dn_${esc(day.date)}"><strong>${classes ? 'Otras notas' : 'Notas del día'}</strong></label>
      <textarea class="day-note-text" id="${prefix}dn_${esc(day.date)}" data-note-date="${esc(day.date)}" rows="${slim ? 1 : (classes ? 2 : rows)}" maxlength="5000"
        placeholder="Recordatorios, avisos…" aria-label="Notas del ${esc(formatLong(day.date))}">${esc(day.day_note || '')}</textarea>
      <small class="day-note-status" aria-live="polite"></small>
    </div>
    ${hidden ? `<div class="notes-hidden"><span>Cerradas:</span>${hidden}</div>` : ''}
  </div>`;
}

// Icono de las notas propias: pósit amarillo con lápiz (las tareas no llevan icono).
const NOTE_SVG = '<svg class="note-svg" viewBox="0 0 24 24" role="img" aria-label="Nota"><path fill="#FFD84D" stroke="#7A5B00" stroke-width="1.3" stroke-linejoin="round" d="M4 3.5h13.5a1 1 0 0 1 1 1V14l-5.5 6H4.5a1 1 0 0 1-1-1V4.5a1 1 0 0 1 .5-1z"/><path fill="#F0B800" stroke="#7A5B00" stroke-width="1.3" stroke-linejoin="round" d="M18.5 14H14a1 1 0 0 0-1 1v5z"/><path d="M7 8h7.5M7 11h5" stroke="#7A5B00" stroke-width="1.4" stroke-linecap="round"/><path fill="#E0475B" stroke="#5a1d26" stroke-width="1" stroke-linejoin="round" d="m15.2 21.3.6-2.7 5.8-5.8a1.4 1.4 0 0 1 2 2l-5.8 5.8z"/><path fill="#F6D7B0" d="m15.2 21.3.6-2.7 2.1 2.1z"/></svg>';

// Casilla del mes: cada nota escrita sale como un recuadro de color (como las tareas).
// Al pulsarla se abre el panel del día con esa nota lista para editar.
function monthNoteChips(day) {
  const chips = (day.class_notes || [])
    .filter((entry) => entry.body)
    .map((entry) => {
      const name = entry.subject_short || entry.subject_name;
      return `<div class="note-chip" style="--c:${esc(entry.subject_color || '#8C929B')}" data-note-subject="${entry.subject_id}"
        title="${esc(`${name}: ${entry.body}`)} (pulsa para editar)">${NOTE_SVG} <b>${esc(name)}:</b> ${esc(entry.body)}</div>`;
    });
  if (day.day_note) {
    chips.push(`<div class="note-chip general" data-note-subject="" title="${esc(day.day_note)} (pulsa para editar)">${NOTE_SVG} ${esc(day.day_note)}</div>`);
  }
  return chips.join('');
}

const dayNoteTimers = {};

function noteKey(textarea) {
  return `${textarea.dataset.noteDate}|${textarea.dataset.subjectId || ''}`;
}

async function saveDayNote(textarea) {
  const dateKey = textarea.dataset.noteDate;
  const subjectId = textarea.dataset.subjectId ? Number(textarea.dataset.subjectId) : null;
  const body = textarea.value.trim();
  const day = findDay(dateKey);
  const entry = day && subjectId ? (day.class_notes || []).find((item) => item.subject_id === subjectId) : null;
  const previous = subjectId ? (entry ? entry.body : null) : (day ? day.day_note : null);
  if ((previous || '') === body && previous !== null) return;
  const status = textarea.parentElement.querySelector('.day-note-status');
  const url = subjectId ? `/api/class-notes/${dateKey}/${subjectId}` : `/api/day-notes/${dateKey}`;
  try {
    await api(url, { method: 'PUT', body: { body } });
    if (entry) entry.body = body;
    else if (day && !subjectId) day.day_note = body;
    // Mantener sincronizado el otro recuadro de la misma nota (semana ↔ panel)
    $$('.day-note-text').forEach((other) => {
      if (other !== textarea && noteKey(other) === noteKey(textarea)) other.value = body;
    });
    // Desde el panel del día (vista mes), refrescar la vista previa de la casilla
    if (textarea.closest('#modal') && state.calendar.data) renderCalendar(state.calendar.data);
    if (status) {
      status.textContent = 'Guardado ✓';
      setTimeout(() => { status.textContent = ''; }, 1800);
    }
  } catch (error) {
    if (status) status.textContent = '';
    toast(error.message, 'error');
  }
}

function scheduleDayNoteSave(textarea) {
  const key = noteKey(textarea);
  clearTimeout(dayNoteTimers[key]);
  dayNoteTimers[key] = setTimeout(() => saveDayNote(textarea), 700);
}

function flushDayNoteSave(textarea) {
  clearTimeout(dayNoteTimers[noteKey(textarea)]);
  return saveDayNote(textarea);
}

// ---- Estado de los recuadros de notas (minimizar / cerrar) ----

// Guarda el estado ('open', 'collapsed' o 'hidden') de una nota de clase.
async function saveNoteState(dateKey, subjectId, state) {
  try {
    await api(`/api/class-notes/${dateKey}/${subjectId}/state`, { method: 'PUT', body: { state } });
    return true;
  } catch (error) {
    toast(error.message, 'error');
    return false;
  }
}

// Guarda en el servidor lo que se esté escribiendo en ese día antes de
// repintar los recuadros, para no perder texto con el guardado pendiente.
async function flushPendingNotes(dateKey) {
  const pending = $$('.day-note-text[data-note-date]').filter((textarea) => textarea.dataset.noteDate === dateKey);
  await Promise.all(pending.map((textarea) => flushDayNoteSave(textarea)));
}

// Vuelve a pintar los recuadros de notas de un día concreto (semana y panel).
function refreshDayNotes(dateKey) {
  const day = findDay(dateKey);
  if (!day) return;
  $$('.day-notes[data-notes-day]').forEach((block) => {
    if (block.dataset.notesDay !== dateKey) return;
    const rows = Number(block.dataset.notesRows) || 3;
    const prefix = block.dataset.notesPrefix || '';
    const autoCollapse = block.dataset.notesAuto !== '0';
    block.outerHTML = dayNoteEditor(day, rows, prefix, autoCollapse);
  });
}

function byScheduleOrder(a, b) {
  return (a.order ?? 0) - (b.order ?? 0);
}

// Botones de minimizar / cerrar / restaurar de los recuadros de notas.
async function handleClassNoteAction(button) {
  const action = button.dataset.noteAction;
  const dateKey = button.dataset.date;
  const subjectId = Number(button.dataset.noteSubjectId);
  const day = findDay(dateKey);
  if (!day) return;

  // El texto que se esté escribiendo se guarda antes de repintar.
  await flushPendingNotes(dateKey);

  if (action === 'collapse-all' || action === 'expand-all') {
    const target = action === 'collapse-all' ? 'collapsed' : 'open';
    const entries = day.class_notes || [];
    const results = await Promise.all(entries.map((entry) => saveNoteState(dateKey, entry.subject_id, target)));
    entries.forEach((entry, index) => { if (results[index]) entry.state = target; });
  } else if (action === 'restore') {
    const entry = (day.hidden_notes || []).find((item) => item.subject_id === subjectId);
    if (!entry) return;
    if (!await saveNoteState(dateKey, subjectId, 'open')) return;
    day.hidden_notes = day.hidden_notes.filter((item) => item.subject_id !== subjectId);
    entry.state = 'open';
    // Vuelve a su sitio según el horario, no al final
    day.class_notes = (day.class_notes || []).concat(entry).sort(byScheduleOrder);
  } else if (action === 'hide') {
    const entry = (day.class_notes || []).find((item) => item.subject_id === subjectId);
    if (!entry) return;
    if (!await saveNoteState(dateKey, subjectId, 'hidden')) return;
    day.class_notes = day.class_notes.filter((item) => item.subject_id !== subjectId);
    entry.state = 'hidden';
    day.hidden_notes = (day.hidden_notes || []).concat(entry);
  } else if (action === 'collapse' || action === 'expand') {
    const state = action === 'collapse' ? 'collapsed' : 'open';
    if (!await saveNoteState(dateKey, subjectId, state)) return;
    const entry = (day.class_notes || []).find((item) => item.subject_id === subjectId);
    if (entry) entry.state = state;
  }
  refreshDayNotes(dateKey);
}

function renderCalendar(data) {
  const container = $('#calendar');
  $('#monthTitle').textContent = data.title;
  $('#prev').disabled = !data.can_prev;
  $('#next').disabled = !data.can_next;
  $$('#calendarSwitch [data-calview]').forEach((button) => {
    button.classList.toggle('chosen', button.dataset.calview === data.view);
  });

  if (data.view === 'week') {
    container.className = 'calendar week';
    container.innerHTML = data.days.map((day) => {
      const classes = ['weekday-col'];
      if (day.holidays.length) classes.push('is-holiday');
      if (day.date === data.today) classes.push('is-today');
      const holidays = day.holidays
        .map((holiday) => `<div class="day-holiday">${esc(holiday.name)}</div>`)
        .join('');
      const items = day.items.length
        ? day.items.map(calendarItemHTML).join('')
        : '<div class="week-empty">Sin eventos</div>';
      return `<div class="${classes.join(' ')}" data-day="${day.date}">
        <div class="weekday-head">${esc(WEEKDAYS_SHORT[day.weekday - 1])}<small>${esc(formatShort(day.date))}</small></div>
        <div class="week-items">${holidays}${items}</div>
        ${dayNoteEditor(day, 4)}
      </div>`;
    }).join('');
    return;
  }

  if (data.view === 'year') {
    container.className = 'calendar year';
    const byDate = {};
    data.days.forEach((day) => { byDate[day.date] = day; });
    container.innerHTML = `<div class="yeargrid">${data.months.map((month) => {
      const first = new Date(month.year, month.month - 1, 1);
      const offset = (first.getDay() + 6) % 7;
      const total = month.days_in_month;
      let cells = '';
      for (let index = 0; index < offset; index += 1) cells += '<span class="empty"></span>';
      for (let dayNumber = 1; dayNumber <= total; dayNumber += 1) {
        const key = `${month.year}-${pad2(month.month)}-${pad2(dayNumber)}`;
        const day = byDate[key];
        const holidays = day && day.holidays.length > 0;
        const marks = day && day.items.length > 0;
        let css = '';
        let markStyle = '';
        let markTitle = '';
        if (holidays && marks) {
          css = 'mark-hol';
          markTitle = day.holidays.map((holiday) => holiday.name).join(', ');
          // Use first task color for the mark
          const taskColor = itemColor(day.items.find(i => i.kind === 'task') || day.items[0]);
          markStyle = `style="--mark:${esc(colorBackground(taskColor))}"`;
        } else if (holidays) {
          css = 'hol';
          markTitle = day.holidays.map((holiday) => holiday.name).join(', ');
        } else if (marks) {
          css = 'mark';
          const taskColor = itemColor(day.items.find(i => i.kind === 'task') || day.items[0]);
          markStyle = `style="--mark:${esc(colorBackground(taskColor))}"`;
          markTitle = day.items.map(i => i.title).join(', ');
        }
        cells += `<span class="${css}" ${markStyle} title="${esc(markTitle)}">${dayNumber}</span>`;
      }
      return `<div class="yearmonth" data-month="${month.year}-${pad2(month.month)}">
        <h3>${esc(capitalize(month.label))}</h3>
        <div class="mini">
          ${['L', 'M', 'X', 'J', 'V', 'S', 'D'].map((letter) => `<span class="mini-head">${letter}</span>`).join('')}
          ${cells}
        </div>
      </div>`;
    }).join('')}</div>`;
    return;
  }

  container.className = 'calendar';
  let html = data.weekdays_short.map((weekday) => `<div class="calhead">${esc(weekday)}</div>`).join('');
  data.days.forEach((day) => {
    const classes = ['day'];
    if (!day.in_month) classes.push('mutedday');
    if (day.weekend) classes.push('weekend');
    if (day.holidays.length) classes.push('is-holiday');
    if (day.date === data.today) classes.push('today');
    const holidays = day.holidays
      .map((holiday) => `<div class="day-holiday">${esc(holiday.name)}</div>`)
      .join('');
    // Mostrar todas las tareas y eventos del día; la fila crece si hace falta
    const shown = day.items.map(calendarItemHTML).join('');
    const note = monthNoteChips(day);
    html += `<div class="${classes.join(' ')}" data-day="${day.date}">
      <div class="day-top"><span class="daynum">${day.day}</span><span class="day-add">＋</span></div>
      ${holidays}${note}${shown}
    </div>`;
  });
  container.innerHTML = html;
}

function capitalize(value) {
  return value ? value.charAt(0).toUpperCase() + value.slice(1) : '';
}

function findDay(dateKey) {
  if (!state.calendar.data) return null;
  return state.calendar.data.days.find((day) => day.date === dateKey) || null;
}

function openCalendarItem(kind, id) {
  const data = state.calendar.data;
  if (!data) return;
  let found = null;
  for (const day of data.days) {
    found = day.items.find((item) => item.kind === kind && item.id === id);
    if (found) break;
  }
  if (!found) return;
  if (kind === 'task') {
    openTaskForm({
      id: found.id,
      title: found.title,
      description: found.description,
      subject_id: found.subject_id,
      kind: found.category,
      target: found.target,
      priority: found.priority,
      status: found.status,
      due_date: found.date,
      due_time: found.time,
      color: found.color,
      marked: found.marked
    });
  } else if (kind === 'event') {
    openEventForm({
      id: found.id,
      title: found.title,
      description: found.description,
      start_date: found.date,
      end_date: found.end_date,
      start_time: found.time,
      end_time: found.end_time || '',
      all_day: found.all_day,
      subject_id: found.subject_id,
      category: found.category,
      color: found.color
    });
  } else if (kind === 'evaluation') {
    state.evaluationCourse = found.subject_course || '1LFP';
    navigate('evaluaciones');
  }
}

function openDayPanel(dateKey) {
  const day = findDay(dateKey);
  if (!day) return;
  const holidays = day.holidays.map((holiday) => `
    <div class="day-modal-item">
      <i class="holiday"></i>
      <span><strong>${esc(holiday.name)}</strong><small>${esc(holiday.scope_label || 'No lectivo')}</small></span>
    </div>
  `).join('');
  const items = day.items.length ? day.items.map((item) => {
    const targetClass = '';
    const targetIcon = '';
    return `
    <div class="day-modal-item" data-kind="${esc(item.kind)}" data-id="${item.id}">
      ${colorDot(item)}
      <span>
        <strong>${esc(item.title)}${item.kind === 'task' && item.marked ? ` ${MARK_DOT}` : ''}</strong>
        <small>
          ${targetIcon ? `<span class="mini-target ${targetClass}">${targetIcon}</span>` : ''}
          ${esc(item.subject_name || '')}${item.time ? ` · ${esc(item.time)}` : ''}
        </small>
      </span>
      <span class="kind-badge">${esc(item.category_label || '')}</span>
    </div>
    `;
  }).join('') : '<p class="panel-empty">No hay tareas ni eventos este día.</p>';

  $$('#modal .modal-extra').forEach((button) => button.remove());
  $('#modalTitle').textContent = formatLong(dateKey);
  $('#modalEyebrow').textContent = 'DÍA DEL CALENDARIO';
  $('#modalFields').innerHTML = `${holidays}${items}
    <div class="day-modal-note">
      <p class="eyebrow">NOTAS DEL DÍA</p>
      ${dayNoteEditor(day, 4, 'm', false)}
    </div>
    <div class="day-modal-actions">
      <button type="button" class="primary" id="dayAddEvent">＋ Evento</button>
      <button type="button" class="ghost" id="dayAddTask">＋ Tarea</button>
    </div>`;
  $('#modalError').hidden = true;
  $('#modalSubmit').hidden = true;
  $('#modalCancel').textContent = 'Cerrar';
  modalSubmitHandler = null;
  $('#modal').hidden = false;
  document.body.style.overflow = 'hidden';

  $('#modalFields').querySelectorAll('.day-modal-item[data-kind]').forEach((element) => {
    element.addEventListener('click', () => {
      const kind = element.dataset.kind;
      const id = Number(element.dataset.id);
      closeModal();
      openCalendarItem(kind, id);
    });
  });
  $('#dayAddEvent').addEventListener('click', () => {
    closeModal();
    openEventForm(null, dateKey);
  });
  $('#dayAddTask').addEventListener('click', () => {
    closeModal();
    openTaskForm(null, dateKey);
  });
}

/* ---------- Tareas ---------- */

async function loadTasks() {
  const params = new URLSearchParams();
  if (state.taskFilter.status && state.taskFilter.status !== 'todas') {
    params.set('status', state.taskFilter.status);
  }
  if (state.taskFilter.q) params.set('q', state.taskFilter.q);
  if (state.taskFilter.priority) params.set('priority', state.taskFilter.priority);
  const data = await api(`/api/tasks?${params.toString()}`);
  state.tasks = data.tasks || [];
  updateTaskFilterCounts(data.counts || {});
  renderTaskList();
}

function updateTaskFilterCounts(counts) {
  const labels = { todas: 'Todas', pendiente: 'Pendientes', en_curso: 'En curso', completada: 'Completadas' };
  $$('#taskFilters [data-status]').forEach((button) => {
    const key = button.dataset.status;
    button.textContent = `${labels[key]}　${counts[key] ?? 0}`;
    button.classList.toggle('chosen', state.taskFilter.status === key);
  });
}

function taskRow(task) {
  const today = todayISO();
  const overdue = task.due_date && task.status !== 'completada' && task.due_date < today;
  const checked = task.status === 'completada' ? 'checked' : '';
  const priorityClass = task.priority === 'alta' ? 'high' : task.priority === 'baja' ? 'low' : '';
  const due = task.due_date ? formatShort(task.due_date) : 'Sin fecha';
  const dueTime = task.due_time ? ` ${task.due_time}` : '';
  const subject = task.subject_name
    ? `${task.subject_name}${task.subject_course ? ` · ${task.subject_course}` : ''}`
    : 'Sin asignatura';
  // Color handling for task row background
  let rowStyle = '';
  let textColor = '';
  if (task.color === 'gradient-pink-blue') {
    rowStyle = 'background:linear-gradient(135deg,#E83E9C 0%,#EC6FB0 45%,#4295E8 100%)';
    textColor = 'color:white';
  } else if (task.color) {
    rowStyle = `background:${esc(task.color)}`;
    textColor = 'color:white';
  }
  
  return `<div class="task${task.status === 'completada' ? ' done' : ''}${overdue ? ' overdue' : ''}" data-id="${task.id}" style="${rowStyle};${textColor}">
    <i class="${checked}" data-action="toggle" role="button" tabindex="0" title="${task.status === 'completada' ? 'Marcar como pendiente' : 'Marcar como completada'}">${task.status === 'completada' ? '✓' : ''}</i>
    <span>
      <strong>${kinesisIcon(task.color)}${esc(task.title)}${task.marked ? ` ${MARK_DOT}` : ''}</strong>
      <small>${esc(subject)}</small>
      <div class="task-meta">
        <label class="${priorityClass}">${esc(TASK_PRIORITY_LABELS[task.priority] || task.priority)}</label>
        <small>${esc(TASK_KIND_LABELS[task.kind] || task.kind)} · ${esc(TASK_STATUS_LABELS[task.status] || task.status)}</small>
      </div>
    </span>
    <time>${esc(due + dueTime)}</time>
    <div class="task-actions">
      <button type="button" class="icon-btn" data-action="edit" title="Editar tarea">✎</button>
      <button type="button" class="icon-btn" data-action="delete" title="Eliminar tarea">✕</button>
    </div>
  </div>`;
}

function renderTaskList() {
  const container = $('#taskList');
  if (!state.tasks.length) {
    container.innerHTML = `<div class="empty">
      <b>☷</b>
      <h2>No hay tareas con estos filtros</h2>
      <p>Puedes crear una nueva tarea o cambiar los filtros de la lista.</p>
    </div>`;
    return;
  }
  container.innerHTML = state.tasks.map(taskRow).join('');
}

async function toggleTask(task) {
  const next = task.status === 'completada' ? 'pendiente' : 'completada';
  try {
    await api(`/api/tasks/${task.id}/status`, { method: 'PATCH', body: { status: next } });
    toast(next === 'completada' ? 'Tarea completada.' : 'Tarea reabierta.', 'success');
    await loadTasks();
  } catch (error) {
    toast(error.message, 'error');
  }
}

async function deleteTask(task) {
  const confirmed = await askConfirm({
    title: '¿Eliminar esta tarea?',
    message: `Se eliminará «${task.title}». Esta acción no se puede deshacer.`,
    accept: 'Eliminar',
    danger: true
  });
  if (!confirmed) return;
  try {
    await api(`/api/tasks/${task.id}`, { method: 'DELETE' });
    toast('Tarea eliminada.', 'success');
    await refreshCurrent();
  } catch (error) {
    toast(error.message, 'error');
  }
}

function openTaskForm(task = null, presetDate = null, presetSubject = null) {
  const isEdit = Boolean(task && task.id);
  // Una tarea es una entrega del alumnado; lo que hace la docente va en las notas del día.
  const kindOptions = ['entrega', 'examen', 'otro'];
  if (task && task.kind && !kindOptions.includes(task.kind)) kindOptions.push(task.kind);
  openModal({
    title: isEdit ? 'Editar tarea' : 'Nueva tarea',
    eyebrow: 'TAREAS Y ENTREGAS',
    submitLabel: isEdit ? 'Guardar cambios' : 'Crear tarea',
    fields: [
      { name: 'title', label: 'Título', type: 'text', required: true, full: true, placeholder: 'Por ejemplo: preparar material de aula' },
      { name: 'description', label: 'Descripción', type: 'textarea', full: true, placeholder: 'Detalles opcionales' },
      { name: 'subject_id', label: 'Asignatura', type: 'select', options: subjectOptions(task ? task.subject_id : presetSubject) },
      { name: 'kind', label: 'Tipo', type: 'select', options: kindOptions.map((value) => ({ value, label: TASK_KIND_LABELS[value] || value })) },
      { name: 'priority', label: 'Prioridad', type: 'select', options: Object.entries(TASK_PRIORITY_LABELS).map(([value, label]) => ({ value, label })) },
      { name: 'status', label: 'Estado', type: 'select', options: Object.entries(TASK_STATUS_LABELS).map(([value, label]) => ({ value, label })) },
      { name: 'due_date', label: 'Fecha de entrega', type: 'date' },
      { name: 'due_time', label: 'Hora de entrega (hasta 23:59)', type: 'time' },
      { name: 'color', label: 'Color', type: 'colorpicker', options: TASK_COLORS },
      { name: 'marked', label: 'Marcar con el círculo turquesa y rosa', type: 'checkbox', full: true }
    ],
    values: {
      title: task ? task.title : '',
      description: task ? task.description : '',
      subject_id: task ? (task.subject_id ?? '') : (presetSubject || ''),
      kind: task ? task.kind : 'entrega',
      priority: task ? task.priority : 'media',
      status: task ? task.status : 'pendiente',
      due_date: task ? (task.due_date || '') : (presetDate || ''),
      due_time: task ? (task.due_time || '') : '',
      color: task ? (task.color || '') : '',
      marked: task ? Boolean(task.marked) : false
    },
    onSubmit: async (values) => {
      if (!values.title) throw new Error('El título es obligatorio.');
      const payload = {
        title: values.title,
        description: values.description,
        subject_id: values.subject_id || null,
        kind: values.kind,
        target: 'alumno',
        priority: values.priority,
        status: values.status,
        due_date: values.due_date || null,
        due_time: values.due_time || null,
        color: values.color || null,
        marked: Boolean(values.marked)
      };
      if (isEdit) {
        await api(`/api/tasks/${task.id}`, { method: 'PUT', body: payload });
        toast('Tarea actualizada.', 'success');
      } else {
        await api('/api/tasks', { method: 'POST', body: payload });
        toast('Tarea creada.', 'success');
      }
      await refreshCurrent();
    }
  });
}

/* ---------- Eventos ---------- */

function openEventForm(event = null, presetDate = null) {
  const isEdit = Boolean(event && event.id);
  openModal({
    title: isEdit ? 'Editar evento' : 'Nuevo evento',
    eyebrow: 'CALENDARIO',
    submitLabel: isEdit ? 'Guardar cambios' : 'Crear evento',
    fields: [
      { name: 'title', label: 'Título', type: 'text', required: true, full: true, placeholder: 'Por ejemplo: reunión de seguimiento' },
      { name: 'description', label: 'Descripción', type: 'textarea', full: true },
      { name: 'start_date', label: 'Fecha de inicio', type: 'date', required: true },
      { name: 'end_date', label: 'Fecha de fin', type: 'date' },
      { name: 'start_time', label: 'Hora de inicio', type: 'time' },
      { name: 'end_time', label: 'Hora de fin', type: 'time' },
      { name: 'all_day', label: 'Todo el día', type: 'checkbox', full: true },
      { name: 'subject_id', label: 'Asignatura', type: 'select', options: subjectOptions(event ? event.subject_id : null) },
      { name: 'category', label: 'Categoría', type: 'select', options: Object.entries(EVENT_CATEGORY_LABELS).map(([value, label]) => ({ value, label })) },
      { name: 'color', label: 'Color', type: 'colorpicker', options: EVENT_COLORS }
    ],
    values: {
      title: event ? event.title : '',
      description: event ? event.description : '',
      start_date: event ? event.start_date : (presetDate || todayISO()),
      end_date: event ? (event.end_date || '') : '',
      start_time: event ? (event.start_time || '') : '',
      end_time: event ? (event.end_time || '') : '',
      all_day: event ? Boolean(event.all_day) : true,
      subject_id: event ? (event.subject_id ?? '') : '',
      category: event ? event.category : 'evento',
      color: event ? (event.color || '') : ''
    },
    onSubmit: async (values) => {
      if (!values.title) throw new Error('El título es obligatorio.');
      if (!values.start_date) throw new Error('La fecha de inicio es obligatoria.');
      const payload = {
        title: values.title,
        description: values.description,
        start_date: values.start_date,
        end_date: values.end_date || null,
        start_time: values.start_time || null,
        end_time: values.end_time || null,
        all_day: values.all_day,
        subject_id: values.subject_id || null,
        category: values.category,
        color: values.color || null
      };
      if (isEdit) {
        await api(`/api/events/${event.id}`, { method: 'PUT', body: payload });
        toast('Evento actualizado.', 'success');
      } else {
        await api('/api/events', { method: 'POST', body: payload });
        toast('Evento creado.', 'success');
      }
      await refreshCurrent();
    }
  });
  // Add delete button for existing events
  // Botón «Eliminar» para eventos existentes (se añade ya, sin esperar a un temporizador)
  if (isEdit) {
    const actions = $('#modal .modal-actions');
    if (actions) {
      const deleteBtn = document.createElement('button');
      deleteBtn.type = 'button';
      deleteBtn.className = 'primary danger modal-extra';
      deleteBtn.textContent = 'Eliminar';
      deleteBtn.onclick = async () => {
        const confirmed = await askConfirm({
          title: '¿Eliminar este evento?',
          message: `Se eliminará «${event.title}». Esta acción no se puede deshacer.`,
          accept: 'Eliminar',
          danger: true
        });
        if (!confirmed) return;
        try {
          await api(`/api/events/${event.id}`, { method: 'DELETE' });
          toast('Evento eliminado.', 'success');
          closeModal();
          await refreshCurrent();
        } catch (error) {
          toast(error.message, 'error');
        }
      };
      actions.insertBefore(deleteBtn, actions.firstChild);
    }
  }
}

/* ---------- Horario ---------- */

async function loadSchedule() {
  const data = await api('/api/schedule');
  state.scheduleTimes = data.times || [];
  state.scheduleTimesOriginal = JSON.stringify(state.scheduleTimes);
  state.schedule = (data.slots || []).map((slot) => Object.assign({}, slot));
  state.scheduleOriginal = JSON.stringify(state.schedule);
  renderSchedule();
}

function slotFor(weekday, startTime) {
  return state.schedule.find(
    (slot) => slot.weekday === weekday && slot.start_time === startTime
  ) || null;
}

function lessonHTML(slot) {
  if (!slot) return '<div class="lesson rest">Libre</div>';
  if (slot.kind === 'break') {
    return `<div class="lesson rest">${esc(slot.label || 'Descanso')}</div>`;
  }
  if (slot.kind === 'free') {
    return `<div class="lesson rest">${esc(slot.label || 'Libre')}</div>`;
  }
  const slug = slugById(slot.subject_id);
  const css = subjectCss(slug) || 'custom-subject';
  const style = ` style="--sc:${esc(slot.subject_color || '#8C929B')}"`;
  return `<div class="lesson ${css}"${style}><b>${esc(slot.subject_short || slot.subject_name || 'Clase')}</b>${esc(slot.subject_course || '')}</div>`;
}

function renderSchedule() {
  const container = $('#schedule');
  if (!state.scheduleTimes.length) {
    container.innerHTML = '<p class="panel-empty">No hay franjas horarias.</p>';
    return;
  }
  const days = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes'];
  let html = '<div class="slot head">HORA</div>';
  html += days.map((day) => `<div class="slot head">${day}</div>`).join('');
  state.scheduleTimes.forEach((time) => {
    html += `<div class="slot time">${esc(time.start)}–${esc(time.end)}</div>`;
    for (let weekday = 1; weekday <= 5; weekday += 1) {
      const slot = slotFor(weekday, time.start);
      html += `<div class="slot editable" data-weekday="${weekday}" data-start="${esc(time.start)}" data-end="${esc(time.end)}">
        ${lessonHTML(slot)}
      </div>`;
    }
  });
  container.innerHTML = html;
  updateScheduleDirtyState();
}

function updateScheduleDirtyState() {
  const dirty = scheduleIsDirty();
  const reset = $('#resetSchedule');
  reset.hidden = !dirty;
  const note = $('#scheduleNote');
  note.classList.toggle('dirty', dirty);
  note.textContent = dirty
    ? 'Tienes cambios sin guardar. Pulsa «Guardar horario» para conservarlos.'
    : 'Los cambios se guardan en tu ordenador.';
}

function openSlotForm(weekday, startTime, endTime) {
  const slot = slotFor(weekday, startTime);
  const days = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes'];
  openModal({
    title: `${days[weekday - 1]} · ${startTime}–${endTime}`,
    eyebrow: 'EDITAR HORARIO',
    submitLabel: 'Aplicar cambio',
    fields: [
      { name: 'kind', label: 'Tipo de celda', type: 'select', options: [
        { value: 'class', label: 'Clase' },
        { value: 'break', label: 'Descanso' },
        { value: 'free', label: 'Libre' }
      ] },
      { name: 'subject_id', label: 'Asignatura', type: 'select', options: subjectOptions(slot ? slot.subject_id : null) },
      { name: 'label', label: 'Etiqueta (descanso o libre)', type: 'text', full: true, placeholder: 'Descanso, Libre…' }
    ],
    values: {
      kind: slot ? slot.kind : 'class',
      subject_id: slot ? (slot.subject_id ?? '') : '',
      label: slot ? (slot.label || '') : ''
    },
    onSubmit: async (values) => {
      if (values.kind === 'class' && !values.subject_id) {
        throw new Error('Elige una asignatura para la clase.');
      }
      const subject = state.subjects.find((item) => item.id === Number(values.subject_id));
      const existing = slotFor(weekday, startTime);
      const prepared = {
        id: existing ? existing.id : null,
        weekday,
        start_time: startTime,
        end_time: endTime,
        kind: values.kind,
        subject_id: values.kind === 'class' ? Number(values.subject_id) : null,
        subject_short: subject ? subject.short_name : '',
        subject_name: subject ? subject.name : '',
        subject_color: subject ? subject.color : '#8C929B',
        subject_course: subject ? subject.course : '',
        label: values.kind === 'class'
          ? null
          : (values.label || (values.kind === 'break' ? 'Descanso' : 'Libre'))
      };
      if (existing) {
        Object.assign(existing, prepared);
      } else {
        state.schedule.push(prepared);
      }
      renderSchedule();
    }
  });
}

function scheduleIsDirtyTimes() {
  return JSON.stringify(state.scheduleTimes) !== state.scheduleTimesOriginal;
}

function openTimesForm() {
  const current = state.scheduleTimes.map((time) => `${time.start}-${time.end}`).join('\n');
  openModal({
    title: 'Franjas horarias',
    eyebrow: 'MI HORARIO',
    submitLabel: 'Aplicar',
    fields: [
      { name: 'times', label: 'Una franja por línea (por ejemplo 08:15-09:15)', type: 'textarea', full: true }
    ],
    values: { times: current },
    onSubmit: async (values) => {
      const lines = values.times.split(/\n+/).map((line) => line.trim()).filter(Boolean);
      if (!lines.length) throw new Error('Escribe al menos una franja.');
      const parsed = lines.map((line, index) => {
        const match = line.match(/^(\d{1,2})[:.](\d{2})\s*[-–a]+\s*(\d{1,2})[:.](\d{2})$/);
        if (!match) throw new Error(`La línea ${index + 1} («${line}») no tiene el formato 08:15-09:15.`);
        const start = `${match[1].padStart(2, '0')}:${match[2]}`;
        const end = `${match[3].padStart(2, '0')}:${match[4]}`;
        if (start >= end) throw new Error(`En «${line}» la hora de fin debe ser posterior a la de inicio.`);
        return { start, end };
      }).sort((a, b) => a.start.localeCompare(b.start));
      for (let i = 1; i < parsed.length; i += 1) {
        if (parsed[i].start < parsed[i - 1].end) throw new Error(`Las franjas ${parsed[i - 1].start} y ${parsed[i].start} se solapan.`);
      }
      // Cada celda se queda en la franja que ocupa la misma posición; las que sobran se quitan.
      const moves = new Map(state.scheduleTimes.map((time, index) => [time.start, parsed[index]]));
      state.schedule = state.schedule
        .filter((slot) => moves.get(slot.start_time))
        .map((slot) => Object.assign(slot, {
          start_time: moves.get(slot.start_time).start,
          end_time: moves.get(slot.start_time).end
        }));
      state.scheduleTimes = parsed;
      renderSchedule();
    }
  });
}

async function saveSchedule() {
  const button = $('#saveSchedule');
  button.disabled = true;
  button.textContent = 'Guardando…';
  try {
    const payload = {
      times: state.scheduleTimes,
      slots: state.schedule.map((slot) => ({
        weekday: slot.weekday,
        start_time: slot.start_time,
        end_time: slot.end_time,
        kind: slot.kind,
        subject_id: slot.kind === 'class' ? slot.subject_id : null,
        label: slot.label || null
      }))
    };
    const data = await api('/api/schedule', { method: 'PUT', body: payload });
    state.scheduleTimes = data.times || state.scheduleTimes;
    state.scheduleTimesOriginal = JSON.stringify(state.scheduleTimes);
    state.schedule = (data.slots || []).map((slot) => Object.assign({}, slot));
    state.scheduleOriginal = JSON.stringify(state.schedule);
    renderSchedule();
    toast('Horario guardado.', 'success');
  } catch (error) {
    toast(error.message, 'error');
  } finally {
    button.disabled = false;
    button.textContent = 'Guardar horario';
  }
}

/* ---------- Asignatura ---------- */

async function loadSubject(slug) {
  const data = await api(`/api/subjects/${encodeURIComponent(slug)}`);
  state.subjectData = data;
  const subject = data.subject;
  // Si mientras cargaba se ha cambiado de sección, no se pinta el tema
  if (state.currentView === 'asignatura' && state.subject === subject.slug) {
    applySubjectTheme(subject.color);
    document.title = `${subject.short_name || subject.name} · Mi agenda`;
  }
  $('#subjectTitle').textContent = subject.name;
  $('#subjectMeta').textContent = `${subject.course || 'Sin curso'} · ${data.stats.open} tarea${data.stats.open === 1 ? '' : 's'} abierta${data.stats.open === 1 ? '' : 's'} · ${data.stats.exams} examen${data.stats.exams === 1 ? '' : 'es'}`;

  const openTasks = data.open_tasks.map((task) => miniTask(task)).join('');
  const exams = data.exams.slice(0, 6).map((exam) => (exam.source === 'event' ? miniExamEvent(exam) : miniTask(exam))).join('');
  const plans = data.plans.slice(0, 6).map((plan) => miniPlan(plan)).join('');
  const materials = data.materials.slice(0, 6).map((material) => miniMaterial(material)).join('');
  const notes = data.notes.slice(0, 6).map((note) => miniNote(note)).join('');
  const history = data.history.slice(0, 8).map((item) => `
    <div class="mini-item">
      <i class="dot practicas"></i>
      <span><strong>${esc(item.title)}</strong><small>${esc(item.detail)}</small></span>
      <time>${esc(formatShort(item.date))}</time>
    </div>
  `).join('');

  const stats = [
    { icon: '☷', value: data.stats.open, label: 'Tareas abiertas', note: `${data.stats.completed} completadas` },
    { icon: '▦', value: data.stats.exams, label: 'Exámenes', note: 'De esta asignatura' },
    { icon: '✎', value: data.stats.notes, label: 'Notas', note: `${data.stats.materials} materiales` }
  ];

  $('#subjectContent').innerHTML = `
    <div class="stats">
      ${stats.map((item) => `<article><i>${item.icon}</i><span>${esc(item.label)}</span><b>${pad2(item.value)}</b><small>${esc(item.note)}</small></article>`).join('')}
    </div>
    <div class="subject-grid-panels">
      ${subjectPanel('Tareas y entregas', 'PENDIENTE', openTasks, 'No hay tareas abiertas.', 'add-task')}
      ${subjectPanel('Exámenes', 'EVALUACIÓN', exams, 'No hay exámenes registrados.', 'add-task')}
      ${subjectPanel('Planificación de clases', 'SESIONES', plans, 'Todavía no hay planificaciones.', 'add-plan')}
      ${subjectPanel('Materiales', 'RECURSOS', materials, 'No hay materiales guardados.', 'add-material')}
      ${subjectPanel('Notas', 'APUNTES', notes, 'No hay notas de esta asignatura.', 'add-note')}
      ${subjectPanel('Historial', 'SEGUIMIENTO', history, 'Todavía no hay historial.', null)}
    </div>
  `;
}

function subjectPanel(title, eyebrow, content, emptyText, action) {
  const labels = {
    'add-task': '＋ Tarea', 'add-plan': '＋ Planificación',
    'add-material': '＋ Material', 'add-note': '＋ Nota'
  };
  const button = action
    ? `<button type="button" class="link" data-subject-action="${action}">${labels[action]}</button>`
    : '';
  return `<article class="panel subject-panel">
    <div class="panel-title">
      <div><p class="eyebrow">${esc(eyebrow)}</p><h2>${esc(title)}</h2></div>
      ${button}
    </div>
    ${content || `<p class="panel-empty">${esc(emptyText)}</p>`}
  </article>`;
}

function miniTask(task) {
  const dueTime = task.due_time ? ` ${task.due_time}` : '';
  return `<div class="mini-item">
    ${colorDot(task)}
    <span>
      <strong>${esc(task.title)}${task.marked ? ` ${MARK_DOT}` : ''}</strong>
      <small>
        ${esc(TASK_KIND_LABELS[task.kind] || task.kind)} · ${esc(TASK_PRIORITY_LABELS[task.priority] || task.priority)}
        ${task.due_date ? ` · ${esc(formatShort(task.due_date) + dueTime)}` : ''}
      </small>
    </span>
    <button type="button" class="icon-btn" data-subject-action="edit-task" data-id="${task.id}" title="Editar">✎</button>
    <button type="button" class="icon-btn" data-subject-action="delete-task" data-id="${task.id}" title="Eliminar">✕</button>
  </div>`;
}

function miniExamEvent(event) {
  const time = event.start_time && !event.all_day ? ` ${event.start_time}` : '';
  return `<div class="mini-item">
    ${colorDot(event)}
    <span>
      <strong>${esc(event.title)}</strong>
      <small>Examen (calendario) · ${esc(formatShort(event.start_date) + time)}</small>
    </span>
    <button type="button" class="icon-btn" data-subject-action="edit-event" data-id="${event.id}" title="Editar">✎</button>
  </div>`;
}

function miniPlan(plan) {
  return `<div class="mini-item">
    <i class="dot practicas"></i>
    <span><strong>${esc(plan.title)}</strong><small>${esc(plan.plan_date ? formatShort(plan.plan_date) : 'Sin fecha')} · ${esc((plan.objectives || '').slice(0, 60))}</small></span>
    <button type="button" class="icon-btn" data-subject-action="edit-plan" data-id="${plan.id}" title="Editar">✎</button>
    <button type="button" class="icon-btn" data-subject-action="delete-plan" data-id="${plan.id}" title="Eliminar">✕</button>
  </div>`;
}

function miniMaterial(material) {
  return `<div class="mini-item">
    <i class="dot practicas"></i>
    <span><strong>${esc(material.title)}</strong><small>${esc(material.kind || 'Material')}${material.link ? ` · ${esc(material.link)}` : ''}</small></span>
    <button type="button" class="icon-btn" data-subject-action="edit-material" data-id="${material.id}" title="Editar">✎</button>
    <button type="button" class="icon-btn" data-subject-action="delete-material" data-id="${material.id}" title="Eliminar">✕</button>
  </div>`;
}

function miniNote(note) {
  return `<div class="mini-item">
    <i class="dot practicas"></i>
    <span><strong>${esc(note.title)}</strong><small>${esc((note.body || '').slice(0, 70))}</small></span>
    <button type="button" class="icon-btn" data-subject-action="edit-note" data-id="${note.id}" title="Editar">✎</button>
    <button type="button" class="icon-btn" data-subject-action="delete-note" data-id="${note.id}" title="Eliminar">✕</button>
  </div>`;
}

/* ---------- Evaluaciones ---------- */

async function loadEvaluations() {
  const data = await api(`/api/evaluations?course=${encodeURIComponent(state.evaluationCourse)}`);
  $$('#courseSwitch [data-course]').forEach((button) => {
    button.classList.toggle('chosen', button.dataset.course === state.evaluationCourse);
  });

  const groups = {};
  data.items.forEach((item) => {
    const key = item.start_date.slice(0, 7);
    if (!groups[key]) groups[key] = [];
    groups[key].push(item);
  });
  const keys = Object.keys(groups).sort();

  if (!keys.length) {
    $('#evaluationsList').innerHTML = '<p class="panel-empty">No hay fechas registradas para este curso.</p>';
  } else {
    $('#evaluationsList').innerHTML = keys.map((key) => {
      const [year, month] = key.split('-').map(Number);
      const rows = groups[key].map((item) => {
        const sameDay = item.end_date === item.start_date;
        return `<div class="eval-row">
          <div class="eval-date">${pad2(parseISO(item.start_date).getDate())}<small>${MONTHS_SHORT[month - 1]}</small></div>
          <div class="eval-body">
            <strong>${esc(item.title)}</strong>
            <small>${sameDay ? '' : `Hasta el ${esc(formatShort(item.end_date))} · `}${esc(item.source_page || '')}</small>
          </div>
          <span class="kind-badge kind-${esc(item.kind)}">${esc(item.kind_label)}</span>
        </div>`;
      }).join('');
      return `<div class="eval-month"><h3>${capitalize(MONTHS[month - 1])} ${year}</h3>${rows}</div>`;
    }).join('');
  }
  $('#evaluationsNote').textContent = data.source_note;
}

/* ---------- Tutoría ---------- */

async function loadTutoring() {
  const data = await api('/api/tutoring');
  state.tutoring = data.items || [];
  const counts = data.counts || { total: 0, pendiente: 0, realizado: 0 };
  $('#tutoringStats').innerHTML = `
    <article><i>♡</i><span>Seguimientos</span><b>${pad2(counts.total)}</b><small>En total</small></article>
    <article><i>◷</i><span>Pendientes</span><b>${pad2(counts.pendiente)}</b><small>Por realizar</small></article>
    <article><i>✓</i><span>Realizados</span><b>${pad2(counts.realizado)}</b><small>Completados</small></article>
  `;

  const container = $('#tutoringList');
  if (!state.tutoring.length) {
    container.innerHTML = `<div class="empty"><b>♡</b><h2>Tu espacio de tutoría</h2><p>Aquí podrás organizar seguimientos individuales, visitas, reuniones y fechas importantes.</p></div>`;
    return;
  }
  container.innerHTML = state.tutoring.map((item) => `
    <div class="tutoring-row" data-id="${item.id}">
      <div class="when">${pad2(parseISO(item.start_date).getDate())}<small>${MONTHS_SHORT[parseISO(item.start_date).getMonth()]}</small></div>
      <div class="main">
        <strong>${esc(item.student)}</strong>
        <small>${esc(item.kind_label)} · ${esc(item.subject_name || 'Sin asignatura')}${item.start_time ? ` · ${esc(item.start_time)}` : ''}</small>
        ${item.notes ? `<small>${esc(item.notes)}</small>` : ''}
      </div>
      <span class="status-badge status-${esc(item.status)}">${esc(TUTORING_STATUS_LABELS[item.status] || item.status)}</span>
      <div class="task-actions">
        <button type="button" class="icon-btn" data-tutoring-action="edit" data-id="${item.id}" title="Editar">✎</button>
        <button type="button" class="icon-btn" data-tutoring-action="delete" data-id="${item.id}" title="Eliminar">✕</button>
      </div>
    </div>
  `).join('');
}

function openTutoringForm(item = null) {
  const isEdit = Boolean(item && item.id);
  openModal({
    title: isEdit ? 'Editar seguimiento' : 'Nuevo seguimiento',
    eyebrow: 'PRÁCTICAS Y TUTORÍA',
    submitLabel: isEdit ? 'Guardar cambios' : 'Crear seguimiento',
    fields: [
      { name: 'kind', label: 'Tipo', type: 'select', options: Object.entries(TUTORING_KIND_LABELS).map(([value, label]) => ({ value, label })) },
      { name: 'student', label: 'Alumno o grupo', type: 'text', required: true },
      { name: 'start_date', label: 'Fecha', type: 'date', required: true },
      { name: 'start_time', label: 'Hora', type: 'time' },
      { name: 'subject_id', label: 'Asignatura', type: 'select', options: subjectOptions(item ? item.subject_id : null) },
      { name: 'status', label: 'Estado', type: 'select', options: Object.entries(TUTORING_STATUS_LABELS).map(([value, label]) => ({ value, label })) },
      { name: 'notes', label: 'Notas', type: 'textarea', full: true }
    ],
    values: {
      kind: item ? item.kind : 'seguimiento',
      student: item ? item.student : '',
      start_date: item ? item.start_date : todayISO(),
      start_time: item ? (item.start_time || '') : '',
      subject_id: item ? (item.subject_id ?? '') : '',
      status: item ? item.status : 'pendiente',
      notes: item ? item.notes : ''
    },
    onSubmit: async (values) => {
      if (!values.student) throw new Error('Indica el alumno o el grupo.');
      if (!values.start_date) throw new Error('La fecha es obligatoria.');
      const payload = {
        kind: values.kind,
        student: values.student,
        start_date: values.start_date,
        start_time: values.start_time || null,
        subject_id: values.subject_id || null,
        status: values.status,
        notes: values.notes
      };
      if (isEdit) {
        await api(`/api/tutoring/${item.id}`, { method: 'PUT', body: payload });
        toast('Seguimiento actualizado.', 'success');
      } else {
        await api('/api/tutoring', { method: 'POST', body: payload });
        toast('Seguimiento creado.', 'success');
      }
      await refreshCurrent();
    }
  });
}

/* ---------- Notas ---------- */

async function loadNotes() {
  const params = new URLSearchParams();
  const search = $('#noteSearch').value.trim();
  if (search) params.set('q', search);
  const data = await api(`/api/notes?${params.toString()}`);
  state.notes = data.notes || [];
  renderNotes();
}

function renderNotes() {
  const container = $('#notesList');
  if (!state.notes.length) {
    container.innerHTML = `<article class="panel empty" style="grid-column:1/-1"><b>✎</b><h2>Tu cuaderno digital</h2><p>Crea notas generales o asócialas a una asignatura y una fecha.</p></article>`;
    return;
  }
  container.innerHTML = state.notes.map((note) => `
    <article class="note-card${note.pinned ? ' pinned' : ''}" data-id="${note.id}">
      <div style="display:flex;gap:8px;align-items:flex-start;justify-content:space-between">
        <h3>${esc(note.title)}</h3>
        <button type="button" class="note-pin${note.pinned ? ' on' : ''}" data-note-action="pin" data-id="${note.id}" title="${note.pinned ? 'Quitar de fijadas' : 'Fijar nota'}">${note.pinned ? '★' : '☆'}</button>
      </div>
      <p class="note-body">${esc(note.body || 'Sin contenido.')}</p>
      <div class="note-foot">
        <span>
          ${note.subject_name ? `<span class="note-tag">${esc(note.subject_name)}</span>` : '<span class="note-tag">General</span>'}
          ${note.note_date ? `<span> · ${esc(formatShort(note.note_date))}</span>` : ''}
        </span>
        <span class="task-actions">
          <button type="button" class="icon-btn to-reminder" data-note-action="to-reminder" data-id="${note.id}" title="Pasar a Recordatorios (por semanas)">→ Recordatorio</button>
          <button type="button" class="icon-btn" data-note-action="edit" data-id="${note.id}" title="Editar">✎</button>
          <button type="button" class="icon-btn" data-note-action="delete" data-id="${note.id}" title="Eliminar">✕</button>
        </span>
      </div>
    </article>
  `).join('');
}

function openNoteForm(note = null, presetSubject = null) {
  const isEdit = Boolean(note && note.id);
  openModal({
    title: isEdit ? 'Editar nota' : 'Nueva nota',
    eyebrow: 'NOTAS',
    submitLabel: isEdit ? 'Guardar cambios' : 'Crear nota',
    fields: [
      { name: 'title', label: 'Título', type: 'text', required: true, full: true },
      { name: 'body', label: 'Contenido', type: 'textarea', full: true, rows: 7 },
      { name: 'subject_id', label: 'Asignatura', type: 'select', options: subjectOptions(note ? note.subject_id : presetSubject) },
      { name: 'note_date', label: 'Fecha', type: 'date' },
      { name: 'pinned', label: 'Fijar esta nota arriba', type: 'checkbox', full: true }
    ],
    values: {
      title: note ? note.title : '',
      body: note ? note.body : '',
      subject_id: note ? (note.subject_id ?? '') : (presetSubject || ''),
      note_date: note ? (note.note_date || '') : todayISO(),
      pinned: note ? Boolean(note.pinned) : false
    },
    onSubmit: async (values) => {
      if (!values.title) throw new Error('El título es obligatorio.');
      const payload = {
        title: values.title,
        body: values.body,
        subject_id: values.subject_id || null,
        note_date: values.note_date || null,
        pinned: values.pinned
      };
      if (isEdit) {
        await api(`/api/notes/${note.id}`, { method: 'PUT', body: payload });
        toast('Nota actualizada.', 'success');
      } else {
        await api('/api/notes', { method: 'POST', body: payload });
        toast('Nota creada.', 'success');
      }
      await refreshCurrent();
    }
  });
}

async function toggleNotePin(note) {
  try {
    await api(`/api/notes/${note.id}`, { method: 'PUT', body: { pinned: !note.pinned } });
    await loadNotes();
  } catch (error) {
    toast(error.message, 'error');
  }
}

/* ---------- Materiales y planificaciones ---------- */

function openMaterialForm(material = null) {
  if (!state.subjectData) return;
  const isEdit = Boolean(material && material.id);
  openModal({
    title: isEdit ? 'Editar material' : 'Nuevo material',
    eyebrow: 'MATERIALES',
    submitLabel: isEdit ? 'Guardar cambios' : 'Guardar material',
    fields: [
      { name: 'title', label: 'Título', type: 'text', required: true, full: true },
      { name: 'kind', label: 'Tipo', type: 'text', placeholder: 'Ficha, enlace, documento…' },
      { name: 'link', label: 'Enlace o ubicación', type: 'text', full: true, placeholder: 'Opcional' },
      { name: 'notes', label: 'Notas', type: 'textarea', full: true }
    ],
    values: {
      title: material ? material.title : '',
      kind: material ? (material.kind || '') : '',
      link: material ? (material.link || '') : '',
      notes: material ? (material.notes || '') : ''
    },
    onSubmit: async (values) => {
      if (!values.title) throw new Error('El título es obligatorio.');
      const slug = state.subjectData.subject.slug;
      const payload = { title: values.title, kind: values.kind, link: values.link, notes: values.notes };
      if (isEdit) {
        await api(`/api/materials/${material.id}`, { method: 'PUT', body: payload });
        toast('Material actualizado.', 'success');
      } else {
        await api(`/api/subjects/${encodeURIComponent(slug)}/materials`, { method: 'POST', body: payload });
        toast('Material guardado.', 'success');
      }
      await refreshCurrent();
    }
  });
}

function openPlanForm(plan = null) {
  if (!state.subjectData) return;
  const isEdit = Boolean(plan && plan.id);
  openModal({
    title: isEdit ? 'Editar planificación' : 'Nueva planificación',
    eyebrow: 'PLANIFICACIÓN DE CLASES',
    submitLabel: isEdit ? 'Guardar cambios' : 'Guardar planificación',
    fields: [
      { name: 'title', label: 'Título de la sesión', type: 'text', required: true, full: true },
      { name: 'plan_date', label: 'Fecha', type: 'date' },
      { name: 'objectives', label: 'Objetivos', type: 'textarea', full: true },
      { name: 'activities', label: 'Actividades', type: 'textarea', full: true },
      { name: 'resources', label: 'Recursos', type: 'textarea', full: true }
    ],
    values: {
      title: plan ? plan.title : '',
      plan_date: plan ? (plan.plan_date || '') : todayISO(),
      objectives: plan ? plan.objectives : '',
      activities: plan ? plan.activities : '',
      resources: plan ? plan.resources : ''
    },
    onSubmit: async (values) => {
      if (!values.title) throw new Error('El título es obligatorio.');
      const slug = state.subjectData.subject.slug;
      const payload = {
        title: values.title,
        plan_date: values.plan_date || null,
        objectives: values.objectives,
        activities: values.activities,
        resources: values.resources
      };
      if (isEdit) {
        await api(`/api/plans/${plan.id}`, { method: 'PUT', body: payload });
        toast('Planificación actualizada.', 'success');
      } else {
        await api(`/api/subjects/${encodeURIComponent(slug)}/plans`, { method: 'POST', body: payload });
        toast('Planificación guardada.', 'success');
      }
      await refreshCurrent();
    }
  });
}

/* ---------- Copias y datos ---------- */

async function loadData() {
  const info = await api('/api/data-info');
  state.data = info;
  const counts = info.counts || {};
  $('#dataInfo').innerHTML = `
    <div><b>Base de datos:</b> ${esc(info.database)}</div>
    <div><b>Tamaño:</b> ${esc(humanSize(info.database_size))}</div>
    <div><b>Carpeta de copias:</b> ${esc(info.backups_dir)}</div>
    <div class="counts-grid">
      <div><b>${counts.tasks ?? 0}</b><small>Tareas</small></div>
      <div><b>${counts.events ?? 0}</b><small>Eventos</small></div>
      <div><b>${counts.notes ?? 0}</b><small>Notas</small></div>
      <div><b>${counts.tutoring ?? 0}</b><small>Seguimientos</small></div>
      <div><b>${counts.materials ?? 0}</b><small>Materiales</small></div>
      <div><b>${counts.lesson_plans ?? 0}</b><small>Planificaciones</small></div>
    </div>
  `;

  const container = $('#backupList');
  if (!info.backups || !info.backups.length) {
    container.innerHTML = '<p class="panel-empty">Todavía no hay copias de seguridad.</p>';
    return;
  }
  container.innerHTML = info.backups.map((backup) => `
    <div class="backup-row">
      <span><strong>${esc(backup.name)}</strong><small>${esc(formatDateTime(backup.created_at))} · ${esc(humanSize(backup.size))}</small></span>
      <button type="button" class="ghost" data-restore="${esc(backup.name)}">Restaurar</button>
    </div>
  `).join('');
}

/* ---------- Acciones de asignatura, tutoría y notas ---------- */

async function handleSubjectAction(action, id) {
  const data = state.subjectData;
  if (!data) return;
  if (action === 'add-task') {
    openTaskForm(null, null, data.subject.id);
    return;
  }
  if (action === 'add-plan') {
    openPlanForm();
    return;
  }
  if (action === 'add-material') {
    openMaterialForm();
    return;
  }
  if (action === 'add-note') {
    openNoteForm(null, data.subject.id);
    return;
  }

  if (action === 'edit-task') {
    const task = data.tasks.find((item) => item.id === id);
    if (task) openTaskForm(task);
    return;
  }
  if (action === 'edit-event') {
    const event = data.events.find((item) => item.id === id);
    if (event) openEventForm(event);
    return;
  }
  if (action === 'edit-plan') {
    const plan = data.plans.find((item) => item.id === id);
    if (plan) openPlanForm(plan);
    return;
  }
  if (action === 'edit-material') {
    const material = data.materials.find((item) => item.id === id);
    if (material) openMaterialForm(material);
    return;
  }
  if (action === 'edit-note') {
    const note = data.notes.find((item) => item.id === id);
    if (note) openNoteForm(note);
    return;
  }

  if (action === 'delete-task') {
    const task = data.tasks.find((item) => item.id === id);
    if (task) await deleteTask(task);
    return;
  }

  const config = {
    'delete-plan': { url: `/api/plans/${id}`, label: 'la planificación' },
    'delete-material': { url: `/api/materials/${id}`, label: 'el material' },
    'delete-note': { url: `/api/notes/${id}`, label: 'la nota' }
  }[action];
  if (config) {
    const confirmed = await askConfirm({
      title: `¿Eliminar ${config.label}?`,
      message: 'Esta acción no se puede deshacer.',
      accept: 'Eliminar',
      danger: true
    });
    if (!confirmed) return;
    try {
      await api(config.url, { method: 'DELETE' });
      toast('Eliminado.', 'success');
      await refreshCurrent();
    } catch (error) {
      toast(error.message, 'error');
    }
  }
}

async function handleTutoringAction(action, id) {
  const item = state.tutoring.find((entry) => entry.id === id);
  if (!item) return;
  if (action === 'edit') {
    openTutoringForm(item);
    return;
  }
  if (action === 'delete') {
    const confirmed = await askConfirm({
      title: '¿Eliminar este seguimiento?',
      message: `Se eliminará el seguimiento de «${item.student}». Esta acción no se puede deshacer.`,
      accept: 'Eliminar',
      danger: true
    });
    if (!confirmed) return;
    try {
      await api(`/api/tutoring/${id}`, { method: 'DELETE' });
      toast('Seguimiento eliminado.', 'success');
      await loadTutoring();
    } catch (error) {
      toast(error.message, 'error');
    }
  }
}

async function handleNoteAction(action, id) {
  if (action === 'pin') {
    const note = state.notes.find((entry) => entry.id === id);
    if (note) await toggleNotePin(note);
    return;
  }
  if (action === 'edit') {
    const note = state.notes.find((entry) => entry.id === id);
    if (note) openNoteForm(note);
    return;
  }
  if (action === 'to-reminder') {
    const note = state.notes.find((entry) => entry.id === id);
    if (!note) return;
    const confirmed = await askConfirm({
      title: '¿Pasar esta nota a Recordatorios?',
      message: `«${note.title}» se moverá a Recordatorios, en la semana del ${formatShort(note.note_date || todayISO())}, como pendiente. Dejará de aparecer en Notas.`,
      accept: 'Pasar a Recordatorios'
    });
    if (!confirmed) return;
    try {
      await api(`/api/notes/${id}/to-reminder`, { method: 'POST' });
      toast('Nota pasada a Recordatorios.', 'success');
      await loadNotes();
      await refreshReminderBadge();
    } catch (error) {
      toast(error.message, 'error');
    }
    return;
  }
  if (action === 'delete') {
    const note = state.notes.find((entry) => entry.id === id);
    if (!note) return;
    const confirmed = await askConfirm({
      title: '¿Eliminar esta nota?',
      message: `Se eliminará «${note.title}». Esta acción no se puede deshacer.`,
      accept: 'Eliminar',
      danger: true
    });
    if (!confirmed) return;
    try {
      await api(`/api/notes/${id}`, { method: 'DELETE' });
      toast('Nota eliminada.', 'success');
      await loadNotes();
    } catch (error) {
      toast(error.message, 'error');
    }
  }
}

/* ---------- Recordatorios (plan semanal) ---------- */

const REMINDER_CATEGORY_LABELS = {
  pendiente: 'Pendiente', corregir: 'Por corregir', revisar: 'Revisar', otro: 'Otro'
};

function toISO(date) {
  return `${date.getFullYear()}-${pad2(date.getMonth() + 1)}-${pad2(date.getDate())}`;
}

function mondayOf(iso) {
  const date = parseISO(iso);
  date.setDate(date.getDate() - ((date.getDay() + 6) % 7));
  return toISO(date);
}

function addDaysISO(iso, days) {
  const date = parseISO(iso);
  date.setDate(date.getDate() + days);
  return toISO(date);
}

// «9 – 15 de noviembre de 2026» o «30 nov – 6 dic 2026» si cambia de mes
function weekLabel(monday) {
  const start = parseISO(monday);
  const end = parseISO(addDaysISO(monday, 6));
  if (start.getMonth() === end.getMonth()) {
    return `${start.getDate()} – ${end.getDate()} de ${MONTHS[end.getMonth()]} de ${end.getFullYear()}`;
  }
  const startYear = start.getFullYear() !== end.getFullYear() ? ` ${start.getFullYear()}` : '';
  return `${start.getDate()} ${MONTHS_SHORT[start.getMonth()]}${startYear} – ${end.getDate()} ${MONTHS_SHORT[end.getMonth()]} ${end.getFullYear()}`;
}

function updateReminderBadge(items) {
  const badge = $('#reminderNavCount');
  if (!badge) return;
  const current = mondayOf(todayISO());
  // Pendientes de esta semana y de las anteriores (lo que «llevas arrastrando»)
  const pending = items.filter((item) => !item.done && item.week_start <= current).length;
  badge.textContent = pending;
  badge.hidden = pending === 0;
  badge.title = `${pending} recordatorio${pending === 1 ? '' : 's'} pendiente${pending === 1 ? '' : 's'}`;
}

async function refreshReminderBadge() {
  try {
    const data = await api('/api/reminders');
    state.reminders.items = data.reminders || [];
    updateReminderBadge(state.reminders.items);
  } catch (error) {
    /* El contador es secundario: no molestar con avisos. */
  }
}

async function loadReminders() {
  const data = await api('/api/reminders');
  const rem = state.reminders;
  rem.items = data.reminders || [];
  rem.today = data.today || todayISO();
  rem.currentWeek = data.current_week || mondayOf(rem.today);
  if (!rem.anchor) rem.anchor = rem.currentWeek;
  updateReminderBadge(rem.items);
  renderReminders();
}

function reminderMatches(item) {
  const rem = state.reminders;
  if (rem.status === 'pending' && item.done) return false;
  if (rem.status === 'done' && !item.done) return false;
  if (rem.category && item.category !== rem.category) return false;
  return true;
}

// Progreso de corrección (Aula Virtual): barra corregidas / por corregir / sin entregar.
function plural(count, one, many) {
  return `${count} ${count === 1 ? one : many}`;
}

function gradingProgressHTML(progress) {
  if (!progress || !progress.total) return '';
  const { graded, ungraded, not_submitted: missing, submitted, total, percent } = progress;
  const width = (value) => `${(value * 100 / total).toFixed(2)}%`;
  const parts = [
    `Se han subido <b>${submitted}/${total}</b>`,
    `has corregido <b>${graded}</b>`,
    ungraded ? `te quedan <b>${ungraded}</b> por corregir` : '<b>¡todo corregido!</b>'
  ];
  if (missing) parts.push(`tienes <b>${plural(missing, 'alumna/o', 'alumnas/os')}</b> que no la ${missing === 1 ? 'ha' : 'han'} entregado`);
  return `<div class="grading-progress" title="Corregidas ${graded} · Por corregir ${ungraded} · Sin entregar ${missing}">
    <div class="gp-top">
      <div class="gp-bar" role="img" aria-label="${percent} % corregido">
        <span class="gp-graded" style="width:${width(graded)}"></span><span class="gp-pending" style="width:${width(ungraded)}"></span><span class="gp-missing" style="width:${width(missing)}"></span>
      </div>
      <strong class="gp-percent">${percent} %</strong>
    </div>
    <small class="gp-text">${parts.join(', ')}.</small>
  </div>`;
}

function reminderRow(item, showWeek = false) {
  const subject = item.subject_name
    ? `<span class="note-tag">${esc(item.subject_short || item.subject_name)}</span>`
    : '';
  const when = showWeek ? `Semana del ${weekLabel(item.week_start)}` : formatShort(item.reminder_date);
  return `<div class="task${item.done ? ' done' : ''}" data-id="${item.id}">
    <i class="${item.done ? 'checked' : ''}" data-rem-action="toggle" data-id="${item.id}" role="button" tabindex="0" title="${item.done ? 'Marcar como pendiente' : 'Marcar como hecho'}">${item.done ? '✓' : ''}</i>
    <span>
      <strong>${esc(item.title)}</strong>
      ${item.body ? `<small class="reminder-body">${esc(item.body)}</small>` : ''}
      ${gradingProgressHTML(item.progress)}
      <div class="task-meta">
        <span class="reminder-cat cat-${esc(item.category)}">${esc(REMINDER_CATEGORY_LABELS[item.category] || item.category)}</span>
        ${subject}
      </div>
    </span>
    <time>${esc(when)}</time>
    <div class="task-actions">
      <button type="button" class="icon-btn" data-rem-action="edit" data-id="${item.id}" title="Editar">✎</button>
      <button type="button" class="icon-btn" data-rem-action="delete" data-id="${item.id}" title="Eliminar">✕</button>
    </div>
  </div>`;
}

function reminderWeekBlock(monday, items, { title, extraClass = '', showWeek = false, emptyText = '' } = {}) {
  const pending = items.filter((item) => !item.done).length;
  const rows = items.length
    ? items.map((item) => reminderRow(item, showWeek)).join('')
    : `<p class="reminder-empty">${esc(emptyText)}</p>`;
  return `<section class="reminder-week ${extraClass}">
    <div class="reminder-week-head">
      <h3>${title}</h3>
      <small>${pending} pendiente${pending === 1 ? '' : 's'} · ${items.length - pending} hecho${items.length - pending === 1 ? '' : 's'}</small>
    </div>
    <div class="tasklist">${rows}</div>
  </section>`;
}

function renderReminders() {
  const rem = state.reminders;
  const container = $('#reminderList');
  const isWeek = rem.view === 'week';
  $$('#reminderSwitch [data-remview]').forEach((button) => button.classList.toggle('chosen', button.dataset.remview === rem.view));
  $$('#reminderFilters [data-remstatus]').forEach((button) => button.classList.toggle('chosen', button.dataset.remstatus === rem.status));
  $('#reminderPrev').hidden = !isWeek;
  $('#reminderNext').hidden = !isWeek;
  $('#reminderToday').hidden = !isWeek || rem.anchor === rem.currentWeek;
  $('#reminderQuick').hidden = !isWeek;

  const visible = rem.items.filter(reminderMatches);

  if (isWeek) {
    const isCurrent = rem.anchor === rem.currentWeek;
    $('#reminderWeekTitle').textContent = weekLabel(rem.anchor);
    $('#reminderQuickText').placeholder = isCurrent
      ? 'Apunta algo para esta semana y pulsa Intro…'
      : `Apunta algo para la semana del ${weekLabel(rem.anchor)}…`;
    const weekItems = visible.filter((item) => item.week_start === rem.anchor);
    const emptyText = rem.status === 'done'
      ? 'No hay recordatorios hechos esta semana.'
      : 'Nada apuntado para esta semana. Escribe arriba lo que tengas pendiente.';
    let html = reminderWeekBlock(rem.anchor, weekItems, {
      title: `${isCurrent ? 'Esta semana' : 'Recordatorios de la semana'}`,
      extraClass: isCurrent ? 'current' : '',
      emptyText
    });
    // En la semana actual, lo que quedó sin hacer de semanas anteriores
    if (isCurrent && rem.status !== 'done') {
      const carry = rem.items.filter((item) => !item.done && item.week_start < rem.currentWeek
        && (!rem.category || item.category === rem.category));
      if (carry.length) {
        html += reminderWeekBlock(null, carry, {
          title: 'Pendiente de semanas anteriores',
          extraClass: 'carry',
          showWeek: true
        });
      }
    }
    container.innerHTML = html;
    return;
  }

  $('#reminderWeekTitle').textContent = 'Todas las semanas';
  if (!visible.length) {
    container.innerHTML = `<div class="empty"><b>🔔</b><h2>No hay recordatorios</h2><p>${rem.status === 'pending' ? '¡Lo tienes todo al día!' : 'Prueba con otro filtro o crea un recordatorio nuevo.'}</p></div>`;
    return;
  }
  const groups = new Map();
  visible.forEach((item) => {
    if (!groups.has(item.week_start)) groups.set(item.week_start, []);
    groups.get(item.week_start).push(item);
  });
  container.innerHTML = Array.from(groups.keys()).sort().map((monday) => {
    const isCurrent = monday === rem.currentWeek;
    const title = `${esc(weekLabel(monday))}${isCurrent ? ' <span class="pill">Esta semana</span>' : ''}`;
    return reminderWeekBlock(monday, groups.get(monday), {
      title,
      extraClass: isCurrent ? 'current' : (monday < rem.currentWeek ? 'past' : '')
    });
  }).join('');
}

function defaultReminderDate() {
  const rem = state.reminders;
  const today = todayISO();
  if (state.currentView === 'recordatorios' && rem.view === 'week' && rem.anchor && rem.anchor !== mondayOf(today)) {
    return rem.anchor;
  }
  return today;
}

async function afterReminderChange() {
  if (state.currentView === 'recordatorios') await loadReminders();
  else await refreshReminderBadge();
}

function openReminderForm(item = null, presetSubject = null) {
  const isEdit = Boolean(item && item.id);
  openModal({
    title: isEdit ? 'Editar recordatorio' : 'Nuevo recordatorio',
    eyebrow: 'PLAN SEMANAL',
    submitLabel: isEdit ? 'Guardar cambios' : 'Crear recordatorio',
    fields: [
      { name: 'title', label: 'Recordatorio', type: 'text', required: true, full: true, placeholder: 'Por ejemplo: corregir el examen del tema 3' },
      { name: 'body', label: 'Detalle', type: 'textarea', full: true, rows: 3 },
      { name: 'category', label: 'Tipo', type: 'select', options: Object.entries(REMINDER_CATEGORY_LABELS).map(([value, label]) => ({ value, label })) },
      { name: 'subject_id', label: 'Asignatura', type: 'select', options: subjectOptions(item ? item.subject_id : presetSubject) },
      { name: 'reminder_date', label: 'Semana (elige cualquier día)', type: 'date', required: true },
      ...(isEdit ? [{ name: 'done', label: 'Hecho', type: 'checkbox', full: true }] : [])
    ],
    values: {
      title: item ? item.title : '',
      body: item ? item.body : '',
      category: item ? item.category : (state.reminders.category || 'pendiente'),
      subject_id: item ? (item.subject_id ?? '') : (presetSubject || ''),
      reminder_date: item ? item.reminder_date : defaultReminderDate(),
      done: item ? Boolean(item.done) : false
    },
    onSubmit: async (values) => {
      if (!values.title) throw new Error('Escribe el recordatorio.');
      if (!values.reminder_date) throw new Error('Elige un día de la semana del recordatorio.');
      const payload = {
        title: values.title,
        body: values.body,
        category: values.category,
        subject_id: values.subject_id || null,
        reminder_date: values.reminder_date
      };
      if (isEdit) {
        payload.done = values.done;
        await api(`/api/reminders/${item.id}`, { method: 'PUT', body: payload });
        toast('Recordatorio actualizado.', 'success');
      } else {
        await api('/api/reminders', { method: 'POST', body: payload });
        toast(`Recordatorio añadido a la semana del ${weekLabel(mondayOf(values.reminder_date))}.`, 'success');
      }
      await afterReminderChange();
    }
  });
}

async function handleReminderAction(action, id) {
  const item = state.reminders.items.find((entry) => entry.id === id);
  if (!item) return;
  if (action === 'toggle') {
    try {
      await api(`/api/reminders/${id}`, { method: 'PUT', body: { done: !item.done } });
      toast(item.done ? 'Recordatorio pendiente de nuevo.' : '¡Hecho!', 'success');
      await afterReminderChange();
    } catch (error) {
      toast(error.message, 'error');
    }
    return;
  }
  if (action === 'edit') {
    openReminderForm(item);
    return;
  }
  if (action === 'delete') {
    const confirmed = await askConfirm({
      title: '¿Eliminar este recordatorio?',
      message: `Se eliminará «${item.title}». Si ya lo has hecho, puedes marcarlo como hecho en lugar de eliminarlo.`,
      accept: 'Eliminar',
      danger: true
    });
    if (!confirmed) return;
    try {
      await api(`/api/reminders/${id}`, { method: 'DELETE' });
      toast('Recordatorio eliminado.', 'success');
      await afterReminderChange();
    } catch (error) {
      toast(error.message, 'error');
    }
  }
}

async function quickAddReminder() {
  const input = $('#reminderQuickText');
  const title = input.value.trim();
  if (!title) return;
  try {
    await api('/api/reminders', {
      method: 'POST',
      body: {
        title,
        reminder_date: defaultReminderDate(),
        category: state.reminders.category || 'pendiente'
      }
    });
    input.value = '';
    await loadReminders();
    input.focus();
  } catch (error) {
    toast(error.message, 'error');
  }
}

function bindReminderEvents() {
  const rem = state.reminders;
  const rerender = () => renderReminders();
  $('#addReminder').addEventListener('click', () => openReminderForm());
  $('#reminderPrev').addEventListener('click', () => { rem.anchor = addDaysISO(rem.anchor, -7); rerender(); });
  $('#reminderNext').addEventListener('click', () => { rem.anchor = addDaysISO(rem.anchor, 7); rerender(); });
  $('#reminderToday').addEventListener('click', () => { rem.anchor = rem.currentWeek; rerender(); });
  $('#reminderSwitch').addEventListener('click', (event) => {
    const button = event.target.closest('[data-remview]');
    if (!button) return;
    rem.view = button.dataset.remview;
    rerender();
  });
  $('#reminderFilters').addEventListener('click', (event) => {
    const button = event.target.closest('[data-remstatus]');
    if (!button) return;
    rem.status = button.dataset.remstatus;
    rerender();
  });
  $('#reminderCategory').addEventListener('change', (event) => {
    rem.category = event.target.value;
    rerender();
  });
  $('#reminderQuick').addEventListener('submit', (event) => {
    event.preventDefault();
    quickAddReminder();
  });
  $('#reminderList').addEventListener('click', (event) => {
    const action = event.target.closest('[data-rem-action]');
    if (!action) return;
    handleReminderAction(action.dataset.remAction, Number(action.dataset.id));
  });
  $('#reminderList').addEventListener('keydown', (event) => {
    const toggle = event.target.closest('[data-rem-action="toggle"]');
    if (toggle && (event.key === 'Enter' || event.key === ' ')) {
      event.preventDefault();
      toggle.click();
    }
  });
}

/* ---------- Importar y restaurar ---------- */

async function importFromFile(file) {
  if (!file) return;
  if (file.size > 16 * 1024 * 1024) {
    toast('El archivo es demasiado grande (máximo 16 MB).', 'error');
    return;
  }
  let payload;
  try {
    payload = JSON.parse(await file.text());
  } catch (error) {
    toast('El archivo no es un JSON válido.', 'error');
    return;
  }
  const confirmed = await askConfirm({
    title: '¿Importar este archivo?',
    message: 'Se sustituirán todos los datos actuales. Antes se guardará una copia automática de seguridad.',
    accept: 'Importar',
    danger: true
  });
  if (!confirmed) return;
  const button = $('#importButton');
  button.disabled = true;
  button.textContent = 'Importando…';
  try {
    const result = await api('/api/import', { method: 'POST', body: { data: payload, confirm: true } });
    toast(`Datos importados. Copia automática: ${result.safety_backup}`, 'success');
    await loadSubjects();
    await refreshCurrent();
    if (state.currentView === 'datos') await loadData();
  } catch (error) {
    toast(error.message, 'error');
  } finally {
    button.disabled = false;
    button.textContent = 'Importar archivo…';
    $('#importFile').value = '';
  }
}

async function restoreBackup(filename) {
  const confirmed = await askConfirm({
    title: '¿Restaurar esta copia?',
    message: 'Se sustituirán todos los datos actuales por los de la copia. Antes se guardará una copia del estado actual.',
    accept: 'Restaurar',
    danger: true
  });
  if (!confirmed) return;
  try {
    const result = await api('/api/restore', { method: 'POST', body: { file: filename, confirm: true } });
    toast(`Copia restaurada. Copia de seguridad previa: ${result.safety_backup}`, 'success');
    await loadSubjects();
    await loadData();
  } catch (error) {
    toast(error.message, 'error');
  }
}

async function createBackup() {
  try {
    const result = await api('/api/backup', { method: 'POST', body: { reason: 'manual' } });
    toast(`Copia creada: ${result.backup.name}`, 'success');
    await loadData();
  } catch (error) {
    toast(error.message, 'error');
  }
}

/* ---------- Eventos globales ---------- */

function bindEvents() {
  document.addEventListener('click', (event) => {
    const setup = event.target.closest('[data-action="manage-subjects"], [data-action="sync-canvas"]');
    if (setup) {
      if (setup.dataset.action === 'manage-subjects') openSubjectsManager();
      else syncCanvas();
      return;
    }
    const subjectButton = event.target.closest('[data-subject]');
    if (subjectButton) {
      openSubject(subjectButton.dataset.subject);
      return;
    }
    const viewButton = event.target.closest('[data-view]');
    if (viewButton) {
      navigate(viewButton.dataset.view);
      return;
    }
    const goButton = event.target.closest('[data-go]');
    if (goButton) {
      navigate(goButton.dataset.go);
    }
  });

  $('#menu').addEventListener('click', () => $('#sidebar').classList.toggle('open'));

  $('#modalClose').addEventListener('click', closeModal);
  $('#modalCancel').addEventListener('click', closeModal);
  $('#modal').addEventListener('click', (event) => {
    if (event.target === $('#modal')) closeModal();
  });
  $('#confirmCancel').addEventListener('click', () => closeConfirm(false));
  $('#confirmAccept').addEventListener('click', () => closeConfirm(true));
  $('#confirm').addEventListener('click', (event) => {
    if (event.target === $('#confirm')) closeConfirm(false);
  });
  document.addEventListener('keydown', (event) => {
    if (event.key !== 'Escape') return;
    if (!$('#confirm').hidden) closeConfirm(false);
    else if (!$('#modal').hidden) closeModal();
  });

  $('#addEvent').addEventListener('click', () => openEventForm());
  $('#addTask').addEventListener('click', () => openTaskForm());
  $('#dedupeEvents').addEventListener('click', async () => {
    const confirmed = await askConfirm({
      title: '¿Limpiar eventos duplicados?',
      message: 'Se eliminarán los eventos duplicados (mismo título, fecha, asignatura y categoría), conservando solo el más reciente.',
      accept: 'Limpiar',
      danger: true
    });
    if (!confirmed) return;
    try {
      const result = await api('/api/events/deduplicate', { method: 'POST' });
      toast(result.message, 'success');
      await loadCalendar();
    } catch (error) {
      toast(error.message, 'error');
    }
  });
  $('#addTutoring').addEventListener('click', () => openTutoringForm());
  $('#addNote').addEventListener('click', () => openNoteForm());

  $('#calendarSwitch').addEventListener('click', (event) => {
    const button = event.target.closest('[data-calview]');
    if (!button) return;
    state.calendar.view = button.dataset.calview;
    loadCalendar().catch((error) => toast(error.message, 'error'));
  });
  $('#prev').addEventListener('click', () => {
    const data = state.calendar.data;
    if (data && data.prev_anchor) {
      state.calendar.anchor = data.prev_anchor;
      loadCalendar().catch((error) => toast(error.message, 'error'));
    }
  });
  $('#next').addEventListener('click', () => {
    const data = state.calendar.data;
    if (data && data.next_anchor) {
      state.calendar.anchor = data.next_anchor;
      loadCalendar().catch((error) => toast(error.message, 'error'));
    }
  });

  // Notas libres por día (vista semana y panel del día): guardado automático
  document.addEventListener('input', (event) => {
    if (event.target.matches && event.target.matches('.day-note-text')) scheduleDayNoteSave(event.target);
  });
  document.addEventListener('focusout', (event) => {
    if (event.target.matches && event.target.matches('.day-note-text')) flushDayNoteSave(event.target);
  });

  // Botones de los recuadros de notas: minimizar, cerrar y volver a mostrar.
  document.addEventListener('click', (event) => {
    const button = event.target.closest('[data-note-action]');
    if (!button) return;
    event.preventDefault();
    event.stopPropagation();
    handleClassNoteAction(button);
  });

  $('#calendar').addEventListener('click', (event) => {
    // Escribir en las notas (o usar sus botones) no debe abrir el panel del día
    if (event.target.closest('.day-notes')) return;
    const item = event.target.closest('.event');
    if (item) {
      event.stopPropagation();
      openCalendarItem(item.dataset.kind, Number(item.dataset.id));
      return;
    }
    const month = event.target.closest('[data-month]');
    if (month) {
      state.calendar.view = 'month';
      state.calendar.anchor = `${month.dataset.month}-01`;
      loadCalendar().catch((error) => toast(error.message, 'error'));
      return;
    }
    const day = event.target.closest('[data-day]');
    if (day) {
      openDayPanel(day.dataset.day);
      // Si se ha pulsado una nota de la vista mes, dejarla lista para escribir
      const chip = event.target.closest('[data-note-subject]');
      if (chip) {
        const selector = chip.dataset.noteSubject
          ? `#modal .day-note-text[data-subject-id="${chip.dataset.noteSubject}"]`
          : '#modal .day-note-text:not([data-subject-id])';
        const textarea = $(selector);
        if (textarea) {
          textarea.focus();
          textarea.setSelectionRange(textarea.value.length, textarea.value.length);
        }
      }
    }
  });

  $('#taskFilters').addEventListener('click', (event) => {
    const button = event.target.closest('[data-status]');
    if (!button) return;
    state.taskFilter.status = button.dataset.status;
    loadTasks().catch((error) => toast(error.message, 'error'));
  });

  let taskSearchTimer = null;
  $('#taskSearch').addEventListener('input', (event) => {
    state.taskFilter.q = event.target.value;
    clearTimeout(taskSearchTimer);
    taskSearchTimer = setTimeout(() => {
      loadTasks().catch((error) => toast(error.message, 'error'));
    }, 250);
  });
  $('#taskPriority').addEventListener('change', (event) => {
    state.taskFilter.priority = event.target.value;
    loadTasks().catch((error) => toast(error.message, 'error'));
  });

  $('#taskList').addEventListener('click', (event) => {
    const row = event.target.closest('.task');
    if (!row) return;
    const task = state.tasks.find((item) => item.id === Number(row.dataset.id));
    if (!task) return;
    const action = event.target.closest('[data-action]');
    if (!action) return;
    if (action.dataset.action === 'toggle') toggleTask(task);
    else if (action.dataset.action === 'edit') openTaskForm(task);
    else if (action.dataset.action === 'delete') deleteTask(task);
  });

  window.addEventListener('beforeunload', (event) => {
    if (state.currentView === 'horario' && scheduleIsDirty()) {
      event.preventDefault();
      event.returnValue = '';
    }
  });

  $('#saveSchedule').addEventListener('click', saveSchedule);
  $('#editTimes').addEventListener('click', openTimesForm);
  $('#manageSubjects').addEventListener('click', openSubjectsManager);
  $('#resetSchedule').addEventListener('click', () => {
    loadSchedule().catch((error) => toast(error.message, 'error'));
  });
  $('#schedule').addEventListener('click', (event) => {
    const cell = event.target.closest('.slot.editable');
    if (!cell) return;
    openSlotForm(Number(cell.dataset.weekday), cell.dataset.start, cell.dataset.end);
  });

  $('#courseSwitch').addEventListener('click', (event) => {
    const button = event.target.closest('[data-course]');
    if (!button) return;
    state.evaluationCourse = button.dataset.course;
    loadEvaluations().catch((error) => toast(error.message, 'error'));
  });

  $('#tutoringList').addEventListener('click', (event) => {
    const action = event.target.closest('[data-tutoring-action]');
    if (!action) return;
    handleTutoringAction(action.dataset.tutoringAction, Number(action.dataset.id));
  });

  $('#notesList').addEventListener('click', (event) => {
    const action = event.target.closest('[data-note-action]');
    if (!action) return;
    handleNoteAction(action.dataset.noteAction, Number(action.dataset.id));
  });

  let noteSearchTimer = null;
  $('#noteSearch').addEventListener('input', () => {
    clearTimeout(noteSearchTimer);
    noteSearchTimer = setTimeout(() => {
      loadNotes().catch((error) => toast(error.message, 'error'));
    }, 250);
  });

  $('#subjectContent').addEventListener('click', (event) => {
    const action = event.target.closest('[data-subject-action]');
    if (!action) return;
    handleSubjectAction(action.dataset.subjectAction, Number(action.dataset.id));
  });
  $('#addSubjectTask').addEventListener('click', () => {
    if (state.subjectData) openTaskForm(null, null, state.subjectData.subject.id);
  });
  $('#addSubjectNote').addEventListener('click', () => {
    if (state.subjectData) openNoteForm(null, state.subjectData.subject.id);
  });
  $('#addSubjectMaterial').addEventListener('click', () => openMaterialForm());
  $('#addSubjectPlan').addEventListener('click', () => openPlanForm());

  $('#createBackup').addEventListener('click', createBackup);
  $('#backupList').addEventListener('click', (event) => {
    const button = event.target.closest('[data-restore]');
    if (button) restoreBackup(button.dataset.restore);
  });
  $('#importButton').addEventListener('click', () => $('#importFile').click());
  $('#importFile').addEventListener('change', (event) => {
    importFromFile(event.target.files[0]);
  });

  $('#upcoming').addEventListener('click', (event) => {
    const element = event.target.closest('[data-upcoming-kind]');
    if (!element) return;
    const kind = element.dataset.upcomingKind;
    if (kind === 'task') navigate('tareas');
    else if (kind === 'evaluation') navigate('evaluaciones');
    else navigate('calendario');
  });
}

/* ---------- Aula Virtual (Canvas) ---------- */

function syncSummary(result) {
  const parts = [];
  if (result.created) parts.push(`${result.created} ${result.created === 1 ? 'entrega nueva' : 'entregas nuevas'}`);
  if (result.updated) parts.push(`${result.updated} ${result.updated === 1 ? 'actualizada' : 'actualizadas'}`);
  if (result.grading) parts.push(`${result.grading} por corregir`);
  return parts.length ? `Aula Virtual: ${parts.join(', ')}.` : 'Aula Virtual: todo al día.';
}

async function syncCanvas({ silent = false } = {}) {
  const button = $('#syncBtn');
  if (button.disabled) return;
  button.disabled = true;
  button.classList.add('syncing');
  try {
    const result = await api('/api/canvas/sync', { method: 'POST' });
    const changed = result.created || result.updated || result.grading || result.grading_done;
    button.title = `Sincronizar con el Aula Virtual (última: ${new Date(result.synced_at).toLocaleString('es-ES')})`;
    if (changed) {
      await loadSubjects();
      refreshReminderBadge();
      await refreshCurrent();
    }
    if (!silent || changed) toast(syncSummary(result), 'success');
  } catch (error) {
    if (!/en curso/.test(error.message)) toast(`Aula Virtual: ${error.message}`, 'error');
  } finally {
    button.disabled = false;
    button.classList.remove('syncing');
  }
}

async function logout() {
  const ok = await askConfirm({
    title: 'Cerrar sesión',
    message: 'Se borrará la contraseña guardada en este equipo y tendrás que volver a entrar con tu usuario de MEDAC.',
    accept: 'Cerrar sesión',
  });
  if (!ok) return;
  try {
    await api('/api/auth/logout', { method: 'POST' });
  } catch (error) {
    /* Aunque falle, se vuelve a la pantalla de acceso. */
  }
  window.location.href = '/login';
}

/* ---------- Mis asignaturas ---------- */

function openSubjectsManager() {
  openModal({ title: 'Mis asignaturas', eyebrow: 'CONFIGURACIÓN', fields: [], onSubmit: null });
  $('#modalSubmit').hidden = true;
  $('#modalCancel').textContent = 'Cerrar';
  const list = state.subjects.map((subject) => `
    <li class="subject-row">
      ${subjectDot(subject.slug, subject.color)}
      <span><strong>${esc(subject.name)}</strong><small>${esc(subject.course || 'Sin curso')}</small></span>
      <button type="button" class="icon-btn" data-manage="edit" data-slug="${esc(subject.slug)}" title="Editar">✎</button>
      <button type="button" class="icon-btn" data-manage="delete" data-slug="${esc(subject.slug)}" title="Eliminar">✕</button>
    </li>`).join('');
  $('#modalFields').innerHTML = `
    <div class="field full subjects-manager">
      ${state.subjects.length ? `<ul class="subject-list">${list}</ul>` : '<p class="panel-empty">Aún no tienes asignaturas. Añádelas aquí o pulsa «Sincronizar» para traerlas del Aula Virtual.</p>'}
      <button type="button" class="primary" data-manage="new"><svg class="ico"><use href="#i-plus"/></svg>Nueva asignatura</button>
    </div>`;
  $('#modalFields').onclick = async (event) => {
    const button = event.target.closest('[data-manage]');
    if (!button) return;
    const subject = state.subjects.find((item) => item.slug === button.dataset.slug);
    if (button.dataset.manage === 'new') openSubjectForm(null);
    if (button.dataset.manage === 'edit' && subject) openSubjectForm(subject);
    if (button.dataset.manage === 'delete' && subject) await deleteSubject(subject);
  };
}

function openSubjectForm(subject) {
  $('#modalFields').onclick = null;
  openModal({
    title: subject ? 'Editar asignatura' : 'Nueva asignatura',
    eyebrow: 'MIS ASIGNATURAS',
    submitLabel: subject ? 'Guardar' : 'Añadir',
    fields: [
      { name: 'name', label: 'Nombre', type: 'text', full: true, placeholder: 'Habilidades Sociales' },
      { name: 'short_name', label: 'Nombre corto (menú y horario)', type: 'text', placeholder: 'Opcional' },
      { name: 'course', label: 'Curso o grupo', type: 'text', placeholder: '1.º INF' },
      { name: 'icon', label: 'Icono', type: 'select', options: SUBJECT_ICONS.map((icon) => ({ value: icon, label: icon })) },
      { name: 'color', label: 'Color', type: 'colorpicker', full: true }
    ],
    values: subject
      ? { name: subject.name, short_name: subject.short_name === subject.name ? '' : subject.short_name, course: subject.course, icon: subject.icon || '◇', color: subject.color }
      : { icon: '◇', color: '#7C8CD8' },
    onSubmit: async (values) => {
      if (!values.name) throw new Error('Escribe el nombre de la asignatura.');
      const body = { name: values.name, short_name: values.short_name, course: values.course, icon: values.icon, color: values.color || '#7C8CD8' };
      if (subject) {
        await api(`/api/subjects/${encodeURIComponent(subject.slug)}`, { method: 'PUT', body });
      } else {
        await api('/api/subjects', { method: 'POST', body });
      }
      await loadSubjects();
      toast(subject ? 'Asignatura guardada.' : 'Asignatura añadida.', 'success');
      await refreshCurrent();
      setTimeout(openSubjectsManager, 0);
    }
  });
}

async function deleteSubject(subject) {
  const ok = await askConfirm({
    title: `¿Eliminar «${subject.name}»?`,
    message: 'Sus tareas, eventos y notas se conservan sin asignatura. Se borran sus materiales, planificaciones y notas de clase, y sus horas del horario pasan a «Libre». Si viene del Aula Virtual, no se volverá a crear.',
    accept: 'Eliminar',
    danger: true
  });
  if (!ok) return;
  try {
    await api(`/api/subjects/${encodeURIComponent(subject.slug)}`, { method: 'DELETE' });
    if (state.subject === subject.slug) state.subject = null;
    await loadSubjects();
    toast('Asignatura eliminada.', 'success');
    if (state.currentView === 'asignatura') navigate('inicio'); else await refreshCurrent();
    openSubjectsManager();
  } catch (error) {
    toast(error.message, 'error');
  }
}

/* ---------- Cuenta atrás hasta el próximo descanso ---------- */

function breakIcon(name, scope) {
  const lower = (name || '').toLowerCase();
  if (lower.includes('navidad')) return '🎄';
  if (lower.includes('semana santa')) return '🌷';
  if (lower.includes('verano')) return '☀️';
  if (scope === 'no_lectivo') return '🌿';
  return '🎉';
}

// «Vacaciones de Navidad» → «las vacaciones de Navidad»; «Día no lectivo…» → «el día no lectivo…»
function breakPhrase(name) {
  const clean = (name || '').replace(/\s*\([^)]*\)\s*$/, '').trim();
  const rules = [
    [/^Vacaciones\b/, 'las '], [/^Días\b/, 'los '], [/^Día\b/, 'el '], [/^Fiesta\b/, 'la ']
  ];
  for (const [pattern, article] of rules) {
    if (pattern.test(clean)) {
      const lowered = /^Fiesta\b/.test(clean) ? clean : clean.charAt(0).toLowerCase() + clean.slice(1);
      return article + lowered;
    }
  }
  return clean;
}

function formatDayMonth(iso) {
  const date = parseISO(iso);
  if (!date) return '';
  return new Intl.DateTimeFormat('es-ES', { weekday: 'long', day: 'numeric', month: 'long' }).format(date);
}

async function loadCountdown() {
  let data;
  try {
    data = await api('/api/countdown');
  } catch (error) {
    return;
  }
  const box = $('#countdown');
  const text = $('#countdownText');
  const phrase = breakPhrase(data.name);
  const isPeriod = data.scope === 'vacaciones' || /^(Días|Vacaciones)\b/.test(data.name || '');
  $('#countdownIcon').textContent = data.state === 'done' ? '☀️' : breakIcon(data.name, data.scope);
  // Texto completo (pantallas anchas) y versión corta (móvil).
  let full;
  let short;
  if (data.state === 'now') {
    const back = `<small>Vuelves el ${esc(formatDayMonth(data.back))}</small>`;
    full = isPeriod ? `¡Disfruta de ${esc(phrase)}! ${back}` : `¡Hoy es fiesta: ${esc(phrase)}! ${back}`;
    short = isPeriod ? '¡A disfrutar!' : '¡Hoy es fiesta!';
  } else if (data.state === 'upcoming' && data.days === 1) {
    full = isPeriod ? `¡Mañana empiezan ${esc(phrase)}!` : `¡Mañana es fiesta: ${esc(phrase)}!`;
    short = '¡Mañana descanso!';
  } else if (data.state === 'upcoming') {
    const school = data.school_days === 1 ? '1 día de clase' : `${data.school_days} días de clase`;
    full = `Faltan <b>${data.days} días</b> para ${esc(phrase)} <small>· ${school}</small>`;
    short = `<b>${data.days} días</b>`;
  } else {
    full = '¡Curso completado! <small>Feliz verano</small>';
    short = '¡Feliz verano!';
  }
  text.innerHTML = `<span class="hide-sm">${full}</span><span class="only-sm">${short}</span>`;
  const plain = text.querySelector('.hide-sm').textContent.replace(/\s+/g, ' ').trim();
  box.title = `${plain} · Ver el calendario`;
  box.setAttribute('aria-label', `${plain}. Ver el calendario`);
  box.hidden = false;
}

/* ---------- Actualizaciones ---------- */

const UPDATE_SKIP_KEY = 'agenda-update-omitida';

async function checkForUpdate() {
  let info;
  try {
    info = await api('/api/update');
  } catch (error) {
    return;
  }
  const version = $('#appVersion');
  if (version && info.current) version.textContent = `v${info.current}`;
  if (!info.available) return;
  let skipped = '';
  try { skipped = window.localStorage.getItem(UPDATE_SKIP_KEY) || ''; } catch (error) { /* sin almacenamiento */ }
  if (skipped === info.latest) return;
  const card = $('#updateCard');
  $('#updateText').textContent = `Ya está disponible la versión ${info.latest} (tienes la ${info.current}).`;
  $('#updateNotes').textContent = info.notes || '';
  $('#updateNotes').hidden = !info.notes;
  card.hidden = false;
  $('#updateLater').onclick = () => {
    try { window.localStorage.setItem(UPDATE_SKIP_KEY, info.latest); } catch (error) { /* sin almacenamiento */ }
    card.hidden = true;
  };
  $('#updateInstall').onclick = () => installUpdate(info);
}

async function installUpdate(info) {
  const button = $('#updateInstall');
  button.disabled = true;
  button.textContent = 'Descargando…';
  try {
    await api('/api/update/install', { method: 'POST' });
  } catch (error) {
    button.disabled = false;
    button.textContent = 'Actualizar ahora';
    toast(error.message, 'error');
    return;
  }
  $('#updateCard').hidden = true;
  $('#updateOverlay').hidden = false;
  // La agenda se reinicia con la versión nueva; cuando responda, se recarga la ventana.
  const started = Date.now();
  const poll = async () => {
    try {
      const response = await fetch('/api/ping', { cache: 'no-store' });
      const data = await response.json();
      if (data.version === info.latest) {
        window.location.reload();
        return;
      }
    } catch (error) { /* reiniciándose */ }
    if (Date.now() - started > 90000) {
      $('#updateOverlayText').textContent = 'Está tardando más de la cuenta. Cierra esta ventana y vuelve a abrir la agenda.';
      return;
    }
    setTimeout(poll, 1000);
  };
  setTimeout(poll, 1500);
}

/* ---------- Arranque ---------- */

async function init() {
  bindEvents();
  bindReminderEvents();
  bindFichajeEvents();
  $('#taskPriority').value = state.taskFilter.priority;
  try {
    await loadSubjects();
  } catch (error) {
    toast(error.message, 'error');
  }
  refreshReminderBadge();
  navigate('inicio');
  $('#syncBtn').addEventListener('click', () => syncCanvas());
  $('#logoutBtn').addEventListener('click', logout);
  syncCanvas({ silent: true });
  checkForUpdate();
  loadCountdown();
}

document.addEventListener('DOMContentLoaded', init);
