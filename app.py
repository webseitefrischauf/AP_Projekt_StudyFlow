import os
import pandas as pd
import streamlit as st

st.title("StudyFlow")
st.write("Trage deine Aufgaben ein")

DATEI = "ausgaben.csv"

def lade_ausgaben():
    if os.path.exists(DATEI):
        return pd.read_csv(DATEI)
    return pd.DataFrame(columns=["datum", "betrag", "kategorie"])

def speichere_ausgaben(df):
    df.to_csv(DATEI, index=False)

# Tabelle testen
df = lade_ausgaben()
st.subheader("Deine Ausgaben-Liste")
st.dataframe(df)