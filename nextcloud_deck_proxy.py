#!/usr/bin/env python3
"""
Proxy local pour Nextcloud Deck
Lance ce script puis ouvre http://localhost:8765 dans Chrome.
Usage : python nextcloud_deck_proxy.py
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import os
import urllib.request, urllib.error, urllib.parse
import json, sys

PORT = 8765

HTML = r"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Nextcloud Deck v2</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&family=DM+Mono&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --blue: #0082C9; --blue-d: #005f96;
    --bg: #f0f2f5; --surface: #fff; --surface2: #f7f8fa;
    --border: #e2e5ea; --text: #1a1d23; --muted: #6b7280; --hint: #9ca3af;
    --ok: #16a34a; --ok-bg: #f0fdf4; --ok-b: #bbf7d0;
    --err: #dc2626; --err-bg: #fef2f2; --err-b: #fecaca;
    --info: #1d4ed8; --info-bg: #eff6ff; --info-b: #bfdbfe;
    --r: 10px; --rs: 6px;
  }
  body { font-family:'DM Sans',sans-serif; background:var(--bg); color:var(--text); margin:0; min-height:100vh; }
  .app-layout { display:block; max-width:560px; }
  .wrap { padding:1.5rem 1rem; }
  .history-panel { position:fixed; top:0; left:560px; width:336px;  background:var(--surface); border-left:2px solid var(--blue); display:flex; flex-direction:column; overflow:hidden; box-sizing:border-box; z-index:100; min-width:200px; max-width:600px; }
  .history-list { flex:1; overflow-y:auto; overflow-x:hidden; padding:8px; min-height:0; }
  .resize-handle { position:absolute; left:0; top:0; width:4px; height:100%; cursor:ew-resize; background:transparent; z-index:101; }
  .resize-handle:hover { background:var(--blue); opacity:0.3; }

  .history-header { display:flex; align-items:center; justify-content:space-between; padding:1rem; border-bottom:1px solid var(--border); font-size:13px; font-weight:600; color:var(--muted); text-transform:uppercase; letter-spacing:.05em; }
  .history-count { background:#0082C9; color:white; border-radius:10px; padding:2px 8px; font-size:11px; font-weight:600; }
  .history-empty { font-size:12px; color:var(--hint); text-align:center; padding:2rem 1rem; }
  .history-item { padding:8px 10px; border-radius:var(--rs); margin-bottom:4px; background:var(--surface2); border:1px solid var(--border); }
  .history-date { font-size:11px; color:var(--hint); font-family:'DM Mono',monospace; margin-bottom:2px; }
  .history-titre { font-size:12px; color:var(--text); line-height:1.4; overflow:hidden; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; }
  .hdr { display:flex; align-items:center; gap:12px; margin-bottom:1.5rem; }
  .logo { width:38px; height:38px; background:var(--blue); border-radius:10px; display:flex; align-items:center; justify-content:center; flex-shrink:0; }
  .hdr h1 { font-size:20px; font-weight:600; }
  .hdr p { font-size:13px; color:var(--muted); margin-top:2px; }
  .card { background:var(--surface); border:1px solid var(--border); border-radius:var(--r); padding:1.25rem; margin-bottom:1rem; }
  .sect { font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:.08em; color:var(--muted); margin-bottom:1rem; }
  .sect-row { display:flex; align-items:center; justify-content:space-between; margin-bottom:1rem; }
  .sect-row .sect { margin-bottom:0; }
  .g2 { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-bottom:12px; }
  .g3 { display:grid; grid-template-columns:1fr 1fr 1fr; gap:10px; }
  .f { display:flex; flex-direction:column; gap:5px; margin-bottom:12px; }
  .f:last-child { margin-bottom:0; }
  .lbl { font-size:12px; font-weight:500; color:var(--muted); }
  input,select,textarea { font-family:'DM Sans',sans-serif; font-size:14px; color:var(--text); background:var(--surface2); border:1px solid var(--border); border-radius:var(--rs); padding:8px 11px; width:100%; outline:none; transition:border-color .15s,box-shadow .15s; -webkit-appearance:none; appearance:none; }
  input:focus,select:focus,textarea:focus { border-color:var(--blue); box-shadow:0 0 0 3px rgba(0,130,201,.12); background:#fff; }
  textarea { min-height:192px; resize:vertical; line-height:1.5; }
  select { background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%236b7280' d='M6 8L1 3h10z'/%3E%3C/svg%3E"); background-repeat:no-repeat; background-position:right 10px center; padding-right:28px; cursor:pointer; }
  .fzone { display:flex; align-items:center; gap:10px; padding:9px 12px; border:1.5px dashed var(--border); border-radius:var(--rs); cursor:pointer; background:var(--surface2); transition:border-color .15s,background .15s; }
  .fzone:hover { border-color:var(--blue); background:#f0f7fd; }
  .fzone span { font-size:13px; color:var(--muted); }
  .fname { font-size:12px; color:var(--hint); margin-top:4px; font-family:'DM Mono',monospace; }
  .row { display:flex; align-items:center; gap:8px; margin-top:10px; flex-wrap:wrap; }
  .dot { width:8px; height:8px; border-radius:50%; background:#d1d5db; flex-shrink:0; transition:background .2s; }
  .dot.ok { background:#22c55e; } .dot.ko { background:#ef4444; }
  .plabel { font-size:12px; color:var(--muted); }
  .btn { font-family:'DM Sans',sans-serif; cursor:pointer; border-radius:var(--rs); transition:all .15s; }
  .btn-sm { font-size:12px; font-weight:500; padding:5px 10px; border:1px solid var(--border); background:var(--surface); color:var(--muted); }
  .btn-sm:hover { background:var(--surface2); }
  .btn-primary { font-size:14px; font-weight:600; padding:10px 24px; border:none; background:var(--blue); color:#fff; }
  .btn-primary:hover { background:var(--blue-d); }
  .btn-primary:active { transform:scale(.98); }
  .btn-primary:disabled { background:#9ca3af; cursor:not-allowed; transform:none; }
  .btn-save { font-size:13px; font-weight:500; padding:7px 16px; border:none; background:var(--blue); color:#fff; }
  .btn-save:hover { background:var(--blue-d); }
  .btn-reset { font-size:14px; padding:10px 18px; border:1px solid var(--border); background:transparent; color:var(--muted); }
  .btn-reset:hover { background:var(--surface2); }
  .actions { display:flex; gap:10px; margin-top:1rem; align-items:center; }
  .status { display:none; padding:10px 14px; border-radius:var(--rs); font-size:13px; margin-top:12px; line-height:1.5; }
  .status.ok     { display:block; background:var(--ok-bg);   color:var(--ok);   border:1px solid var(--ok-b); }
  .status.err    { display:block; background:var(--err-bg);  color:var(--err);  border:1px solid var(--err-b); }
  .status.loading{ display:block; background:var(--info-bg); color:var(--info); border:1px solid var(--info-b); }
  .spin { display:inline-block; width:12px; height:12px; border:2px solid currentColor; border-top-color:transparent; border-radius:50%; animation:spin .6s linear infinite; margin-right:6px; vertical-align:middle; }
  @keyframes spin { to { transform:rotate(360deg); } }
  .note { font-size:11px; color:var(--hint); margin-top:6px; }
  details summary { font-size:12px; color:var(--muted); cursor:pointer; user-select:none; margin-bottom:4px; }
  details[open] summary { margin-bottom:12px; }
  .saved-badge { font-size:11px; background:var(--ok-bg); color:var(--ok); border:1px solid var(--ok-b); border-radius:4px; padding:2px 7px; margin-left:6px; }
  .tags-wrap { display:flex; flex-wrap:wrap; gap:6px; margin-top:4px; }
  .tag { display:inline-flex; align-items:center; gap:5px; padding:4px 10px; border-radius:20px; font-size:12px; font-weight:500; cursor:pointer; border:2px solid transparent; transition:all .15s; }
  .tag.selected { border-color: rgba(0,0,0,0.25); box-shadow: 0 0 0 2px rgba(0,0,0,0.15); }
  .tag-dot { width:8px; height:8px; border-radius:50%; background:currentColor; opacity:0.7; }
</style>
</head>
<body>
<div class="app-layout">
<div class="wrap">

  <div class="hdr">
    <div class="logo">
      <svg width="22" height="22" viewBox="0 0 24 24" fill="white">
        <rect x="3" y="4" width="5" height="16" rx="1.5"/>
        <rect x="9.5" y="4" width="5" height="10" rx="1.5"/>
        <rect x="16" y="4" width="5" height="13" rx="1.5"/>
      </svg>
    </div>
    <div><h1>Nextcloud Deck</h1><p>Créer une carte</p></div>
  </div>

  <!-- Connexion -->
  <div class="card">
    <details id="conn-details">
      <summary>
        Connexion
        <span class="saved-badge" id="saved-badge" style="display:none">identifiants sauvegardés</span>
      </summary>
      <div class="g3">
        <div class="f">
          <label class="lbl">URL instance</label>
          <input type="text" id="url" value="https://switchcompetences.cloud.in-cubes.com"/>
        </div>
        <div class="f">
          <label class="lbl">Utilisateur</label>
          <input type="text" id="user" placeholder="identifiant"/>
        </div>
        <div class="f">
          <label class="lbl">Mot de passe</label>
          <input type="password" id="pass" placeholder="mot de passe ou token"/>
        </div>
      </div>
      <div class="row">
        <button class="btn btn-save" onclick="saveAndConnect()">Enregistrer et connecter</button>
        <span class="dot" id="dot"></span>
        <span class="plabel" id="plabel">non connecté</span>
      </div>
    </details>
  </div>


  <div class="card">
    
    <div class="g2">
      <div class="f">
        <label class="lbl">Tableau (Board)</label>
        <select id="board" onchange="onBoardChange()"><option value="">— sélectionner —</option></select>
      </div>
      <div class="f">
        <label class="lbl">Liste (Stack)</label>
        <select id="stack"><option value="">— sélectionner —</option></select>
      </div>
    </div>
    <div class="note" id="bstatus"></div>
  </div>

  <!-- Carte -->
  <div class="card">
    
    <div class="f"><label class="lbl">Titre</label><input type="text" id="title" placeholder="Titre de la carte..."/></div>
    <div class="f"><label class="lbl">Description</label><textarea id="desc" placeholder="Description (optionnel)..."></textarea></div>
    <div class="f" id="tags-field">
      
      <div class="tags-wrap" id="tags-wrap"></div>
    </div>
    <div class="g2">
      <div class="f" id="users-field">
        <label class="lbl">Assigner à</label>
        <select id="assignee"><option value="">— aucun —</option></select>
      </div>
      <div class="f"><label class="lbl">Date d'échéance</label><input type="date" id="due"/></div>
    </div>
    <div class="f">
      <label class="lbl">Fichier joint</label>
      <label class="fzone" for="file">
        <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M14 8l-6 6a4 4 0 01-5.66-5.66l6-6a2.5 2.5 0 013.54 3.54l-6.01 6a1 1 0 01-1.42-1.42l5.5-5.49" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg>
        <span>Ajouter un fichier</span>
        <input type="file" id="file" style="display:none" onchange="updateFile(this)"/>
      </label>
      <div class="fname" id="fname">Aucun fichier sélectionné</div>

    </div>
  </div>

  <div class="actions">
    <button class="btn btn-primary" id="submit" onclick="createCard()">Créer la carte</button>

    <button class="btn btn-reset" style="color:var(--err);border-color:var(--err-b);" onclick="excludeMail()">Exclure</button>
  </div>
  <div class="status" id="status"></div>
</div>

<script>
const PROXY='/proxy';
const LS_USER='nd_user', LS_PASS='nd_pass';
let selectedTagId = null;
let availableTags = [];

function purl(t){return PROXY+'?url='+encodeURIComponent(t);}
function ncurl(){return document.getElementById('url').value.trim().replace(/\/$/,'');}
function creds(){return{user:document.getElementById('user').value.trim(),pass:document.getElementById('pass').value.trim()};}
function auth(u,p){return'Basic '+btoa(unescape(encodeURIComponent(u+':'+p)));}
function hdrs(u,p){return{'Authorization':auth(u,p),'OCS-APIRequest':'true','Accept':'application/json','Content-Type':'application/json'};}
function updateFile(i){document.getElementById('fname').textContent=i.files[0]?i.files[0].name:'Aucun fichier sélectionné';}

function saveCredentials(){
  const{user,pass}=creds();
  if(user)localStorage.setItem(LS_USER,user);
  if(pass)localStorage.setItem(LS_PASS,pass);
}

function loadCredentials(){
  const user=localStorage.getItem(LS_USER)||'';
  const pass=localStorage.getItem(LS_PASS)||'';
  if(user)document.getElementById('user').value=user;
  if(pass)document.getElementById('pass').value=pass;
  if(user&&pass)document.getElementById('saved-badge').style.display='inline';
}

async function checkConnection(){
  const{user,pass}=creds();
  const dot=document.getElementById('dot'),lbl=document.getElementById('plabel');
  if(!user||!pass){dot.className='dot ko';lbl.textContent='identifiants manquants';return false;}
  try{
    const r=await fetch(purl(ncurl()+'/index.php/apps/deck/api/v1.0/boards?details=true'),{headers:hdrs(user,pass)});
    if(r.ok){dot.className='dot ok';lbl.textContent='connecté ✓';return true;}
    else{dot.className='dot ko';lbl.textContent='erreur HTTP '+r.status;return false;}
  }catch(e){dot.className='dot ko';lbl.textContent='proxy injoignable';return false;}
}

async function saveAndConnect(){
  saveCredentials();
  document.getElementById('saved-badge').style.display='inline';
  const ok=await checkConnection();
  if(ok)loadBoards();
}

async function loadBoards(){
  const{user,pass}=creds();
  const st=document.getElementById('bstatus');
  st.textContent='';
  try{
    const r=await fetch(purl(ncurl()+'/index.php/apps/deck/api/v1.0/boards?details=true'),{headers:hdrs(user,pass)});
    if(!r.ok)throw new Error('HTTP '+r.status);
    const boards=await r.json();
    const sel=document.getElementById('board');
    sel.innerHTML='<option value="">— sélectionner —</option>';
    boards.forEach(b=>{
      const o=document.createElement('option');
      o.value=b.id;
      o.textContent=b.title;
      // Stocker les labels du board dans data-labels
      o.dataset.labels=JSON.stringify(b.labels||[]);
      o.dataset.users=JSON.stringify(b.users||[]);
      sel.appendChild(o);
    });
    st.textContent='';
    document.getElementById('conn-details').removeAttribute('open');
  }catch(e){st.textContent='Erreur : '+e.message;}
}

async function onBoardChange(){
  await loadStacks();
  loadTagsFromBoard();
  loadUsersFromBoard();
}

async function loadStacks(){
  const bid=document.getElementById('board').value;
  if(!bid)return;
  const{user,pass}=creds();
  try{
    const r=await fetch(purl(ncurl()+'/index.php/apps/deck/api/v1.0/boards/'+bid+'/stacks'),{headers:hdrs(user,pass)});
    if(!r.ok)return;
    const stacks=await r.json();
    const sel=document.getElementById('stack');
    sel.innerHTML='<option value="">— sélectionner —</option>';
    let beatriceIdx=-1;
    stacks.forEach((s,i)=>{
      const o=document.createElement('option');
      o.value=s.id;
      o.textContent=s.title;
      sel.appendChild(o);
      if(s.title.toLowerCase().includes('béatrice')||s.title.toLowerCase().includes('beatrice'))beatriceIdx=i+1;
    });
    // Sélectionner automatiquement si une seule liste, sinon Béatrice par défaut
    if(stacks.length===1){
      sel.selectedIndex=1;
      document.getElementById('bstatus').textContent='';
    } else if(beatriceIdx>0){
      sel.selectedIndex=beatriceIdx;
      document.getElementById('bstatus').textContent='';
    }
  }catch(e){}
}

function loadTagsFromBoard(){
  const sel=document.getElementById('board');
  const opt=sel.options[sel.selectedIndex];
  if(!opt||!opt.dataset.labels)return;
  try{
    availableTags=JSON.parse(opt.dataset.labels);
  }catch(e){availableTags=[];}
  renderTags();
}

function loadUsersFromBoard(){
  const sel=document.getElementById('board');
  const opt=sel.options[sel.selectedIndex];
  if(!opt||!opt.dataset.users)return;
  try{
    const users=JSON.parse(opt.dataset.users);
    const asel=document.getElementById('assignee');
    asel.innerHTML='<option value="">— aucun —</option>';
    users.forEach(u=>{
      const o=document.createElement('option');
      o.value=u.uid;
      o.textContent=u.displayname;
      asel.appendChild(o);
    });
    // users toujours visible
  }catch(e){}
}

function renderTags(){
  const wrap=document.getElementById('tags-wrap');
  const field=document.getElementById('tags-field');
  wrap.innerHTML='';
  selectedTagId=null;

  if(!availableTags||availableTags.length===0){
    wrap.innerHTML='<span style="font-size:12px;color:var(--hint)">Aucun tag dans ce tableau</span>';
    return;
  }
  // tags toujours visible

  // Chercher "En cours" pour le sélectionner par défaut
  let defaultTag=availableTags.find(t=>t.title.toLowerCase().includes('en cours'));

  availableTags.forEach(tag=>{
    const color=tag.color?'#'+tag.color.replace('#',''):'#888';
    const div=document.createElement('div');
    div.className='tag';
    div.dataset.id=tag.id;
    div.style.background=color+'22';
    div.style.color=color;
    div.innerHTML='<span class="tag-dot" style="background:'+color+'"></span>'+tag.title;
    div.onclick=()=>selectTag(tag.id);
    wrap.appendChild(div);
    if(defaultTag&&tag.id===defaultTag.id){
      selectTag(tag.id);
    }
  });

  // Si pas de "En cours", afficher sans sélection
  if(!defaultTag)selectedTagId=null;
}

function selectTag(id){
  selectedTagId=id;
  document.querySelectorAll('.tag').forEach(el=>{
    el.classList.toggle('selected',el.dataset.id==id);
  });
}

async function createCard(){
  const{user,pass}=creds();
  const bid=document.getElementById('board').value,sid=document.getElementById('stack').value;
  const title=document.getElementById('title').value.trim();
  const desc=document.getElementById('desc').value.trim();
  const due=document.getElementById('due').value;
  const fileInput=document.getElementById('file');
  const st=document.getElementById('status'),btn=document.getElementById('submit');
  if(!bid||!sid||!title){st.className='status err';st.textContent='Tableau, liste et titre sont requis.';return;}
  btn.disabled=true;st.className='status loading';st.innerHTML='<span class="spin"></span>Création de la carte...';
  try{
    const body={title,description:desc||''};
    if(due)body.duedate=new Date(due).toISOString();
    const r=await fetch(purl(ncurl()+'/index.php/apps/deck/api/v1.0/boards/'+bid+'/stacks/'+sid+'/cards'),{method:'POST',headers:hdrs(user,pass),body:JSON.stringify(body)});
    if(!r.ok)throw new Error('HTTP '+r.status);
    const card=await r.json();

    // Assigner un utilisateur à la carte
    const assignee=document.getElementById('assignee').value;
    if(assignee){
      await fetch('/assignuser',{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({
          ncurl:ncurl(), user:creds().user, pass:creds().pass,
          boardId:bid, stackId:sid, cardId:card.id, userId:assignee
        })
      });
    }

    // Assigner le tag via endpoint dédié du proxy local (évite preflight CORS)
    if(selectedTagId){
      const tr = await fetch('/assignlabel', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({
          ncurl: ncurl(), user: creds().user, pass: creds().pass,
          boardId: bid, stackId: sid, cardId: card.id,
          labelId: parseInt(selectedTagId)
        })
      });
      console.log('Tag status:', tr.status);
    }

    // Pièce jointe via endpoint web (affichage inline)
    if(fileInput.files[0]){
      st.innerHTML='<span class="spin"></span>Envoi du fichier joint...';
      const fd=new FormData();
      fd.append('cardId', card.id);
      fd.append('type','file');
      fd.append('file',fileInput.files[0]);
      const ar=await fetch(purl(ncurl()+'/index.php/apps/deck/cards/'+card.id+'/attachment'),{
        method:'POST',headers:{'Authorization':auth(user,pass),'OCS-APIRequest':'true','requesttoken': ''},body:fd
      });
      if(!ar.ok){const e=await ar.text();throw new Error('Pièce jointe : HTTP '+ar.status+' — '+e.substring(0,80));}
    }

    st.className='status ok';st.textContent='Carte "'+card.title+'" créée avec succès !';btn.disabled=false;
    // Notifier le proxy et charger le mail suivant
    try {
      const pf = await fetch('/get-prefill').then(r=>r.json());
      const mid = pf.mail_mid || '';
      const res = await fetch('/mark-processed',{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({mid, action: 'Créé', titre: title})
      }).then(r=>r.json());
      if(res.next){
        // Mail suivant disponible — recharger la page
        setTimeout(()=>{ window.location.reload(); }, 2000);
        st.textContent='Carte créée ! Chargement du mail suivant...';
      } else {
        // File vide — réinitialiser le formulaire
        setTimeout(()=>{ resetForm(); st.className='status'; }, 2000);
        st.textContent='Carte créée ! Aucun autre mail en attente.';
      }
    } catch(e){
      setTimeout(()=>window.close(), 3000);
    }
  }catch(e){st.className='status err';st.textContent='Erreur : '+e.message;btn.disabled=false;}
}

function resetForm(){
  ['title','desc','due'].forEach(id=>document.getElementById(id).value='');
  document.getElementById('file').value='';
  document.getElementById('fname').textContent='Aucun fichier sélectionné';
  document.getElementById('status').className='status';
  document.getElementById('board').value='';
  document.getElementById('stack').innerHTML='<option value="">— sélectionner —</option>';
  document.getElementById('tags-field').style.display='none';
  document.getElementById('assignee').innerHTML='<option value="">— aucun —</option>';
  document.getElementById('tags-wrap').innerHTML='';
  selectedTagId=null;
}

// Vérification silencieuse d'un nouveau mail toutes les 15s (sans rafraîchir)
let pollingActive = true;

// Ajuster hauteur du panneau log à la hauteur du formulaire
function adjustPanelHeight(){
  const wrap = document.querySelector('.wrap');
  const panel = document.getElementById('history-panel');
  if(wrap && panel){
    const h = wrap.scrollHeight;
    panel.style.height = Math.min(h, window.innerHeight) + 'px';
  }
}
window.addEventListener('resize', adjustPanelHeight);
setInterval(adjustPanelHeight, 1000);

// Poignée de redimensionnement du panneau historique
(function(){
  const handle = document.getElementById('resize-handle');
  const panel = document.getElementById('history-panel');
  if(!handle || !panel) return;
  let startX, startW;
  handle.addEventListener('mousedown', e=>{
    startX = e.clientX;
    startW = panel.offsetWidth;
    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', ()=> document.removeEventListener('mousemove', onMove));
    e.preventDefault();
  });
  function onMove(e){
    const diff = startX - e.clientX;
    const newW = Math.min(600, Math.max(200, startW + diff));
    panel.style.width = newW + 'px';
  }
})();

async function checkNewMail(){
  if(!pollingActive) return;
  try {
    const r = await fetch('/has-prefill').then(res=>res.json());
    if(r.has){
      document.title = '📧 Nouveau mail — Nextcloud Deck';
      pollingActive = false;
      await loadNewMail();
    }
  } catch(e){}
}
setInterval(checkNewMail, 5000);

async function excludeMail(){
  const st = document.getElementById('status');
  st.className = 'status loading';
  st.innerHTML = '<span class="spin"></span>Exclusion...';
  try {
    const pf = await fetch('/get-prefill').then(r=>r.json());
    const mid = pf.mail_mid || '';
    await fetch('/mark-processed', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({mid: mid, titre: pf.titre || 'Mail exclu', action: 'Exclu'})
    });
    st.className = 'status ok';
    st.textContent = 'Mail exclu.';
    setTimeout(()=>{ resetForm(); st.className='status'; pollingActive = true; }, 1500);
  } catch(e){
    st.className = 'status err';
    st.textContent = 'Erreur : ' + e.message;
  }
}

async function loadNewMail(){
  pollingActive = false;
  document.title = 'Nextcloud Deck';
  try {
    const data = await fetch('/get-prefill').then(r=>r.json());
    if(data.titre) document.getElementById('title').value = data.titre;
    if(data.description) document.getElementById('desc').value = data.description;
    if(data.pdf) prefillPdf(data.pdf);
    if(data.boardId){
      await loadBoards();
      setTimeout(()=>{
        const sel = document.getElementById('board');
        for(let i=0; i<sel.options.length; i++){
          if(sel.options[i].value == data.boardId){
            sel.selectedIndex = i;
            onBoardChange();
            break;
          }
        }
      }, 1500);
    }
  } catch(e){ console.log('loadNewMail:', e); }
}

// Charger et rafraîchir l'historique toutes les 5 secondes
async function loadHistory(){
  try {
    const items = await fetch('/history').then(r=>r.json());
    const list = document.getElementById('history-list');
    const count = document.getElementById('history-count');
    count.textContent = items.length;
    if(items.length === 0){
      list.innerHTML = '<div class="history-empty">Aucun mail traité</div>';
      return;
    }
    list.innerHTML = items.slice().reverse().map(item=>`
      <div class="history-item">
        <div class="history-date">${item.date} — <span style="color:${item.action==='Exclu'?'var(--err)':'var(--ok)'};">${item.action||'Créé'}</span></div>
        <div class="history-titre" title="${item.titre}">${item.titre}</div>
      </div>
    `).join('');
  } catch(e){}
}
setInterval(loadHistory, 5000);

window.addEventListener('DOMContentLoaded',async()=>{
  adjustPanelHeight();
  loadHistory();
  // Charger la config serveur (variables d'environnement Railway)
  try {
    const cfg = await fetch('/config').then(r=>r.json());
    if(cfg.ncurl) document.getElementById('url').value = cfg.ncurl;
    if(cfg.user) document.getElementById('user').value = cfg.user;
    if(cfg.pass) document.getElementById('pass').value = cfg.pass;
    // Masquer le panneau connexion si tout est pré-rempli
    if(cfg.ncurl && cfg.user && cfg.pass){
      document.getElementById('saved-badge').style.display='inline';
    }
  } catch(e) {}
  loadCredentials();
  const ok=await checkConnection();
  if(ok){
    await loadBoards();
    // Récupérer les données pré-remplies depuis le proxy uniquement si disponibles
    try {
      const check = await fetch('/has-prefill').then(r=>r.json());
      if(check.has){
        const data = await fetch('/get-prefill').then(r=>r.json());
        if(data.titre) document.getElementById('title').value = data.titre;
        if(data.description) document.getElementById('desc').value = data.description;
        if(data.pdf) prefillPdf(data.pdf);
        if(data.boardId){
          setTimeout(()=>{
            const sel = document.getElementById('board');
            for(let i=0; i<sel.options.length; i++){
              if(sel.options[i].value == data.boardId){
                sel.selectedIndex = i;
                onBoardChange();
                break;
              }
            }
          }, 1500);
        }
      }
    } catch(e) { console.log('Pas de prefill:', e); }
  }
});

async function prefillPdf(pdfPath){
  try {
    const r = await fetch('/file?path=' + encodeURIComponent(pdfPath));
    if(!r.ok) return;
    const blob = await r.blob();
    const filename = pdfPath.split(/[\/\\]/).pop();
    const file = new File([blob], filename, {type: blob.type});
    const dt = new DataTransfer();
    dt.items.add(file);
    document.getElementById('file').files = dt.files;
    document.getElementById('fname').textContent = filename;

  } catch(e) { console.log('PDF prefill:', e); }
}
</script>
</div>
<!-- Panneau historique -->
<div class="history-panel" id="history-panel"><div class="resize-handle" id="resize-handle"></div>
  <div class="history-header">
    <span>Historique</span>
    <span class="history-count" id="history-count">0</span>
  </div>
  <div class="history-list" id="history-list">
    <div class="history-empty">Aucun mail traité</div>
  </div>
</div>
</div>
</body>
</html>"""


# Stockage en mémoire des données pré-remplies
prefill_data = {}
current_mid = ''  # Mid du mail en cours de traitement
prefill_queue = []  # File d'attente des mails à traiter
processed_mids = set()  # Mails traités partagés entre proxy et watcher
history_log = []  # Historique des mails traités

class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"  {self.command} {self.path[:80]}")

    def send_cors(self):
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Methods","GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers","Authorization, Content-Type, OCS-APIRequest, Accept")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors()
        self.send_header("Access-Control-Max-Age", "86400")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        if self.path in ('/', '/index.html'):
            body=HTML.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type','text/html; charset=utf-8')
            self.send_header('Content-Length',len(body))
            self.end_headers(); self.wfile.write(body)
        elif self.path.startswith('/proxy'):
            self._proxy('GET')
        elif self.path == '/config':
            self._get_config()
        elif self.path == '/history':
            self._get_history()
        elif self.path == '/get-processed':
            self._get_processed()
        elif self.path == '/clear-processed':
            self._clear_processed()
        elif self.path == '/has-prefill':
            self._has_prefill()
        elif self.path == '/get-prefill':
            self._get_prefill()
        elif self.path.startswith('/file'):
            self._serve_file()
        else:
            self.send_response(404); self.end_headers()

    def _get_config(self):
        cfg = {
            'ncurl': os.environ.get('NEXTCLOUD_URL', ''),
            'user': os.environ.get('NEXTCLOUD_USER', ''),
            'pass': os.environ.get('NEXTCLOUD_PASSWORD', '')
        }
        b = json.dumps(cfg).encode()
        self.send_response(200)
        self.send_cors()
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(b))
        self.end_headers()
        self.wfile.write(b)

    def _get_history(self):
        global history_log
        b=json.dumps(history_log).encode()
        self.send_response(200)
        self.send_cors()
        self.send_header('Content-Type','application/json')
        self.send_header('Content-Length',len(b))
        self.end_headers()
        self.wfile.write(b)

    def _get_processed(self):
        global processed_mids
        b=json.dumps(list(processed_mids)).encode()
        self.send_response(200)
        self.send_cors()
        self.send_header('Content-Type','application/json')
        self.send_header('Content-Length',len(b))
        self.end_headers()
        self.wfile.write(b)

    def _has_prefill(self):
        global prefill_data
        has = bool(prefill_data.get('titre')) and not prefill_data.get('_processed', False)
        b = json.dumps({'has': has, 'titre': prefill_data.get('titre','')}).encode()
        self.send_response(200)
        self.send_cors()
        self.send_header('Content-Type','application/json')
        self.send_header('Content-Length',len(b))
        self.end_headers()
        self.wfile.write(b)

    def _get_prefill(self):
        global prefill_data, current_mid
        data = dict(prefill_data)
        if 'mail_mid' not in data and current_mid:
            data['mail_mid'] = current_mid
        b = json.dumps(data).encode()
        self.send_response(200)
        self.send_cors()
        self.send_header('Content-Type','application/json')
        self.send_header('Content-Length', len(b))
        self.end_headers()
        self.wfile.write(b)

    def _serve_file(self):
        parsed=urllib.parse.urlparse(self.path)
        params=urllib.parse.parse_qs(parsed.query)
        if 'path' not in params:
            self.send_response(400); self.end_headers(); return
        fpath=urllib.parse.unquote(params['path'][0])
        if not os.path.exists(fpath):
            self.send_response(404); self.end_headers(); return
        ext=fpath.lower().split('.')[-1]
        ct='application/pdf' if ext=='pdf' else 'text/html'
        with open(fpath,'rb') as f: data=f.read()
        self.send_response(200)
        self.send_cors()
        self.send_header('Content-Type',ct)
        self.send_header('Content-Disposition','inline')
        self.send_header('Content-Length',len(data))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if self.path == '/assignlabel':
            self._assign_label()
        elif self.path == '/assignuser':
            self._assign_user()
        elif self.path == '/clear-processed':
            self._clear_processed()
        elif self.path == '/mark-processed':
            self._mark_processed()
        elif self.path == '/add-label':
            self._add_label()
        elif self.path == '/prefill':
            self._store_prefill()
        else:
            self._proxy("POST")

    def _assign_user(self):
        import base64 as b64
        length=int(self.headers.get('Content-Length',0))
        data=json.loads(self.rfile.read(length))
        ncurl=data['ncurl'].rstrip('/')
        user,passw=data['user'],data['pass']
        bid,sid,cid,uid=data['boardId'],data['stackId'],data['cardId'],data['userId']
        target=f"{ncurl}/index.php/apps/deck/api/v1.0/boards/{bid}/stacks/{sid}/cards/{cid}/assignUser"
        auth=b64.b64encode(f"{user}:{passw}".encode()).decode()
        headers={"Authorization":f"Basic {auth}","OCS-APIRequest":"true","Accept":"application/json","Content-Type":"application/json"}
        body=json.dumps({"userId":uid}).encode()
        try:
            req=urllib.request.Request(target,data=body,headers=headers,method="PUT")
            with urllib.request.urlopen(req,timeout=10) as resp:
                status=resp.status
        except urllib.error.HTTPError as e:
            status=e.code
        except Exception:
            status=502
        rb=json.dumps({"status":status}).encode()
        self.send_response(200)
        self.send_cors()
        self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",len(rb))
        self.end_headers()
        self.wfile.write(rb)

    def _clear_processed(self):
        global processed_mids
        processed_mids = set()
        try:
            import os
            if os.path.exists('/tmp/deck_processed.json'):
                os.remove('/tmp/deck_processed.json')
        except: pass
        b = b'{"ok":true}'
        self.send_response(200); self.send_cors()
        self.send_header('Content-Type','application/json')
        self.send_header('Content-Length',len(b))
        self.end_headers(); self.wfile.write(b)
        print("  Processed vidé.", flush=True)

    def _mark_processed(self):
        global processed_mids, prefill_data, prefill_queue
        length=int(self.headers.get('Content-Length',0))
        data=json.loads(self.rfile.read(length))
        mid=data.get('mid','')
        titre_ext=data.get('titre','')
        action=data.get('action','Créé')
        print(f"  mark-processed: mid={mid} titre_ext='{titre_ext}' action={action}", flush=True)
        processed_mids.add(mid)
        # titre_ext = titre saisi dans l'interface (priorité max)
        titre_courant = titre_ext if titre_ext else (prefill_queue[0].get('titre','') if prefill_queue else str(mid))
        # Retirer le mail traité de la file
        if prefill_queue:
            prefill_queue.pop(0)
        # Charger le suivant ou vider
        if prefill_queue:
            prefill_data = prefill_queue[0]
            current_mid = str(prefill_data.get('mail_mid',''))
            print(f"  Mail suivant chargé : {prefill_data.get('titre','')[:50]}")
        else:
            prefill_data = {}
            current_mid = ''
            print(f"  File d'attente vide.")
        # Ajouter à l'historique
        from datetime import datetime as dt
        history_log.append({
            'date': dt.now().strftime('%d/%m/%Y %H:%M'),
            'titre': titre_courant,
            'action': action
        })
        print(f"  Mail {mid} marqué comme traité ({action}).")
        # Sauvegarder dans le fichier partagé avec le watcher
        try:
            existing = []
            if os.path.exists('/tmp/deck_processed.json'):
                with open('/tmp/deck_processed.json') as fp:
                    existing = json.load(fp)
            existing.append(str(mid))
            with open('/tmp/deck_processed.json', 'w') as fp:
                json.dump(list(set(existing))[-500:], fp)
        except Exception:
            pass
        b=json.dumps({'next': bool(prefill_queue)}).encode()
        self.send_response(200)
        self.send_cors()
        self.send_header('Content-Type','application/json')
        self.send_header('Content-Length',len(b))
        self.end_headers()
        self.wfile.write(b)

    def _add_label(self):
        import imaplib as imap_lib
        length=int(self.headers.get('Content-Length',0))
        data=json.loads(self.rfile.read(length))
        email_addr=data.get('email','')
        password=data.get('password','')
        mid=data.get('mid','')
        result={'ok': False, 'msg': ''}
        try:
            m=imap_lib.IMAP4_SSL('imap.gmail.com',993)
            m.login(email_addr, password)
            # Sélectionner Messages envoyés
            m.select('"[Gmail]/Messages envoy&AOk-s"')
            # Copier le mail dans le dossier DECK (crée le label automatiquement)
            res, _ = m.copy(mid.encode(), 'DECK')
            if res == 'OK':
                result={'ok': True, 'msg': 'Label DECK attribué via copie'}
                print(f"  Label DECK attribué au mail.")
            else:
                # Fallback : essayer avec X-GM-LABELS
                m.store(mid.encode(), '+X-GM-LABELS', '\\DECK')
                result={'ok': True, 'msg': 'Label DECK attribué via X-GM-LABELS'}
                print(f"  Label DECK attribué (fallback).")
            m.logout()
        except Exception as e:
            result={'ok': False, 'msg': str(e)}
            print(f"  Erreur attribution label : {e}")
        rb=json.dumps(result).encode()
        self.send_response(200)
        self.send_cors()
        self.send_header('Content-Type','application/json')
        self.send_header('Content-Length',len(rb))
        self.end_headers()
        self.wfile.write(rb)

    def _store_prefill(self):
        global prefill_data, prefill_queue
        length = int(self.headers.get('Content-Length', 0))
        data = json.loads(self.rfile.read(length))
        print(f"  Prefill reçu : {data.get('titre','')[:50]}")
        data['_processed'] = False
        global current_mid
        prefill_queue.append(data)
        # Si c'est le premier mail, le charger immédiatement
        if len(prefill_queue) == 1:
            prefill_data = data
            current_mid = str(data.get('mail_mid',''))
        print(f"  File d'attente : {len(prefill_queue)} mail(s)")
        b = b'OK'
        self.send_response(200)
        self.send_cors()
        self.send_header('Content-Type','text/plain')
        self.send_header('Content-Length', len(b))
        self.end_headers()
        self.wfile.write(b)

    def _assign_label(self):
        import base64
        length = int(self.headers.get('Content-Length', 0))
        data = json.loads(self.rfile.read(length))
        ncurl = data['ncurl'].rstrip('/')
        user, passw = data['user'], data['pass']
        bid, sid, cid, lid = data['boardId'], data['stackId'], data['cardId'], data['labelId']
        target = f"{ncurl}/index.php/apps/deck/api/v1.0/boards/{bid}/stacks/{sid}/cards/{cid}/assignLabel"
        auth = base64.b64encode(f"{user}:{passw}".encode()).decode()
        headers = {
            "Authorization": f"Basic {auth}",
            "OCS-APIRequest": "true",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        body = json.dumps({"labelId": lid}).encode()
        try:
            req = urllib.request.Request(target, data=body, headers=headers, method="PUT")
            with urllib.request.urlopen(req, timeout=10) as resp:
                status = resp.status
        except urllib.error.HTTPError as e:
            status = e.code
        except Exception as e:
            status = 502
        resp_body = json.dumps({"status": status}).encode()
        self.send_response(200)
        self.send_cors()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(resp_body))
        self.end_headers()
        self.wfile.write(resp_body)
    def do_PUT(self):  self._proxy("PUT")
    def do_DELETE(self): self._proxy("DELETE")

    def _proxy(self, method):
        parsed=urllib.parse.urlparse(self.path)
        params=urllib.parse.parse_qs(parsed.query)
        if "url" not in params:
            self._json_error(400,"Missing ?url="); return
        target=urllib.parse.unquote(params["url"][0])
        length=int(self.headers.get("Content-Length",0))
        body=self.rfile.read(length) if length>0 else None
        fwd={}
        for k in ["Authorization","OCS-APIRequest","Accept","Content-Type"]:
            if k in self.headers: fwd[k]=self.headers[k]
        try:
            req=urllib.request.Request(target,data=body,headers=fwd,method=method)
            with urllib.request.urlopen(req,timeout=20) as resp:
                status=resp.status; rbody=resp.read()
                ct=resp.headers.get("Content-Type","application/json")
            self.send_response(status); self.send_cors()
            self.send_header("Content-Type",ct)
            self.send_header("Content-Length",len(rbody))
            self.end_headers(); self.wfile.write(rbody)
        except urllib.error.HTTPError as e:
            rb=e.read(); self.send_response(e.code); self.send_cors()
            self.send_header("Content-Type","application/json"); self.end_headers(); self.wfile.write(rb)
        except Exception as e:
            self._json_error(502,str(e))

    def _json_error(self,code,msg):
        b=json.dumps({"error":msg}).encode()
        self.send_response(code); self.send_cors()
        self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",len(b))
        self.end_headers(); self.wfile.write(b)


def main():
    # En production, écouter sur 0.0.0.0 et lire le port depuis l'environnement
    host = '0.0.0.0'
    port = int(os.environ.get('PORT', PORT))
    try:
        server = HTTPServer((host, port), Handler)
        print(f"\n  Nextcloud Deck Proxy démarré sur {host}:{port}")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nProxy arrêté."); sys.exit(0)
    except OSError as e:
        print(f"Erreur port {port} : {e}"); sys.exit(1)

if __name__=="__main__":
    main()
