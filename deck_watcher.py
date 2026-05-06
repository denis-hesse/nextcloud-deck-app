#!/usr/bin/env python3
import sys, os, json, time, email, email.header, email.utils
import imaplib, urllib.request, urllib.parse, re, tempfile
from datetime import datetime, timedelta

print("=== DECK WATCHER DEMARRE ===", flush=True)

PROCESSED_FILE = '/tmp/deck_processed.json'

def load_config():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    cfg = {
        'gmail': {
            'email': os.environ.get('GMAIL_EMAIL', ''),
            'app_password': os.environ.get('GMAIL_APP_PASSWORD', ''),
            'label': os.environ.get('GMAIL_LABEL', 'DECK'),
            'check_interval_seconds': int(os.environ.get('CHECK_INTERVAL', '30'))
        },
        'anthropic': {'api_key': os.environ.get('ANTHROPIC_API_KEY', '')},
        'nextcloud': {
            'url': os.environ.get('NEXTCLOUD_URL', ''),
            'user': os.environ.get('NEXTCLOUD_USER', ''),
            'password': os.environ.get('NEXTCLOUD_PASSWORD', '')
        },
        'proxy_port': int(os.environ.get('PORT', '8765')),
        'app_url': os.environ.get('APP_URL', '')
    }
    return cfg

def load_processed():
    """Lire les mids traités depuis le fichier."""
    if os.path.exists(PROCESSED_FILE):
        try:
            with open(PROCESSED_FILE) as f:
                return set(str(x) for x in json.load(f))
        except:
            pass
    return set()

def save_processed(processed_set):
    """Sauvegarder les mids traités dans le fichier."""
    try:
        with open(PROCESSED_FILE, 'w') as f:
            json.dump(list(processed_set)[-500:], f)
    except Exception as e:
        print(f"  Erreur sauvegarde : {e}", flush=True)

def decode_header(value):
    if not value: return ''
    parts = email.header.decode_header(value)
    result = []
    for part, enc in parts:
        if isinstance(part, bytes):
            result.append(part.decode(enc or 'utf-8', errors='replace'))
        else:
            result.append(part)
    return ' '.join(result)

def get_last_message_body(full_body):
    """Extrait uniquement le dernier message en ignorant l'historique cité."""
    lines = full_body.split('\n')
    last_msg_lines = []
    for line in lines:
        stripped = line.strip()
        # Arrêter à la première ligne citée (>, De :, From:, Le ... a écrit, On ... wrote)
        if (stripped.startswith('>') or
            stripped.startswith('De :') or
            stripped.startswith('From:') or
            stripped.startswith('Le ') and ' a écrit' in stripped or
            stripped.startswith('On ') and ' wrote' in stripped or
            stripped.startswith('-----') or
            stripped.startswith('_____')):
            break
        last_msg_lines.append(line)
    result = '\n'.join(last_msg_lines).strip()
    return result if result else full_body  # Fallback si extraction vide

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

def mail_to_pdf(subject, sender, date_str, body, attachments):
    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>body{{font-family:Arial,sans-serif;font-size:13px;margin:40px;color:#333;}}
.header{{border-bottom:2px solid #0082C9;padding-bottom:12px;margin-bottom:20px;}}
.header h2{{color:#0082C9;margin:0 0 8px 0;}}.meta{{font-size:12px;color:#666;line-height:1.8;}}
.body{{white-space:pre-wrap;line-height:1.6;}}</style></head><body>
<div class="header"><h2>{subject}</h2>
<div class="meta"><strong>De :</strong> {sender}<br><strong>Date :</strong> {date_str}</div></div>
<div class="body">{body}</div></body></html>"""
    try:
        import pdfkit
        wk_paths = ['/usr/bin/wkhtmltopdf','C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe']
        config = None
        for p in wk_paths:
            if os.path.exists(p):
                config = pdfkit.configuration(wkhtmltopdf=p)
                break
        safe = re.sub(r'[^\w\s-]', '', subject)[:40].strip().replace(' ', '_')
        path = os.path.join(tempfile.gettempdir(), f'_mail_{safe}.pdf')
        opts = {'encoding': 'UTF-8', 'quiet': ''}
        if config:
            pdfkit.from_string(html, path, configuration=config, options=opts)
        else:
            pdfkit.from_string(html, path, options=opts)
        return path
    except Exception as e:
        print(f"  (PDF indisponible : {e})", flush=True)
        safe = re.sub(r'[^\w\s-]', '', subject)[:40].strip().replace(' ', '_')
        path = os.path.join(tempfile.gettempdir(), f'_mail_{safe}.html')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(html)
        return path

def ask_claude(api_key, boards, subject, sender, date_str, body, full_body=None):
    boards_list = '\n'.join([f'- {b["title"]} (id:{b["id"]})' for b in boards])
    prompt = f"""Tu es un assistant qui aide à organiser des emails dans Nextcloud Deck.

Email reçu :
De : {sender}
Objet : {subject}
Dernier message (pour analyse) :
{body[:2000]}

Texte intégral (pour paragraphe Mail avec historique) :
{(full_body or body)[:3000]}

Tableaux disponibles :
{boards_list}

RÈGLES STRICTES :
- Ne jamais mentionner @deck, Nextcloud, outils techniques, coordonnées de l'expéditeur
- Si mail de test ou vide : description = "**Résumé**\\nMail de test."
- Si aucun tableau ne correspond clairement : boardId = null, boardTitle = ""
- Description proportionnelle au contenu réel

Ta mission :
1. Choisir le tableau le plus pertinent ou null si incertain
2. Titre court (max 80 caractères) — supprimer "Re:", "Fw:", "Fwd:" — ne pas répéter l'objet mot pour mot
3. Description structurée :
   - Première ligne TOUJOURS : "{subject} — {date_str}" (sans label, sans gras)
   - **Résumé** : synthèse unique du contenu, maximum 600 caractères (souvent moins si peu d'informations). Si mail de test : "Mail de test." uniquement.
   - **Actions à suivre** : toujours présent. Si actions identifiées : liste avec bullet points (• action). Sinon : "Pas d'action identifiée."
   - **Mail avec historique** : coller ici le texte intégral du mail (corps complet)

Réponds UNIQUEMENT en JSON :
{{
  "boardId": <id ou null>,
  "boardTitle": "<nom ou vide>",
  "titre": "<titre sans Re:/Fw:/Fwd:>",
  "description": "{subject} — {date_str}\\n\\n**Résumé**\\n<résumé max 600 caractères>\\n\\n**Actions à suivre**\\n<actions ou Pas d'action identifiée.>\\n\\n**Mail avec historique**\\n<texte intégral>"
}}"""
    payload = json.dumps({
        "model": "claude-sonnet-4-5",
        "max_tokens": 4000,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()
    req = urllib.request.Request(
        'https://api.anthropic.com/v1/messages',
        data=payload,
        headers={'Content-Type':'application/json','x-api-key':api_key,'anthropic-version':'2023-06-01'},
        method='POST'
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        resp = json.loads(r.read())
    text = resp['content'][0]['text'].strip()
    text = re.sub(r'^```json\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    return json.loads(text)

def get_boards(nc_url, user, password):
    import base64
    auth = base64.b64encode(f'{user}:{password}'.encode()).decode()
    req = urllib.request.Request(
        nc_url.rstrip('/') + '/index.php/apps/deck/api/v1.0/boards?details=true',
        headers={'Authorization':f'Basic {auth}','OCS-APIRequest':'true','Accept':'application/json'}
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

def send_prefill(app_url, port, data):
    base = app_url or f'http://localhost:{port}'
    payload = json.dumps(data).encode()
    req = urllib.request.Request(
        f'{base}/prefill',
        data=payload,
        headers={'Content-Type':'application/json'},
        method='POST'
    )
    urllib.request.urlopen(req, timeout=5)
    print(f"  Formulaire prêt.", flush=True)

STARTUP_TIME = datetime.now()

def fetch_deck_mails(cfg, processed):
    """Récupère les mails envoyés avec @deck non encore traités."""
    try:
        mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
        mail.login(cfg['gmail']['email'], cfg['gmail']['app_password'])

        status, _ = mail.select('"[Gmail]/Messages envoy&AOk-s"')
        if status != 'OK':
            print("  Impossible d'accéder aux Messages envoyés", flush=True)
            mail.logout()
            return []

        # Chercher mails depuis hier
        since = (datetime.now() - timedelta(hours=1)).strftime("%d-%b-%Y")
        _, data = mail.search(None, f'SINCE {since}')
        mail_ids = data[0].split()
        print(f"  {len(mail_ids)} mail(s) trouvés depuis hier", flush=True)

        new_mails = []

        for mid in mail_ids:
            mid_str = mid.decode() if isinstance(mid, bytes) else str(mid)

            # Déjà traité ?
            if mid_str in processed:
                continue

            # Récupérer le mail
            _, msg_data = mail.fetch(mid, '(RFC822)')
            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)

            # Vérifier @deck dans corps ou sujet
            body = get_body(msg)
            last_body = get_last_message_body(body)
            full_body = body
            subject = decode_header(msg.get('Subject', ''))
            if '@deck' not in body.lower() and '@deck' not in subject.lower():
                processed.add(mid_str)
                save_processed(processed)
                continue

            print(f"  @deck trouvé : {subject} (mid={mid_str})", flush=True)
            new_mails.append((mid_str, msg))

        mail.logout()
        return new_mails
    except Exception as e:
        print(f"  Erreur Gmail : {e}", flush=True)
        return []

def process_mail(cfg, mid_str, msg, processed):
    subject = decode_header(msg.get('Subject', '(sans objet)'))
    sender = decode_header(msg.get('From', ''))
    date_str_raw = msg.get('Date', '')
    try:
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(date_str_raw)
        date_str = dt.strftime('%d/%m/%Y %H:%M')
    except:
        date_str = date_str_raw
    full_body = get_body(msg)
    last_body = get_last_message_body(full_body)
    attachments = get_attachments(msg)

    print(f"  📧 {subject}", flush=True)

    # Marquer immédiatement comme traité pour éviter doublons
    processed.add(mid_str)
    save_processed(processed)

    nc = cfg['nextcloud']
    print("  Récupération tableaux...", flush=True)
    boards = get_boards(nc['url'], nc['user'], nc['password'])

    print("  Analyse Claude...", flush=True)
    result = ask_claude(cfg['anthropic']['api_key'], boards, subject, sender, date_str, last_body, full_body=full_body)
    print(f"  → Tableau : {result.get('boardTitle','')}", flush=True)
    print(f"  → Titre   : {result['titre']}", flush=True)

    print("  Génération PDF...", flush=True)
    pdf_path = mail_to_pdf(subject, sender, date_str, full_body, attachments)
    print(f"  → PDF : {pdf_path}", flush=True)

    # Sauvegarder les pièces jointes en fichiers temporaires
    attachment_paths = [pdf_path]
    for att in attachments:
        try:
            safe_name = re.sub(r'[^\w\.\-]', '_', att['name'])
            att_path = os.path.join(tempfile.gettempdir(), f'att_{safe_name}')
            with open(att_path, 'wb') as f:
                f.write(att['data'])
            attachment_paths.append(att_path)
            print(f"  → Pièce jointe : {att['name']}", flush=True)
        except Exception as e:
            print(f"  Erreur pièce jointe {att['name']} : {e}", flush=True)

    send_prefill(cfg.get('app_url',''), cfg['proxy_port'], {
        'subject': subject,
        'mail_date': date_str,
        'boardId': result.get('boardId'),
        'titre': result['titre'],
        'description': result.get('description', ''),
        'pdf': pdf_path,
        'attachments': attachment_paths,
        'mail_mid': mid_str,
        'mail_folder': 'SENT',
        'mail_email': cfg['gmail']['email'],
        'mail_password': cfg['gmail']['app_password'],
        'mail_label': cfg['gmail']['label']
    })

def main():
    cfg = load_config()
    interval = cfg['gmail']['check_interval_seconds']

    print(f"  Deck Watcher démarré", flush=True)
    print(f"  Surveillance : mails envoyés contenant @deck", flush=True)
    print(f"  Intervalle   : toutes les {interval}s", flush=True)
    print(f"  APP_URL : {cfg.get('app_url','NON DEFINI')}", flush=True)
    print(f"  Ctrl+C pour arrêter\n", flush=True)

    while True:
        print(f"  [{datetime.now().strftime('%H:%M:%S')}] Vérification...", flush=True)
        # Recharger processed à chaque cycle
        processed = load_processed()
        mails = fetch_deck_mails(cfg, processed)
        if mails:
            print(f"  {len(mails)} nouveau(x) mail(s)", flush=True)
            for mid_str, msg in mails:
                try:
                    process_mail(cfg, mid_str, msg, processed)
                except Exception as e:
                    print(f"  Erreur : {e}", flush=True)
        else:
            print(f"  Aucun nouveau mail.", flush=True)
        time.sleep(interval)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nDeck Watcher arrêté.')
