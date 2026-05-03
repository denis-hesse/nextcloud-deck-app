#!/bin/bash

echo "=== Démarrage Nextcloud Deck App ==="
echo "Python : $(python --version)"
echo "Fichiers :"
ls -la /app

PROXY=$(find /app -name "*nextcloud_deck_proxy*" | head -1)
echo "Proxy : $PROXY"

# Tester la syntaxe du watcher avant de le lancer
echo "Test syntaxe watcher..."
python -m py_compile /app/deck_watcher.py && echo "Syntaxe OK" || echo "ERREUR SYNTAXE"

# Lancer le watcher en arrière-plan
echo "Lancement watcher..."
python /app/deck_watcher.py &
WATCHER_PID=$!
echo "Watcher PID : $WATCHER_PID"

sleep 5
if kill -0 $WATCHER_PID 2>/dev/null; then
    echo "Watcher actif apres 5s."
else
    echo "ERREUR : Watcher mort apres 5s !"
    # Relancer pour voir l'erreur
    python /app/deck_watcher.py &
fi

# Lancer le proxy au premier plan
echo "Lancement proxy..."
python "$PROXY"
