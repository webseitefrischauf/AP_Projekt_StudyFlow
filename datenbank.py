# datenbank.py
# Zweck: Verbindung zur SQLite-Datenbank (Datei studyflow.db) herstellen
# und beim ersten Start alle Tabellen aus schema.sql anlegen.
# Alle anderen Dateien holen sich ihre Verbindung von hier.
# Verantwortlich: Person D (Woche 2)
#
# Was hier hineinkommt:
#
# 1. verbindung_holen()
#    - öffnet studyflow.db mit dem eingebauten Modul sqlite3
#    - schaltet Fremdschlüssel ein: PRAGMA foreign_keys = ON
#    - Tipp: verbindung.row_factory = sqlite3.Row, dann kann man
#      zeile["titel"] statt zeile[4] schreiben
#    - gibt die Verbindung zurück
#
# 2. tabellen_anlegen()
#    - liest den Text aus schema.sql
#    - führt ihn mit executescript(...) aus
#    - wird einmal ganz oben in app.py aufgerufen
#
# Lernziel: Was ist eine Verbindung, was ist ein Cursor,
# und warum braucht man commit() nach INSERT/UPDATE/DELETE?
