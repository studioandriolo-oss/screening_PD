import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image

# Configurazione Pagina
st.set_page_config(page_title="GECO Immobiliare - Screening Engine", layout="wide")

# Caricamento Logo (Assicurati di caricare 'geco_logo.png' su GitHub nella cartella principale)
try:
    logo = Image.open("geco_logo.png")
    st.sidebar.image(logo, use_column_width=True)
except:
    st.sidebar.title("GECO IMMOBILIARE")

st.sidebar.markdown("---")

# 1. IMPOSTAZIONE PARAMETRI (INPUT UTENTE SIDEBAR)
st.sidebar.header("Filtri Ricerca")
prezzo_range = st.sidebar.slider("Range Prezzo (€)", 0, 1000000, (50000, 300000), step=5000)
comune = st.sidebar.multiselect("Comune", ["Padova", "Ponte di Brenta", "Vigodarzere", "Albignasego"], default="Padova")
tipologia = st.sidebar.selectbox("Tipologia", ["Residenziale", "Commerciale", "Ufficio"])

st.sidebar.header("Parametri Costi (%)")
perc_imposta = st.sidebar.number_input("Imposta Registro (%)", value=2.0, step=0.5) / 100
costo_notaio_fisso = st.sidebar.number_input("Notaio (€)", value=2500)
perc_agenzia_acq = st.sidebar.number_input("Agenzia Acquisto (%)", value=3.0, step=0.5) / 100
perc_imprevisti = st.sidebar.number_input("Imprevisti Ristr. (%)", value=10.0, step=1.0) / 100

# 2. LOGICA DI CALCOLO (MOTORE PANDAS)
def calculate_metrics(df):
    # Acquisto (Col J - O)
    df['Imposta'] = df['Prezzo_J'] * perc_imposta
    df['Notaio'] = costo_notaio_fisso
    df['Agenzia_Acq'] = df['Prezzo_J'] * perc_agenzia_acq
    df['Costo_Acquisto_Totale'] = df['Prezzo_J'] + df['Imposta'] + df['Notaio'] + df['Agenzia_Acq']
    df['Incidenza_MQ'] = df['Costo_Acquisto_Totale'] / df['Superficie']

    # Ristrutturazione (Col P - T)
    # Colonna P 'Costo_Ristr_P' è input utente
    df['Costi_Tecnici'] = df['Costo_Ristr_P'] * 0.10 # Esempio 10%
    df['Imprevisti'] = df['Costo_Ristr_P'] * perc_imprevisti
    df['Costo_Ristr_Totale'] = df['Costo_Ristr_P'] + df['Costi_Tecnici'] + df['Imprevisti']

    # Vendita & Utile (Col U - Y)
    # Colonna U 'Ipotesi_Vendita_U' è input utente
    df['Agenzia_Vendita'] = df['Ipotesi_Vendita_U'] * 0.03 # Default 3%
    df['Interessi'] = -75 # Valore fisso come da tuo foglio
    df['Utile_Lordo'] = df['Ipotesi_Vendita_U'] - df['Costo_Acquisto_Totale'] - df['Costo_Ristr_Totale'] - df['Agenzia_Vendita'] + df['Interessi']
    
    return df

# 3. INTERFACCIA PRINCIPALE
st.title("🚀 GECO Screening Engine")
st.subheader("Analisi Operazioni Immobiliari - Provincia di Padova")

# Mock Data (In attesa della Fase 2 - Scraping)
data = {
    'Comune': ['Padova', 'Ponte di Brenta', 'Vigodarzere', 'Padova'],
    'Zona': ['Centro Storico', 'Guizza', 'Sacra Famiglia', 'Portello'],
    'Superficie': [100, 85, 120, 70],
    'Prezzo_J': [150000, 120000, 180000, 95000],
    'Costo_Ristr_P': [30000, 20000, 45000, 15000], # Colonna P
    'Ipotesi_Vendita_U': [240000, 190000, 290000, 155000] # Colonna U
}

df = pd.DataFrame(data)

# Applica Filtri
mask = (df['Prezzo_J'] >= prezzo_range[0]) & (df['Prezzo_J'] <= prezzo_range[1]) & (df['Comune'].isin(comune))
df_filtered = df[mask].copy()

# Esegui Calcoli
if not df_filtered.empty:
    df_final = calculate_metrics(df_filtered)
    
    # Visualizzazione Professionale
    st.write("### Risultati Analisi")
    
    # Evidenzia la colonna Risultato (Utile Lordo)
    def highlight_profit(s):
        return ['background-color: #10b981; color: white' if s.name == 'Utile_Lordo' else '' for v in s]

    st.dataframe(df_final.style.apply(highlight_profit).format(precision=2))
    
    # Grafico ROI veloce
    st.bar_chart(df_final.set_index('Zona')['Utile_Lordo'])
else:
    st.warning("Nessun immobile trovato con i filtri selezionati.")

st.markdown("---")
st.caption("GECO Engine v1.0 - Sviluppato per scouting immobiliare professionale.")
