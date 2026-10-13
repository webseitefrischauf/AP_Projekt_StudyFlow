# benutzer.py
# Zweck: alles rund ums Konto: registrieren, einloggen, Passwort zurücksetzen.
# Tabellen: benutzer, passwort_reset
# Verantwortlich: Person A (Woche 3 Login, Woche 5 Passwort-Reset)
#
# Was hier hineinkommt:
#
# 1. passwort_hashen(passwort)
#    - macht aus dem Passwort einen Hash mit dem eingebauten Modul hashlib
#      (z. B. hashlib.pbkdf2_hmac mit einem zufälligen "Salt" aus secrets)
#    - Merksatz: Die Datenbank kennt das Passwort nie, nur den Hash.
#
# 2. registrieren(email, passwort)
#    - prüft, ob die E-Mail schon existiert
#    - speichert E-Mail + Hash in der Tabelle benutzer
#
# 3. einloggen(email, passwort)
#    - sucht den Benutzer per E-Mail, hasht das eingegebene Passwort
#      und vergleicht mit dem gespeicherten Hash
#    - gibt die benutzer_id zurück oder None
#
# 4. reset_code_erstellen(email) und passwort_neu_setzen(code, neues_passwort)
#    - Code mit secrets erzeugen, in passwort_reset speichern, auf dem
#      Bildschirm anzeigen (statt E-Mail, siehe Plan)
#    - Code nur einmal und nur bis gueltig_bis erlaubt
#
# Wichtig: Werte immer mit ? in SQL einsetzen, nie mit f-Strings.
# Beispiel: "SELECT * FROM benutzer WHERE email = ?", (email,)
# Sonst ist SQL-Injection möglich.
