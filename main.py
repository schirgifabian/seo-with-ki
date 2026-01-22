import os
import json
import asyncio
from nicegui import ui, run, app
import trafilatura
from mistralai import Mistral

# --- SETUP ---
api_key = os.environ.get("MISTRAL_API_KEY")
client = Mistral(api_key=api_key) if api_key else None

# --- STYLES (SaaS Look) ---
CARD_STYLE = 'w-full bg-white rounded-xl shadow-sm border border-slate-200 p-6 transition hover:shadow-md'
LABEL_STYLE = 'text-xs font-bold text-slate-500 uppercase tracking-wider mb-1 block'
INPUT_STYLE = 'w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-slate-700 focus:bg-white focus:border-blue-500 transition outline-none'
BTN_ICON_STYLE = 'text-slate-400 hover:text-blue-600 cursor-pointer'

# --- LOGIK ---
def extract_json_from_text(text: str):
    """Versucht, JSON aus der KI-Antwort zu extrahieren, auch wenn Text drumherum steht."""
    try:
        # Suche nach dem ersten { und dem letzten }
        start = text.find('{')
        end = text.rfind('}') + 1
        if start != -1 and end != -1:
            json_str = text[start:end]
            return json.loads(json_str)
        return None
    except:
        return None

def blocking_analysis(url: str, business_context: str):
    if not client:
        return {"error": "Kein API Key gefunden."}

    # 1. Scraping
    try:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return {"error": "URL nicht erreichbar."}
        text_content = trafilatura.extract(downloaded)
        if not text_content:
            return {"error": "Kein Text gefunden."}
        text_content = text_content[:5000] # Limit
    except Exception as e:
        return {"error": f"Scraping Fehler: {str(e)}"}

    # 2. KI Prompt (Striktes JSON Format)
    prompt = f"""
    Du bist ein SEO-Experte für Rank Math.
    
    KONTEXT ZUM UNTERNEHMEN (Beachte dies für Local SEO!):
    "{business_context}"
    
    WEBSEITEN TEXT:
    "{text_content}"
    
    AUFGABE:
    Erstelle optimierte Metadaten als JSON.
    
    REGELN:
    1. title: 50-60 Zeichen. Keyword am Anfang.
    2. description: 150-160 Zeichen. Call-to-Action am Ende. Keyword enthalten.
    3. focus_keyword: Das eine Hauptkeyword.
    4. suggestions: Liste mit 3-5 konkreten Verbesserungen (kurz).
    
    ANTWORTE NUR IN DIESEM JSON FORMAT:
    {{
        "focus_keyword": "...",
        "title": "...",
        "description": "...",
        "suggestions": ["...", "..."]
    }}
    """

    try:
        chat_response = client.chat.complete(
            model="mistral-large-latest",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"} # Erzwingt JSON Mode bei Mistral
        )
        content = chat_response.choices[0].message.content
        data = extract_json_from_text(content)
        if not data:
            return {"error": "KI hat kein gültiges JSON geliefert."}
        return data
    except Exception as e:
        return {"error": f"KI Fehler: {str(e)}"}

# --- GUI ---
@ui.page('/')
def main_page():
    ui.colors(primary='#3B82F6', secondary='#64748B', positive='#22C55E')
    ui.query('body').classes('bg-slate-50 font-sans')

    # State Container für Ergebnisse
    results = {
        'keyword': ui.item_value(''), 
        'title': ui.item_value(''),
        'desc': ui.item_value(''),
        'suggestions': []
    }

    # Helper: Kopier-Funktion
    def copy_to_clipboard(text):
        ui.clipboard.write(text)
        ui.notify('Kopiert!', type='positive', position='top')

    # Helper: Zeichenzähler Update
    def update_char_count(input_element, label_element, target_min, target_max):
        chars = len(input_element.value)
        label_element.set_text(f"{chars} Zeichen")
        if target_min <= chars <= target_max:
            label_element.classes('text-green-600', remove='text-red-500 text-slate-400')
        else:
            label_element.classes('text-red-500', remove='text-green-600 text-slate-400')

    async def run_seo():
        if not url_input.value:
            ui.notify('Bitte URL eingeben', type='warning')
            return
        
        loading_spinner.set_visibility(True)
        analyze_btn.disable()
        result_area.set_visibility(False)
        
        # Analyse starten
        data = await run.io_bound(blocking_analysis, url_input.value, context_input.value)
        
        if "error" in data:
            ui.notify(data['error'], type='negative')
        else:
            # Werte in die Felder füllen
            keyword_input.value = data.get('focus_keyword', '')
            title_input.value = data.get('title', '')
            desc_input.value = data.get('description', '')
            
            # Vorschläge rendern
            suggestions_col.clear()
            with suggestions_col:
                for s in data.get('suggestions', []):
                    with ui.row().classes('items-start gap-2 mb-2'):
                        ui.icon('check_circle', color='green').classes('mt-1')
                        ui.label(s).classes('text-slate-700 text-sm')

            result_area.set_visibility(True)
            ui.notify('Analyse fertig!', type='positive')

        loading_spinner.set_visibility(False)
        analyze_btn.enable()

    # --- LAYOUT ---
    with ui.column().classes('w-full max-w-4xl mx-auto p-6 md:p-10 gap-6'):
        
        # Header
        with ui.row().classes('items-center gap-3 mb-4'):
            ui.icon('rocket_launch', size='2.5em', color='primary')
            with ui.column().classes('gap-0'):
                ui.label('SEO Generator Pro').classes('text-2xl font-bold text-slate-800')
                ui.label('Rank Math Optimized • JSON Mode').classes('text-xs text-slate-500 font-bold uppercase tracking-widest')

        # 1. Konfiguration & Input
        with ui.column().classes(CARD_STYLE):
            ui.label('1. Business Kontext (Wichtig für Local SEO)').classes(LABEL_STYLE)
            context_input = ui.input(placeholder='z.B. Veganes Restaurant in Tirol, Fokus auf Regionalität')\
                .classes(INPUT_STYLE).props('clearable')
            
            ui.label('2. Ziel-URL').classes(LABEL_STYLE + ' mt-4')
            with ui.row().classes('w-full gap-2'):
                url_input = ui.input(placeholder='https://deine-seite.de/angebot')\
                    .classes(INPUT_STYLE + ' flex-grow')
                
                analyze_btn = ui.button('Analysieren', on_click=run_seo)\
                    .props('unelevated').classes('bg-blue-600 text-white font-bold px-6 rounded-lg')

            loading_spinner = ui.spinner('dots', size='lg', color='primary').classes('self-center mt-4')
            loading_spinner.set_visibility(False)

        # 2. Ergebnisse (Versteckt bis fertig)
        result_area = ui.column().classes('w-full gap-6')
        result_area.set_visibility(False)
        
        with result_area:
            
            # Focus Keyword
            with ui.column().classes(CARD_STYLE):
                with ui.row().classes('justify-between w-full'):
                    ui.label('Focus Keyword').classes(LABEL_STYLE)
                    ui.button(icon='content_copy', on_click=lambda: copy_to_clipboard(keyword_input.value))\
                        .props('flat round dense color=grey')
                
                keyword_input = ui.input().classes(INPUT_STYLE + ' font-bold text-blue-700')

            # SEO Title
            with ui.column().classes(CARD_STYLE):
                with ui.row().classes('justify-between w-full'):
                    ui.label('SEO Title (Rank Math)').classes(LABEL_STYLE)
                    title_count = ui.label('0 Zeichen').classes('text-xs font-mono text-slate-400')
                
                with ui.row().classes('w-full gap-2 items-center'):
                    title_input = ui.input(on_change=lambda: update_char_count(title_input, title_count, 50, 60))\
                        .classes(INPUT_STYLE + ' flex-grow').props('clearable')
                    ui.button(icon='content_copy', on_click=lambda: copy_to_clipboard(title_input.value))\
                        .props('flat round dense color=grey')
                
                ui.label('Ziel: 50-60 Zeichen').classes('text-xs text-slate-400 mt-1')

            # Meta Description
            with ui.column().classes(CARD_STYLE):
                with ui.row().classes('justify-between w-full'):
                    ui.label('Meta Description').classes(LABEL_STYLE)
                    desc_count = ui.label('0 Zeichen').classes('text-xs font-mono text-slate-400')
                
                with ui.row().classes('w-full gap-2 items-start'):
                    desc_input = ui.textarea(on_change=lambda: update_char_count(desc_input, desc_count, 150, 160))\
                        .classes(INPUT_STYLE + ' flex-grow h-24').props('clearable')
                    ui.button(icon='content_copy', on_click=lambda: copy_to_clipboard(desc_input.value))\
                        .props('flat round dense color=grey')
                
                ui.label('Ziel: 150-160 Zeichen • Inkl. Call-to-Action').classes('text-xs text-slate-400 mt-1')

            # Content Optimierung
            with ui.column().classes(CARD_STYLE + ' bg-blue-50 border-blue-100'):
                ui.label('Content Optimierung & Vorschläge').classes(LABEL_STYLE + ' text-blue-600')
                suggestions_col = ui.column().classes('w-full')


# App Start
ui.run(
    host='0.0.0.0', 
    port=9999, 
    title='SEO Master Pro', 
    storage_secret='secure-key',
    reconnect_timeout=10.0,
    reload=False
)
