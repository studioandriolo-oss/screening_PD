import os
import time
import random
import pandas as pd
from playwright.sync_api import sync_playwright

def pulisci_prezzo(testo_prezzo):
    if not testo_prezzo or "trattativa" in testo_prezzo.lower() or "asta" in testo_prezzo.lower():
        return None
    try:
        puro = testo_prezzo.replace("€", "").replace(".", "").replace(",00", "").strip()
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

AGENZIE = [
    {
        "nome": "Engel & Völkers Padova",
        "url": "https://www.engelvoelkers.com/it-it/padova/comprare/",
        "selettori": {
            "card": "article", 
            "link": "a[href*='/exposes/']", 
            "prezzo": "div:has-text('€')", 
            "mq": "li:has-text('m²')"       
        }
    }
]

def esegui_scouting_multiplo():
    risultati = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        for agenzia in AGENZIE:
            print(f"Scansione agenzia: {agenzia['nome']}")
            try:
                page.goto(agenzia['url'], timeout=30000)
                time.sleep(random.uniform(2.0, 4.0))
                
                cards = page.locator(agenzia['selettori']['card']).all()
                print(f"Trovati {len(cards)} annunci potenziali.")
                
                for card in cards:
                    try:
                        el_link = card.locator(agenzia['selettori']['link']).first
                        link = el_link.get_attribute("href")
                        if link and link.startswith("/"):
                            dominio = "/".join(agenzia['url'].split("/")[:3])
                            link = dominio + link
                            
                        el_prezzo = card.locator(agenzia['selettori']['prezzo']).first
                        prezzo = pulisci_prezzo(el_prezzo.text_content()) if el_prezzo.is_visible() else None
                        
                        el_mq = card.locator(agenzia['selettori']['mq']).first
                        superficie = pulisci_superficie(el_mq.text_content()) if el_mq.is_visible() else None
                        
                        if prezzo and superficie and link:
                            risultati.append({
                                'Comune': 'Padova',
                                'Zona': 'Centro Storico (Agenzia)',
                                'Tipologia': 'Residenziale',
                                'Superficie': superficie,
                                'Prezzo_J': prezzo,
                                'Link': link,
                                'Fonte': agenzia['nome']
                            })
                    except Exception:
                        continue 
            except Exception as e:
                print(f"Errore connessione a {agenzia['nome']}: {e}")
                
        browser.close()
        
    # ---------------------------------------------------------
    # PARACADUTE DI TEST: Se il sito ci ha bloccato (0 risultati)
    # ---------------------------------------------------------
    if len(risultati) == 0:
        print("NESSUN IMMOBILE ESTRATTO (Possibile blocco server). Inserisco dato di test per confermare la pipeline.")
        risultati.append({
            'Comune': 'Padova (TEST BOT)',
            'Zona': 'Test Sistema',
            'Tipologia': 'Residenziale',
            'Superficie': 100,
            'Prezzo_J': 250000,
            'Link': 'https://github.com',
            'Fonte': 'Test Fallback'
        })

    df_scout = pd.DataFrame(risultati)
    df_scout.to_csv("annunci_padova.csv", index=False, encoding="utf-8")
    print(f"Salvato file CSV con {len(df_scout)} righe.")

if __name__ == "__main__":
    esegui_scouting_multiplo()
