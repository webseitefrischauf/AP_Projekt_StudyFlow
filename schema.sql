-- schema.sql
-- Zweck: Bauplan der Datenbank. Hier stehen alle Tabellen von StudyFlow.
-- Das Schema kommt aus eurem ER-Diagramm ("StudyFlow Datenmodell").
-- datenbank.py liest diese Datei einmal beim Start und legt die Tabellen an.
-- Verantwortlich: Person D

PRAGMA foreign_keys = ON;  -- SQLite prüft Fremdschlüssel nur, wenn das eingeschaltet ist

-- Wer sich anmeldet. Passwort nie im Klartext, nur als Hash.
CREATE TABLE IF NOT EXISTS benutzer (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  email         TEXT NOT NULL UNIQUE,
  passwort_hash TEXT NOT NULL,
  erstellt_am   DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Einmal-Codes für "Passwort vergessen".
CREATE TABLE IF NOT EXISTS passwort_reset (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  benutzer_id INTEGER NOT NULL REFERENCES benutzer(id) ON DELETE CASCADE,
  token       TEXT NOT NULL UNIQUE,
  gueltig_bis DATETIME NOT NULL,
  verwendet   BOOLEAN NOT NULL DEFAULT 0
);

-- Prüfung, Abgabe oder To-do (User Story 7).
CREATE TABLE IF NOT EXISTS kategorie (
  id   INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE
);
-- "OR IGNORE": beim zweiten Start nicht nochmal einfügen
INSERT OR IGNORE INTO kategorie (id, name) VALUES (1, 'Prüfung'), (2, 'Abgabe'), (3, 'To-do');

-- Optional: Fächer. Kann weggelassen werden, wenn die Zeit knapp wird.
CREATE TABLE IF NOT EXISTS fach (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  benutzer_id INTEGER NOT NULL REFERENCES benutzer(id) ON DELETE CASCADE,
  name        TEXT NOT NULL,
  farbe       TEXT
);

-- Das Herzstück: jede Prüfung, Abgabe und jedes To-do ist ein Eintrag.
CREATE TABLE IF NOT EXISTS eintrag (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  benutzer_id  INTEGER NOT NULL REFERENCES benutzer(id) ON DELETE CASCADE,
  kategorie_id INTEGER NOT NULL REFERENCES kategorie(id),
  fach_id      INTEGER REFERENCES fach(id) ON DELETE SET NULL,
  titel        TEXT NOT NULL,
  beschreibung TEXT,
  deadline     DATE,               -- darf leer sein (NFA 4)
  erledigt     BOOLEAN NOT NULL DEFAULT 0,
  erledigt_am  DATETIME,
  erstellt_am  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Hochgeladene Dateien. Die Datei selbst liegt im Ordner uploads/, hier steht nur der Pfad.
CREATE TABLE IF NOT EXISTS dokument (
  id             INTEGER PRIMARY KEY AUTOINCREMENT,
  eintrag_id     INTEGER NOT NULL REFERENCES eintrag(id) ON DELETE CASCADE,
  dateiname      TEXT NOT NULL,
  dateipfad      TEXT NOT NULL,
  dateityp       TEXT,
  hochgeladen_am DATETIME DEFAULT CURRENT_TIMESTAMP
);
