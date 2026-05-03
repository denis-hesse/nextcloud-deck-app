#!/bin/bash

echo "=== Démarrage Nextcloud Deck App ==="
echo "Python : $(python --version)"
echo "Fichiers :"
ls -la /app

PROXY=$(find /app -name "*nextcloud_deck_proxy*" | head -1)
echo "Proxy : $PROXY"

# Lancer le watcher avec output non-bufférisé
echo "Lancement watcher..."
PYTHONUNBUFFERED=1 python -u /app/deck_watcher.py &
WATCHER_PID=$!
echo "Watcher PID : $WATCHER_PID"

sleep 3
if kill -0 $WATCHER_PID 2>/dev/null; then
    echo "Watcher actif."
else
    echo "ERREUR : Watcher mort !"
fi

# Lancer le proxy avec output non-bufférisé
echo "Lancement proxy..."
PYTHONUNBUFFERED=1 python -u "$PROXY"
