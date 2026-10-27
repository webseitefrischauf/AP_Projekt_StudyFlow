"""
db.py – Datenbank-Grundgerüst für StudyFlow

Hier wird die SQLite-Datenbank angelegt. Alle anderen Dateien (Seiten)
greifen später nur über Funktionen aus dieser Datei auf die Daten zu.

Tabellen (siehe ER-Diagramm):
    benutzer   – Login per E-Mail
    fach       – z.B. Mathe, Marketing (gehört zu einem Benutzer)
    kategorie  – Prüfung, Abgabe, To-do (fest vorgegeben)
    eintrag    – die eigentlichen Aufgaben/Deadlines
    dokument   – hochgeladene Dateien zu einem Eintrag
"""

import sqlite3

# Name der Datenbank-Datei. Sie wird automatisch im Projektordner erstellt,
# sobald init_db() zum ersten Mal aufgerufen wird.
DB_DATEI = "studyflow.db"

# Diese Kategorien werden beim ersten Start automatisch eingetragen.
STANDARD_KATEGORIEN = ["Prüfung", "Abgabe", "To-do", "Präsentation"]


def verbindung():
    """Öffnet eine Verbindung zur Datenbank und gibt sie zurück."""
    conn = sqlite3.connect(DB_DATEI)

    # Ergebnisse wie ein Dictionary lesbar machen: zeile["titel"] statt zeile[5]
    conn.row_factory = sqlite3.Row

    # SQLite prüft Fremdschlüssel nur, wenn man es bei jeder Verbindung einschaltet
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Erstellt alle Tabellen (falls sie noch nicht existieren)
    und trägt die Standard-Kategorien ein.

    Kann bei jedem App-Start aufgerufen werden – bestehende Daten
    bleiben erhalten (wegen 'IF NOT EXISTS' bzw. 'WHERE NOT EXISTS').
    """
    conn = verbindung()

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS benutzer (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            email         TEXT    NOT NULL UNIQUE,
            passwort_hash TEXT    NOT NULL          -- nie das Klartext-Passwort speichern!
        );

        CREATE TABLE IF NOT EXISTS fach (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            benutzer_id INTEGER NOT NULL,
            name        TEXT    NOT NULL,
            farbe       TEXT,                       -- z.B. '#E57373'
            FOREIGN KEY (benutzer_id) REFERENCES benutzer(id) ON DELETE CASCADE,
            UNIQUE (benutzer_id, name)              -- jedes Fach pro Benutzer nur einmal
        );

        CREATE TABLE IF NOT EXISTS kategorie (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT    NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS eintrag (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            benutzer_id  INTEGER NOT NULL,
            kategorie_id INTEGER NOT NULL,
            fach_id      INTEGER,                   -- darf leer sein
            titel        TEXT    NOT NULL,
            beschreibung TEXT,
            deadline     TEXT,                      -- Datum als 'JJJJ-MM-TT', darf leer sein
            erledigt     INTEGER NOT NULL DEFAULT 0, -- 0 = offen, 1 = erledigt
            FOREIGN KEY (benutzer_id)  REFERENCES benutzer(id)  ON DELETE CASCADE,
            FOREIGN KEY (kategorie_id) REFERENCES kategorie(id),
            FOREIGN KEY (fach_id)      REFERENCES fach(id)      ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS dokument (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            eintrag_id INTEGER NOT NULL,
            dateiname  TEXT    NOT NULL,            -- Originalname, z.B. 'Angabe.pdf'
            dateipfad  TEXT    NOT NULL,            -- wo die Datei liegt, z.B. 'uploads/17_Angabe.pdf'
            dateityp   TEXT,                        -- z.B. 'application/pdf'
            FOREIGN KEY (eintrag_id) REFERENCES eintrag(id) ON DELETE CASCADE
        );
    """)

    # Standard-Kategorien eintragen, aber nur wenn es sie noch nicht gibt.
    # (Nicht 'INSERT OR IGNORE' verwenden: das verbraucht bei AUTOINCREMENT
    #  trotzdem eine id, dadurch entstehen Lücken in der Nummerierung.)
    for name in STANDARD_KATEGORIEN:
        conn.execute(
            "INSERT INTO kategorie (name) SELECT ? "
            "WHERE NOT EXISTS (SELECT 1 FROM kategorie WHERE name = ?)",
            (name, name),
        )

    conn.commit()
    conn.close()


# Zum Testen direkt ausführen:  python db.py
if __name__ == "__main__":
    init_db()
    conn = verbindung()
    tabellen = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    print("Tabellen:", [t["name"] for t in tabellen])
    kategorien = conn.execute("SELECT * FROM kategorie").fetchall()
    print("Kategorien:", [k["name"] for k in kategorien])
    conn.close()
