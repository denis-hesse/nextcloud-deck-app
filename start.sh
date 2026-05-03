#!/bin/bash
# Lancer le watcher en arrière-plan
python deck_watcher.py &
# Lancer le proxy au premier plan
python nextcloud_deck_proxy.py
