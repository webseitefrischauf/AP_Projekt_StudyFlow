# dokumente.py
# Zweck: hochgeladene Dateien (z. B. die Aufgabenstellung) speichern
# und beim Eintrag wieder anzeigen.
# Tabelle: dokument
# Verantwortlich: Person D (Woche 4 und 5)
# User Story: 8
#
# Was hier hineinkommt:
#
# 1. dokument_speichern(eintrag_id, hochgeladene_datei)
#    - hochgeladene_datei kommt von st.file_uploader(...)
#    - Datei in den Ordner uploads/ schreiben, mit eindeutigem Namen
#      (z. B. eintrag_id + Originalname), damit nichts überschrieben wird
#    - Name, Pfad und Typ in die Tabelle dokument eintragen
#
# 2. dokumente_zu_eintrag(eintrag_id)
#    - alle Dokumente eines Eintrags holen
#      SELECT * FROM dokument WHERE eintrag_id = ?
#
# 3. Anzeigen/Herunterladen passiert in der Seite mit st.download_button(...)
#
# Merksatz: Die Datei liegt im Ordner, die Datenbank merkt sich nur, wo.
