import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
from fpdf import FPDF
import io

def format_euro(val):
    if pd.isna(val) or val == np.inf or val == -np.inf:
        return "N/A"
    # Formatta il numero con i separatori delle migliaia
    return f"€ {val:,.0f}".replace(",", ".")

def generate_pdf_report(row, params):
    # Inizializza il PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # 1. Pulisce caratteri strani (spazi web, trattini lunghi) dai nomi di zona e comune
    titolo = f"Report Immobiliare: {row['Comune']} - {row['Zona']}"
    titolo_sicuro = titolo.encode('latin-1', 'ignore').decode('latin-1')
    
    # 2. Sostituisci il simbolo € con la parola "Euro"
    prezzo_pulito = format_euro(row['Prezzo_J']).replace("€", "Euro")
    utile_pulito = format_euro(row['Utile_Lordo']).replace("€", "Euro")
    
    # 3. Stampa nel PDF
    pdf.cell(200, 10, txt=titolo_sicuro, ln=True, align='C')
    pdf.cell(200, 10, txt=f"Acquisto: {prezzo_pulito}", ln=True, align='C')
    pdf.cell(200, 10, txt=f"Utile Lordo Stimato: {utile_pulito}", ln=True, align='C')
    
    return bytes(pdf.output(dest="S"))
# -----------------------------------------
# 1. CONFIGURAZIONE PAGINA
# -----------------------------------------
st.set_page_config(page_title="GECO Immobiliare - Screening Engine", layout="wide")

# -----------------------------------------
# 2. CARICAMENTO DATABASE (Prima della Sidebar!)
# -----------------------------------------
try:
    df = pd.read_csv("annunci_padova.csv", encoding="utf-8")
    lista_comuni = sorted(df['Comune'].dropna().unique().tolist())
    lista_zone = sorted(df['Zona'].dropna().unique().tolist())
except FileNotFoundError:
    st.warning("⚠️ Database non trovato. Verranno usati dati di test. Avvia lo scraper su GitHub Actions.")
    # Fallback dati
    data = {
        'Comune': ['Padova', 'Padova', 'Vigodarzere', 'Padova', 'Padova'],
        'Zona': ['Centro Storico', 'Centro Storico', 'Sacra Famiglia', 'Portello', 'Centro Storico'],
        'Tipologia': ['Residenziale', 'Residenziale', 'Residenziale', 'Residenziale', 'Residenziale'],
        'Superficie': [100, 150, 120, 70, 90],
        'Prezzo_J': [150000, 450000, 180000, 95000, 220000],
        'Link': ['https://www.immobiliare.it/1', 'https://www.immobiliare.it/2', 'https://www.immobiliare.it/3', 'https://www.immobiliare.it/4', 'https://www.immobiliare.it/5']
    }
    df = pd.DataFrame(data)
    lista_comuni = sorted(df['Comune'].unique().tolist())
    lista_zone = sorted(df['Zona'].unique().tolist())

# -----------------------------------------
# 3. SIDEBAR: FILTRI E RICERCA
# -----------------------------------------
try:
    logo = Image.open("geco_logo.png")
    st.sidebar.image(logo, use_column_width=True)
except FileNotFoundError:
    st.sidebar.title("GECO IMMOBILIARE")

st.sidebar.markdown("### Filtri di Ricerca")
# CORREZIONE QUI: Aggiunte le etichette "Comune" e "Zona", e impostati i default
comune = st.sidebar.multiselect("Comune", options=lista_comuni, default=lista_comuni)
zona = st.sidebar.multiselect("Zona", options=lista_zone, default=lista_zone)
tipologia = st.sidebar.selectbox("Tipologia", ["Residenziale", "Commerciale", "Ufficio"])
prezzo_range = st.sidebar.slider("Range Prezzo Ricerca (€)", 0, 1000000, (50000, 300000), step=5000)

st.sidebar.markdown("---")
st.sidebar.caption("GECO Engine v1.7")

# -----------------------------------------
# MAIN: TARGET RENDIMENTO E PARAMETRI
# -----------------------------------------
st.title("🚀 GECO Screening Engine")

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

current_params = {
    "plusvalore": plusvalore_atteso_perc, "costo_mq": param_prezzo, "imposta": imposta_perc,
    "notaio": notaio_euro, "agenzia_acq": agenzia_acq_perc, "imprevisti": imprevisti_perc,
    "tecnici": costs_tecnici_perc if 'costs_tecnici_perc' in locals() else costi_tecnici_perc, 
    "agenzia_ven": agenzia_ven_perc, "interessi": interessi_perc
}

st.markdown("---")

# -----------------------------------------
# DATABASE DI SCOUTING REALE (Lettura CSV)
# -----------------------------------------
try:
    # Carica i dati estratti dal motore di scraping
    df = pd.read_csv("annunci_padova.csv", encoding="utf-8")
    
    # Aggiorna dinamicamente i filtri della sidebar basandosi sui dati realmente presenti nel DB
    lista_comuni = sorted(df['Comune'].unique().tolist())
    lista_zone = sorted(df['Zona'].unique().tolist())
except FileNotFoundError:
    # Fallback sicuro se lo scraper non è ancora stato eseguito sul server
    st.warning("⚠️ Database immobiliare locale non trovato. Esegui 'scraper.py' per popolare i dati. Utilizzo dati di test provvisori.")
    data_fallback = {
        'Comune': ['Padova', 'Padova', 'Padova'],
        'Zona': ['Centro Storico', 'Guizza', 'Portello'],
        'Tipologia': ['Residenziale', 'Residenziale', 'Residenziale'],
        'Superficie': [100, 85, 70],
        'Prezzo_J': [150000, 120000, 95000],
        'Link': ['https://www.immobiliare.it', 'https://www.immobiliare.it', 'https://www.immobiliare.it']
    }
    df = pd.DataFrame(data_fallback)
    lista_comuni = ["Padova"]
    lista_zone = ["Centro Storico", "Guizza", "Portello"]

# -----------------------------------------
# MOTORE DI CALCOLO PANDAS
# -----------------------------------------
def calculate_metrics(df_calc):
    df_calc = df_calc.copy()
    df_calc['Costo_Ristr_P'] = df_calc['Superficie'] * param_prezzo
    df_calc['Costi_Tecnici_Val'] = df_calc['Costo_Ristr_P'] * costi_tecnici_perc
    df_calc['Imprevisti_Val'] = df_calc['Costo_Ristr_P'] * imprevisti_perc
    df_calc['Costo_Ristr_Totale'] = df_calc['Costo_Ristr_P'] + df_calc['Costi_Tecnici_Val'] + df_calc['Imprevisti_Val']

    df_calc['Imposta'] = df_calc['Prezzo_J'] * imposta_perc
    df_calc['Notaio'] = notaio_euro
    df_calc['Agenzia_Acq'] = df_calc['Prezzo_J'] * agenzia_acq_perc
    df_calc['Costo_Acquisto_Totale'] = df_calc['Prezzo_J'] + df_calc['Imposta'] + df_calc['Notaio'] + df_calc['Agenzia_Acq']

    # Calcolo Target Vendita ed Incidenza al MQ richiesta
    df_calc['Ipotesi_Vendita_U'] = (df_calc['Costo_Acquisto_Totale'] + df_calc['Costo_Ristr_Totale']) * (1 + plusvalore_atteso_perc)
    df_calc['Incidenza_MQ'] = df_calc['Ipotesi_Vendita_U'] / df_calc['Superficie']
    
    df_calc['Agenzia_Vendita_Val'] = df_calc['Ipotesi_Vendita_U'] * agenzia_ven_perc
    df_calc['Interessi_Val'] = df_calc['Costo_Acquisto_Totale'] * interessi_perc

    df_calc['Utile_Lordo'] = (
        df_calc['Ipotesi_Vendita_U'] - df_calc['Costo_Acquisto_Totale'] - 
        df_calc['Costo_Ristr_Totale'] - df_calc['Agenzia_Vendita_Val'] - df_calc['Interessi_Val']
    )
    return df_calc

# -----------------------------------------
# TABELLA RISULTATI CON COLONNA INCIDENZA AL MQ
# -----------------------------------------
st.write("### Risultati Analisi")

mask_geo = df['Comune'].isin(comune) & df['Zona'].isin(zona) & (df['Tipologia'] == tipologia)
df_geo_filtered = df[mask_geo].copy()
mask_price = (df_geo_filtered['Prezzo_J'] >= prezzo_range[0]) & (df_geo_filtered['Prezzo_J'] <= prezzo_range[1])
df_final_filtered = df_geo_filtered[mask_price].copy()

if not df_final_filtered.empty:
    df_calculated = calculate_metrics(df_final_filtered)
    
    # Rimodulazione larghezze colonne per inserire l'Incidenza al MQ (11 colonne totali)
    hdr_cols = st.columns([1.0, 1.3, 0.5, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 0.6, 0.8])
    headers = ["Comune", "Zona", "Mq", "Acquisto Iniz.", "Costo Acq. Tot", "Costo Ristr.", "Target Vendita", "Incidenza al MQ", "Utile Lordo", "Annuncio", "Report"]
    for col, text in zip(hdr_cols, headers):
        col.markdown(f"**{text}**")
    st.markdown("<hr style='margin: 5px 0 10px 0;'>", unsafe_allow_html=True)
    
    # Ciclo di popolamento righe
    for idx, row in df_calculated.iterrows():
        row_cols = st.columns([1.0, 1.3, 0.5, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 0.6, 0.8])
        
        row_cols[0].write(row['Comune'])
        row_cols[1].write(row['Zona'])
        row_cols[2].write(f"{row['Superficie']}")
        row_cols[3].write(format_euro(row['Prezzo_J']))
        row_cols[4].write(format_euro(row['Costo_Acquisto_Totale']))
        row_cols[5].write(format_euro(row['Costo_Ristr_Totale']))
        row_cols[6].write(format_euro(row['Ipotesi_Vendita_U']))
        row_cols[7].write(f"{format_euro(row['Incidenza_MQ'])}/mq")
        
        # Utile Lordo evidenziato
        row_cols[8].markdown(f"<span style='color: #10b981; font-weight: bold;'>{format_euro(row['Utile_Lordo'])}</span>", unsafe_allow_html=True)
        row_cols[9].markdown(f"[Link]({row['Link']})")
        
        # Generazione PDF dinamica con blocco di sicurezza 
        try:
            pdf_data = generate_pdf_report(row, current_params)
            
            row_cols[10].download_button(
                label="📄 PDF",
                data=pdf_data,
                file_name=f"Report_{row['Zona']}_{idx}.pdf",
                mime="application/pdf",
                key=f"btn_dl_{idx}"
            )
        except Exception:
            row_cols[10].write("Err. PDF")

else:
    st.info("Nessun immobile trovato nel range di prezzo indicato per i filtri selezionati.")

st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------------------
# BENCHMARK DI MERCATO
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
