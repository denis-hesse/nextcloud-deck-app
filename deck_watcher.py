#!/usr/bin/env python3
import sys
print("=== DECK WATCHER DEMARRE ===", flush=True)
sys.stdout.flush()
"""
Deck Watcher — Surveillance Gmail et création de cartes Nextcloud Deck
-----------------------------------------------------------------------
Ce script surveille ta boîte Gmail, détecte les mails labelisés DECK,
les analyse avec Claude et ouvre le formulaire pré-rempli dans Chrome.

Prérequis :
    pip install anthropic pdfkit --break-system-packages
    + wkhtmltopdf : https://wkhtmltopdf.org/downloads.html

Usage :
    python deck_watcher.py
"""

import imaplib
import email
import email.header
import json
import os
import sys
import time
import urllib.request
import urllib.parse
import base64
import webbrowser
import tempfile
import re
from datetime import datetime
from email.utils import parseaddr

# ── Config ──────────────────────────────────────────────────────────────────

def load_config():
    # Lire depuis variables d'environnement (Railway) ou config.json (local)
    path = os.path.join(os.path.dirname(__file__), 'config.json')
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    # Variables d'environnement Railway
    cfg = {
        'gmail': {
            'email': os.environ.get('GMAIL_EMAIL', ''),
            'app_password': os.environ.get('GMAIL_APP_PASSWORD', ''),
            'label': os.environ.get('GMAIL_LABEL', 'DECK'),
            'check_interval_seconds': int(os.environ.get('CHECK_INTERVAL', '30'))
        },
        'anthropic': {
            'api_key': os.environ.get('ANTHROPIC_API_KEY', '')
        },
        'nextcloud': {
            'url': os.environ.get('NEXTCLOUD_URL', ''),
            'user': os.environ.get('NEXTCLOUD_USER', ''),
            'password': os.environ.get('NEXTCLOUD_PASSWORD', '')
        },
        'proxy_port': int(os.environ.get('PORT', '8765')),
        'app_url': os.environ.get('APP_URL', f"http://localhost:{os.environ.get('PORT', '8765')}")
    }
    # Vérifier les variables obligatoires
    missing = []
    if not cfg['gmail']['email']: missing.append('GMAIL_EMAIL')
    if not cfg['gmail']['app_password']: missing.append('GMAIL_APP_PASSWORD')
    if not cfg['anthropic']['api_key']: missing.append('ANTHROPIC_API_KEY')
    if not cfg['nextcloud']['url']: missing.append('NEXTCLOUD_URL')
    if missing:
        print(f"ERREUR : variables d'environnement manquantes : {', '.join(missing)}", flush=True)
        sys.exit(1)
    return cfg

# ── Décodage mail ────────────────────────────────────────────────────────────

def decode_header(value):
    if not value:
        return ''
    parts = email.header.decode_header(value)
    result = []
    for part, enc in parts:
        if isinstance(part, bytes):
            result.append(part.decode(enc or 'utf-8', errors='replace'))
        else:
            result.append(part)
    return ' '.join(result)

def get_body(msg):
    body = ''
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            cd = str(part.get('Content-Disposition', ''))
            if ct == 'text/plain' and 'attachment' not in cd:
                charset = part.get_content_charset() or 'utf-8'
                body += part.get_payload(decode=True).decode(charset, errors='replace')
            elif ct == 'text/html' and not body and 'attachment' not in cd:
                charset = part.get_content_charset() or 'utf-8'
                html = part.get_payload(decode=True).decode(charset, errors='replace')
                # Nettoyer le HTML basiquement
                body += re.sub(r'<[^>]+>', ' ', html)
    else:
        charset = msg.get_content_charset() or 'utf-8'
        body = msg.get_payload(decode=True).decode(charset, errors='replace')
    return body.strip()

def get_attachments(msg):
    attachments = []
    for part in msg.walk():
        cd = str(part.get('Content-Disposition', ''))
        if 'attachment' in cd:
            filename = decode_header(part.get_filename() or 'fichier')
            data = part.get_payload(decode=True)
            if data:
                attachments.append({'name': filename, 'data': data})
    return attachments

# ── Conversion PDF ───────────────────────────────────────────────────────────

def mail_to_pdf(subject, sender, date_str, body, attachments):
    """Convertit le mail en PDF via wkhtmltopdf ou fallback texte."""
    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
  body {{ font-family: Arial, sans-serif; font-size: 13px; margin: 40px; color: #333; }}
  .header {{ border-bottom: 2px solid #0082C9; padding-bottom: 12px; margin-bottom: 20px; }}
  .header h2 {{ color: #0082C9; margin: 0 0 8px 0; }}
  .meta {{ font-size: 12px; color: #666; line-height: 1.8; }}
  .body {{ white-space: pre-wrap; line-height: 1.6; }}
  .attachments {{ margin-top: 20px; font-size: 12px; color: #666; border-top: 1px solid #eee; padding-top: 10px; }}
</style></head><body>
<div class="header">
  <h2>{subject}</h2>
  <div class="meta">
    <strong>De :</strong> {sender}<br>
    <strong>Date :</strong> {date_str}
  </div>
</div>
<div class="body">{body}</div>
"""
    if attachments:
        html += '<div class="attachments"><strong>Pièces jointes :</strong><ul>'
        for a in attachments:
            html += f'<li>{a["name"]}</li>'
        html += '</ul></div>'
    html += '</body></html>'

    # Essayer pdfkit (wkhtmltopdf)
    try:
        import pdfkit
        wk_paths = [
            '/usr/bin/wkhtmltopdf',          # Linux (Railway/Docker)
            'C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe',
            'C:/Program Files (x86)/wkhtmltopdf/bin/wkhtmltopdf.exe',
        ]
        config = None
        for p in wk_paths:
            if os.path.exists(p):
                config = pdfkit.configuration(wkhtmltopdf=p)
                print(f'  wkhtmltopdf trouve : {p}', flush=True)
                break
        # Nom propre basé sur le sujet du mail
        safe_subject = re.sub(r'[^\w\s-]', '', subject)[:40].strip().replace(' ', '_')
        pdf_name = f'mail_{safe_subject}.pdf'
        tmp_path = os.path.join(tempfile.gettempdir(), pdf_name)
        options = {'encoding': 'UTF-8', 'quiet': ''}
        if config:
            pdfkit.from_string(html, tmp_path, configuration=config, options=options)
        else:
            pdfkit.from_string(html, tmp_path, options=options)
        return tmp_path
    except Exception as e:
        print(f'  (pdfkit indisponible : {e}, fallback HTML)', flush=True)

    # Fallback : sauvegarder en HTML
    tmp = tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w', encoding='utf-8')
    tmp.write(html)
    tmp.close()
    print(f"  (PDF non disponible, fichier HTML généré : {tmp.name})", flush=True)
    return tmp.name

# ── Appel Claude API ─────────────────────────────────────────────────────────

def ask_claude(api_key, boards, subject, sender, body):
    """Demande à Claude de choisir le tableau, la liste, le titre et la description."""
    boards_list = '\n'.join([f'- {b["title"]} (id:{b["id"]})' for b in boards])

    prompt = f"""Tu es un assistant qui aide à organiser des emails dans Nextcloud Deck.

Voici un email reçu :
De : {sender}
Objet : {subject}
Corps :
{body[:4000]}

Voici les tableaux Nextcloud Deck disponibles :
{boards_list}

RÈGLES STRICTES pour la description :
- Ne jamais mentionner : @deck, Nextcloud, outils techniques, l'expéditeur, ses coordonnées, son profil
- Si le mail est un test ou vide de contenu réel : écrire uniquement "**Résumé**\\nMail de test." sans autres sections
- Proportionner la longueur au contenu réel du mail — peu de contenu = peu de texte

Ta mission :
1. Choisir le tableau le plus pertinent (basé sur le nom du client/projet dans l'email)
2. Proposer un titre court et clair pour la carte (max 80 caractères)
3. Rédiger une description structurée uniquement si le mail a un contenu substantiel :
   - **Résumé** : 1-3 phrases sur l'essentiel du contenu
   - **Actions à suivre** : uniquement si des actions concrètes sont demandées, sinon omettre
   - **Synthèse** : uniquement si contenu riche, un retour à la ligne après chaque phrase

Réponds UNIQUEMENT en JSON valide, sans aucun texte avant ou après :
{{
  "boardId": <id du tableau choisi>,
  "boardTitle": "<nom du tableau>",
  "titre": "<titre de la carte>",
  "description": "<description selon les règles ci-dessus>"
}}"""

    payload = json.dumps({
        "model": "claude-sonnet-4-5",
        "max_tokens": 1500,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()

    req = urllib.request.Request(
        'https://api.anthropic.com/v1/messages',
        data=payload,
        headers={
            'Content-Type': 'application/json',
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01'
        },
        method='POST'
    )

    with urllib.request.urlopen(req, timeout=30) as r:
        resp = json.loads(r.read())

    text = resp['content'][0]['text'].strip()
    # Nettoyer si markdown
    text = re.sub(r'^```json\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    return json.loads(text)

# ── Récupérer boards Nextcloud ───────────────────────────────────────────────

def get_boards(nc_url, user, password):
    auth = base64.b64encode(f'{user}:{password}'.encode()).decode()
    req = urllib.request.Request(
        nc_url.rstrip('/') + '/index.php/apps/deck/api/v1.0/boards?details=true',
        headers={
            'Authorization': f'Basic {auth}',
            'OCS-APIRequest': 'true',
            'Accept': 'application/json'
        }
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

# ── Ouvrir formulaire pré-rempli ─────────────────────────────────────────────

def open_form(port, board_id, titre, description, pdf_path, folder='DECK', mid=None, label=None, gmail_email=None, gmail_password=None, app_url=None):
    """Envoie les données au proxy puis ouvre Chrome sur localhost simple."""
    import subprocess, os
    # Envoyer les données au proxy via /prefill
    data = json.dumps({
        'boardId': board_id,
        'titre': titre,
        'description': description,
        'pdf': pdf_path,
        'mail_folder': folder,
        'mail_mid': mid,
        'mail_label': label,
        'mail_email': gmail_email,
        'mail_password': gmail_password
    }).encode()
    base = app_url or f'http://localhost:{port}'
    req = urllib.request.Request(
        f'{base}/prefill',
        data=data,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    try:
        urllib.request.urlopen(req, timeout=5)
        print(f"  Formulaire prêt sur : {base}", flush=True)
    except Exception as e:
        print(f"  Erreur envoi prefill : {e}", flush=True)
        return

# ── Gmail IMAP ───────────────────────────────────────────────────────────────

class GmailWatcher:
    def __init__(self, cfg):
        self.email = cfg['gmail']['email']
        self.password = cfg['gmail']['app_password']
        self.label = cfg['gmail']['label']
        self.interval = cfg['gmail'].get('check_interval_seconds', 120)
        self.processed = set()
        self.cfg = cfg

    def connect(self):
        mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
        mail.login(self.email, self.password)
        return mail

    def fetch_deck_mails(self):
        try:
            from datetime import datetime, timedelta
            from email.utils import parsedate_to_datetime

            mail = self.connect()
            new_mails = []

            # Sélectionner Messages envoyés
            status, data_sel = mail.select('"[Gmail]/Messages envoy&AOk-s"')
            print(f"  Sélection Messages envoyés : {status}", flush=True)
            if status != 'OK':
                # Essayer sans encodage
                status, data_sel = mail.select('[Gmail]/Sent Mail')
                print(f"  Essai Sent Mail : {status}", flush=True)
            if status != 'OK':
                print("  Impossible d'accéder aux Messages envoyés")
                mail.logout()
                return []
            print(f"  Nombre total de mails dans le dossier : {data_sel[0].decode()}", flush=True)

            # Chercher les mails d'aujourd'hui
            since = datetime.now().strftime("%d-%b-%Y")
            _, data = mail.search(None, f'SINCE {since}')
            mail_ids = data[0].split()
            print(f"  {len(mail_ids)} mail(s) envoyés aujourd'hui trouvés", flush=True)

            # Récupérer les mails traités côté proxy
            try:
                r = urllib.request.urlopen(
                    f'http://localhost:{self.cfg["proxy_port"]}/get-processed', timeout=2)
                proxy_processed = set(json.loads(r.read()))
            except Exception:
                proxy_processed = set()

            cutoff = datetime.now() - timedelta(minutes=30)

            for mid in mail_ids:
                mid_str = mid.decode() if isinstance(mid, bytes) else str(mid)

                # Déjà traité ?
                if mid in self.processed or mid_str in proxy_processed or mid_str in self.processed:
                    continue

                # Vérifier le label DECK (déjà traité précédemment)
                try:
                    _, ldata = mail.fetch(mid, '(X-GM-LABELS)')
                    lstr = ldata[0].decode('utf-8', errors='replace') if ldata[0] else ''
                    if 'DECK' in lstr:
                        self.processed.add(mid)
                        continue
                except Exception:
                    pass

                # Récupérer le mail complet
                _, msg_data = mail.fetch(mid, '(RFC822)')
                raw = msg_data[0][1]
                msg = email.message_from_bytes(raw)

                # Vérifier la date (30 dernières minutes)
                try:
                    msg_date = parsedate_to_datetime(msg.get('Date', ''))
                    if msg_date.tzinfo:
                        from datetime import timezone
                        msg_date = msg_date.astimezone(timezone.utc).replace(tzinfo=None)
                    if msg_date < cutoff:
                        self.processed.add(mid)
                        continue
                except Exception:
                    pass

                # Vérifier si @deck est dans le corps ou le sujet
                body = get_body(msg)
                subject = decode_header(msg.get('Subject', ''))
                if '@deck' not in body.lower() and '@deck' not in subject.lower():
                    self.processed.add(mid)
                    continue

                print(f"  @deck trouvé : {subject}", flush=True)
                new_mails.append(('SENT', mid, msg))

            mail.logout()
            return new_mails
        except Exception as e:
            print(f"  Erreur Gmail : {e}", flush=True)
            return []

    def process_mail(self, folder, mid, msg):
        subject = decode_header(msg.get('Subject', '(sans objet)'))
        sender_raw = msg.get('From', '')
        _, sender_email = parseaddr(sender_raw)
        sender = decode_header(sender_raw)
        date_str = msg.get('Date', '')
        body = get_body(msg)
        attachments = get_attachments(msg)

        print(f"\n  📧 Nouveau mail : {subject}", flush=True)
        print(f"     De : {sender}", flush=True)

        # Récupérer les boards
        print("  Récupération des tableaux Nextcloud...")
        nc = self.cfg['nextcloud']
        boards = get_boards(nc['url'], nc['user'], nc['password'])

        # Appel Claude
        print("  Analyse par Claude...")
        api_key = self.cfg['anthropic']['api_key']
        result = ask_claude(api_key, boards, subject, sender, body)
        print(f"  → Tableau : {result['boardTitle']}", flush=True)
        print(f"  → Titre   : {result['titre']}", flush=True)

        # Générer PDF
        print("  Génération du PDF...")
        pdf_path = mail_to_pdf(subject, sender, date_str, body, attachments)
        print(f"  → PDF : {pdf_path}", flush=True)

        # Ouvrir formulaire
        open_form(
            self.cfg['proxy_port'],
            result['boardId'],
            result['titre'],
            result['description'],
            pdf_path
        )

        self._save_processed(mid)

    def run(self):
        print(f"\n  Deck Watcher démarré", flush=True)
        print(f"  Surveillance : mails envoyés contenant @deck", flush=True)
        print(f"  Intervalle   : toutes les {self.interval}s", flush=True)
        print(f"  Ctrl+C pour arrêter\n", flush=True)

        while True:
            print(f"  [{datetime.now().strftime('%H:%M:%S')}] Vérification des mails...", flush=True)
            mails = self.fetch_deck_mails()
            if mails:
                print(f"  {len(mails)} nouveau(x) mail(s) trouvé(s)", flush=True)
                for folder, mid, msg in mails:
                    try:
                        self.process_mail(folder, mid, msg)
                    except Exception as e:
                        print(f"  Erreur traitement : {e}", flush=True)
            else:
                print(f"  Aucun nouveau mail.", flush=True)
            time.sleep(self.interval)


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    cfg = load_config()
    watcher = GmailWatcher(cfg)
    try:
        watcher.run()
    except KeyboardInterrupt:
        print('\nDeck Watcher arrêté.')

if __name__ == '__main__':
    main()
