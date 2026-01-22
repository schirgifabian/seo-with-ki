import os
from nicegui import ui
import trafilatura
from mistralai import Mistral

# --- Konfiguration ---
# Wir holen den Key aus der Docker-Umgebungsvariable
api_key = os.environ.get("MISTRAL_API_KEY")

# Fallback, falls kein Key gesetzt ist (nur Warnung)
if not api_key:
    print("ACHTUNG: MISTRAL_API_KEY fehlt!")

client = Mistral(api_key=api_key)

def analyze_url(url_input, result_area):
    url = url_input.value
    if not url:
        ui.notify('Bitte eine URL eingeben', type='warning')
        return

    # Bereich leeren und Lade-Animation starten
    result_area.clear()
    with result_area:
        ui.spinner('dots', size='lg', color='primary')
        ui.label('Webseite wird gescannt...').classes('text-gray-500 animate-pulse')

    # 1. Scrapen der Webseite
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded is None:
            raise Exception("URL konnte nicht abgerufen werden (Timeout oder Block).")
        text_content = trafilatura.extract(downloaded)
        
        if not text_content or len(text_content) < 50:
            raise Exception("Kein verwertbarer Text auf der Seite gefunden.")
            
    except Exception as e:
        result_area.clear()
        ui.notify(f'Fehler beim Scrapen: {str(e)}', type='negative')
        return

    # 2. KI Prompt erstellen
    prompt = f"""
    Du bist ein SEO-Profi für WordPress. Analysiere den folgenden Text einer Webseite.
    Erstelle optimierte Daten, die ich direkt in das WordPress Plugin "Rank Math" oder "Yoast" kopieren kann.

    Inhalt der Seite:
    {text_content[:12000]} 

    Bitte erstelle folgende Analyse auf DEUTSCH und nutze Markdown Formatierung:

    ### 1. Fokus Keyword
    (Nenne das beste Hauptkeyword für diesen Text)

    ### 2. SEO Titel
    (Max 60 Zeichen, klickstark, muss Keyword enthalten)

    ### 3. Meta Beschreibung
    (Max 160 Zeichen, animiert zum Klicken, enthält Keyword)

    ### 4. Content Analyse
    * Was ist gut?
    * Was fehlt inhaltlich für ein Top-Ranking?
    * Stimmt die H-Struktur?

    ### 5. Keyword Vorschläge (Long-Tail)
    * [Keyword 1]
    * [Keyword 2]
    * [Keyword 3]
    """

    # 3. Anfrage an Mistral
    try:
        chat_response = client.chat.complete(
            model="mistral-large-latest", # Das intelligenteste Modell
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                },
            ]
        )
        
        response_text = chat_response.choices[0].message.content
        
        # 4. Ergebnis anzeigen
        result_area.clear()
        with result_area:
            with ui.card().classes('w-full bg-white shadow-lg'):
                ui.markdown(response_text).classes('prose max-w-none p-4')
            
            ui.button('Neue Analyse', on_click=lambda: result_area.clear()).classes('mt-4 bg-gray-500 text-white')

    except Exception as e:
        result_area.clear()
        ui.notify(f'Fehler bei Mistral: {str(e)}', type='negative')

# --- GUI Aufbau ---
@ui.page('/')
def main_page():
    # Styling
    ui.colors(primary='#f59e0b', secondary='#262626') # Mistral Farben
    
    with ui.column().classes('w-full max-w-4xl mx-auto p-6 gap-6'):
        # Header
        with ui.row().classes('items-center gap-4'):
            ui.icon('auto_awesome', size='3em', color='primary')
            ui.label('AI SEO Agent').classes('text-4xl font-bold text-gray-800')
        
        ui.label('Füge einen Link ein. Die KI scannt den Inhalt und erstellt SEO-Metadaten für WordPress.').classes('text-gray-600')
        
        # Input Bereich
        with ui.card().classes('w-full p-4 gap-4 bg-gray-50'):
            url_input = ui.input(label='URL der Webseite (z.B. https://mein-blog.de/artikel)').classes('w-full text-lg')
            ui.button('SEO Analyse starten', icon='search', 
                      on_click=lambda: analyze_url(url_input, result_area)).classes('w-full h-12 text-lg font-bold')

        # Ergebnis Bereich
        result_area = ui.column().classes('w-full')

ui.run(host='0.0.0.0', port=9999, title='SEO Tool', favicon='🚀')
