-- Esquema de la base de datos de Mi Agenda Digital 2026-2027.
-- Todas las fechas se guardan como texto ISO: YYYY-MM-DD.
-- Todas las horas se guardan como texto: HH:MM.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS subjects (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    slug        TEXT NOT NULL UNIQUE,
    name        TEXT NOT NULL,
    short_name  TEXT NOT NULL,
    course      TEXT,
    color       TEXT NOT NULL,
    icon        TEXT NOT NULL DEFAULT '',
    is_area     INTEGER NOT NULL DEFAULT 0 CHECK (is_area IN (0, 1)),
    sort_order  INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS schedule_slots (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    weekday     INTEGER NOT NULL CHECK (weekday BETWEEN 1 AND 5),
    start_time  TEXT NOT NULL,
    end_time    TEXT NOT NULL,
    subject_id  INTEGER REFERENCES subjects(id) ON DELETE SET NULL,
    label       TEXT,
    kind        TEXT NOT NULL CHECK (kind IN ('class', 'break', 'free')),
    notes       TEXT,
    UNIQUE (weekday, start_time)
);

CREATE TABLE IF NOT EXISTS tasks (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    title        TEXT NOT NULL,
    description  TEXT NOT NULL DEFAULT '',
    subject_id   INTEGER REFERENCES subjects(id) ON DELETE SET NULL,
    kind         TEXT NOT NULL DEFAULT 'tarea'
                 CHECK (kind IN ('tarea', 'entrega', 'examen', 'reunion', 'otro')),
    target       TEXT NOT NULL DEFAULT 'docente'
                 CHECK (target IN ('docente', 'alumno')),
    priority     TEXT NOT NULL DEFAULT 'media'
                 CHECK (priority IN ('alta', 'media', 'baja')),
    status       TEXT NOT NULL DEFAULT 'pendiente'
                 CHECK (status IN ('pendiente', 'en_curso', 'completada')),
    due_date     TEXT,
    due_time     TEXT,
    color        TEXT,
    marked       INTEGER NOT NULL DEFAULT 0 CHECK (marked IN (0, 1)),
    created_at   TEXT NOT NULL,
    updated_at   TEXT NOT NULL,
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    start_date  TEXT NOT NULL,
    end_date    TEXT,
    start_time  TEXT,
    end_time    TEXT,
    all_day     INTEGER NOT NULL DEFAULT 1 CHECK (all_day IN (0, 1)),
    subject_id  INTEGER REFERENCES subjects(id) ON DELETE SET NULL,
    category    TEXT NOT NULL DEFAULT 'evento'
                CHECK (category IN ('evento', 'entrega', 'reunion', 'examen', 'otro')),
    color       TEXT,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL,
    UNIQUE (title, start_date, subject_id, category)
);

CREATE TABLE IF NOT EXISTS holidays (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    start_date  TEXT NOT NULL,
    end_date    TEXT,
    name        TEXT NOT NULL,
    scope       TEXT NOT NULL
                CHECK (scope IN ('nacional', 'autonomico', 'local', 'vacaciones', 'no_lectivo')),
    verified    INTEGER NOT NULL DEFAULT 0 CHECK (verified IN (0, 1)),
    source      TEXT,
    notes       TEXT,
    UNIQUE (start_date, name)
);

CREATE TABLE IF NOT EXISTS evaluations (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    course      TEXT NOT NULL CHECK (course IN ('1LFP', '2LFP')),
    start_date  TEXT NOT NULL,
    end_date    TEXT,
    title       TEXT NOT NULL,
    kind        TEXT NOT NULL
                CHECK (kind IN ('comienzo', 'plazo', 'entrega_notas', 'no_lectivo', 'festivo', 'otro')),
    source_page TEXT,
    notes       TEXT,
    UNIQUE (course, start_date, title)
);

CREATE TABLE IF NOT EXISTS tutoring (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    kind        TEXT NOT NULL CHECK (kind IN ('seguimiento', 'visita', 'reunion')),
    student     TEXT NOT NULL,
    start_date  TEXT NOT NULL,
    start_time  TEXT,
    subject_id  INTEGER REFERENCES subjects(id) ON DELETE SET NULL,
    status      TEXT NOT NULL DEFAULT 'pendiente'
                CHECK (status IN ('pendiente', 'realizado', 'cancelado')),
    notes       TEXT NOT NULL DEFAULT '',
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS notes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    body        TEXT NOT NULL DEFAULT '',
    subject_id  INTEGER REFERENCES subjects(id) ON DELETE SET NULL,
    note_date   TEXT,
    pinned      INTEGER NOT NULL DEFAULT 0 CHECK (pinned IN (0, 1)),
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

-- Recordatorios semanales (como el recuadro «recordatorios» del plan semanal del PDF).
-- La semana se deduce de reminder_date (lunes a domingo).
CREATE TABLE IF NOT EXISTS reminders (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    title         TEXT NOT NULL,
    body          TEXT NOT NULL DEFAULT '',
    subject_id    INTEGER REFERENCES subjects(id) ON DELETE SET NULL,
    reminder_date TEXT NOT NULL,
    category      TEXT NOT NULL DEFAULT 'pendiente'
                  CHECK (category IN ('pendiente', 'corregir', 'revisar', 'otro')),
    done          INTEGER NOT NULL DEFAULT 0 CHECK (done IN (0, 1)),
    done_at       TEXT,
    progress      TEXT,  -- JSON del Aula Virtual: {"graded", "ungraded", "not_submitted"}
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL
);

-- Notas libres escritas directamente en un día del calendario (no son tareas).
CREATE TABLE IF NOT EXISTS day_notes (
    note_date   TEXT PRIMARY KEY,
    body        TEXT NOT NULL DEFAULT '',
    updated_at  TEXT NOT NULL
);

-- Notas de clase: qué se hace un día concreto en cada asignatura del horario.
CREATE TABLE IF NOT EXISTS class_notes (
    note_date   TEXT NOT NULL,
    subject_id  INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    body        TEXT NOT NULL DEFAULT '',
    updated_at  TEXT NOT NULL,
    PRIMARY KEY (note_date, subject_id)
);

-- Estado de cada nota de clase: 'open' (abierta), 'collapsed' (minimizada)
-- o 'hidden' (cerrada: esa asignatura no se imparte ese día).
CREATE TABLE IF NOT EXISTS class_note_state (
    note_date   TEXT NOT NULL,
    subject_id  INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    state       TEXT NOT NULL DEFAULT 'open'
                CHECK (state IN ('open', 'collapsed', 'hidden')),
    updated_at  TEXT NOT NULL,
    PRIMARY KEY (note_date, subject_id)
);

CREATE TABLE IF NOT EXISTS materials (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id  INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    title       TEXT NOT NULL,
    kind        TEXT,
    link        TEXT,
    notes       TEXT NOT NULL DEFAULT '',
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS lesson_plans (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id  INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    plan_date   TEXT,
    title       TEXT NOT NULL,
    objectives  TEXT NOT NULL DEFAULT '',
    activities  TEXT NOT NULL DEFAULT '',
    resources   TEXT NOT NULL DEFAULT '',
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

-- Vínculos con el Aula Virtual (Canvas): qué elemento local corresponde a cada
-- curso, tarea o corrección pendiente importada. kind: course | assignment | grading.
CREATE TABLE IF NOT EXISTS canvas_links (
    kind        TEXT NOT NULL,
    canvas_id   TEXT NOT NULL,
    local_id    INTEGER NOT NULL,
    meta        TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (kind, canvas_id)
);

CREATE INDEX IF NOT EXISTS idx_tasks_due      ON tasks (due_date);
CREATE INDEX IF NOT EXISTS idx_tasks_status   ON tasks (status);
CREATE INDEX IF NOT EXISTS idx_tasks_subject  ON tasks (subject_id);
CREATE INDEX IF NOT EXISTS idx_events_start   ON events (start_date);
CREATE INDEX IF NOT EXISTS idx_events_subject ON events (subject_id);
CREATE INDEX IF NOT EXISTS idx_holidays_start ON holidays (start_date);
CREATE INDEX IF NOT EXISTS idx_eval_course    ON evaluations (course, start_date);
CREATE INDEX IF NOT EXISTS idx_notes_subject  ON notes (subject_id);
CREATE INDEX IF NOT EXISTS idx_tutoring_date  ON tutoring (start_date);
CREATE INDEX IF NOT EXISTS idx_reminders_date ON reminders (reminder_date);
