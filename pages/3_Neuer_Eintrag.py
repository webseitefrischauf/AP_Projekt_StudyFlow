# pages/3_Neuer_Eintrag.py
# Zweck: Formular, um einen neuen Eintrag anzulegen, inklusive Datei-Upload.
# Verantwortlich: Person B (Formular), Person D (Upload-Feld)
# User Stories 1, 7, 8
#
# Regel: Diese Datei zeigt nur an. Speichern läuft über
# eintraege.eintrag_anlegen(...) und dokumente.dokument_speichern(...).
#
# Was hier hineinkommt:
# - with st.form("neuer_eintrag"): ...  (ein Formular mit Absenden-Knopf)
#   - Titel: st.text_input
#   - Kategorie: st.selectbox mit alle_kategorien()
#   - Deadline: st.date_input, plus Häkchen "keine Deadline"
#   - Beschreibung: st.text_area
#   - Datei: st.file_uploader
# - Beim Absenden: prüfen, dass der Titel nicht leer ist,
#   dann speichern und st.success("Gespeichert") anzeigen
