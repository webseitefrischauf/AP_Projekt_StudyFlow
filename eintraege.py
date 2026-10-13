# eintraege.py
# Zweck: Einträge (Prüfungen, Abgaben, To-dos) anlegen, lesen, ändern, löschen.
# Tabellen: eintrag, kategorie
# Verantwortlich: Person B (Woche 3 und 4)
# User Stories: 1, 4, 5, 6, 7
#
# Was hier hineinkommt (jede Funktion bekommt die benutzer_id,
# damit jeder nur seine eigenen Einträge sieht):
#
# 1. eintrag_anlegen(benutzer_id, titel, kategorie_id, deadline, beschreibung)
#    - INSERT INTO eintrag ...
#    - deadline darf None sein
#    - gibt die neue id zurück (cursor.lastrowid), die braucht dokumente.py
#
# 2. alle_eintraege(benutzer_id)
#    - SELECT mit ORDER BY deadline, damit die nächste Deadline oben steht
#    - Einträge ohne Deadline ans Ende: ORDER BY deadline IS NULL, deadline
#
# 3. eintrag_aendern(eintrag_id, benutzer_id, ...)   -> UPDATE
# 4. eintrag_loeschen(eintrag_id, benutzer_id)       -> DELETE
# 5. als_erledigt_markieren(eintrag_id, benutzer_id) -> erledigt = 1
#
# 6. alle_kategorien()
#    - für die Auswahlliste im Formular
