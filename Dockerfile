FROM python:3.11-slim

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    wget \
    xvfb \
    libfontconfig1 \
    libxrender1 \
    libxtst6 \
    libxi6 \
    libjpeg62-turbo \
    libssl3 \
    fontconfig \
    && rm -rf /var/lib/apt/lists/*

# Installer wkhtmltopdf depuis le binaire officiel
RUN wget -q https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-3/wkhtmltox_0.12.6.1-3.bookworm_amd64.deb \
    && apt-get update && apt-get install -y ./wkhtmltox_0.12.6.1-3.bookworm_amd64.deb \
    && rm wkhtmltox_0.12.6.1-3.bookworm_amd64.deb \
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
