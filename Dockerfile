FROM python:3.11-slim

WORKDIR /app

# System-Abhängigkeiten für lxml (wichtig für Trafilatura/Scraping)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

# Python Pakete
RUN pip install --no-cache-dir nicegui trafilatura mistralai

# App kopieren
COPY main.py .

EXPOSE 9999

CMD ["python", "main.py"]
