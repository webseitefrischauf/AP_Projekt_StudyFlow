import html
from datetime import date

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

        # Navigation: der key merkt sich die gewählte Seite in st.session_state["seite"]
        seite = st.radio(
            "Navigation",
            ["Dashboard", "Neuer Eintrag", "Fächer"],
            key="seite",
            label_visibility="collapsed",  # Überschrift "Navigation" ausblenden
        )

        st.divider()
        if st.button("Logout"):
            st.session_state["benutzer_id"] = None
            st.session_state["email"] = None
            st.rerun()

    # Je nach Auswahl in der Sidebar die passende Seite zeigen
    if seite == "Dashboard":
        dashboard_seite()
    elif seite == "Neuer Eintrag":
        neuer_eintrag_seite()
    else:
        faecher_seite()


# Erste Auswahl im Fach-Dropdown, wenn ein Eintrag zu keinem Fach gehört
KEIN_FACH = "– kein Fach –"


def faecher_dropdown_daten():
    """Gibt {Fachname: id} zurück, mit 'kein Fach' (-> None) an erster Stelle."""
    faecher = {KEIN_FACH: None}
    for fach in db.faecher_laden(st.session_state["benutzer_id"]):
        faecher[fach["name"]] = fach["id"]
    return faecher


def dashboard_seite():
    """Liste der eigenen Einträge."""
    benutzer_id = st.session_state["benutzer_id"]
    st.subheader("Meine Einträge")

    # Werden für die Bearbeiten-Formulare der Einträge gebraucht
    kategorien = {k["name"]: k["id"] for k in db.kategorien_laden()}
    faecher = faecher_dropdown_daten()

    eintraege = db.eintraege_laden(benutzer_id)
    if not eintraege:
        st.info("Du hast noch keine Einträge. Lege links unter „Neuer Eintrag“ einen an.")

    for eintrag in eintraege:
        eintrag_anzeigen(eintrag, kategorien, faecher)


def neuer_eintrag_seite():
    """Formular für einen neuen Eintrag."""
    benutzer_id = st.session_state["benutzer_id"]
    st.subheader("Neuer Eintrag")

    # Dictionary {Name: id}, damit im Dropdown Namen stehen,
    # wir aber die id speichern können
    kategorien = {k["name"]: k["id"] for k in db.kategorien_laden()}
    faecher = faecher_dropdown_daten()

    # clear_on_submit=True leert die Felder nach dem Speichern
    with st.form("neuer_eintrag", clear_on_submit=True):
        titel = st.text_input("Titel")
        kategorie = st.selectbox("Kategorie", list(kategorien.keys()))
        fach = st.selectbox("Fach", list(faecher.keys()))
        deadline = st.date_input("Deadline", value=None, format="DD.MM.YYYY")
        beschreibung = st.text_area("Beschreibung (optional)")
        abgeschickt = st.form_submit_button("Speichern")

    if abgeschickt:
        if not titel.strip():
            st.error("Bitte einen Titel eingeben.")
        else:
            db.eintrag_anlegen(
                benutzer_id,
                kategorien[kategorie],
                titel.strip(),
                beschreibung.strip() or None,                # leerer Text -> None
                deadline.isoformat() if deadline else None,  # Datum -> 'JJJJ-MM-TT'
                faecher[fach],                               # "kein Fach" -> None
            )
            st.success(f"„{titel.strip()}“ wurde gespeichert. Du findest ihn im Dashboard.")


def faecher_seite():
    """Fächer anlegen, anzeigen und löschen."""
    benutzer_id = st.session_state["benutzer_id"]

    st.subheader("Neues Fach")
    with st.form("neues_fach", clear_on_submit=True):
        name = st.text_input("Name, z.B. Mathe")
        farbe = st.color_picker("Farbe", value="#4A90E2")
        abgeschickt = st.form_submit_button("Fach anlegen")

    if abgeschickt:
        if not name.strip():
            st.error("Bitte einen Namen eingeben.")
        elif db.fach_anlegen(benutzer_id, name.strip(), farbe) is None:
            st.error(f"Das Fach „{name.strip()}“ gibt es schon.")
        else:
            st.success(f"Fach „{name.strip()}“ wurde angelegt.")

    st.subheader("Meine Fächer")
    faecher = db.faecher_laden(benutzer_id)
    if not faecher:
        st.info("Du hast noch keine Fächer.")

    for fach in faecher:
        spalte_name, spalte_button = st.columns([5, 1])
        with spalte_name:
            st.markdown(fach_label(fach["name"], fach["farbe"]), unsafe_allow_html=True)
        with spalte_button:
            if st.button("Löschen", key=f"fach_loeschen_{fach['id']}"):
                db.fach_loeschen(fach["id"], benutzer_id)
                st.rerun()

    if faecher:
        st.caption("Wird ein Fach gelöscht, bleiben seine Einträge erhalten, nur ohne Fach.")


def fach_label(name, farbe):
    """Ein farbiger Punkt vor dem Fachnamen, als HTML.

    html.escape sorgt dafür, dass ein Name wie '<b>Mathe' als Text
    angezeigt und nicht als HTML ausgeführt wird.
    """
    return f'<span style="color:{farbe or "#888888"}">●</span> {html.escape(name)}'


def eintrag_anzeigen(eintrag, kategorien, faecher):
    """Zeigt einen Eintrag als Kästchen mit Erledigt-Haken, Bearbeiten und Löschen."""
    benutzer_id = st.session_state["benutzer_id"]
    eid = eintrag["id"]

    # Jedes Widget braucht einen eindeutigen key, sonst verwechselt
    # Streamlit die Checkboxen/Buttons der verschiedenen Einträge.
    with st.container(border=True):
        spalte_text, spalte_haken = st.columns([5, 1])

        with spalte_haken:
            erledigt = st.checkbox("Erledigt", value=bool(eintrag["erledigt"]), key=f"erledigt_{eid}")
        # Haken wurde geändert -> speichern und neu laden (Sortierung ändert sich)
        if erledigt != bool(eintrag["erledigt"]):
            db.eintrag_erledigt_setzen(eid, benutzer_id, erledigt)
            st.rerun()

        with spalte_text:
            titel = f"**{eintrag['titel']}** · {eintrag['kategorie']}"
            st.markdown(f"~~{titel}~~" if erledigt else titel)  # ~~ = durchgestrichen
            if eintrag["fach"]:
                st.markdown(fach_label(eintrag["fach"], eintrag["fach_farbe"]), unsafe_allow_html=True)
            if eintrag["deadline"]:
                # 'JJJJ-MM-TT' -> 'TT.MM.JJJJ'
                jahr, monat, tag = eintrag["deadline"].split("-")
                st.caption(f"Fällig am {tag}.{monat}.{jahr}")
            if eintrag["beschreibung"]:
                st.write(eintrag["beschreibung"])

        with st.expander("Bearbeiten"):
            namen = list(kategorien.keys())
            fach_namen = list(faecher.keys())
            with st.form(f"bearbeiten_{eid}"):
                neuer_titel = st.text_input("Titel", value=eintrag["titel"])
                neue_kategorie = st.selectbox("Kategorie", namen, index=namen.index(eintrag["kategorie"]))
                neues_fach = st.selectbox(
                    "Fach", fach_namen, index=fach_namen.index(eintrag["fach"] or KEIN_FACH)
                )
                neue_deadline = st.date_input(
                    "Deadline",
                    # 'JJJJ-MM-TT' -> Datum, damit das Feld vorausgefüllt ist
                    value=date.fromisoformat(eintrag["deadline"]) if eintrag["deadline"] else None,
                    format="DD.MM.YYYY",
                )
                neue_beschreibung = st.text_area("Beschreibung", value=eintrag["beschreibung"] or "")
                speichern = st.form_submit_button("Änderungen speichern")

            if speichern:
                if not neuer_titel.strip():
                    st.error("Der Titel darf nicht leer sein.")
                else:
                    db.eintrag_bearbeiten(
                        eid,
                        benutzer_id,
                        kategorien[neue_kategorie],
                        neuer_titel.strip(),
                        neue_beschreibung.strip() or None,
                        neue_deadline.isoformat() if neue_deadline else None,
                        faecher[neues_fach],
                    )
                    st.rerun()

            if st.button("Eintrag löschen", key=f"loeschen_{eid}", type="primary"):
                db.eintrag_loeschen(eid, benutzer_id)
                st.rerun()


# Wer nicht eingeloggt ist, sieht nur die Login-Seite
if st.session_state["benutzer_id"] is None:
    login_seite()
else:
    hauptseite()
