import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image

# -----------------------------------------
# CONFIGURAZIONE PAGINA
# -----------------------------------------
st.set_page_config(page_title="GECO Immobiliare - Screening Engine", layout="wide")

# -----------------------------------------
# SIDEBAR: FILTRI E RICERCA
# -----------------------------------------
try:
    logo = Image.open("geco_logo.png")
    st.sidebar.image(logo, use_column_width=True)
except FileNotFoundError:
    st.sidebar.title("GECO IMMOBILIARE")

st.sidebar.markdown("### Filtri di Ricerca")
comune = st.sidebar.multiselect("Comune", ["Padova", "Ponte di Brenta", "Vigodarzere", "Albignasego"], default=["Padova"])
zona = st.sidebar.multiselect("Zona", ["Centro Storico", "Guizza", "Sacra Famiglia", "Portello"], default=["Centro Storico"])
tipologia = st.sidebar.selectbox("Tipologia", ["Residenziale", "Commerciale", "Ufficio"])
prezzo_range = st.sidebar.slider("Range Prezzo Ricerca (€)", 0, 1000000, (50000, 300000), step=5000)

st.sidebar.markdown("---")
st.sidebar.caption("GECO Engine v1.1 - Motore di Scouting")

# -----------------------------------------
# MAIN: INPUT EDITABILI E PARAMETRI FINANZIARI
# -----------------------------------------
st.title("🚀 GECO Screening Engine")
st.markdown("##### Parametri Finanziari e Costi")

# Plancia parametri in colonne per ottimizzare lo spazio
col1, col2, col3, col4 = st.columns(4)
param_prezzo = col1.number_input("Costo Base Ristr. (€/mq)", value=800, step=50)
imposta_perc = col2.number_input("Imposta Registro (%)", value=2.0, step=0.5) / 100
notaio_perc = col3.number_input("Notaio (%)", value=1.5, step=0.1) / 100
agenzia_acq_perc = col4.number_input("Agenzia Acquisto (%)", value=3.0, step=0.5) / 100

col5, col6, col7, col8 = st.columns(4)
imprevisti_perc = col5.number_input("Imprevisti Ristr. (%)", value=10.0, step=1.0) / 100
costi_tecnici_perc = col6.number_input("Costi Tecnici (%)", value=10.0, step=1.0) / 100
agenzia_ven_perc = col7.number_input("Agenzia Vendita (%)", value=3.0, step=0.5) / 100
interessi_perc = col8.number_input("Interessi Passivi (%)", value=4.0, step=0.5) / 100

st.markdown("---")

# -----------------------------------------
# DATABASE FITTIZIO (In attesa di Playwright)
# -----------------------------------------
data = {
    'Comune': ['Padova', 'Padova', 'Vigodarzere', 'Padova', 'Padova'],
    'Zona': ['Centro Storico', 'Centro Storico', 'Sacra Famiglia', 'Portello', 'Centro Storico'],
    'Tipologia': ['Residenziale', 'Residenziale', 'Residenziale', 'Residenziale', 'Residenziale'],
    'Superficie': [100, 150, 120, 70, 90],
    'Prezzo_J': [150000, 450000, 180000, 95000, 220000],
    'Ipotesi_Vendita_U': [240000, 580000, 290000, 155000, 310000]
}
df = pd.DataFrame(data)

# -----------------------------------------
# MOTORE DI CALCOLO PANDAS
# -----------------------------------------
def calculate_metrics(df_calc):
    # Calcolo Costo Ristrutturazione (P) basato sui mq per automatizzare l'ipotesi iniziale
    df_calc['Costo_Ristr_P'] = df_calc['Superficie'] * param_prezzo

    # Area Acquisto
    df_calc['Imposta'] = df_calc['Prezzo_J'] * imposta_perc
    df_calc['Notaio'] = df_calc['Prezzo_J'] * notaio_perc
    df_calc['Agenzia_Acq'] = df_calc['Prezzo_J'] * agenzia_acq_perc
    df_calc['Costo_Acquisto_Totale'] = df_calc['Prezzo_J'] + df_calc['Imposta'] + df_calc['Notaio'] + df_calc['Agenzia_Acq']

    # Area Ristrutturazione
    df_calc['Costi_Tecnici_Val'] = df_calc['Costo_Ristr_P'] * costi_tecnici_perc
    df_calc['Imprevisti_Val'] = df_calc['Costo_Ristr_P'] * imprevisti_perc
    df_calc['Costo_Ristr_Totale'] = df_calc['Costo_Ristr_P'] + df_calc['Costi_Tecnici_Val'] + df_calc['Imprevisti_Val']

    # Area Vendita
    df_calc['Agenzia_Vendita_Val'] = df_calc['Ipotesi_Vendita_U'] * agenzia_ven_perc
    df_calc['Interessi_Val'] = df_calc['Costo_Acquisto_Totale'] * interessi_perc

    # Utile Lordo
    df_calc['Utile_Lordo'] = (
        df_calc['Ipotesi_Vendita_U'] 
        - df_calc['Costo_Acquisto_Totale'] 
        - df_calc['Costo_Ristr_Totale'] 
        - df_calc['Agenzia_Vendita_Val'] 
        - df_calc['Interessi_Val']
    )
    
    return df_calc

# -----------------------------------------
# APPLICAZIONE FILTRI E VISUALIZZAZIONE
# -----------------------------------------
# 1. Filtro di Base (Geografia e Tipologia) per il calcolo del Prezzo Medio
mask_geo = (
    (df['Comune'].isin(comune) if comune else True) & 
    (df['Zona'].isin(zona) if zona else True) & 
    (df['Tipologia'] == tipologia)
)
df_geo_filtered = df[mask_geo].copy()

# 2. Filtro Prezzo (Applicato solo ai risultati della tabella)
mask_price = (df_geo_filtered['Prezzo_J'] >= prezzo_range[0]) & (df_geo_filtered['Prezzo_J'] <= prezzo_range[1])
df_final_filtered = df_geo_filtered[mask_price].copy()

st.write("### Risultati Analisi")

if not df_final_filtered.empty:
    df_calculated = calculate_metrics(df_final_filtered)
    
    # Seleziona solo le colonne rilevanti per mantenere la tabella snella
    colonne_display = [
        'Comune', 'Zona', 'Superficie', 'Prezzo_J', 
        'Costo_Acquisto_Totale', 'Costo_Ristr_Totale', 
        'Ipotesi_Vendita_U', 'Utile_Lordo'
    ]
    df_display = df_calculated[colonne_display]
    
    # Formattazione visiva: evidenzia l'utile lordo
    def highlight_profit(s):
        return ['background-color: #2ecc71; color: #0f172a; font-weight: bold' if s.name == 'Utile_Lordo' else '' for _ in s]

    # Mostra il dataframe con Streamlit
    st.dataframe(
        df_display.style.apply(highlight_profit).format({
            'Prezzo_J': '€ {:,.2f}',
            'Costo_Acquisto_Totale': '€ {:,.2f}',
            'Costo_Ristr_Totale': '€ {:,.2f}',
            'Ipotesi_Vendita_U': '€ {:,.2f}',
            'Utile_Lordo': '€ {:,.2f}'
        }),
        use_container_width=True
    )
else:
    st.info("Nessun immobile trovato nel range di prezzo indicato per i filtri selezionati.")

st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------------------
# BENCHMARK DI MERCATO (Prezzo Medio Zona)
# -----------------------------------------
# Calcolato su df_geo_filtered (ignora il filtro prezzo imposto dall'utente)
if not df_geo_filtered.empty:
    prezzo_medio_richiesta = df_geo_filtered['Prezzo_J'].mean()
    prezzo_medio_vendita = df_geo_filtered['Ipotesi_Vendita_U'].mean()
    
    st.markdown("### Benchmark di Mercato (Area Selezionata)")
    st.write(f"*Dato calcolato sui filtri geografici e tipologia, **escludendo il range di prezzo**.*")
    
    col_bench1, col_bench2 = st.columns(2)
    col_bench1.metric(label="Prezzo Medio di Acquisto (Richiesta)", value=f"€ {prezzo_medio_richiesta:,.0f}")
    col_bench2.metric(label="Prezzo Medio di Vendita (Immobili Finiti)", value=f"€ {prezzo_medio_vendita:,.0f}")
else:
    st.warning("Dati insufficienti nell'area selezionata per calcolare il benchmark di mercato.")
