import os
import time
import random
import pandas as pd
from playwright.sync_api import sync_playwright

def pulisci_prezzo(testo_prezzo):
    """Estrae il numero puro dal testo del prezzo (es. '€ 150.000' -> 150000)"""
    if not testo_prezzo or "asta" in testo_prezzo.lower():
        return None
    try:
        # Rimuove simboli e punti delle migliaia
        puro = testo_prezzo.replace("€", "").replace(".", "").strip()
        return float(puro)
    except ValueError:
        return None

def pulisci_superficie(testo_sup):
    """Estrae i mq puri (es. '100 m²' -> 100)"""
    if not testo_sup:
        return None
    try:
        puro = testo_sup.lower().replace("m²", "").replace("mq", "").strip()
        return int(puro)
    except ValueError:
        return None

def esegui_scouting_padova(max_pagine=3):
    risultati = []
    
    # URL base per la ricerca di case in vendita a Padova
    # Modificabile per estendere alla provincia o a tipologie commerciali
    url_base = "https://www.immobiliare.it/vendita-case/padova/?criterio=rilevanza"

    with sync_playwright() as p:
        # Lancio del browser con configurazioni per ridurre il rilevamento anti-bot
        browser = p.chromium.launch(
            headless=True, # Cambiare in False per vedere il browser in azione in locale
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        
        page = context.new_page()
        
        for pagina in range(1, max_pagine + 1):
            url_corrente = f"{url_base}&pag={pagina}" if pagina > 1 else url_base
            print(f"Esplorazione pagina {pagina}: {url_corrente}")
            
            try:
                page.goto(url_corrente, timeout=60000)
                # Attesa casuale per simulare la lettura umana
                time.sleep(random.uniform(3.0, 6.0))
                
                # Gestione iniziale dei cookie se presenti
                if pagina == 1:
                    bottone_cookie = page.locator("button:has-text('Accetta'), button:has-text('Acconsento')").first
                    if bottone_cookie.is_visible():
                        bottone_cookie.click()
                        time.sleep(1)

                # Selettore delle card dei singoli annunci (struttura standard dei portali)
                annunci = page.locator("li.in-reListCard").all()
                
                if not annunci:
                    print("Nessun annuncio trovato. Possibile blocco o cambio layout.")
                    break
                    
                for annuncio in annunci:
                    try:
                        # Estrazione Link e Titolo (contiene la zona)
                        link_elemento = annuncio.locator("a.in-reListCard__title").first
                        link = link_elemento.get_attribute("href")
                        titolo = link_elemento.text_content().strip()
                        
                        # Estrazione Prezzo
                        prezzo_testo = annuncio.locator(".in-reListCard__price").text_content().strip()
                        prezzo = pulisci_prezzo(prezzo_testo)
                        
                        # Estrazione Superficie
                        # Spesso i dettagli sono in liste con icone, cerchiamo il testo con 'm²'
                        sup_elemento = annuncio.locator("li:has-text('m²')").first
                        superficie = pulisci_superficie(sup_elemento.text_content()) if sup_elemento.is_visible() else None
                        
                        # Analisi euristica della zona dal titolo (es. 'Appartamento in Centro Storico, Padova')
                        zona = "Non Specificata"
                        if "in " in titolo:
                            parti = titolo.split("in ")[1].split(",")
                            if parti:
                                zona = parti[0].strip()
                        
                        # Salviamo solo se abbiamo i dati fondamentali per il calcolo finanziario
                        if prezzo and superficie and link:
                            risultati.append({
                                'Comune': 'Padova',
                                'Zona': zona,
                                'Tipologia': 'Residenziale',
                                'Superficie': superficie,
                                'Prezzo_J': prezzo,
                                'Link': link
                            })
                    except Exception as e:
                        # Salta l'annuncio singolo se corrotto, per non bloccare il ciclo
                        continue
                        
            except Exception as e:
                print(f"Errore durante lo scaricamento della pagina {pagina}: {e}")
                break
                
        browser.close()
        
    # Conversione in DataFrame e salvataggio
    df_scout = pd.DataFrame(risultati)
    if not df_scout.empty:
        df_scout.to_csv("annunci_padova.csv", index=False, encoding="utf-8")
        print(f"Scouting completato. Salvati {len(df_scout)} immobili in 'annunci_padova.csv'")
    else:
        print("Nessun dato raccolto.")

if __name__ == "__main__":
    esegui_scouting_padova(max_pagine=3)
