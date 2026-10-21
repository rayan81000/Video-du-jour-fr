"""Génère index.html (liste déjà écrite dans la page, pour Google), sitemap.xml et robots.txt à partir de data.json."""
import html, json, os
from datetime import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE_URL = os.environ.get("SITE_URL", "https://rayan81000.github.io/Video-du-jour-fr/")

# Grands YouTubeurs français : on repère le nom de la chaîne (sans majuscules ni accents).
def load_favs():
    path = os.path.join(ROOT, "favoris.txt")
    try:
        with open(path, encoding="utf-8") as f:
            return [l.strip().lower() for l in f if l.strip() and not l.startswith("#")]
    except FileNotFoundError:
        return []


FAVS = load_favs()
BIG_SUBS = 1_000_000

JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
        "septembre", "octobre", "novembre", "décembre"]


def is_fav(v):
    name = v["channel"].lower()
    return any(n in name for n in FAVS)


def is_big(v):
    return v.get("subs", 0) >= BIG_SUBS


def fv(n):
    if n >= 1_000_000:
        return f"{n/1e6:.1f}".replace(".", ",") + " M"
    if n >= 1000:
        return f"{n/1e3:.1f}".replace(".", ",") + " k"
    return str(n)


def age(h):
    return "il y a 1 jour" if h >= 24 else f"il y a {h} h"


TEMPLATE = r"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Vidéo du jour : les vidéos françaises du jour sur YouTube</title>
<meta name="description" content="La vidéo du jour : les nouvelles vidéos françaises des dernières 24 heures sur YouTube, avec les grands YouTubeurs en premier. Mise à jour chaque jour.">
<link rel="canonical" href="__URL__">
<meta name="robots" content="index,follow,max-snippet:-1,max-image-preview:large">
<meta property="og:type" content="website">
<meta property="og:locale" content="fr_FR">
<meta property="og:title" content="Vidéo du jour : les vidéos françaises du jour sur YouTube">
<meta property="og:description" content="Les nouvelles vidéos françaises des dernières 24 heures, grands YouTubeurs en premier.">
<meta property="og:url" content="__URL__">
<script type="application/ld+json">__JSONLD__</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@700;800&family=DM+Sans:wght@400;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root{--bg:#f6f7fb;--surface:#fff;--fg:#14172b;--muted:#5b6078;--line:#dfe2ee;--accent:#2b3fd9;--accent-fg:#fff;
--music:#c2185b;--game:#00796b;--cine:#a65b00;--star:#b7791f;
--font-display:'Bricolage Grotesque','Arial Narrow',system-ui,sans-serif;--font-body:'DM Sans',system-ui,-apple-system,'Segoe UI',sans-serif;--font-data:'IBM Plex Mono',ui-monospace,Menlo,monospace}
@media (prefers-color-scheme:dark){:root{--bg:#0f1220;--surface:#171b2e;--fg:#eef0fa;--muted:#9aa1c0;--line:#2a2f48;--accent:#8c9bff;--accent-fg:#0f1220;--music:#ff7bb0;--game:#4fd1c0;--cine:#ffb454;--star:#ffd166;color-scheme:dark}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font-family:var(--font-body);font-size:16px;line-height:1.5;padding:32px max(16px,env(safe-area-inset-right,0px)) 56px max(16px,env(safe-area-inset-left,0px))}
main{max-width:860px;margin:0 auto}
header{display:flex;flex-direction:column;gap:6px;margin-bottom:24px}
.date{font-family:var(--font-data);font-size:13px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
h1{font-family:var(--font-display);font-weight:800;font-size:clamp(34px,7vw,56px);line-height:1;margin:0;letter-spacing:-.02em}
.lead{color:var(--muted);max-width:60ch;margin:6px 0 0}
.bar{display:flex;flex-wrap:wrap;gap:10px 16px;align-items:center;justify-content:space-between;margin-bottom:16px;padding-bottom:16px;border-bottom:1px solid var(--line)}
.tabs,.sort{display:flex;flex-wrap:wrap;gap:6px}
button{font:inherit;cursor:pointer}
.tab,.sbtn{border:1px solid var(--line);background:var(--surface);color:var(--fg);padding:6px 14px;border-radius:999px;font-size:14px}
.tab[aria-pressed="true"],.sbtn[aria-pressed="true"]{background:var(--accent);color:var(--accent-fg);border-color:var(--accent)}
button:focus-visible,a:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.favpanel{border:1px solid var(--line);background:var(--surface);border-radius:10px;padding:10px 14px;margin-bottom:14px}
.favpanel summary{cursor:pointer;font-weight:600}
.favbody{display:flex;flex-direction:column;gap:10px;margin-top:10px}
.favbody form{display:flex;gap:8px;flex-wrap:wrap}
.favbody input{flex:1 1 200px;min-width:0;font:inherit;padding:8px 12px;border:1px solid var(--line);border-radius:8px;background:var(--bg);color:var(--fg)}
.favlist{display:flex;flex-wrap:wrap;gap:6px}
.favtag{display:inline-flex;align-items:center;gap:6px;border:1px solid var(--line);border-radius:999px;padding:3px 6px 3px 12px;font-size:14px}
.favtag button{border:0;background:transparent;color:var(--muted);font-size:16px;line-height:1;padding:2px 6px}
.auth{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-top:10px}
.who{display:inline-flex;align-items:center;gap:8px;font-size:14px}
.who img{width:28px;height:28px;border-radius:50%}
.hint{margin:0;color:var(--muted);font-size:13px}
.star{border:0;background:transparent;font-size:22px;line-height:1;padding:4px 6px;color:var(--star)}
.count{font-family:var(--font-data);font-size:13px;color:var(--muted);margin-bottom:6px}
ol{list-style:none;margin:0;padding:0}
li{display:grid;grid-template-columns:40px minmax(0,1fr) auto;gap:4px 14px;align-items:center;padding:14px 0;border-bottom:1px solid var(--line)}
.rank{font-family:var(--font-display);font-weight:800;font-size:22px;color:var(--muted);text-align:right}
.t{min-width:0}
.t a{color:var(--fg);text-decoration:none;font-weight:600;overflow-wrap:anywhere}
.t a:hover{color:var(--accent);text-decoration:underline}
.meta{display:flex;flex-wrap:wrap;gap:4px 10px;align-items:center;font-size:13.5px;color:var(--muted);margin-top:2px}
.chip{font-family:var(--font-data);font-size:11px;letter-spacing:.06em;text-transform:uppercase;border:1px solid currentColor;padding:1px 7px;border-radius:4px}
.chip.Musique{color:var(--music)}.chip.Jeux{color:var(--game)}.chip.Cinéma{color:var(--cine)}.chip.Divers{color:var(--muted)}.chip.big{color:var(--muted)}.chip.fav{color:var(--star)}
.v{font-family:var(--font-data);font-size:14px;text-align:right;white-space:nowrap}
.v small{display:block;color:var(--muted);font-size:12px}
footer{margin-top:28px;color:var(--muted);font-size:13.5px;display:flex;flex-direction:column;gap:6px}
footer a{color:var(--accent)}
@media (max-width:480px){li{grid-template-columns:28px minmax(0,1fr)}.v{grid-column:2;text-align:left}.v small{display:inline;margin-left:8px}}
</style>
</head>
<body>
<main>
<header>
<span class="date">__DATE__</span>
<h1>Vidéo du jour</h1>
<p class="lead">Les nouvelles vidéos françaises des dernières 24 heures sur YouTube. Les grands YouTubeurs sont affichés en premier.</p>
<div class="auth" id="auth"><button type="button" class="sbtn" id="login" hidden>Se connecter avec Google</button><span class="who" id="who" hidden></span><button type="button" class="sbtn" id="logout" hidden>Se déconnecter</button><span class="hint" id="authmsg" role="status"></span></div>
</header>
<div class="bar">
<div class="tabs" id="tabs" role="group" aria-label="Catégorie"></div>
<div class="sort" id="sort" role="group" aria-label="Tri">
<button class="sbtn" data-s="big" aria-pressed="true">Favoris et grandes chaînes</button>
<button class="sbtn" data-s="views" aria-pressed="false">Plus vues</button>
<button class="sbtn" data-s="age" aria-pressed="false">Plus récentes</button>
</div>
</div>
<details class="favpanel" id="favpanel"><summary>Mes YouTubeurs favoris</summary><div class="favbody">
<form id="favform"><input id="favin" type="text" placeholder="Nom d'une chaîne (ex. Squeezie)" autocomplete="off" aria-label="Nom d'une chaîne"><button type="submit" class="sbtn">Ajouter</button></form>
<div class="favlist" id="favlist"></div>
<p class="hint">Touchez l'étoile à côté d'une vidéo pour ajouter ou retirer sa chaîne. Votre liste est enregistrée sur cet appareil.</p>
<div><button type="button" class="sbtn" id="favreset">Remettre la liste de départ</button></div>
</div></details>
<div class="count" id="count">__COUNT__</div>
<ol id="list">__LIST__</ol>
<footer>
<span>Vidéos issues des tendances YouTube France, relevées une fois par jour.</span>
<span>Liste en direct : <a href="https://www.youtube.com/feed/trending?gl=FR&amp;hl=fr" target="_blank" rel="noopener">tendances YouTube France</a>.</span>
</footer>
</main>
<script id="data" type="application/json">__DATA__</script>
<script id="favs" type="application/json">__FAVS__</script>
<script>
var D=JSON.parse(document.getElementById('data').textContent);
var DEF=JSON.parse(document.getElementById('favs').textContent);
var FAVS=DEF.slice();
try{var sv=localStorage.getItem('favs');if(sv)FAVS=JSON.parse(sv)}catch(e){}
function saveFavs(){try{localStorage.setItem('favs',JSON.stringify(FAVS))}catch(e){}if(window.cloudSave)window.cloudSave(FAVS)}
function isFav(r){var n=r.channel.toLowerCase();return FAVS.some(function(f){return n.indexOf(f)>-1})}
var cat="Tout",sort="big";
function fv(n){return n>=1e6?(n/1e6).toFixed(1).replace('.',',')+' M':n>=1e3?(n/1e3).toFixed(1).replace('.',',')+' k':String(n)}
function age(h){return h>=24?'il y a 1 jour':'il y a '+h+' h'}
function esc(s){var d=document.createElement('div');d.textContent=s;return d.innerHTML}
function render(){
var rows=D.filter(function(r){return cat==="Tout"||r.category===cat});
rows.sort(function(a,b){
if(sort==="big"){var fa=isFav(a),fb=isFav(b);if(fa!==fb)return fa?-1:1;if(a.big!==b.big)return a.big?-1:1;}
if(sort==="age")return (a.hours-b.hours)||(b.views-a.views);
return b.views-a.views});
document.getElementById('count').textContent=rows.length+' vidéo'+(rows.length>1?'s':'');
document.getElementById('list').innerHTML=rows.map(function(r,i){
var f=isFav(r);
return '<li><span class="rank">'+(i+1)+'</span><div class="t"><a class="yt" data-id="'+r.id+'" href="https://www.youtube.com/watch?v='+r.id+'" target="_blank" rel="noopener">'+esc(r.title)+'</a><div class="meta"><span>'+esc(r.channel)+'</span><span class="chip '+r.category+'">'+r.category+'</span>'+(f?'<span class="chip fav">Favori</span>':(r.big?'<span class="chip big">Grande chaîne</span>':''))+'</div></div><div class="v"><button class="star" data-i="'+D.indexOf(r)+'" aria-pressed="'+f+'" aria-label="'+(f?'Retirer des favoris':'Ajouter aux favoris')+'">'+(f?'★':'☆')+'</button> '+fv(r.views)+' vues<small>'+age(r.hours)+'</small></div></li>';
}).join('');
}
var tabs=document.getElementById('tabs');
["Tout","Musique","Jeux","Cinéma","Divers"].forEach(function(c){
var b=document.createElement('button');b.className='tab';b.textContent=c==="Jeux"?"Jeux & streamers":c;b.dataset.c=c;
b.setAttribute('aria-pressed',c===cat);tabs.appendChild(b)});
tabs.addEventListener('click',function(e){var b=e.target.closest('.tab');if(!b)return;cat=b.dataset.c;
tabs.querySelectorAll('.tab').forEach(function(x){x.setAttribute('aria-pressed',x===b)});render()});
document.getElementById('sort').addEventListener('click',function(e){var b=e.target.closest('.sbtn');if(!b)return;sort=b.dataset.s;
this.querySelectorAll('.sbtn').forEach(function(x){x.setAttribute('aria-pressed',x===b)});render()});

function renderFavs(){
document.getElementById('favlist').innerHTML=FAVS.length?FAVS.map(function(f,i){return '<span class="favtag">'+esc(f)+'<button type="button" data-f="'+i+'" aria-label="Retirer '+esc(f)+'">×</button></span>'}).join(''):'<span class="hint">Aucun favori pour le moment.</span>';
}
function refresh(){saveFavs();render();renderFavs()}
document.getElementById('list').addEventListener('click',function(e){
var b=e.target.closest('.star');if(!b)return;
var r=D[+b.dataset.i],n=r.channel.toLowerCase();
if(isFav(r)){FAVS=FAVS.filter(function(f){return n.indexOf(f)===-1})}else{FAVS.push(n)}
refresh()});
document.getElementById('favlist').addEventListener('click',function(e){
var b=e.target.closest('button[data-f]');if(!b)return;
FAVS.splice(+b.dataset.f,1);refresh()});
document.getElementById('favform').addEventListener('submit',function(e){
e.preventDefault();var inp=document.getElementById('favin'),v=inp.value.trim().toLowerCase();
if(v&&FAVS.indexOf(v)===-1)FAVS.push(v);inp.value='';refresh()});
document.getElementById('favreset').addEventListener('click',function(){
FAVS=DEF.slice();try{localStorage.removeItem('favs')}catch(e){}render();renderFavs()});
render();renderFavs();
document.addEventListener('click',function(e){
var a=e.target.closest('a.yt');if(!a)return;
var id=a.dataset.id,ua=navigator.userAgent;
var ios=/iPad|iPhone|iPod/.test(ua)||(navigator.platform==='MacIntel'&&navigator.maxTouchPoints>1);
var and=/Android/.test(ua);
if(!ios&&!and)return;
e.preventDefault();
var web='https://www.youtube.com/watch?v='+id;
if(and){location.href='intent://www.youtube.com/watch?v='+id+'#Intent;scheme=https;package=com.google.android.youtube;S.browser_fallback_url='+encodeURIComponent(web)+';end';return;}
var t=setTimeout(function(){location.href=web},1500);
document.addEventListener('visibilitychange',function(){if(document.hidden)clearTimeout(t)},{once:true});
window.addEventListener('pagehide',function(){clearTimeout(t)},{once:true});
location.href='youtube://www.youtube.com/watch?v='+id;
});
</script>
<script type="module">
(async function(){
var $=function(i){return document.getElementById(i)};
var msg=function(t){$('authmsg').textContent=t||''};
try{
var cfg=(await import('./firebase-config.js')).firebaseConfig;
if(!cfg||!cfg.apiKey)return;
var B='https://www.gstatic.com/firebasejs/10.14.1/';
var mods=await Promise.all([import(B+'firebase-app.js'),import(B+'firebase-auth.js'),import(B+'firebase-firestore.js')]);
var A=mods[0],Au=mods[1],Fs=mods[2];
var app=A.initializeApp(cfg),auth=Au.getAuth(app),db=Fs.getFirestore(app);
$('login').hidden=false;
$('login').addEventListener('click',async function(){
msg('');
try{await Au.signInWithPopup(auth,new Au.GoogleAuthProvider())}
catch(e){
if(e&&(e.code==='auth/popup-blocked'||e.code==='auth/operation-not-supported-in-this-environment')){Au.signInWithRedirect(auth,new Au.GoogleAuthProvider());return}
if(e&&e.code==='auth/popup-closed-by-user')return;
msg('Connexion impossible : '+((e&&e.code)||'erreur inconnue'))}
});
$('logout').addEventListener('click',function(){Au.signOut(auth)});
Au.onAuthStateChanged(auth,async function(u){
if(!u){window.cloudSave=null;$('login').hidden=false;$('logout').hidden=true;$('who').hidden=true;return}
$('login').hidden=true;$('logout').hidden=false;$('who').hidden=false;
$('who').textContent='';
if(u.photoURL){var im=document.createElement('img');im.src=u.photoURL;im.alt='';im.referrerPolicy='no-referrer';$('who').appendChild(im)}
$('who').appendChild(document.createTextNode(u.displayName||u.email||'Connecté'));
var ref=Fs.doc(db,'users',u.uid);
try{
var snap=await Fs.getDoc(ref);
if(snap.exists()&&Array.isArray(snap.data().favs)){window.FAVS=snap.data().favs;try{localStorage.setItem('favs',JSON.stringify(window.FAVS))}catch(e){}render();renderFavs()}
else{await Fs.setDoc(ref,{favs:window.FAVS})}
window.cloudSave=function(f){Fs.setDoc(ref,{favs:f}).catch(function(){msg('Enregistrement impossible pour le moment.')})};
msg('Vos favoris sont enregistrés sur votre compte.')
}catch(e){msg('Favoris du compte indisponibles : '+((e&&e.code)||'erreur'))}
});
}catch(e){/* Firebase indisponible : le site fonctionne sans connexion */}
})();
</script>
</body>
</html>
"""


def main():
    with open(os.path.join(ROOT, "data.json"), encoding="utf-8") as f:
        data = json.load(f)
    gen = datetime.fromisoformat(data["generated"])
    vids = data["videos"]
    for v in vids:
        v["fav"] = is_fav(v)
        v["big"] = is_big(v)
    vids.sort(key=lambda v: (not v["fav"], not v["big"], -v["views"]))

    items = []
    for i, v in enumerate(vids, 1):
        badge = ('<span class="chip fav">Favori</span>' if v["fav"]
                 else '<span class="chip big">Grande chaîne</span>' if v["big"] else "")
        items.append(
            f'<li><span class="rank">{i}</span><div class="t">'
            f'<a class="yt" data-id="{html.escape(v["id"])}" href="https://www.youtube.com/watch?v={html.escape(v["id"])}" target="_blank" rel="noopener">{html.escape(v["title"])}</a>'
            f'<div class="meta"><span>{html.escape(v["channel"])}</span>'
            f'<span class="chip {v["category"]}">{v["category"]}</span>{badge}</div></div>'
            f'<div class="v">{fv(v["views"])} vues<small>{age(v["hours"])}</small></div></li>'
        )

    date_txt = f"{JOURS[gen.weekday()].capitalize()} {gen.day} {MOIS[gen.month-1]} {gen.year}"
    jsonld = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "Vidéo du jour : les vidéos françaises du jour sur YouTube",
        "itemListElement": [
            {"@type": "ListItem", "position": i, "url": f"https://www.youtube.com/watch?v={v['id']}", "name": v["title"]}
            for i, v in enumerate(vids, 1)
        ],
    }
    safe = lambda obj: json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")
    page = (TEMPLATE.replace("__URL__", SITE_URL).replace("__DATE__", date_txt)
            .replace("__COUNT__", f"{len(vids)} vidéos").replace("__LIST__", "".join(items))
            .replace("__FAVS__", safe(FAVS)).replace("__JSONLD__", safe(jsonld)).replace("__DATA__", safe(vids)))
    with open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8") as f:
        f.write(page)
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                f'<url><loc>{SITE_URL}</loc><lastmod>{gen.date().isoformat()}</lastmod><changefreq>daily</changefreq></url>\n</urlset>\n')
    with open(os.path.join(ROOT, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}sitemap.xml\n")
    print(f"index.html généré ({len(vids)} vidéos, {sum(v['fav'] for v in vids)} favoris, {sum(v['big'] for v in vids)} grandes chaînes).")


if __name__ == "__main__":
    main()
