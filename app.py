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
st.sidebar.caption("GECO Engine v1.2 - Motore di Scouting")

# -----------------------------------------
# MAIN: INPUT EDITABILI E PARAMETRI FINANZIARI
# -----------------------------------------
st.title("🚀 GECO Screening Engine")
st.markdown("##### Parametri Finanziari e Costi")

col1, col2, col3, col4 = st.columns(4)
param_prezzo = col1.number_input("Costo Base Ristr. (€/mq)", value=800, step=50)
imposta_perc = col2.number_input("Imposta Registro (%)", value=2.0, step=0.5) / 100
notaio_euro = col3.number_input("Notaio (€)", value=2500, step=100) # Modificato in Euro
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
# Aggiunta colonna Link
if 'dati_mock' not in st.session_state:
    st.session_state.dati_mock = pd.DataFrame({
        'Comune': ['Padova', 'Padova', 'Vigodarzere', 'Padova', 'Padova'],
        'Zona': ['Centro Storico', 'Centro Storico', 'Sacra Famiglia', 'Portello', 'Centro Storico'],
        'Tipologia': ['Residenziale', 'Residenziale', 'Residenziale', 'Residenziale', 'Residenziale'],
        'Superficie': [100, 150, 120, 70, 90],
        'Prezzo_J': [150000, 450000, 180000, 95000, 220000],
        'Ipotesi_Vendita_U': [240000, 580000, 290000, 155000, 310000],
        'Link': ['https://www.immobiliare.it/1', 'https://www.immobiliare.it/2', 'https://www.immobiliare.it/3', 'https://www.immobiliare.it/4', 'https://www.immobiliare.it/5']
    })

df = st.session_state.dati_mock

# -----------------------------------------
# MOTORE DI CALCOLO PANDAS
# -----------------------------------------
def calculate_metrics(df_calc):
    df_calc = df_calc.copy()
    
    # Ristrutturazione
    df_calc['Costo_Ristr_P'] = df_calc['Superficie'] * param_prezzo
    df_calc['Costi_Tecnici_Val'] = df_calc['Costo_Ristr_P'] * costi_tecnici_perc
    df_calc['Imprevisti_Val'] = df_calc['Costo_Ristr_P'] * imprevisti_perc
    df_calc['Costo_Ristr_Totale'] = df_calc['Costo_Ristr_P'] + df_calc['Costi_Tecnici_Val'] + df_calc['Imprevisti_Val']

    # Acquisto
    df_calc['Imposta'] = df_calc['Prezzo_J'] * imposta_perc
    df_calc['Notaio'] = notaio_euro # Valore fisso in Euro
    df_calc['Agenzia_Acq'] = df_calc['Prezzo_J'] * agenzia_acq_perc
    df_calc['Costo_Acquisto_Totale'] = df_calc['Prezzo_J'] + df_calc['Imposta'] + df_calc['Notaio'] + df_calc['Agenzia_Acq']

    # Vendita
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
mask_geo = (
    (df['Comune'].isin(comune) if comune else True) & 
    (df['Zona'].isin(zona) if zona else True) & 
    (df['Tipologia'] == tipologia)
)
df_geo_filtered = df[mask_geo].copy()

mask_price = (df_geo_filtered['Prezzo_J'] >= prezzo_range[0]) & (df_geo_filtered['Prezzo_J'] <= prezzo_range[1])
df_final_filtered = df_geo_filtered[mask_price].copy()

st.write("### Risultati Analisi")

if not df_final_filtered.empty:
    # Calcolo iniziale per popolare la tabella
    df_calculated = calculate_metrics(df_final_filtered)
    
    colonne_display = [
        'Comune', 'Zona', 'Superficie', 'Prezzo_J', 
        'Costo_Acquisto_Totale', 'Costo_Ristr_Totale', 
        'Ipotesi_Vendita_U', 'Utile_Lordo', 'Link'
    ]
    
    st.caption("💡 *Doppio clic sulla cella **Ipotesi Vendita_U** per modificare il valore e ricalcolare l'Utile Lordo.*")
    
    # Renderizza la tabella editabile
    edited_df = st.data_editor(
        df_calculated[colonne_display],
        column_config={
            "Ipotesi_Vendita_U": st.column_config.NumberColumn("Ipotesi Vendita (€)", format="€ %d", step=5000),
            "Prezzo_J": st.column_config.NumberColumn("Prezzo Acquisto (€)", format="€ %d"),
            "Costo_Acquisto_Totale": st.column_config.NumberColumn("Costo Acquisto (€)", format="€ %d"),
            "Costo_Ristr_Totale": st.column_config.NumberColumn("Costo Ristrutturazione (€)", format="€ %d"),
            "Utile_Lordo": st.column_config.NumberColumn("Utile Lordo (€)", format="€ %d"),
            "Link": st.column_config.LinkColumn("Pagina Web", display_text="Apri Annuncio")
        },
        disabled=["Comune", "Zona", "Superficie", "Prezzo_J", "Costo_Acquisto_Totale", "Costo_Ristr_Totale", "Utile_Lordo", "Link"],
        use_container_width=True,
        hide_index=True
    )
    
    # Se l'utente modifica l'ipotesi di vendita, ricalcola e aggiorna silenziosamente la vista
    if not edited_df.equals(df_calculated[colonne_display]):
        # Aggiorna i dati nel session state per mantenere la modifica
        for idx in edited_df.index:
            st.session_state.dati_mock.loc[idx, 'Ipotesi_Vendita_U'] = edited_df.loc[idx, 'Ipotesi_Vendita_U']
        st.rerun()

else:
    st.info("Nessun immobile trovato nel range di prezzo indicato per i filtri selezionati.")

st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------------------
# BENCHMARK DI MERCATO (Prezzo Medio Zona)
# -----------------------------------------
if not df_geo_filtered.empty:
    # Calcolo prezzi medi assoluti
    prezzo_medio_richiesta = df_geo_filtered['Prezzo_J'].mean()
    prezzo_medio_vendita = df_geo_filtered['Ipotesi_Vendita_U'].mean()
    
    # Calcolo prezzi medi al mq
    prezzo_medio_mq_richiesta = (df_geo_filtered['Prezzo_J'] / df_geo_filtered['Superficie']).mean()
    prezzo_medio_mq_vendita = (df_geo_filtered['Ipotesi_Vendita_U'] / df_geo_filtered['Superficie']).mean()
    
    st.markdown("### Benchmark di Mercato (Area Selezionata)")
    st.write(f"*Dato calcolato sui filtri geografici e tipologia, escludendo il range di prezzo di ricerca.*")
    
    col_bench1, col_bench2 = st.columns(2)
    
    # Formattazione HTML per rendere il prezzo totale più piccolo e il valore €/mq ben visibile
    with col_bench1:
        st.markdown(f"**Acquisto (Richiesta)**<br><span style='font-size: 1.2rem;'>**€ {prezzo_medio_mq_richiesta:,.0f} / mq**</span><br><span style='font-size: 0.9rem; color: #a1a1aa;'>Totale medio: € {prezzo_medio_richiesta:,.0f}</span>", unsafe_allow_html=True)
        
    with col_bench2:
        st.markdown(f"**Vendita (Finito)**<br><span style='font-size: 1.2rem; color: #10b981;'>**€ {prezzo_medio_mq_vendita:,.0f} / mq**</span><br><span style='font-size: 0.9rem; color: #a1a1aa;'>Totale medio: € {prezzo_medio_vendita:,.0f}</span>", unsafe_allow_html=True)
else:
    st.warning("Dati insufficienti nell'area selezionata per calcolare il benchmark di mercato.")
