import os
import time
import random
import pandas as pd
from playwright.sync_api import sync_playwright

# ---------------------------------------------------------
# 1. FUNZIONI DI PULIZIA DATI
# ---------------------------------------------------------
def pulisci_prezzo(testo_prezzo):
    if not testo_prezzo or "trattativa" in testo_prezzo.lower() or "asta" in testo_prezzo.lower():
        return None
    try:
        puro = testo_prezzo.replace("€", "").replace(".", "").replace(",00", "").strip()
        # Estrae solo i numeri usando la list comprehension
        puro = ''.join(c for c in puro if c.isdigit())
        return float(puro) if puro else None
    except:
        return None

def pulisci_superficie(testo_sup):
    if not testo_sup:
        return None
    try:
        puro = testo_sup.lower().replace("m²", "").replace("mq", "").strip()
        puro = ''.join(c for c in puro if c.isdigit())
        return int(puro) if puro else None
    except:
        return None

# ---------------------------------------------------------
# 2. DIZIONARIO DELLE AGENZIE (La Mappa dei Selettori CSS)
# ---------------------------------------------------------
# NOTA: I selettori CSS (es. '.property-card') andranno calibrati guardando il codice sorgente 
# reale dei vari siti. Questa è l'architettura pronta per ospitarli.
AGENZIE = [
    {
        "nome": "Engel & Völkers Padova",
        "url": "https://www.engelvoelkers.com/it-it/padova/comprare/",
        "selettori": {
            # Prendiamo il tag <article> puro, dato che racchiude tutto l'annuncio
            "card": "article", 
            
            # Il link è nel tag <a> che contiene la stringa '/exposes/'
            "link": "a[href*='/exposes/']", 
            
            # Non vedendo l'HTML espanso per il prezzo nello screen, usiamo i selettori testuali di Playwright
            "prezzo": "div:has-text('€')", 
            
            # Stessa cosa per i metri quadri: cerchiamo l'elemento lista che contiene 'm²'
            "mq": "li:has-text('m²')"       
        }
    },
    {
        "nome": "Agenzia Locale Standard (Test)",
        "url": "https://example.com/immobili-padova", # Placeholder per le agenzie locali
        "selettori": {
            "card": ".listing-item",
            "link": "a.listing-link",
            "prezzo": ".price-text",
            "mq": ".area-text"
        }
    }
]

# ---------------------------------------------------------
# 3. IL MOTORE DI ESTRAZIONE
# ---------------------------------------------------------
def esegui_scouting_multiplo():
    risultati = []
    
    with sync_playwright() as p:
        # Avviamo il browser. Senza protezioni militari, passiamo in scioltezza.
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        for agenzia in AGENZIE:
            print(f"Scansione agenzia: {agenzia['nome']}")
            
            try:
                # Naviga al sito dell'agenzia
                page.goto(agenzia['url'], timeout=45000)
                time.sleep(random.uniform(2.0, 4.0)) # Attesa umana
                
                # Identifica tutti gli annunci sulla pagina usando il selettore 'card'
                cards = page.locator(agenzia['selettori']['card']).all()
                print(f"Trovati {len(cards)} annunci potenziali.")
                
                for card in cards:
                    try:
                        # Estrazione Link
                        el_link = card.locator(agenzia['selettori']['link']).first
                        link = el_link.get_attribute("href")
                        # Se il link è relativo (es. /immobile/123), aggiungiamo la radice del sito
                        if link and link.startswith("/"):
                            dominio = "/".join(agenzia['url'].split("/")[:3])
                            link = dominio + link
                            
                        # Estrazione Prezzo
                        el_prezzo = card.locator(agenzia['selettori']['prezzo']).first
                        prezzo = pulisci_prezzo(el_prezzo.text_content()) if el_prezzo.is_visible() else None
                        
                        # Estrazione Mq
                        el_mq = card.locator(agenzia['selettori']['mq']).first
                        superficie = pulisci_superficie(el_mq.text_content()) if el_mq.is_visible() else None
                        
                        if prezzo and superficie and link:
                            risultati.append({
                                'Comune': 'Padova',
                                'Zona': 'Centro Storico (Agenzia)', # Da affinare in base al sito
                                'Tipologia': 'Residenziale',
                                'Superficie': superficie,
                                'Prezzo_J': prezzo,
                                'Link': link,
                                'Fonte': agenzia['nome'] # Tracciamo da quale agenzia arriva
                            })
                    except Exception as e:
                        continue # Salta l'annuncio se la struttura è rotta
                        
            except Exception as e:
                print(f"Errore connessione a {agenzia['nome']}: {e}")
                
        browser.close()
        
    # ---------------------------------------------------------
    # 4. SALVATAGGIO DATI
    # ---------------------------------------------------------
    df_scout = pd.DataFrame(risultati)
    if not df_scout.empty:
        # Se esiste un database precedente, possiamo decidere se sovrascriverlo o appenderlo.
        # Per ora lo sovrascriviamo per avere sempre la fotografia attuale.
        df_scout.to_csv("annunci_padova.csv", index=False, encoding="utf-8")
        print(f"Scouting completato. Salvati {len(df_scout)} immobili in 'annunci_padova.csv'")
    else:
        print("Nessun dato raccolto valido. Controllare i selettori CSS.")

if __name__ == "__main__":
    esegui_scouting_multiplo()
