#!/bin/bash
set -e

echo "=== Démarrage Nextcloud Deck App ==="
echo "Python : $(python --version)"
echo "Fichiers :"
ls -la /app

PROXY=$(find /app -name "*nextcloud_deck_proxy*" | head -1)
echo "Proxy : $PROXY"

# Lancer le watcher en arrière-plan avec logs d'erreur visibles
echo "Lancement watcher..."
python /app/deck_watcher.py 2>&1 &
WATCHER_PID=$!
echo "Watcher PID : $WATCHER_PID"

# Attendre un peu pour voir si le watcher démarre
sleep 3
if kill -0 $WATCHER_PID 2>/dev/null; then
    echo "Watcher actif."
else
    echo "ERREUR : Watcher s'est arrêté !"
fi

# Lancer le proxy
echo "Lancement proxy..."
python "$PROXY" 2>&1
