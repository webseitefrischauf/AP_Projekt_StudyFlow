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

import hashlib
import hmac
import os
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


# ---------------------------------------------------------------------------
# Benutzer
# ---------------------------------------------------------------------------

def _passwort_hashen(passwort, salt=None):
    """Erzeugt einen Hash aus dem Passwort.

    Das 'Salt' ist eine Zufallszahl pro Benutzer. Dadurch bekommen zwei
    Benutzer mit demselben Passwort trotzdem unterschiedliche Hashes.
    Gespeichert wird beides zusammen als 'salt$hash'.
    """
    if salt is None:
        salt = os.urandom(16).hex()
    hash_wert = hashlib.pbkdf2_hmac("sha256", passwort.encode(), salt.encode(), 100_000).hex()
    return f"{salt}${hash_wert}"


def benutzer_registrieren(email, passwort):
    """Legt einen neuen Benutzer an.

    Gibt die id des neuen Benutzers zurück,
    oder None, wenn die E-Mail schon vergeben ist.
    """
    email = email.strip().lower()
    conn = verbindung()
    try:
        cursor = conn.execute(
            "INSERT INTO benutzer (email, passwort_hash) VALUES (?, ?)",
            (email, _passwort_hashen(passwort)),
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        # UNIQUE bei email verletzt -> E-Mail gibt es schon
        return None
    finally:
        conn.close()


def benutzer_einloggen(email, passwort):
    """Prüft E-Mail und Passwort.

    Gibt die id des Benutzers zurück, wenn alles stimmt, sonst None.
    """
    email = email.strip().lower()
    conn = verbindung()
    zeile = conn.execute(
        "SELECT id, passwort_hash FROM benutzer WHERE email = ?", (email,)
    ).fetchone()
    conn.close()

    if zeile is None:
        return None

    # Das eingegebene Passwort mit demselben Salt hashen und vergleichen
    salt = zeile["passwort_hash"].split("$")[0]
    if hmac.compare_digest(_passwort_hashen(passwort, salt), zeile["passwort_hash"]):
        return zeile["id"]
    return None


# ---------------------------------------------------------------------------
# Kategorien
# ---------------------------------------------------------------------------

def kategorien_laden():
    """Gibt alle Kategorien zurück (z.B. für ein Dropdown)."""
    conn = verbindung()
    kategorien = conn.execute("SELECT id, name FROM kategorie ORDER BY id").fetchall()
    conn.close()
    return kategorien


# ---------------------------------------------------------------------------
# Fächer
# ---------------------------------------------------------------------------

def fach_anlegen(benutzer_id, name, farbe=None):
    """Legt ein neues Fach an.

    Gibt die id des neuen Fachs zurück,
    oder None, wenn der Benutzer schon ein Fach mit diesem Namen hat.
    """
    conn = verbindung()
    try:
        cursor = conn.execute(
            "INSERT INTO fach (benutzer_id, name, farbe) VALUES (?, ?, ?)",
            (benutzer_id, name, farbe),
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        # UNIQUE (benutzer_id, name) verletzt -> Fach gibt es schon
        return None
    finally:
        conn.close()


def faecher_laden(benutzer_id):
    """Gibt alle Fächer eines Benutzers zurück, alphabetisch sortiert."""
    conn = verbindung()
    faecher = conn.execute(
        "SELECT id, name, farbe FROM fach WHERE benutzer_id = ? ORDER BY name",
        (benutzer_id,),
    ).fetchall()
    conn.close()
    return faecher


def fach_loeschen(fach_id, benutzer_id):
    """Löscht ein Fach. Die Einträge bleiben erhalten,
    ihr fach_id wird per ON DELETE SET NULL auf leer gesetzt."""
    conn = verbindung()
    conn.execute("DELETE FROM fach WHERE id = ? AND benutzer_id = ?", (fach_id, benutzer_id))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Einträge
# ---------------------------------------------------------------------------

def eintrag_anlegen(benutzer_id, kategorie_id, titel, beschreibung=None, deadline=None, fach_id=None):
    """Speichert einen neuen Eintrag und gibt seine id zurück.

    deadline ist ein Text im Format 'JJJJ-MM-TT' oder None.
    fach_id ist die id eines Fachs oder None (kein Fach).
    """
    conn = verbindung()
    cursor = conn.execute(
        "INSERT INTO eintrag (benutzer_id, kategorie_id, titel, beschreibung, deadline, fach_id) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (benutzer_id, kategorie_id, titel, beschreibung, deadline, fach_id),
    )
    conn.commit()
    conn.close()
    return cursor.lastrowid


def eintraege_laden(benutzer_id):
    """Gibt alle Einträge eines Benutzers zurück, nach Deadline sortiert.

    Einträge ohne Deadline kommen ans Ende. Über den JOIN bekommt jede
    Zeile zusätzlich den Namen der Kategorie (zeile["kategorie"]) und
    Name und Farbe des Fachs (zeile["fach"], zeile["fach_farbe"]).

    LEFT JOIN statt JOIN beim Fach: Einträge ohne Fach sollen trotzdem
    mitkommen (fach und fach_farbe sind dann None).
    """
    conn = verbindung()
    eintraege = conn.execute(
        """
        SELECT eintrag.*, kategorie.name AS kategorie,
               fach.name AS fach, fach.farbe AS fach_farbe
        FROM eintrag
        JOIN kategorie ON kategorie.id = eintrag.kategorie_id
        LEFT JOIN fach ON fach.id = eintrag.fach_id
        WHERE eintrag.benutzer_id = ?
        ORDER BY eintrag.erledigt, eintrag.deadline IS NULL, eintrag.deadline
        """,
        (benutzer_id,),
    ).fetchall()
    conn.close()
    return eintraege


# Bei den folgenden Funktionen steht immer auch 'benutzer_id = ?' im WHERE.
# So kann niemand fremde Einträge ändern, auch wenn er eine falsche id schickt.

def eintrag_bearbeiten(eintrag_id, benutzer_id, kategorie_id, titel, beschreibung=None, deadline=None, fach_id=None):
    """Überschreibt Titel, Kategorie, Beschreibung, Deadline und Fach eines Eintrags."""
    conn = verbindung()
    conn.execute(
        "UPDATE eintrag SET kategorie_id = ?, titel = ?, beschreibung = ?, deadline = ?, fach_id = ? "
        "WHERE id = ? AND benutzer_id = ?",
        (kategorie_id, titel, beschreibung, deadline, fach_id, eintrag_id, benutzer_id),
    )
    conn.commit()
    conn.close()


def eintrag_erledigt_setzen(eintrag_id, benutzer_id, erledigt):
    """Markiert einen Eintrag als erledigt (True) oder wieder offen (False)."""
    conn = verbindung()
    conn.execute(
        "UPDATE eintrag SET erledigt = ? WHERE id = ? AND benutzer_id = ?",
        (1 if erledigt else 0, eintrag_id, benutzer_id),
    )
    conn.commit()
    conn.close()


def eintrag_loeschen(eintrag_id, benutzer_id):
    """Löscht einen Eintrag (seine Dokumente werden per CASCADE mitgelöscht)."""
    conn = verbindung()
    conn.execute(
        "DELETE FROM eintrag WHERE id = ? AND benutzer_id = ?",
        (eintrag_id, benutzer_id),
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
