import os
import asyncio
from nicegui import ui, run, app
import trafilatura
from mistralai import Mistral

# --- SETUP ---
# API Key laden
api_key = os.environ.get("MISTRAL_API_KEY")
client = Mistral(api_key=api_key) if api_key else None

# --- DESIGN STYLES (Tailwind Helper) ---
CARD_STYLE = 'w-full bg-white rounded-xl shadow-lg p-6 border border-gray-100'
BUTTON_STYLE = 'bg-blue-600 text-white font-bold py-2 px-6 rounded-lg hover:bg-blue-700 transition shadow-md'
INPUT_STYLE = 'w-full text-lg p-3 rounded-lg border-2 border-gray-200 focus:border-blue-500 transition'

# --- LOGIK (Läuft im Hintergrund) ---
def blocking_analysis(url: str):
    """Diese Funktion führt die teuren Aufgaben aus (Scraping + AI)."""
    if not client:
        return "Fehler: Kein Mistral API Key gefunden. Bitte Checke deine Umgebungsvariablen."

    # 1. Scraping
    try:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return "Fehler: Die URL konnte nicht abgerufen werden."
        text_content = trafilatura.extract(downloaded)
        if not text_content:
            return "Fehler: Es konnte kein Text extrahiert werden."
        
        # Text kürzen um Tokens zu sparen
        text_content = text_content[:6000]
    except Exception as e:
        return f"Scraping Fehler: {str(e)}"

    # 2. KI Anfrage
    prompt = f"""
    Du bist ein professioneller SEO-Experte für WordPress.
    Analysiere den folgenden Webseitentext:
    
    TEXT:
    {text_content}
    
    AUFGABE:
    Erstelle eine strukturierte SEO-Optimierung für das Plugin 'Rank Math'.
    Antworte NUR im folgenden Format (Markdown):
    
    ## Analyse
    (Kurze Einschätzung worum es geht)
    
    ## Fokus Keyword
    (Das eine perfekte Keyword für Rank Math)
    
    ## Meta Titel (SEO Title)
    (Max 60 Zeichen, Klickstark)
    
    ## Meta Beschreibung
    (Max 160 Zeichen, animiert zum Klicken)
    
    ## Verbesserungsvorschläge
    * (Punkt 1)
    * (Punkt 2)
    """

    try:
        chat_response = client.chat.complete(
            model="mistral-large-latest",
            messages=[{"role": "user", "content": prompt}]
        )
        return chat_response.choices[0].message.content
    except Exception as e:
        return f"KI Fehler: {str(e)}"

# --- GUI ---
@ui.page('/')
def main_page():
    # Hintergrund Farbe setzen (SaaS Grau)
    ui.colors(primary='#2563EB', secondary='#64748B', accent='#F59E0B')
    ui.query('body').classes('bg-slate-50')

    async def start_analysis():
        url = url_input.value
        if not url:
            ui.notify('Bitte URL eingeben', type='warning')
            return

        # UI Update: Ladezustand
        analyze_btn.disable()
        spinner.set_visibility(True)
        result_container.clear()
        
        # WICHTIG: run.io_bound verhindert "Connection Lost"
        # Es lagert die Arbeit in einen Thread aus
        result_text = await run.io_bound(blocking_analysis, url)
        
        # UI Update: Ergebnis anzeigen
        with result_container:
            ui.markdown(result_text).classes('prose lg:prose-xl text-slate-700')
            
            # Copy Button für faule User
            ui.button('Ergebnis kopieren', on_click=lambda: ui.clipboard.write(result_text))\
                .props('icon=content_copy outline').classes('mt-4')

        analyze_btn.enable()
        spinner.set_visibility(False)


    # --- LAYOUT AUFBAU ---
    with ui.column().classes('w-full max-w-5xl mx-auto p-4 md:p-10 gap-8'):
        
        # HEADER
        with ui.row().classes('w-full items-center justify-between mb-4'):
            with ui.row().classes('items-center gap-2'):
                ui.icon('auto_graph', size='3em', color='primary')
                with ui.column().classes('gap-0'):
                    ui.label('SEO Master').classes('text-2xl font-bold text-slate-800 tracking-tight')
                    ui.label('Automated RankMath Optimization').classes('text-sm text-slate-500 uppercase tracking-widest')
            
            ui.chip('v1.0 Pro', color='green').props('dense outline')

        # INPUT CARD
        with ui.column().classes(CARD_STYLE):
            ui.label('URL Analyse').classes('text-lg font-semibold text-slate-700 mb-2')
            url_input = ui.input(placeholder='https://deine-website.de/beitrag')\
                .classes(INPUT_STYLE).props('clearable')
            
            with ui.row().classes('w-full mt-4 items-center'):
                analyze_btn = ui.button('SEO Optimieren generieren', on_click=start_analysis)\
                    .classes(BUTTON_STYLE)
                spinner = ui.spinner('dots', size='lg', color='primary')
                spinner.set_visibility(False)

        # RESULT CARD
        with ui.column().classes(CARD_STYLE + ' min-h-[200px]'):
            ui.label('Ergebnisse').classes('text-lg font-semibold text-slate-700 mb-4 border-b pb-2 border-gray-100 w-full')
            result_container = ui.column().classes('w-full')
            with result_container:
                 ui.label('Warte auf Eingabe...').classes('text-gray-400 italic')

# Start Konfiguration
# reconnect_timeout: Verhindert sofortigen Abbruch bei kleinen Netzwerkwacklern
ui.run(
    host='0.0.0.0', 
    port=9999, 
    title='SEO Master Dashboard', 
    storage_secret='seo-secure-key-123',
    reconnect_timeout=10.0,
    reload=False # Wichtig für Docker Stabilität
)
