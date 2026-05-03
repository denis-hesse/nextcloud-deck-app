# Nextcloud Deck App

Application de création de cartes Nextcloud Deck depuis Gmail.

## Déploiement Railway

### 1. Préparer GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/denis-hesse/nextcloud-deck-app.git
git push -u origin main
```

### 2. Créer le projet Railway

1. Va sur [railway.app](https://railway.app) et connecte-toi avec GitHub
2. Clique **New Project → Deploy from GitHub repo**
3. Sélectionne `denis-hesse/nextcloud-deck-app`
4. Railway détecte automatiquement le Dockerfile et lance le build

### 3. Configurer les variables d'environnement

Dans Railway → ton projet → **Variables**, ajoute :

| Variable | Valeur |
|---|---|
| `GMAIL_EMAIL` | beatrice@bt-conseil.net |
| `GMAIL_APP_PASSWORD` | ton mot de passe app Gmail |
| `GMAIL_LABEL` | DECK |
| `ANTHROPIC_API_KEY` | ta clé API Anthropic |
| `NEXTCLOUD_URL` | https://switchcompetences.cloud.in-cubes.com |
| `NEXTCLOUD_USER` | BThelemaque |
| `NEXTCLOUD_PASSWORD` | ton mot de passe Nextcloud |
| `CHECK_INTERVAL` | 120 |

### 4. Obtenir l'URL publique

Dans Railway → ton projet → **Settings → Networking → Generate Domain**
Tu obtiens une URL comme `https://nextcloud-deck-app.up.railway.app`

### 5. Utilisation

Ouvre l'URL dans n'importe quel navigateur — l'app fonctionne sans installation !

## Déploiement d'un nouvel utilisateur

1. Fork le repo GitHub
2. Crée un nouveau projet Railway depuis ce fork
3. Configure les variables d'environnement avec les identifiants du nouvel utilisateur
4. Railway génère une URL indépendante

## Utilisation locale

```bash
pip install -r requirements.txt
# Créer config.json avec tes identifiants
python nextcloud_deck_proxy.py  # fenêtre 1
python deck_watcher.py          # fenêtre 2
```
