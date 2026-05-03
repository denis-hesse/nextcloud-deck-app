#!/usr/bin/env python3
"""
Lanceur principal — démarre le proxy et le watcher en parallèle
"""
import threading
import subprocess
import sys
import os

def run_proxy():
    import nextcloud_deck_proxy as proxy
    proxy.main()

def run_watcher():
    import deck_watcher as watcher
    watcher.main()

if __name__ == '__main__':
    print("Démarrage Nextcloud Deck App...")
    
    t1 = threading.Thread(target=run_proxy, daemon=True)
    t2 = threading.Thread(target=run_watcher, daemon=True)
    
    t1.start()
    t2.start()
    
    t1.join()
    t2.join()
