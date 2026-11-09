import calendar
import html
import os
import re
import subprocess
import sys
from datetime import date, timedelta

import streamlit as st

import db

# Muss der erste Streamlit-Befehl sein: Titel im Browser-Tab, Icon, volle Breite
st.set_page_config(page_title="StudyFlow", page_icon="📚", layout="wide")

# Tabellen anlegen, falls es sie noch nicht gibt (bei jedem Start sicher)
db.init_db()

# st.session_state merkt sich Werte, solange der Browser-Tab offen ist.
# Ist "benutzer_id" gesetzt, ist jemand eingeloggt.
if "benutzer_id" not in st.session_state:
    st.session_state["benutzer_id"] = None
    st.session_state["email"] = None


# ---------------------------------------------------------------------------
# Konstanten
# ---------------------------------------------------------------------------

# Erste Auswahl im Fach-Dropdown, wenn ein Eintrag zu keinem Fach gehört
KEIN_FACH = "– kein Fach –"

MONATE = ["Jänner", "Februar", "März", "April", "Mai", "Juni",
          "Juli", "August", "September", "Oktober", "November", "Dezember"]
WOCHENTAGE = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]

# Auswahl im Filter "Zeitraum" auf der Seite "Alle Einträge"
ZEITRAEUME = ["Alle", "Überfällig", "Heute", "Nächste 7 Tage", "Diesen Monat", "Ohne Datum", "Eigener Zeitraum"]

# Farben, die in der ganzen App verwendet werden
LILA = "#6C5CE7"
ROT = "#E5484D"
BLAU = "#3B82F6"
GRUEN = "#10B981"
ORANGE = "#F59E0B"
GRAU = "#9AA0B4"

# Jede Kategorie hat ihre eigene Farbe (für die Etiketten)
KATEGORIE_FARBEN = {
    "Prüfung": ROT,
    "Abgabe": BLAU,
    "To-do": GRUEN,
    "Präsentation": ORANGE,
}

# Eigenes Design zusätzlich zu .streamlit/config.toml.
# Streamlit gibt jedem Container mit key="abc" die CSS-Klasse "st-key-abc".
# [class*="st-key-karte_"] trifft alle Container, deren key mit "karte_" beginnt.
CSS = """
<style>
/* Karten für die Einträge: weiß, mit farbigem Rand links */
[class*="st-key-karte_"] {
    background: #FFFFFF;
    border: 1px solid #E4E3EE;
    border-left: 6px solid #6C5CE7;
    border-radius: 12px;
    padding: 12px 16px;
}
[class*="st-key-karte_ueberfaellig_"] { border-left-color: #E5484D; background: #FFF5F5; }
[class*="st-key-karte_erledigt_"] { border-left-color: #10B981; opacity: 0.6; }

.sf-titel { font-weight: 600; font-size: 1.05rem; }
.sf-titel.erledigt { text-decoration: line-through; }
.sf-titel.ueberfaellig { color: #E5484D; }
.sf-beschreibung { color: #6B6F80; font-size: 0.9rem; margin-top: 6px; }

/* Etiketten (Datum, Kategorie, Fach): die Farbe kommt aus dem Python-Code */
.sf-pill {
    display: inline-block; margin: 6px 6px 0 0; padding: 2px 10px;
    border-radius: 999px; font-size: 0.78rem; font-weight: 600; color: #FFFFFF;
}

/* Kacheln auf dem Dashboard */
.sf-kachel { border-radius: 12px; padding: 14px 18px; color: #FFFFFF; }
.sf-kachel-zahl { font-size: 2rem; font-weight: 700; }

/* Kalender: ein Kästchen pro Tag */
.sf-wochentag { text-align: center; font-weight: 700; color: #6C5CE7; }
[class*="st-key-tag_"] {
    background: #FFFFFF;
    border: 1px solid #E4E3EE;
    border-radius: 10px;
    padding: 6px;
    min-height: 110px;
}
[class*="st-key-tag_anders_"] { opacity: 0.4; }
[class*="st-key-tag_heute_"] { border: 2px solid #6C5CE7; }
[class*="st-key-tag_"] button {
    width: 100%; justify-content: flex-start; min-height: 0;
    padding: 2px 8px; background: #EEEDF7;
}
[class*="st-key-tag_"] button p { font-size: 0.75rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
[class*="st-key-kal_ueberfaellig_"] button { background: #E5484D; color: #FFFFFF; }
[class*="st-key-kal_erledigt_"] button { background: #D1F2E0; text-decoration: line-through; }
</style>
"""


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def faecher_dropdown_daten():
    """Gibt {Fachname: id} zurück, mit 'kein Fach' (-> None) an erster Stelle."""
    faecher = {KEIN_FACH: None}
    for fach in db.faecher_laden(st.session_state["benutzer_id"]):
        faecher[fach["name"]] = fach["id"]
    return faecher


def kategorien_dropdown_daten():
    """Gibt {Kategoriename: id} zurück."""
    return {k["name"]: k["id"] for k in db.kategorien_laden()}


def ist_ueberfaellig(eintrag):
    """True, wenn der Eintrag nicht erledigt ist und die Deadline vor heute liegt.

    Text-Vergleich reicht: '2026-10-31' < '2026-11-02' stimmt, weil das
    Format JJJJ-MM-TT wie ein Datum sortiert.
    """
    return (
        not eintrag["erledigt"]
        and eintrag["deadline"] is not None
        and eintrag["deadline"] < date.today().isoformat()
    )


def status_von(eintrag):
    """'erledigt', 'ueberfaellig' oder 'offen' – wird z.B. für die Kartenfarbe gebraucht."""
    if eintrag["erledigt"]:
        return "erledigt"
    if ist_ueberfaellig(eintrag):
        return "ueberfaellig"
    return "offen"


def datum_deutsch(iso_datum):
    """'2026-12-10' -> '10.12.2026'"""
    jahr, monat, tag = iso_datum.split("-")
    return f"{tag}.{monat}.{jahr}"


def deadline_text(eintrag):
    """Beschreibt die Deadline in Worten und wählt die Farbe dafür.

    Gibt (text, farbe) zurück, z.B. ('Morgen fällig', ORANGE).
    """
    if eintrag["deadline"] is None:
        return "Kein Datum", GRAU

    deadline = date.fromisoformat(eintrag["deadline"])
    tage = (deadline - date.today()).days  # negativ = in der Vergangenheit

    if eintrag["erledigt"]:
        return datum_deutsch(eintrag["deadline"]), GRUEN
    if tage < 0:
        return f"Überfällig seit {-tage} {'Tag' if tage == -1 else 'Tagen'}", ROT
    if tage == 0:
        return "Heute fällig", ORANGE
    if tage == 1:
        return "Morgen fällig", ORANGE
    if tage <= 7:
        return f"In {tage} Tagen · {datum_deutsch(eintrag['deadline'])}", LILA
    return datum_deutsch(eintrag["deadline"]), LILA


def sichere_farbe(farbe):
    """Lässt nur echte Hex-Farben wie '#4A90E2' durch.

    Die Farbe landet im HTML. Weil die Datenbank jetzt über GitHub geteilt
    wird, prüfen wir sie, statt ihr blind zu vertrauen.
    """
    if farbe and re.fullmatch(r"#[0-9A-Fa-f]{6}", farbe):
        return farbe
    return GRAU


def etikett(text, farbe):
    """Ein kleines farbiges Etikett (weiße Schrift auf farbigem Hintergrund) als HTML."""
    return f'<span class="sf-pill" style="background:{farbe}">{html.escape(text)}</span>'


def eintrag_html(eintrag, mit_beschreibung=True):
    """Titel und farbige Etiketten (Deadline, Kategorie, Fach, Dokumente) als HTML.

    html.escape sorgt dafür, dass z.B. ein Titel wie '<b>Test' als Text
    angezeigt und nicht als HTML ausgeführt wird.
    """
    status = status_von(eintrag)
    text, farbe = deadline_text(eintrag)

    etiketten = etikett(f"📅 {text}", farbe)
    etiketten += etikett(eintrag["kategorie"], KATEGORIE_FARBEN.get(eintrag["kategorie"], LILA))
    if eintrag["fach"]:
        etiketten += etikett(eintrag["fach"], sichere_farbe(eintrag["fach_farbe"]))
    if eintrag["anzahl_dokumente"]:
        etiketten += etikett(f"📎 {eintrag['anzahl_dokumente']}", GRAU)

    teile = [f'<div class="sf-titel {status}">{html.escape(eintrag["titel"])}</div>',
             f"<div>{etiketten}</div>"]
    if mit_beschreibung and eintrag["beschreibung"]:
        beschreibung = eintrag["beschreibung"]
        if len(beschreibung) > 160:  # lange Texte in der Karte abkürzen
            beschreibung = beschreibung[:160] + " …"
        teile.append(f'<div class="sf-beschreibung">{html.escape(beschreibung)}</div>')
    return "".join(teile)


def erledigt_geaendert(eintrag_id, key):
    """Wird von Streamlit aufgerufen, sobald ein Erledigt-Haken geklickt wird."""
    db.eintrag_erledigt_setzen(eintrag_id, st.session_state["benutzer_id"], st.session_state[key])

    # Steht derselbe Eintrag noch an einer anderen Stelle, würde sich dessen
    # Checkbox den alten Zustand merken. Wir löschen ihn, damit sie beim
    # Neuladen wieder den Wert aus der Datenbank übernimmt.
    for anderer_key in list(st.session_state.keys()):
        if anderer_key != key and str(anderer_key).endswith(f"_erledigt_{eintrag_id}"):
            del st.session_state[anderer_key]


def datei_oeffnen(pfad):
    """Öffnet eine Datei mit dem Standardprogramm des Computers
    (PDF -> PDF-Reader, .docx -> Word, ...).

    Funktioniert, weil die App lokal läuft: Streamlit und die Datei sind auf
    demselben PC wie der Browser.
    """
    pfad = os.path.abspath(pfad)
    if sys.platform == "win32":         # Windows
        os.startfile(pfad)
    elif sys.platform == "darwin":      # Mac
        subprocess.run(["open", pfad])
    else:                               # Linux
        subprocess.run(["xdg-open", pfad])


# ---------------------------------------------------------------------------
# Bausteine, die auf mehreren Seiten vorkommen
# ---------------------------------------------------------------------------

def eintrag_karte(eintrag, bereich):
    """Ein Eintrag als Karte: Haken links, Infos in der Mitte, 'Details' rechts.

    bereich ist die Stelle, an der die Karte steht (z.B. "woche" oder "liste").
    Er kommt vor jeden key, damit derselbe Eintrag an zwei Stellen
    eindeutige keys hat.
    """
    eid = eintrag["id"]

    # Der key bestimmt die CSS-Klasse -> überfällige Karten bekommen einen roten Rand
    with st.container(key=f"karte_{status_von(eintrag)}_{bereich}_{eid}"):
        spalte_haken, spalte_text, spalte_button = st.columns([0.5, 8, 1.6], vertical_alignment="center")

        with spalte_haken:
            # on_change ruft erledigt_geaendert auf, bevor die Seite neu gezeichnet wird
            haken_key = f"{bereich}_erledigt_{eid}"
            st.checkbox(
                "Erledigt",
                value=bool(eintrag["erledigt"]),
                key=haken_key,
                on_change=erledigt_geaendert,
                args=(eid, haken_key),
                label_visibility="collapsed",
                help="Als erledigt markieren",
            )

        with spalte_text:
            st.html(eintrag_html(eintrag))

        with spalte_button:
            if st.button("Details", key=f"{bereich}_details_{eid}", icon=":material/edit_note:"):
                eintrag_dialog(eid)


def eintrag_liste(eintraege, bereich, leer_text):
    """Mehrere Karten untereinander, oder ein Hinweis, wenn die Liste leer ist."""
    if not eintraege:
        st.info(leer_text, icon=":material/info:")
    for eintrag in eintraege:
        eintrag_karte(eintrag, bereich)


# @st.dialog macht aus der Funktion ein Overlay-Fenster. Es öffnet sich,
# sobald die Funktion aufgerufen wird (z.B. nach einem Klick auf "Details").
@st.dialog("Eintrag", width="large")
def eintrag_dialog(eintrag_id):
    """Overlay mit allen Infos zu einem Eintrag: Details, Bearbeiten, Dokumente, Löschen."""
    benutzer_id = st.session_state["benutzer_id"]
    eintrag = db.eintrag_laden(eintrag_id, benutzer_id)
    if eintrag is None:
        st.error("Dieser Eintrag existiert nicht mehr.")
        return

    st.html(eintrag_html(eintrag, mit_beschreibung=False))

    erledigt = st.toggle("Erledigt", value=bool(eintrag["erledigt"]), key=f"dialog_erledigt_{eintrag_id}")
    if erledigt != bool(eintrag["erledigt"]):
        db.eintrag_erledigt_setzen(eintrag_id, benutzer_id, erledigt)
        st.rerun()  # ganze Seite neu laden -> Overlay schließt, Listen sind aktuell

    tab_details, tab_bearbeiten, tab_dokumente = st.tabs(
        ["Details", "Bearbeiten", f"Dokumente ({eintrag['anzahl_dokumente']})"]
    )

    with tab_details:
        spalte1, spalte2, spalte3 = st.columns(3)
        spalte1.markdown(f"**Kategorie**  \n{eintrag['kategorie']}")
        spalte2.markdown(f"**Fach**  \n{eintrag['fach'] or '–'}")
        spalte3.markdown(
            f"**Deadline**  \n{datum_deutsch(eintrag['deadline']) if eintrag['deadline'] else '–'}"
        )
        st.markdown("**Beschreibung**")
        st.text(eintrag["beschreibung"] or "Keine Beschreibung.")  # st.text = ohne Markdown

    with tab_bearbeiten:
        bearbeiten_formular(eintrag)

        st.divider()
        bestaetigt = st.checkbox("Ja, ich möchte diesen Eintrag löschen", key=f"loeschen_ok_{eintrag_id}")
        if st.button("Eintrag löschen", type="primary", icon=":material/delete:",
                     disabled=not bestaetigt, key=f"loeschen_{eintrag_id}"):
            db.eintrag_loeschen(eintrag_id, benutzer_id)
            st.rerun()

    with tab_dokumente:
        dokumente_bereich(eintrag_id)


def bearbeiten_formular(eintrag):
    """Vorausgefülltes Formular, um einen Eintrag zu ändern."""
    benutzer_id = st.session_state["benutzer_id"]
    kategorien = kategorien_dropdown_daten()
    faecher = faecher_dropdown_daten()
    kategorie_namen = list(kategorien.keys())
    fach_namen = list(faecher.keys())

    with st.form(f"bearbeiten_{eintrag['id']}", border=False):
        neuer_titel = st.text_input("Titel", value=eintrag["titel"])
        spalte1, spalte2, spalte3 = st.columns(3)
        neue_kategorie = spalte1.selectbox(
            "Kategorie", kategorie_namen, index=kategorie_namen.index(eintrag["kategorie"])
        )
        neues_fach = spalte2.selectbox(
            "Fach", fach_namen, index=fach_namen.index(eintrag["fach"] or KEIN_FACH)
        )
        neue_deadline = spalte3.date_input(
            "Deadline",
            # 'JJJJ-MM-TT' -> Datum, damit das Feld vorausgefüllt ist
            value=date.fromisoformat(eintrag["deadline"]) if eintrag["deadline"] else None,
            format="DD.MM.YYYY",
        )
        neue_beschreibung = st.text_area("Beschreibung", value=eintrag["beschreibung"] or "")
        speichern = st.form_submit_button("Änderungen speichern", type="primary", icon=":material/check:")

    if speichern:
        if not neuer_titel.strip():
            st.error("Der Titel darf nicht leer sein.")
        else:
            db.eintrag_bearbeiten(
                eintrag["id"],
                benutzer_id,
                kategorien[neue_kategorie],
                neuer_titel.strip(),
                neue_beschreibung.strip() or None,
                neue_deadline.isoformat() if neue_deadline else None,
                faecher[neues_fach],
            )
            st.rerun()


def dokumente_bereich(eintrag_id):
    """Dateiliste und Upload für einen Eintrag (im Overlay)."""
    benutzer_id = st.session_state["benutzer_id"]
    dokumente = db.dokumente_laden(eintrag_id, benutzer_id)

    if not dokumente:
        st.caption("Noch keine Dokumente.")
    for dokument in dokumente:
        dokument_zeile(dokument)

    # Eigenes Formular für den Upload, damit die Datei erst beim Klick
    # auf "Hochladen" gespeichert wird (und nicht bei jedem Neuladen)
    with st.form(f"upload_{eintrag_id}", clear_on_submit=True, border=False):
        dateien = st.file_uploader("Dateien hinzufügen", accept_multiple_files=True)
        hochladen = st.form_submit_button("Hochladen", icon=":material/upload:")

    if hochladen:
        if not dateien:
            st.error("Bitte zuerst eine Datei auswählen.")
        else:
            for datei in dateien:
                db.dokument_speichern(eintrag_id, benutzer_id, datei.name, datei.getvalue(), datei.type)
            # scope="fragment": nur das Overlay neu zeichnen, es bleibt offen
            st.rerun(scope="fragment")


def dokument_zeile(dokument):
    """Eine Datei: Klick auf den Namen öffnet sie, daneben ein Entfernen-Button."""
    benutzer_id = st.session_state["benutzer_id"]
    did = dokument["id"]

    spalte_name, spalte_loeschen = st.columns([5, 1], vertical_alignment="center")

    with spalte_name:
        # type="tertiary" = Button ohne Rahmen, sieht aus wie ein Link
        if st.button(f"📎 {dokument['dateiname']}", key=f"oeffnen_{did}", type="tertiary"):
            if os.path.exists(dokument["dateipfad"]):
                datei_oeffnen(dokument["dateipfad"])
            else:
                st.error("Die Datei fehlt im Ordner uploads/.")

    with spalte_loeschen:
        if st.button("Entfernen", key=f"dokument_loeschen_{did}", icon=":material/close:"):
            db.dokument_loeschen(did, benutzer_id)
            st.rerun(scope="fragment")


# ---------------------------------------------------------------------------
# Seiten
# ---------------------------------------------------------------------------

def login_seite():
    """Zeigt die Reiter 'Einloggen' und 'Registrieren', mittig auf der Seite."""
    _, mitte, _ = st.columns([1, 1.2, 1])

    with mitte:
        st.title("📚 StudyFlow")
        st.write("Prüfungen, Abgaben und To-dos an einem Ort.")

        tab_login, tab_registrieren = st.tabs(["Einloggen", "Registrieren"])

        with tab_login:
            with st.form("login"):
                email = st.text_input("E-Mail")
                passwort = st.text_input("Passwort", type="password")
                abgeschickt = st.form_submit_button("Einloggen", type="primary")

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
                abgeschickt = st.form_submit_button("Registrieren", type="primary")

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


def dashboard_seite():
    """Begrüßung, Kennzahlen und drei Reiter: nächste 7 Tage, überfällig, ohne Datum."""
    heute = date.today()
    name = st.session_state["email"].split("@")[0].split(".")[0].capitalize()

    eintraege = db.eintraege_laden(st.session_state["benutzer_id"])
    offen = [e for e in eintraege if not e["erledigt"]]
    in_einer_woche = (heute + timedelta(days=7)).isoformat()

    naechste_7_tage = [e for e in offen if e["deadline"] and heute.isoformat() <= e["deadline"] <= in_einer_woche]
    ueberfaellig = [e for e in offen if ist_ueberfaellig(e)]
    ohne_datum = [e for e in offen if e["deadline"] is None]

    st.title(f"Hallo {name} 👋")
    st.caption(f"{WOCHENTAGE[heute.weekday()]}, {heute.day}. {MONATE[heute.month - 1]} {heute.year}")

    # Vier farbige Kacheln mit den Zahlen: (Zahl, Text, Farbe)
    kacheln = [
        (len(offen), "Offen", LILA),
        (len(naechste_7_tage), "Nächste 7 Tage", BLAU),
        (len(ueberfaellig), "Überfällig", ROT),
        (len(ohne_datum), "Ohne Datum", ORANGE),
    ]
    spalten = st.columns(4)
    for spalte, (zahl, text, farbe) in zip(spalten, kacheln):
        spalte.html(f'<div class="sf-kachel" style="background:{farbe}">'
                    f'<div class="sf-kachel-zahl">{zahl}</div>{text}</div>')

    tab_woche, tab_ueberfaellig, tab_ohne = st.tabs([
        f"📅 Nächste 7 Tage ({len(naechste_7_tage)})",
        f"⚠️ Überfällig ({len(ueberfaellig)})",
        f"📝 Ohne Datum ({len(ohne_datum)})",
    ])
    with tab_woche:
        eintrag_liste(naechste_7_tage, "woche", "In den nächsten 7 Tagen ist nichts fällig.")
    with tab_ueberfaellig:
        eintrag_liste(ueberfaellig, "ueberfaellig", "Super, du hast keine überfälligen Aufgaben!")
    with tab_ohne:
        eintrag_liste(ohne_datum, "ohne", "Alle offenen Einträge haben ein Datum.")


def filter_anwenden(eintraege, suche, faecher, kategorien, zeitraum, von_bis, status):
    """Gibt nur die Einträge zurück, die zu allen gewählten Filtern passen.

    Leere Auswahl (z.B. faecher == []) bedeutet: nicht nach Fach filtern.
    """
    heute = date.today().isoformat()
    in_einer_woche = (date.today() + timedelta(days=7)).isoformat()
    ergebnis = []

    for e in eintraege:
        deadline = e["deadline"]  # Text 'JJJJ-MM-TT' oder None

        if suche and suche.lower() not in f"{e['titel']} {e['beschreibung'] or ''}".lower():
            continue
        if faecher and (e["fach"] or KEIN_FACH) not in faecher:
            continue
        if kategorien and e["kategorie"] not in kategorien:
            continue
        if status == "Offen" and e["erledigt"]:
            continue
        if status == "Erledigt" and not e["erledigt"]:
            continue

        if zeitraum == "Überfällig" and not ist_ueberfaellig(e):
            continue
        if zeitraum == "Heute" and deadline != heute:
            continue
        if zeitraum == "Nächste 7 Tage" and not (deadline and heute <= deadline <= in_einer_woche):
            continue
        if zeitraum == "Diesen Monat" and not (deadline and deadline[:7] == heute[:7]):
            continue
        if zeitraum == "Ohne Datum" and deadline is not None:
            continue
        # Während man im Datumsfeld wählt, ist erst ein Datum ausgewählt
        # (len(von_bis) == 1) -> dann noch nicht filtern
        if zeitraum == "Eigener Zeitraum" and len(von_bis) == 2:
            if not (deadline and von_bis[0].isoformat() <= deadline <= von_bis[1].isoformat()):
                continue

        ergebnis.append(e)
    return ergebnis


def alle_eintraege_seite():
    """Liste aller Einträge mit Filtern."""
    benutzer_id = st.session_state["benutzer_id"]
    st.title("Alle Einträge")

    eintraege = db.eintraege_laden(benutzer_id)
    fach_namen = [KEIN_FACH] + [f["name"] for f in db.faecher_laden(benutzer_id)]
    kategorie_namen = [k["name"] for k in db.kategorien_laden()]

    with st.container(border=True):
        spalte1, spalte2, spalte3 = st.columns([2, 1.3, 1.3])
        suche = spalte1.text_input("Suche", placeholder="Titel oder Beschreibung …", icon=":material/search:")
        faecher = spalte2.multiselect("Fach", fach_namen, placeholder="Alle Fächer")
        kategorien = spalte3.multiselect("Kategorie", kategorie_namen, placeholder="Alle Kategorien")

        spalte4, spalte5, spalte6 = st.columns([1.3, 1.3, 2])
        zeitraum = spalte4.selectbox("Zeitraum", ZEITRAEUME)
        # segmented_control gibt None zurück, wenn man die Auswahl wieder abwählt
        status = spalte5.segmented_control("Status", ["Alle", "Offen", "Erledigt"], default="Alle") or "Alle"
        von_bis = ()
        if zeitraum == "Eigener Zeitraum":
            von_bis = spalte6.date_input(
                "Von – bis",
                value=(date.today(), date.today() + timedelta(days=30)),
                format="DD.MM.YYYY",
            )

    gefiltert = filter_anwenden(eintraege, suche, faecher, kategorien, zeitraum, von_bis, status)
    st.caption(f"{len(gefiltert)} von {len(eintraege)} Einträgen")
    eintrag_liste(gefiltert, "liste", "Keine Einträge passen zu deinen Filtern.")


def monat_wechseln(schritt):
    """Springt im Kalender einen Monat vor (+1) oder zurück (-1)."""
    monat = st.session_state["kalender_monat"]
    jahr, monat_nr = monat.year, monat.month + schritt
    if monat_nr == 0:
        jahr, monat_nr = jahr - 1, 12
    elif monat_nr == 13:
        jahr, monat_nr = jahr + 1, 1
    st.session_state["kalender_monat"] = date(jahr, monat_nr, 1)


def kalender_seite():
    """Monatskalender. Klick auf einen Eintrag öffnet das Overlay."""
    benutzer_id = st.session_state["benutzer_id"]
    heute = date.today()
    if "kalender_monat" not in st.session_state:
        st.session_state["kalender_monat"] = heute.replace(day=1)
    monat = st.session_state["kalender_monat"]

    st.title("Kalender")

    # Kopfzeile: November 2026   ‹ Heute ›            [Erledigte anzeigen]
    titel, zurueck, heute_spalte, vor, _, option = st.columns(
        [2.6, 0.45, 0.85, 0.45, 1.2, 2], vertical_alignment="center"
    )
    titel.subheader(f"{MONATE[monat.month - 1]} {monat.year}")
    zurueck.button("‹", key="monat_zurueck", on_click=monat_wechseln, args=(-1,), help="Voriger Monat")
    if heute_spalte.button("Heute", key="monat_heute"):
        st.session_state["kalender_monat"] = heute.replace(day=1)
        st.rerun()
    vor.button("›", key="monat_vor", on_click=monat_wechseln, args=(1,), help="Nächster Monat")
    erledigte_zeigen = option.toggle("Erledigte anzeigen", value=False)

    # Einträge nach Datum gruppieren: {'2026-11-09': [eintrag, eintrag], ...}
    eintraege = db.eintraege_laden(benutzer_id)
    nach_tag = {}
    for e in eintraege:
        if e["deadline"] and (erledigte_zeigen or not e["erledigt"]):
            nach_tag.setdefault(e["deadline"], []).append(e)

    kopf = st.columns(7, gap="small")
    for spalte, name in zip(kopf, WOCHENTAGE):
        spalte.html(f'<div class="sf-wochentag">{name[:2]}</div>')

    # monthdatescalendar liefert ganze Wochen (Mo–So), auch mit Tagen aus dem
    # Vor- und Folgemonat, damit das Raster immer vollständig ist
    for woche in calendar.Calendar(firstweekday=0).monthdatescalendar(monat.year, monat.month):
        spalten = st.columns(7, gap="small")
        for spalte, tag in zip(spalten, woche):
            if tag == heute:
                art = "heute"
            elif tag.month != monat.month:
                art = "anders"
            else:
                art = "normal"

            # key -> CSS-Klasse, z.B. "st-key-tag_heute_2026-11-09"
            with spalte, st.container(key=f"tag_{art}_{tag.isoformat()}"):
                st.html(f'<span class="sf-tagnr {art}">{tag.day}</span>')
                for e in nach_tag.get(tag.isoformat(), []):
                    status = status_von(e)
                    icon = {"erledigt": ":material/check_circle:",
                            "ueberfaellig": ":material/warning:",
                            "offen": ":material/radio_button_unchecked:"}[status]
                    # Status im key -> CSS färbt überfällige rot, erledigte grau
                    if st.button(e["titel"], key=f"kal_{status}_{e['id']}", icon=icon, type="tertiary",
                                 help=f"{e['kategorie']} · {e['fach'] or 'kein Fach'}"):
                        eintrag_dialog(e["id"])

    ohne_datum = [e for e in eintraege if e["deadline"] is None and not e["erledigt"]]
    if ohne_datum:
        with st.expander(f"📝 Offene Einträge ohne Datum ({len(ohne_datum)})"):
            eintrag_liste(ohne_datum, "kalender_ohne", "")


def neuer_eintrag_seite():
    """Formular für einen neuen Eintrag."""
    benutzer_id = st.session_state["benutzer_id"]
    st.title("Neuer Eintrag")

    kategorien = kategorien_dropdown_daten()
    faecher = faecher_dropdown_daten()

    # clear_on_submit=True leert die Felder nach dem Speichern
    with st.form("neuer_eintrag", clear_on_submit=True):
        titel = st.text_input("Titel", placeholder="z.B. Marketing-Präsentation")
        spalte1, spalte2, spalte3 = st.columns(3)
        kategorie = spalte1.selectbox("Kategorie", list(kategorien.keys()))
        fach = spalte2.selectbox("Fach", list(faecher.keys()))
        deadline = spalte3.date_input("Deadline (optional)", value=None, format="DD.MM.YYYY")
        beschreibung = st.text_area("Beschreibung (optional)", placeholder="Was ist zu tun?")
        # accept_multiple_files=True -> man kann mehrere Dateien auf einmal wählen
        dateien = st.file_uploader("Dokumente (optional)", accept_multiple_files=True)
        abgeschickt = st.form_submit_button("Eintrag speichern", type="primary", icon=":material/check:")

    if abgeschickt:
        if not titel.strip():
            st.error("Bitte einen Titel eingeben.")
        else:
            eintrag_id = db.eintrag_anlegen(
                benutzer_id,
                kategorien[kategorie],
                titel.strip(),
                beschreibung.strip() or None,                # leerer Text -> None
                deadline.isoformat() if deadline else None,  # Datum -> 'JJJJ-MM-TT'
                faecher[fach],                               # "kein Fach" -> None
            )
            # datei.getvalue() = Inhalt als Bytes, datei.type = z.B. 'application/pdf'
            for datei in dateien:
                db.dokument_speichern(eintrag_id, benutzer_id, datei.name, datei.getvalue(), datei.type)
            st.success(f"„{titel.strip()}“ wurde gespeichert.", icon=":material/check_circle:")


def faecher_seite():
    """Links ein neues Fach anlegen, rechts die Liste der Fächer."""
    benutzer_id = st.session_state["benutzer_id"]
    st.title("Fächer")

    links, rechts = st.columns([1, 1.6], gap="large")

    with links:
        st.subheader("Neues Fach")
        with st.form("neues_fach", clear_on_submit=True):
            name = st.text_input("Name", placeholder="z.B. Mathe")
            farbe = st.color_picker("Farbe", value="#6C5CE7")
            abgeschickt = st.form_submit_button("Fach anlegen", type="primary", icon=":material/add:")

        if abgeschickt:
            if not name.strip():
                st.error("Bitte einen Namen eingeben.")
            elif db.fach_anlegen(benutzer_id, name.strip(), farbe) is None:
                st.error(f"Das Fach „{name.strip()}“ gibt es schon.")
            else:
                st.success(f"Fach „{name.strip()}“ wurde angelegt.")

    with rechts:
        st.subheader("Meine Fächer")
        faecher = db.faecher_laden(benutzer_id)
        eintraege = db.eintraege_laden(benutzer_id)
        if not faecher:
            st.info("Du hast noch keine Fächer.", icon=":material/info:")

        for fach in faecher:
            anzahl = sum(1 for e in eintraege if e["fach_id"] == fach["id"] and not e["erledigt"])
            with st.container(key=f"karte_fach_{fach['id']}"):
                spalte_name, spalte_button = st.columns([3.5, 1.5], vertical_alignment="center")
                # Name des Fachs + Etikett in der Fachfarbe
                spalte_name.html(
                    f'<div class="sf-titel">{html.escape(fach["name"])}</div>'
                    + etikett(f"{anzahl} offen", sichere_farbe(fach["farbe"]))
                )
                # Popover = kleines Fenster beim Klick, hier als Rückfrage vor dem Löschen
                with spalte_button.popover("Löschen", icon=":material/delete:"):
                    st.write("Die Einträge bleiben erhalten, nur ohne Fach.")
                    if st.button("Ja, löschen", key=f"fach_loeschen_{fach['id']}", type="primary"):
                        db.fach_loeschen(fach["id"], benutzer_id)
                        st.rerun()


# ---------------------------------------------------------------------------
# Start: Login oder App mit Navigation
# ---------------------------------------------------------------------------

st.html(CSS)

if st.session_state["benutzer_id"] is None:
    # Wer nicht eingeloggt ist, sieht nur die Login-Seite
    login_seite()
else:
    # st.navigation baut das Menü in der Sidebar. Jede Seite ist eine unserer
    # Funktionen; das Wörterbuch teilt das Menü in zwei Abschnitte.
    seiten = st.navigation({
        "Übersicht": [
            st.Page(dashboard_seite, title="Dashboard", icon=":material/space_dashboard:", default=True),
            st.Page(alle_eintraege_seite, title="Alle Einträge", icon=":material/list_alt:", url_path="alle"),
            st.Page(kalender_seite, title="Kalender", icon=":material/calendar_month:", url_path="kalender"),
        ],
        "Verwalten": [
            st.Page(neuer_eintrag_seite, title="Neuer Eintrag", icon=":material/add_circle:", url_path="neu"),
            st.Page(faecher_seite, title="Fächer", icon=":material/school:", url_path="faecher"),
        ],
    })

    with st.sidebar:
        st.caption("Eingeloggt als")
        st.text(st.session_state["email"])  # st.text statt st.write: sonst wird die E-Mail ein Link
        if st.button("Logout", icon=":material/logout:"):
            st.session_state["benutzer_id"] = None
            st.session_state["email"] = None
            st.rerun()

    seiten.run()
