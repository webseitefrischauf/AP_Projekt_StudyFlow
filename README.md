# StudyFlow

Eine Web-App für Studierende: Prüfungen, Abgaben und To-dos mit Deadline eintragen,
Dokumente anhängen und auf einen Blick sehen, was als Nächstes ansteht.

Gebaut mit Python, Streamlit und SQLite im Rahmen eines Studienprojekts (4 Personen, 6 Wochen).

## Starten

```
pip install -r requirements.txt
streamlit run app.py
```

Danach öffnet sich die App im Browser unter http://localhost:8501.

## Welche Datei macht was

| Datei | Aufgabe | Verantwortlich |
| --- | --- | --- |
| `app.py` | Startpunkt: Tabellen anlegen, Login prüfen | A |
| `schema.sql` | Bauplan der Datenbank (alle Tabellen) | D |
| `datenbank.py` | Verbindung zu `studyflow.db` | D |
| `benutzer.py` | Registrieren, Login, Passwort-Reset | A |
| `eintraege.py` | Einträge anlegen, lesen, ändern, löschen | B |
| `dokumente.py` | Dateien speichern und laden | D |
| `hilfsfunktionen.py` | Tage bis Deadline, überfällig | C |
| `pages/1_Dashboard.py` | Startseite: 7 Tage, überfällig, ohne Datum | C |
| `pages/2_Eintraege.py` | Liste mit Bearbeiten und Löschen | B |
| `pages/3_Neuer_Eintrag.py` | Formular mit Datei-Upload | B, D |

Regel: Dateien in `pages/` zeigen nur an. Die anderen Dateien rechnen und speichern.

## Regeln im Team

- Vor dem Arbeiten `git pull`, danach `git commit` mit einem deutschen Satz und `git push`.
- Jede Person arbeitet in ihren eigenen Dateien. Gemeinsame Dateien nur nach Absprache ändern.
- Jede Datei hat oben einen Kommentar mit ihrem Zweck, jede Funktion einen Satz, was sie tut.
