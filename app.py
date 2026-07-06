import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
from fpdf import FPDF
import io

# -----------------------------------------
# FUNZIONE FORMATTAZIONE EURO (Formato Italiano)
# -----------------------------------------
def format_euro(val):
    if pd.isna(val):
        return "€ 0,00"
    val_str = f"{val:,.2f}"
    val_str = val_str.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"€ {val_str}"

# -----------------------------------------
# FUNZIONE GENERAZIONE PDF REPORT
# -----------------------------------------
def generate_pdf_report(row, params):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(15, 20, 15)
    
    # Intestazione Professionale
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(16, 185, 129) # Verde GECO
    pdf.cell(0, 10, "GECO IMMOBILIARE - SCREENING REPORT", ln=True, align="C")
    pdf.set_draw_color(16, 185, 129)
    pdf.line(15, 32, 195, 32)
    pdf.ln(10)
    
    # Sezione 1: Dati Immobile
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 8, "1. DATI SPECIFICI DELL'IMMOBILE", ln=True)
    pdf.line(15, 43, 80, 43)
    pdf.ln(2)
    
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(50, 6, f"Comune: {row['Comune']}", ln=False)
    pdf.cell(50, 6, f"Zona: {row['Zona']}", ln=True)
    pdf.cell(50, 6, f"Superficie: {row['Superficie']} mq", ln=False)
    pdf.cell(50, 6, f"Tipologia: {row['Tipologia']}", ln=True)
    pdf.cell(0, 6, f"Link Annuncio: {row['Link']}", ln=True)
    pdf.ln(5)
    
    # Sezione 2: Target Strategico e Parametri Inseriti
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "2. TARGET STRATEGICO E PARAMETRI FINANZIARI", ln=True)
    pdf.line(15, 77, 110, 77)
    pdf.ln(2)
    
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(60, 6, f"Plusvalore Atteso: {params['plusvalore'] * 100:.1f}%", ln=False)
    pdf.cell(60, 6, f"Costo Base Ristr.: {format_euro(params['costo_mq'])}/mq", ln=True)
    pdf.cell(60, 6, f"Imposta Registro: {params['imposta'] * 100:.1f}%", ln=False)
    pdf.cell(60, 6, f"Notaio (Fisso): {format_euro(params['notaio'])}", ln=True)
    pdf.cell(60, 6, f"Agenzia Acquisto: {params['agenzia_acq'] * 100:.1f}%", ln=False)
    pdf.cell(60, 6, f"Imprevisti Ristr.: {params['imprevisti'] * 100:.1f}%", ln=True)
    pdf.cell(60, 6, f"Costi Tecnici: {params['tecnici'] * 100:.1f}%", ln=False)
    pdf.cell(60, 6, f"Agenzia Vendita: {params['agenzia_ven'] * 100:.1f}%", ln=True)
    pdf.cell(60, 6, f"Interessi Passivi: {params['interessi'] * 100:.1f}%", ln=True)
    pdf.ln(5)
    
    # Sezione 3: Elaborazione Calcoli in Ordine Sequenziale
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "3. ELABORAZIONE DETTAGLIATA DEI CALCOLI (FLOW CHART LOGICO)", ln=True)
    pdf.line(15, 123, 150, 123)
    pdf.ln(4)
    
    # Tabella dei calcoli ordinati
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(241, 245, 249)
    pdf.cell(110, 8, " Voce di Spesa / Ricavo", border=1, fill=True)
    pdf.cell(70, 8, " Valore Formattato", border=1, fill=True, align="R")
    pdf.ln()
    
    pdf.set_font("Helvetica", "", 10)
    calcoli = [
        ("Prezzo Immobile Oggetto di Ricerca (Colonna J)", format_euro(row['Prezzo_J'])),
        ("  + Imposta di Registro Calcolata", format_euro(row['Imposta'])),
        ("  + Onorario Notarile", format_euro(row['Notaio'])),
        ("  + Commissione Agenzia in Entrata", format_euro(row['Agenzia_Acq'])),
        ("COSTO ACQUISTO COMPLESSIVO (Colonna N)", format_euro(row['Costo_Acquisto_Totale'])),
        ("----------------------------------------------------------------------", "--------------------------"),
        ("Ipotesi Costo di Ristrutturazione Base (Colonna P)", format_euro(row['Costo_Ristr_P'])),
        ("  + Costi Tecnici di Progettazione", format_euro(row['Costi_Tecnici_Val'])),
        ("  + Fondo di Riserva Imprevisti", format_euro(row['Imprevisti_Val'])),
        ("COSTO RISTRUTTURAZIONE TOTALE (Colonna T)", format_euro(row['Costo_Ristr_Totale'])),
        ("----------------------------------------------------------------------", "--------------------------"),
        ("IPOTESI DI VENDITA TARGET (Colonna U)", format_euro(row['Ipotesi_Vendita_U'])),
        ("  - Oneri Agenzia in Uscita", format_euro(row['Agenzia_Vendita_Val'])),
        ("  - Interessi Passivi Finanziamento", format_euro(row['Interessi_Val'])),
        ("----------------------------------------------------------------------", "--------------------------"),
        ("UTILE LORDO OPERAZIONE (Colonna Y)", format_euro(row['Utile_Lordo']))
    ]
    
    for voce, valore in calcoli:
        if "TOTAL" in voce.upper() or "UTILE" in voce.upper() or "IPOTESI DI VENDITA" in voce.upper():
            pdf.set_font("Helvetica", "B", 10)
        else:
            pdf.set_font("Helvetica", "", 10)
        pdf.cell(110, 7, f" {voce}", border=1)
        pdf.cell(70, 7, f"{valore} ", border=1, align="R")
        pdf.ln()
        
    # Salva il PDF in un buffer di memoria
    pdf_output = io.BytesIO()
    pdf.output(pdf_output)
    pdf_output.seek(0)
    return pdf_output.read()

# -----------------------------------------
# CONFIGURAZIONE PAGINA STREAMLIT
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
st.sidebar.caption("GECO Engine v1.5 - Report System")

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

# Pacchetto parametri da passare al PDF
current_params = {
    "plusvalore": plusvalore_atteso_perc, "costo_mq": param_prezzo, "imposta": imposta_perc,
    "notaio": notaio_euro, "agenzia_acq": agenzia_acq_perc, "imprevisti": imprevisti_perc,
    "tecnici": costi_tecnici_perc, "agenzia_ven": agenzia_ven_perc, "interessi": interessi_perc
}

st.markdown("---")

# -----------------------------------------
# DATABASE FITTIZIO
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
    df_calc['Costo_Ristr_P'] = df_calc['Superficie'] * param_prezzo
    df_calc['Costi_Tecnici_Val'] = df_calc['Costo_Ristr_P'] * costi_tecnici_perc
    df_calc['Imprevisti_Val'] = df_calc['Costo_Ristr_P'] * imprevisti_perc
    df_calc['Costo_Ristr_Totale'] = df_calc['Costo_Ristr_P'] + df_calc['Costi_Tecnici_Val'] + df_calc['Imprevisti_Val']

    df_calc['Imposta'] = df_calc['Prezzo_J'] * imposta_perc
    df_calc['Notaio'] = notaio_euro
    df_calc['Agenzia_Acq'] = df_calc['Prezzo_J'] * agenzia_acq_perc
    df_calc['Costo_Acquisto_Totale'] = df_calc['Prezzo_J'] + df_calc['Imposta'] + df_calc['Notaio'] + df_calc['Agenzia_Acq']

    df_calc['Ipotesi_Vendita_U'] = (df_calc['Costo_Acquisto_Totale'] + df_calc['Costo_Ristr_Totale']) * (1 + plusvalore_atteso_perc)
    df_calc['Agenzia_Vendita_Val'] = df_calc['Ipotesi_Vendita_U'] * agenzia_ven_perc
    df_calc['Interessi_Val'] = df_calc['Costo_Acquisto_Totale'] * interessi_perc

    df_calc['Utile_Lordo'] = (
        df_calc['Ipotesi_Vendita_U'] - df_calc['Costo_Acquisto_Totale'] - 
        df_calc['Costo_Ristr_Totale'] - df_calc['Agenzia_Vendita_Val'] - df_calc['Interessi_Val']
    )
    return df_calc

# -----------------------------------------
# TABELLA RISULTATI INTERATTIVA CON COLS Loop
# -----------------------------------------
st.write("### Risultati Analisi")

mask_geo = (df['Comune'].isin(comune) if comune else True) & (df['Zona'].isin(zona) if zona else True) & (df['Tipologia'] == tipologia)
df_geo_filtered = df[mask_geo].copy()
mask_price = (df_geo_filtered['Prezzo_J'] >= prezzo_range[0]) & (df_geo_filtered['Prezzo_J'] <= prezzo_range[1])
df_final_filtered = df_geo_filtered[mask_price].copy()

if not df_final_filtered.empty:
    df_calculated = calculate_metrics(df_final_filtered)
    
    # Creazione Intestazione Tabella Custom
    hdr_cols = st.columns([1.2, 1.5, 0.7, 1.3, 1.3, 1.3, 1.3, 1.3, 0.8, 1.0])
    headers = ["Comune", "Zona", "Mq", "Acquisto Iniz.", "Costo Acq. Tot", "Costo Ristr.", "Target Vendita", "Utile Lordo", "Annuncio", "Report"]
    for col, text in zip(hdr_cols, headers):
        col.markdown(f"**{text}**")
    st.markdown("<hr style='margin: 5px 0 10px 0;'>", unsafe_allow_html=True)
    
    # Popolamento Righe con pulsante Download integrato alla fine
    for idx, row in df_calculated.iterrows():
        row_cols = st.columns([1.2, 1.5, 0.7, 1.3, 1.3, 1.3, 1.3, 1.3, 0.8, 1.0])
        
        row_cols[0].write(row['Comune'])
        row_cols[1].write(row['Zona'])
        row_cols[2].write(f"{row['Superficie']}")
        row_cols[3].write(format_euro(row['Prezzo_J']))
        row_cols[4].write(format_euro(row['Costo_Acquisto_Totale']))
        row_cols[5].write(format_euro(row['Costo_Ristr_Totale']))
        row_cols[6].write(format_euro(row['Ipotesi_Vendita_U']))
        
        # Evidenziazione Utile Lordo
        row_cols[7].markdown(f"<span style='color: #10b981; font-weight: bold;'>{format_euro(row['Utile_Lordo'])}</span>", unsafe_allow_html=True)
        row_cols[8].markdown(f"[Link]({row['Link']})")
        
        # Generazione Dinamica dei Byte del PDF per la riga corrente
        pdf_data = generate_pdf_report(row, current_params)
        
        row_cols[9].download_button(
            label="📄 PDF",
            data=pdf_data,
            file_name=f"GECO_Report_{row['Comune']}_{row['Zona'].replace(' ', '_')}_{idx}.pdf",
            mime="application/pdf",
            key=f"btn_dl_{idx}"
        )
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
