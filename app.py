import streamlit as st

import db

# Tabellen anlegen, falls es sie noch nicht gibt (bei jedem Start sicher)
db.init_db()

st.title("Studyflow")

# st.session_state merkt sich Werte, solange der Browser-Tab offen ist.
# Ist "benutzer_id" gesetzt, ist jemand eingeloggt.
if "benutzer_id" not in st.session_state:
    st.session_state["benutzer_id"] = None
    st.session_state["email"] = None


def login_seite():
    """Zeigt die Reiter 'Einloggen' und 'Registrieren'."""
    tab_login, tab_registrieren = st.tabs(["Einloggen", "Registrieren"])

    with tab_login:
        with st.form("login"):
            email = st.text_input("E-Mail")
            passwort = st.text_input("Passwort", type="password")
            abgeschickt = st.form_submit_button("Einloggen")

        if abgeschickt:
            benutzer_id = db.benutzer_einloggen(email, passwort)
            if benutzer_id is None:
                st.error("E-Mail oder Passwort ist falsch.")
            else:
                st.session_state["benutzer_id"] = benutzer_id
                st.session_state["email"] = email.strip().lower()
                st.rerun()  # Seite neu laden, damit die App angezeigt wird

    with tab_registrieren:
        with st.form("registrieren"):
            email = st.text_input("E-Mail")
            passwort = st.text_input("Passwort", type="password")
            passwort2 = st.text_input("Passwort wiederholen", type="password")
            abgeschickt = st.form_submit_button("Registrieren")

        if abgeschickt:
            if "@" not in email:
                st.error("Bitte eine gültige E-Mail eingeben.")
            elif len(passwort) < 6:
                st.error("Das Passwort muss mindestens 6 Zeichen lang sein.")
            elif passwort != passwort2:
                st.error("Die Passwörter stimmen nicht überein.")
            elif db.benutzer_registrieren(email, passwort) is None:
                st.error("Diese E-Mail ist schon registriert.")
            else:
                st.success("Registrierung erfolgreich! Du kannst dich jetzt einloggen.")


def hauptseite():
    """Die eigentliche App, nur für eingeloggte Benutzer."""
    with st.sidebar:
        st.write(f"Eingeloggt als **{st.session_state['email']}**")
        if st.button("Logout"):
            st.session_state["benutzer_id"] = None
            st.session_state["email"] = None
            st.rerun()

    st.write("Trage deine To-dos ein")
    st.info("Hier kommen als Nächstes die Einträge hin.")


# Wer nicht eingeloggt ist, sieht nur die Login-Seite
if st.session_state["benutzer_id"] is None:
    login_seite()
else:
    hauptseite()
