# Wir nutzen ein schlankes Python Image
FROM python:3.11-slim

# Arbeitsverzeichnis im Container
WORKDIR /app

# Abhängigkeiten installieren
# nicegui: Das Dashboard
# trafilatura: Der Web-Scraper
# mistralai: Die KI Anbindung
RUN pip install nicegui trafilatura mistralai

# Code kopieren
COPY main.py .

# Port freigeben
EXPOSE 9999

# App starten
CMD ["python", "main.py"]