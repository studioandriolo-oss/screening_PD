import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image

# -----------------------------------------
# FUNZIONE FORMATTAZIONE EURO (Formato Italiano)
# -----------------------------------------
def format_euro(val):
    if pd.isna(val):
        return "€ 0,00"
    # Formatta con standard anglosassone (es. 1,000,000.00)
    val_str = f"{val:,.2f}"
    # Sostituisce virgole con X, punti con virgole, e X con punti -> 1.000.000,00
    val_str = val_str.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"€ {val_str}"

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
st.sidebar.caption("GECO Engine v1.4 - Motore di Scouting")

# -----------------------------------------
# MAIN: TARGET RENDIMENTO E PARAMETRI
# -----------------------------------------
st.title("🚀 GECO Screening Engine")

# Parametro in forte risalto
st.markdown("### 🎯 Target Strategico")
col_target, _ = st.columns([1, 3])
with col_target:
    plusvalore_atteso_perc = st.number_input("🌟 PLUSVALORE ATTESO (%)", value=20.0, step=1.0) / 100

st.markdown("##### Parametri Finanziari e Costi")
col1, col2, col3, col4 = st.columns(4)
param_prezzo = col1.number_input("Costo Base Ristr. (€/mq)", value=800, step=50)
imposta_perc = col2.number_input("Imposta Registro (%)", value=2.0, step=0.5) / 100
notaio_euro = col3.number_input("Notaio (€)", value=2500, step=100)
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
    'Link': ['https://www.immobiliare.it/1', 'https://www.immobiliare.it/2', 'https://www.immobiliare.it/3', 'https://www.immobiliare.it/4', 'https://www.immobiliare.it/5']
}
df = pd.DataFrame(data)

# -----------------------------------------
# MOTORE DI CALCOLO PANDAS
# -----------------------------------------
def calculate_metrics(df_calc):
    df_calc = df_calc.copy()
    
    # 1. Ristrutturazione
    df_calc['Costo_Ristr_P'] = df_calc['Superficie'] * param_prezzo
    df_calc['Costi_Tecnici_Val'] = df_calc['Costo_Ristr_P'] * costi_tecnici_perc
    df_calc['Imprevisti_Val'] = df_calc['Costo_Ristr_P'] * imprevisti_perc
    df_calc['Costo_Ristr_Totale'] = df_calc['Costo_Ristr_P'] + df_calc['Costi_Tecnici_Val'] + df_calc['Imprevisti_Val']

    # 2. Acquisto
    df_calc['Imposta'] = df_calc['Prezzo_J'] * imposta_perc
    df_calc['Notaio'] = notaio_euro
    df_calc['Agenzia_Acq'] = df_calc['Prezzo_J'] * agenzia_acq_perc
    df_calc['Costo_Acquisto_Totale'] = df_calc['Prezzo_J'] + df_calc['Imposta'] + df_calc['Notaio'] + df_calc['Agenzia_Acq']

    # 3. Ipotesi Vendita (CALCOLO DA TARGET)
    df_calc['Ipotesi_Vendita_U'] = (df_calc['Costo_Acquisto_Totale'] + df_calc['Costo_Ristr_Totale']) * (1 + plusvalore_atteso_perc)

    # 4. Costi in Uscita e Utile
    df_calc['Agenzia_Vendita_Val'] = df_calc['Ipotesi_Vendita_U'] * agenzia_ven_perc
    df_calc['Interessi_Val'] = df_calc['Costo_Acquisto_Totale'] * interessi_perc

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
    df_calculated = calculate_metrics(df_final_filtered)
    
    colonne_display = [
        'Comune', 'Zona', 'Superficie', 'Prezzo_J', 
        'Costo_Acquisto_Totale', 'Costo_Ristr_Totale', 
        'Ipotesi_Vendita_U', 'Utile_Lordo', 'Link'
    ]
    
    # Creiamo una copia del dataframe per la visualizzazione formattata
    df_display = df_calculated[colonne_display].copy()
    
    # Applichiamo la formattazione italiana alle colonne valutarie
    colonne_valuta = ['Prezzo_J', 'Costo_Acquisto_Totale', 'Costo_Ristr_Totale', 'Ipotesi_Vendita_U', 'Utile_Lordo']
    for col in colonne_valuta:
        df_display[col] = df_display[col].apply(format_euro)
    
    # Rinominiamo le colonne per una migliore leggibilità nella UI
    df_display = df_display.rename(columns={
        'Prezzo_J': 'Prezzo Acquisto',
        'Costo_Acquisto_Totale': 'Costo Acquisto Tot.',
        'Costo_Ristr_Totale': 'Costo Ristr. Tot.',
        'Ipotesi_Vendita_U': 'Target Vendita',
        'Utile_Lordo': 'Utile Lordo'
    })

    st.dataframe(
        df_display,
        column_config={
            "Link": st.column_config.LinkColumn("Pagina Web", display_text="Apri Annuncio")
        },
        use_container_width=True,
        hide_index=True
    )

else:
    st.info("Nessun immobile trovato nel range di prezzo indicato per i filtri selezionati.")

st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------------------
# BENCHMARK DI MERCATO (Target di Zona)
# -----------------------------------------
if not df_geo_filtered.empty:
    df_geo_calculated = calculate_metrics(df_geo_filtered)
    
    prezzo_medio_richiesta = df_geo_calculated['Prezzo_J'].mean()
    prezzo_medio_vendita = df_geo_calculated['Ipotesi_Vendita_U'].mean()
    
    prezzo_medio_mq_richiesta = (df_geo_calculated['Prezzo_J'] / df_geo_calculated['Superficie']).mean()
    prezzo_medio_mq_vendita = (df_geo_calculated['Ipotesi_Vendita_U'] / df_geo_calculated['Superficie']).mean()
    
    st.markdown("### Benchmark Target Area (Basato sul Plusvalore)")
    st.write(f"*Dato calcolato sui filtri geografici e tipologia, escludendo il range di prezzo di ricerca.*")
    
    col_bench1, col_bench2 = st.columns(2)
    
    with col_bench1:
        st.markdown(f"**Acquisto (Media Richiesta)**<br><span style='font-size: 1.2rem;'>**{format_euro(prezzo_medio_mq_richiesta)} / mq**</span><br><span style='font-size: 0.9rem; color: #a1a1aa;'>Totale medio: {format_euro(prezzo_medio_richiesta)}</span>", unsafe_allow_html=True)
        
    with col_bench2:
        st.markdown(f"**Target Vendita (Finito)**<br><span style='font-size: 1.2rem; color: #10b981;'>**{format_euro(prezzo_medio_mq_vendita)} / mq**</span><br><span style='font-size: 0.9rem; color: #a1a1aa;'>Totale medio: {format_euro(prezzo_medio_vendita)}</span>", unsafe_allow_html=True)
else:
    st.warning("Dati insufficienti nell'area selezionata per calcolare il benchmark di mercato.")
