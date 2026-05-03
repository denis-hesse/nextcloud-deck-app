#!/usr/bin/env python3
"""
Lanceur principal — démarre le proxy et le watcher en parallèle
"""
import threading
import sys
import os

# Ajouter le dossier courant au path Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_proxy():
    import importlib.util
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'nextcloud_deck_proxy.py')
    print(f"Chargement proxy depuis : {path}")
    print(f"Fichiers disponibles : {os.listdir(os.path.dirname(os.path.abspath(__file__)))}")
    spec = importlib.util.spec_from_file_location("proxy", path)
    proxy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(proxy)
    proxy.main()

def run_watcher():
    import importlib.util
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'deck_watcher.py')
    spec = importlib.util.spec_from_file_location("watcher", path)
    watcher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(watcher)
    watcher.main()

if __name__ == '__main__':
    print("Démarrage Nextcloud Deck App...")
    print(f"Dossier de travail : {os.getcwd()}")
    print(f"Fichiers : {os.listdir('.')}")

    t1 = threading.Thread(target=run_proxy, daemon=True)
    t2 = threading.Thread(target=run_watcher, daemon=True)

    t1.start()
    t2.start()

    t1.join()
    t2.join()
