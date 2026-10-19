# hilfsfunktionen.py
# Zweck: kleine Rechnungen rund um Deadlines, die mehrere Seiten brauchen.
# Verantwortlich: Person C (Woche 4)
# User Story 3, NFA 5
#
# Was hier hineinkommt:
#
# 1. tage_bis_deadline(deadline_text)
#    - "2026-11-20" -> Anzahl Tage ab heute (negativ = überfällig)
#    - None -> None (Einträge ohne Deadline sind erlaubt)
#    - Werkzeug: from datetime import date, date.fromisoformat(...), date.today()
#
# 2. ist_ueberfaellig(deadline_text, erledigt)
#    - True, wenn die Deadline vorbei ist und der Eintrag noch offen ist
#
# Ein fertiges, kommentiertes Beispiel für beide Funktionen steht im
# 6-Wochen-Plan unter "Wie ihr den Code versteht".
# Erst selbst versuchen, dann vergleichen.
