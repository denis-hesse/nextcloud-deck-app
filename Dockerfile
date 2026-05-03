FROM python:3.11-slim

# Installer wkhtmltopdf et ses dépendances
RUN apt-get update && apt-get install -y \
    wkhtmltopdf \
    xvfb \
    libfontconfig1 \
    libxrender1 \
    libxtst6 \
    libxi6 \
    && rm -rf /var/lib/apt/lists/*

# Répertoire de travail
WORKDIR /app

# Installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code
COPY . .

# Port exposé
EXPOSE 8765

# Lancer les deux scripts en parallèle
CMD ["python", "start.py"]
