# pages/1_Dashboard.py
# Zweck: die Startseite nach dem Login. Zeigt auf einen Blick, was ansteht.
# Verantwortlich: Person C (Woche 3 bis 5)
# User Stories 2, 3 und NFA 2 bis 5
#
# Streamlit macht aus jeder Datei im Ordner pages/ automatisch eine Seite
# im Menü links. Die Zahl vorne bestimmt die Reihenfolge.
#
# Regel: Diese Datei zeigt nur an. Daten holt sie über eintraege.py,
# Rechnungen über hilfsfunktionen.py. Kein SQL hier.
#
# Was hier hineinkommt, in drei Abschnitten:
# 1. "Nächste 7 Tage": offene Einträge mit Deadline bis heute + 7 Tage,
#    sortiert, mit "noch X Tage"
# 2. "Überfällig": offene Einträge mit Deadline in der Vergangenheit,
#    auffällig markiert, z. B. mit st.error(...)
# 3. "Ohne Datum": offene Einträge ohne Deadline
#
# Vorher prüfen: Ist jemand eingeloggt? (st.session_state, siehe app.py)
