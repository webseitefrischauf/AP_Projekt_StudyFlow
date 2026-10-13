# pages/2_Eintraege.py
# Zweck: Liste aller Einträge, sortiert nach Deadline,
# mit Knöpfen zum Bearbeiten, Löschen und Erledigt-Markieren.
# Verantwortlich: Person B (Woche 3 und 4)
# User Stories 2, 4, 5, 6, 8
#
# Regel: Diese Datei zeigt nur an. Daten und Änderungen laufen über
# eintraege.py und dokumente.py. Kein SQL hier.
#
# Was hier hineinkommt:
# - alle_eintraege(...) holen und jeden Eintrag anzeigen
#   (Titel, Kategorie, Deadline, "noch X Tage", erledigt ja/nein)
# - pro Eintrag: Knopf "Erledigt", Knopf "Löschen", Bereich "Bearbeiten"
#   (st.button, st.expander)
# - angehängte Dokumente zum Herunterladen (st.download_button)
# - Filter offen / erledigt, z. B. mit st.radio
