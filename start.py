#!/usr/bin/env python3
"""
Lanceur principal — démarre le proxy et le watcher en parallèle
"""
import threading
import sys
import os

def run_proxy():
    import importlib.util
    spec = importlib.util.spec_from_file_location("proxy", "/app/nextcloud_deck_proxy.py")
    proxy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(proxy)
    proxy.main()

def run_watcher():
    import importlib.util
    spec = importlib.util.spec_from_file_location("watcher", "/app/deck_watcher.py")
    watcher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(watcher)
    watcher.main()

if __name__ == '__main__':
    print("Démarrage Nextcloud Deck App...")

    t1 = threading.Thread(target=run_proxy, daemon=True)
    t2 = threading.Thread(target=run_watcher, daemon=True)

    t1.start()
    t2.start()

    t1.join()
    t2.join()
