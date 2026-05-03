#!/bin/bash
set -e

echo "=== Démarrage Nextcloud Deck App ==="
echo "Python : $(python --version)"
echo "Fichiers :"
ls -la /app

# Trouver le fichier proxy
PROXY=$(find /app -name "*nextcloud_deck_proxy*" | head -1)
echo "Proxy : $PROXY"

# Lancer le watcher en arrière-plan
python /app/deck_watcher.py &
WATCHER_PID=$!
echo "Watcher PID : $WATCHER_PID"

# Lancer le proxy
echo "Lancement proxy..."
python "$PROXY"
