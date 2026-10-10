#!/usr/bin/env python3
"""Avaruus-Yatzy. Aja: python3 avaruus_yatzy.py  -> avaa selaimessa http://localhost:8000
Pilvessä (esim. Render): portti luetaan PORT-ympäristömuuttujasta.
Huippupisteet tallentuvat pelaajan omaan selaimeen (localStorage)."""
import json, os, socket, tempfile, threading, traceback, webbrowser
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

def pick_file():
    here = os.path.dirname(os.path.abspath(__file__))
    for d in (here, os.getcwd(), os.path.expanduser("~"), tempfile.gettempdir()):
        try:
            if os.access(d, os.W_OK):
                return os.path.join(d, "yatzy_scores.json")
        except Exception:
            pass
    return "yatzy_scores.json"


FILE = pick_file()
LOCK = threading.Lock()
PORT = int(os.environ.get("PORT", 8000))


MODES = ("classic", "duel", "free", "rev")


def load():
    try:
        with open(FILE, encoding="utf-8") as f:
            d = json.load(f)
    except Exception:
        d = {}
    for k in MODES:
        d.setdefault(k, [])
    return d


MANIFEST = {
    "name": "Avaruus-Yatzy", "short_name": "Yatzy",
    "start_url": "/", "scope": "/", "display": "standalone",
    "background_color": "#070717", "theme_color": "#070717",
    "icons": [
        {"src": "/icon.svg", "sizes": "192x192", "type": "image/svg+xml", "purpose": "any"},
        {"src": "/icon.svg", "sizes": "512x512", "type": "image/svg+xml", "purpose": "any"},
    ],
}
ICON = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
<rect width="512" height="512" rx="96" fill="#1a0b3d"/>
<rect x="116" y="116" width="280" height="280" rx="50" fill="#7c3aed"/>
<g fill="#fff"><circle cx="186" cy="186" r="26"/><circle cx="326" cy="186" r="26"/><circle cx="256" cy="256" r="26"/><circle cx="186" cy="326" r="26"/><circle cx="326" cy="326" r="26"/></g></svg>'''
SW = r'''const C='yatzy-v1';
self.addEventListener('install',e=>{e.waitUntil(caches.open(C).then(c=>c.addAll(['/','/icon.svg'])));self.skipWaiting()});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(k=>Promise.all(k.filter(x=>x!=C).map(x=>caches.delete(x)))));self.clients.claim()});
self.addEventListener('fetch',e=>{if(e.request.method!='GET'||e.request.url.includes('/api/'))return;
e.respondWith(fetch(e.request).then(r=>{const cp=r.clone();caches.open(C).then(c=>c.put(e.request,cp));return r}).catch(()=>caches.match(e.request)))});'''


class H(BaseHTTPRequestHandler):
    def _send(self, body, ct="application/json"):
        self.send_response(200)
        self.send_header("Content-Type", ct)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        p = self.path.split("?")[0]
        if p.startswith("/api/scores"):
            with LOCK:
                self._send(json.dumps(load()).encode())
        elif p == "/manifest.json":
            self._send(json.dumps(MANIFEST).encode(), "application/manifest+json")
        elif p == "/sw.js":
            self._send(SW.encode(), "text/javascript")
        elif p == "/icon.svg":
            self._send(ICON.encode(), "image/svg+xml")
        else:
            self._send(HTML.encode("utf-8"), "text/html; charset=utf-8")

    def do_POST(self):
        try:
            d = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            mode, name, score = d["mode"], str(d["name"])[:20], int(d["score"])
            assert mode in MODES
            with LOCK:
                s = load()
                s[mode].append({"name": name, "score": score, "date": date.today().strftime("%d.%m.%Y")})
                sign = 1 if mode == "rev" else -1  # käänteisessä pienin pistemäärä on paras
                s[mode] = sorted(s[mode], key=lambda e: sign * e["score"])[:20]
                with open(FILE, "w", encoding="utf-8") as f:
                    json.dump(s, f, ensure_ascii=False, indent=1)
            self._send(b'{"ok":true}')
        except Exception:
            traceback.print_exc()
            self.send_response(400)
            self.end_headers()

    def log_message(self, *a):
        pass


def lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "localhost"


HTML = r"""<!DOCTYPE html><html lang="fi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Avaruus-Yatzy</title>
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#070717">
<link rel="icon" href="/icon.svg">
<link rel="apple-touch-icon" href="/icon.svg"><style>
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
body{margin:0;min-height:100vh;color:#e8ecff;font-family:system-ui,sans-serif;
background:radial-gradient(circle at 15% 10%,#5b1fa8aa,transparent 45%),radial-gradient(circle at 90% 80%,#0a8fb8aa,transparent 45%),radial-gradient(circle at 50% 100%,#c2186088,transparent 40%),#070717}
body::before{content:"";position:fixed;inset:0;z-index:-1;animation:tw 4s infinite alternate;
background-image:radial-gradient(1.5px 1.5px at 20px 30px,#fff,transparent),radial-gradient(1px 1px at 90px 120px,#9ef,transparent),radial-gradient(1.5px 1.5px at 160px 60px,#fcf,transparent),radial-gradient(1px 1px at 230px 180px,#fff,transparent);background-size:260px 220px}
@keyframes tw{from{opacity:.4}to{opacity:1}}
.scr{max-width:480px;margin:auto;padding:14px;padding-top:calc(14px + env(safe-area-inset-top,0px))}
h1{text-align:center;font-size:2rem;margin:.3em 0;background:linear-gradient(90deg,#4df,#f6f,#fd5);-webkit-background-clip:text;color:transparent}
h1 span{display:inline-block;animation:fl 3s ease-in-out infinite}@keyframes fl{50%{transform:translateY(-8px) rotate(10deg)}}
button,input{font:inherit;color:inherit}
button{border:1px solid #fff3;background:#ffffff14;border-radius:12px;padding:10px 14px;cursor:pointer}
button.on{background:linear-gradient(135deg,#7c3aed,#06b6d4);box-shadow:0 0 14px #7c3aed99}
.big{width:100%;font-size:1.2rem;padding:14px;margin:8px 0;background:linear-gradient(135deg,#f0f,#fa0);border:0;font-weight:700;box-shadow:0 0 18px #f0f6}
.big:disabled{opacity:.35;box-shadow:none}
.seg{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0}.seg button{flex:1 1 40%}
input{width:100%;padding:12px;margin:5px 0;border-radius:12px;border:1px solid #4df6;background:#0008}
.card{background:#0b0b2acc;border:1px solid #fff2;border-radius:16px;padding:10px;margin:8px 0;backdrop-filter:blur(6px)}
#dice{display:flex;justify-content:space-around;margin:26px 0 14px}
.slot{width:56px;height:56px;perspective:500px;transition:transform .2s;position:relative}
.slot.held{transform:translateY(-12px)}.slot.held::after{content:"LUKOSSA";position:absolute;top:66px;left:-4px;width:64px;text-align:center;font-size:9px;color:#fd5}
.die{width:100%;height:100%;transform-style:preserve-3d;transform:rotateX(-20deg) rotateY(-25deg)}
.cube{position:relative;width:100%;height:100%;transform-style:preserve-3d;transition:transform 1s cubic-bezier(.2,.8,.2,1)}
.f{position:absolute;inset:0;display:grid;grid:repeat(3,1fr)/repeat(3,1fr);padding:6px;border-radius:10px;border:1px solid #fff6;
background:linear-gradient(135deg,hsl(var(--h),90%,62%),hsl(calc(var(--h) + 50),90%,38%))}
.slot.held .f{box-shadow:0 0 16px 2px #fd5}
.f i{margin:14%}.f i.on{background:#fff;border-radius:50%;box-shadow:0 0 6px #fff}
.f1{transform:translateZ(28px)}.f2{transform:rotateY(90deg) translateZ(28px)}.f3{transform:rotateX(90deg) translateZ(28px)}
.f4{transform:rotateX(-90deg) translateZ(28px)}.f5{transform:rotateY(-90deg) translateZ(28px)}.f6{transform:rotateY(180deg) translateZ(28px)}
#bar{text-align:center;font-size:1.1rem}.b0{color:#4df}.b1{color:#f7f}
#msg{text-align:center;font-size:.85rem;color:#bcd;min-height:2.4em;margin-top:18px}
table{width:100%;border-collapse:collapse;font-size:.9rem}td,th{padding:6px 4px;text-align:center;border-bottom:1px solid #fff1}
td:first-child{text-align:left}tr.op{cursor:pointer}tr.op:active,tr.cur{background:#7c3aed55}
.gh{color:#fd5;opacity:.7}.sub td{background:#ffffff0d;font-weight:700}.w{color:#6f6;font-weight:700}
#end,#hs{position:fixed;inset:0;background:#000d;overflow:auto;z-index:5}
.pop{animation:pop .5s cubic-bezier(.2,1.6,.4,1)}@keyframes pop{from{transform:scale(.3);opacity:0}}
.fact{background:linear-gradient(135deg,#4df2,#f6f2);border-radius:12px;padding:12px;margin:10px 0;font-size:.95rem}
</style></head><body>
<div id="menu" class="scr"><h1><span>🚀</span> Avaruus-Yatzy</h1>
<div class="card"><b>Pelimuoto</b><div class="seg" id="mode"><button data-v="classic" class="on">Perinteinen</button><button data-v="rev">Käänteinen</button><button data-v="duel">Kaksintaistelu</button><button data-v="free">Vapaa kaksintaistelu</button></div>
<small id="mi"></small></div>
<div class="card"><b>Vastustaja</b><div class="seg" id="opp"><button data-v="1" class="on">🤖 AI</button><button data-v="0">👤 Ihminen</button></div>
<input id="n0" placeholder="Pelaaja 1" maxlength="20"><input id="n1" placeholder="AI Nova" maxlength="20"></div>
<button class="big" id="go">Aloita peli</button><button id="hsb" style="width:100%">🏆 Huippupisteet</button></div>
<div id="game" class="scr" hidden><div id="bar"></div><div id="dice"></div><div id="msg"></div>
<button class="big" id="roll">Heitä</button><div class="card" id="board"></div></div>
<div id="end" hidden><div class="scr"><div class="card pop" id="endc"></div></div></div>
<div id="hs" hidden><div class="scr"><h1>🏆 Huippupisteet</h1><div class="seg" id="hst"><button data-v="classic" class="on">Perinteinen</button><button data-v="rev">Käänteinen</button><button data-v="duel">Kaksintaistelu</button><button data-v="free">Vapaa kaksintaistelu</button></div>
<div class="card" id="hsl"></div><button style="width:100%" id="hsx">Sulje</button></div></div>
<script>
if('serviceWorker' in navigator)navigator.serviceWorker.register('/sw.js').catch(()=>{});
const $=s=>document.querySelector(s),sleep=ms=>new Promise(r=>setTimeout(r,ms)),R=()=>1+Math.floor(Math.random()*6);
const CATS=['Ykköset','Kakkoset','Kolmoset','Neloset','Vitoset','Kuutoset','Pari','Kaksi paria','Kolme samaa','Neljä samaa','Pieni suora','Iso suora','Täyskäsi','Sattuma','Yatzy'];
const AV=[2,4,6,8,10,12,8,10,12,14,7,9,15,22,3];
const FACTS=['Venus pyörii niin hitaasti, että sen vuorokausi on pidempi kuin sen vuosi.','Neutronitähden teelusikallinen painaisi Maassa noin miljardi tonnia.','Voyager 1 on ihmiskunnan kaukaisin luotain – se lähti matkaan vuonna 1977 ja on nyt tähtienvälisessä avaruudessa.','Kuussa on jalanjälkiä, jotka säilyvät miljoonia vuosia, koska siellä ei ole tuulta.','Auringon valo kulkee Maahan noin 8 minuutissa ja 20 sekunnissa.','Jupiterin Suuri punainen pyörremyrsky on ollut päällä ainakin 300 vuotta.','Saturnuksen tiheys on pienempi kuin veden – se kelluisi tarpeeksi isossa altaassa.','James Webb -avaruusteleskooppi katsoo infrapunassa ja näkee galakseja, jotka loistivat vain satoja miljoonia vuosia alkuräjähdyksen jälkeen.','Marsin Olympus Mons on aurinkokunnan korkein vuori, noin kolme kertaa Everestin korkuinen.','Kansainvälinen avaruusasema kiertää Maan noin 90 minuutissa – astronautit näkevät 16 auringonnousua päivässä.','Maapallon kokoisia planeettoja löytyy tuhansia – exoplaneettoja on vahvistettu jo yli 5000.','Linnunradassa on arviolta 100–400 miljardia tähteä.'];
const BASE={1:[0,0],2:[0,-90],3:[-90,0],4:[90,0],5:[0,90],6:[0,180]},P=['','000010000','100000001','100010001','101000101','101010101','101101101'];
let G=null,busy=false,cfg={mode:'classic',ai:1},ang=[[0,0],[0,0],[0,0],[0,0],[0,0]];
const cnt=d=>{const c=[0,0,0,0,0,0,0];d.forEach(v=>c[v]++);return c};
function sc(i,d){const c=cnt(d),s=d.reduce((a,b)=>a+b,0),big=n=>{for(let v=6;v>0;v--)if(c[v]>=n)return v;return 0};
if(i<6)return c[i+1]*(i+1);
switch(i){case 6:return big(2)*2;
case 7:{const p=[];for(let v=6;v>0;v--)if(c[v]>=2)p.push(v);return p.length>1?(p[0]+p[1])*2:0}
case 8:return big(3)*3;case 9:return big(4)*4;
case 10:return c.slice(1,6).every(x=>x==1)?15:0;case 11:return c.slice(2,7).every(x=>x==1)?20:0;
case 12:return c.includes(3)&&c.includes(2)?s:0;case 13:return s;case 14:return c.includes(5)?50:0}}
const done=(r,d)=>r==13?sc(13,d)>=20:sc(r,d)>0;
const isAI=()=>G.ai&&G.p==1, cl=()=>G.mode=='classic', card=()=>G.mode=='classic'||G.mode=='rev';
function show(id){['menu','game'].forEach(x=>$('#'+x).hidden=x!=id)}
function seg(id,fn){$(id).onclick=e=>{const b=e.target.closest('button');if(!b)return;[...$(id).children].forEach(x=>x.classList.toggle('on',x==b));fn(b.dataset.v)}}
const MI={free:'Kuten kaksintaistelu, mutta pelaajat valitsevat vuorotellen minkä rivin heitetään (ei järjestystä). Valitsija heittää ensin.',rev:'Pienin pistemäärä voittaa! Jokaiseen riviin pitää saada tulos, muuten rivi saa maksimipisteet. Yläkerta: valitse numero heti 1. heiton jälkeen – rivi lukittuu, valitut numerot jäävät lukkoon ja loput heitetään uudelleen (3 heittoa); ei yhtään = 4×numero. Alakerta: pienin pari, kaksi paria, kolme/neljä samaa, täyskäsi; epäsuora = viisi eri silmälukua mutta ei suoraa; sattuma = 3 heittoa, pienin summa.',classic:'Normaali yatzy: 15 riviä, 3 heittoa vuorossa, yläkerran bonus 50 p (63 p:llä).',duel:'Rivi kerrallaan ylhäältä alas. Ylärivit: eniten oikeita silmälukuja 3 heitolla. Alarivit: vähiten heittoja tavoitteeseen (sattuma: summa ≥ 20). Voittaja saa 1 p, tasapelistä molemmat.'};
$('#mi').textContent=MI.classic;
seg('#mode',v=>{cfg.mode=v;$('#mi').textContent=MI[v]});
seg('#opp',v=>{cfg.ai=+v;$('#n1').placeholder=+v?'AI Nova':'Pelaaja 2'});
$('#go').onclick=()=>{G={mode:cfg.mode,ai:cfg.ai,n:[$('#n0').value.trim()||'Pelaaja 1',$('#n1').value.trim()||(cfg.ai?'AI Nova':'Pelaaja 2')],p:0,row:cfg.mode=='free'?-1:0,chooser:0,round:0,commit:-1,d:[1,2,3,4,5],held:[0,0,0,0,0],rolls:0,sc:[{},{}],res:[[],[]],lock:false};
 ang=[[0,0],[0,0],[0,0],[0,0],[0,0]];G.d.forEach((v,i)=>setDie(i,v,0));show('game');$('#end').hidden=true;G.mode=='free'?startChoose():startTurn()};
const dice=$('#dice');
for(let i=0;i<5;i++){const s=document.createElement('div');s.className='slot';s.style.setProperty('--h',[200,320,45,150,270][i]);
 s.innerHTML='<div class="die"><div class="cube">'+[1,2,3,4,5,6].map(v=>`<div class="f f${v}">${P[v].split('').map(x=>'<i'+(x=='1'?' class="on"':'')+'></i>').join('')}</div>`).join('')+'</div></div>';
 s.onclick=()=>{if(busy||isAI()||G.lock||G.rolls==0||G.commit>=0||(card()&&G.rolls>=3))return;G.held[i]^=1;render()};dice.appendChild(s)}
function setDie(i,v,spin){const a=ang[i],b=BASE[v],f=(c,t)=>c+(spin?720:0)+((((t-c)%360)+360)%360);
 a[0]=f(a[0],b[0]);a[1]=f(a[1],b[1]);dice.children[i].querySelector('.cube').style.transform=`rotateX(${a[0]}deg) rotateY(${a[1]}deg)`}
function startTurn(){G.held=[0,0,0,0,0];G.rolls=0;G.lock=false;G.commit=-1;render();if(isAI())aiPlay()}
async function roll(){busy=true;G.rolls++;G.d.forEach((_,i)=>{if(!G.held[i]){G.d[i]=R();setDie(i,G.d[i],1);
 dice.children[i].animate([{transform:'translateY(0)'},{transform:'translateY(-60px) scale(1.25)',offset:.4},{transform:'translateY(0)'}],{duration:900,easing:'ease-out'})}});
 render();await sleep(1000);busy=false;const e=after();render();return e}
function after(){if(G.mode=='rev'){if(G.commit>=0){G.held=G.d.map(v=>v==G.commit+1?1:0);if(G.rolls>=3){G.lock=true;const k=G.commit;setTimeout(()=>score(k),1400);return true}return false}return G.rolls>=3}
 if(cl())return G.rolls>=3;const r=G.row,d=G.d;
 if(r<6){if(G.rolls>=3){fin(sc(r,d)/(r+1));return true}return false}
 if(done(r,d)){fin(G.rolls);return true}if(G.rolls>=30){fin(30);return true}return false}
function fin(v){G.lock=true;G.res[G.p][G.row]=v;setTimeout(next,1700)}
function next(){if(G.mode=='free'){if(G.p==G.chooser){G.p=1-G.chooser;startTurn()}else{if(++G.round>=15)return end();G.chooser=1-G.chooser;G.p=G.chooser;startChoose()}return}
 if(G.p==0)G.p=1;else{G.p=0;G.row++}if(G.row>=15)end();else startTurn()}
function startChoose(){G.row=-1;G.held=[0,0,0,0,0];G.rolls=0;G.lock=false;G.commit=-1;render();
 if(isAI())setTimeout(()=>{G.row=[6,13,8,5,4,3,9,2,1,0,7,10,11,12,14].find(i=>G.res[0][i]===undefined);startTurn()},1300)}
function chooseRow(i){if(G.mode!='free'||G.row>=0||isAI()||busy||G.res[0][i]!==undefined)return;G.row=i;startTurn()}
function score(i){G.sc[G.p][i]=(G.mode=='rev'?rsc:sc)(i,G.d);const N=G.mode=='rev'?13:15;if(Object.keys(G.sc[0]).length==N&&Object.keys(G.sc[1]).length==N)return end();G.p=1-G.p;startTurn()}
function canPick(i){if(!card()||isAI()||busy||G.lock||G.rolls==0||G.sc[G.p][i]!==undefined)return false;
 if(cl())return true;if(G.commit>=0)return false;return i<6?G.rolls==1:i==13?G.rolls==3:true}
function pick(i){if(!canPick(i))return;if(G.mode=='rev'&&i<6)return commitRow(i);score(i)}
function commitRow(i){G.commit=i;G.held=G.d.map(v=>v==i+1?1:0);render()}
function canRoll(){if(busy||isAI()||G.lock)return false;const m=G.mode;if(m=='free'&&G.row<0)return false;
 if(card()&&G.rolls>=3)return false;
 if(m=='rev'&&G.rolls==1&&G.commit<0&&!RV.some(i=>i>=6&&G.sc[G.p][i]===undefined))return false;return true}
$('#roll').onclick=()=>{if(canRoll())roll()};
async function aiPlay(){await sleep(800);if(G.mode=='rev')return aiRev();while(!await roll()){aiHold();render();await sleep(600)}
 if(cl()){await sleep(700);score(aiPick())}}
function aiHold(){const d=G.d,c=cnt(d);let t=G.row;
 if(cl()){const o=i=>G.sc[G.p][i]===undefined,u=new Set(d);t=14;
  if(o(10)&&[1,2,3,4,5].filter(v=>u.has(v)).length>=4)t=10;else if(o(11)&&[2,3,4,5,6].filter(v=>u.has(v)).length>=4)t=11;else if(Math.max(...c.slice(1))<2)t=13}
 const mx=()=>{let b=6;for(let v=6;v>0;v--)if(c[v]>c[b])b=v;return b},seen=new Set();
 const q={},top=n=>{const a=[];for(let v=6;v>0;v--)if(c[v]>=n)a.push(v);return a};
 if(t==7)top(2).slice(0,2).forEach(v=>q[v]=2);
 if(t==12){const T=top(3)[0];if(T){q[T]=3;const p=top(2).find(v=>v!=T);if(p)q[p]=2}else top(2).slice(0,2).forEach(v=>q[v]=2)}
 G.held=d.map(v=>{if(t<6)return v==t+1?1:0;if([6,8,9,14].includes(t))return v==mx()?1:0;if(t==7||t==12){if(q[v]>0){q[v]--;return 1}return 0}
  if(t==10||t==11){const ok=t==10?v<6:v>1;if(ok&&!seen.has(v)){seen.add(v);return 1}return 0}return v>=4?1:0});
 if(!cl()&&G.held.every(x=>x)&&!done(G.row,d))G.held[d.indexOf(Math.min(...d))]=0}
function aiPick(){let b=-1,bv=-1e9;for(let i=0;i<15;i++)if(G.sc[G.p][i]===undefined){const v=sc(i,G.d)-AV[i];if(v>bv){bv=v;b=i}}return b}
const RV=[0,1,2,3,4,5,6,7,8,9,10,12,13],RC=[...Array(15).keys()],AVR={6:6,7:13,8:11,9:14,10:18,12:16,13:17};
const rows=()=>G.mode=='rev'?RV:RC,lbl=i=>G.mode=='rev'&&i==10?'Epäsuora':CATS[i];
function rsc(i,d){const c=cnt(d),s=d.reduce((a,b)=>a+b,0),lo=n=>{const a=[];for(let v=1;v<7;v++)if(c[v]>=n)a.push(v);return a};
 if(i<6){const k=c[i+1];return k==0?4*(i+1):Math.min(k,4)*(i+1)}
 switch(i){case 6:{const a=lo(2);return a.length?2*a[0]:12}
 case 7:{const a=lo(2);return a.length>1?2*(a[0]+a[1]):22}
 case 8:{const a=lo(3);return a.length?3*a[0]:18}
 case 9:{const a=lo(4);return a.length?4*a[0]:24}
 case 10:return c.slice(1).every(x=>x<2)&&s!=15&&s!=20?s:19;
 case 12:{let b=28;for(const t of lo(3))for(const p of lo(2))if(p!=t)b=Math.min(b,3*t+2*p);return b}
 case 13:return s}}
function revPick(){let b=-1,bv=1e9;for(const i of RV)if(i>=6&&G.sc[G.p][i]===undefined&&(i!=13||G.rolls>=3)){const v=rsc(i,G.d)-AVR[i];if(v<bv){bv=v;b=i}}return b}
function revHold(){const d=G.d,c=cnt(d),s=d.reduce((a,b)=>a+b,0);let t=revPick();if(t<0)t=13;
 const lo=n=>{const a=[];for(let v=1;v<7;v++)if(c[v]>=n)a.push(v);return a},q={},sn=new Set();
 let b=1;for(let v=2;v<7;v++)if(c[v]>c[b])b=v;
 if(t==6||t==8||t==9)q[b]=5;
 if(t==7)lo(2).slice(0,2).forEach(v=>q[v]=2);
 if(t==12){const T=lo(3)[0];if(T!==undefined){q[T]=3;const p=lo(2).find(v=>v!=T);if(p)q[p]=2}else lo(2).slice(0,2).forEach(v=>q[v]=2)}
 if((t==7||t==12)&&!Object.keys(q).length)q[b]=5;
 G.held=d.map(v=>{if(t==10){if(!sn.has(v)){sn.add(v);return 1}return 0}if(t==13)return v<=2?1:0;if(q[v]>0){q[v]--;return 1}return 0});
 if(t==10&&G.held.every(x=>x)&&(s==15||s==20))G.held[d.indexOf(d.includes(1)?5:2)]=0}
async function aiRev(){await roll();const d=G.d,c=cnt(d),op=i=>G.sc[G.p][i]===undefined;
 const ups=[0,1,2,3,4,5].filter(op),low=RV.filter(i=>i>=6&&op(i));let pk=-1;
 if(ups.length){const one=ups.filter(i=>c[i+1]==1);if(one.length)pk=Math.max(...one);else if(!low.length)pk=ups.reduce((a,b)=>rsc(b,d)<rsc(a,d)?b:a)}
 if(pk>=0){commitRow(pk);await sleep(700);while(!await roll())await sleep(500);return}
 while(G.rolls<3){revHold();render();await sleep(700);if(await roll())break}
 await sleep(700);score(revPick())}
const us=p=>{let s=0;for(let i=0;i<6;i++)s+=G.sc[p][i]||0;return s},bon=p=>G.mode=='classic'&&us(p)>=63?50:0;
const tot=p=>{let s=us(p)+bon(p);for(let i=6;i<15;i++)s+=G.sc[p][i]||0;return s};
function pts(p,r){const a=G.res[0][r],b=G.res[1][r];if(a===undefined||b===undefined)return 0;const x=G.res[p][r],y=G.res[1-p][r];return x==y?1:((r<6?x>y:x<y)?1:0)}
const dtot=p=>{let s=0;for(let r=0;r<15;r++)s+=pts(p,r);return s};
function render(){const m=G.mode,c=card(),r=G.row,nm=G.n[G.p];
 $('#bar').innerHTML=`<b class="b${G.p}">${nm}</b>`+(m=='free'&&r<0?' valitsee rivin':' vuorossa')+(m=='duel'?` · ${r+1}/15`:m=='free'?` · ${G.round+1}/15`:'');
 [...dice.children].forEach((s,i)=>s.classList.toggle('held',!!G.held[i]));
 $('#roll').disabled=!canRoll();
 $('#roll').textContent=c||(r>=0&&r<6)?`🎲 Heitä (${Math.max(0,3-G.rolls)} jäljellä)`:r<0?'Valitse ensin rivi':`🎲 Heitä (heitto ${G.rolls+1})`;
 let ms;
 if(m=='classic')ms=G.rolls==0?'Heitä nopat!':G.rolls<3?'Napauta noppia lukitaksesi – tai valitse rivi':'Valitse rivi pisteille';
 else if(m=='rev')ms=G.commit>=0?`${CATS[G.commit]} lukittu – ${G.commit+1}-nopat pysyvät lukossa, heitä loput`:G.rolls==0?'Heitä! Tavoite: mahdollisimman pienet pisteet':G.rolls==1?'Valitse yläkerran numero (lukitsee rivin, 3 heittoa) – tai lukitse nopat ja jatka alakertaan':G.rolls<3?'Lukitse nopat tai valitse alakerran rivi':'Valitse rivi (sattuma vain nyt)';
 else if(r<0)ms=`${nm}: napauta taulukosta rivi jota heitetään`;
 else ms=`${r<6?'Kerää mahdollisimman monta numeroa '+(r+1):r==13?'Tavoite: summa vähintään 20':'Tavoite: '+CATS[r]+' – vähiten heittoja'} · heittoja: ${G.rolls}`+(G.lock?' ✔':'');
 $('#msg').textContent=ms;
 let h=`<table><tr><th></th><th class="b0">${G.n[0]}</th><th class="b1">${G.n[1]}</th></tr>`;
 if(c){const cell=(p,i)=>{const v=G.sc[p][i];return v!==undefined?v:(p==G.p&&canPick(i)?`<span class="gh">${(m=='rev'?rsc:sc)(i,G.d)}</span>`:'')};
  const row=i=>`<tr class="${canPick(i)?'op':''}" onclick="pick(${i})"><td>${lbl(i)}</td><td>${cell(0,i)}</td><td>${cell(1,i)}</td></tr>`,L=rows();
  L.slice(0,6).forEach(i=>h+=row(i));
  h+=`<tr class="sub"><td>Yläkerta${m=='classic'?' /63':''}</td><td>${us(0)}</td><td>${us(1)}</td></tr>`+(m=='classic'?`<tr class="sub"><td>Bonus</td><td>${bon(0)}</td><td>${bon(1)}</td></tr>`:'');
  L.slice(6).forEach(i=>h+=row(i));h+=`<tr class="sub"><td>Yhteensä${m=='rev'?' (pienin voittaa)':''}</td><td>${tot(0)}</td><td>${tot(1)}</td></tr>`}
 else{const ch=m=='free'&&r<0&&!isAI();for(let i=0;i<15;i++){const f=p=>{const v=G.res[p][i];return v===undefined?'':(i<6?v:v+' hv')+(pts(p,i)?' ⭐':'')};
  h+=`<tr class="${i==r?'cur':''}${ch&&G.res[0][i]===undefined?' op':''}" onclick="chooseRow(${i})"><td>${CATS[i]}</td><td>${f(0)}</td><td>${f(1)}</td></tr>`}
  h+=`<tr class="sub"><td>Pisteet</td><td>${dtot(0)}</td><td>${dtot(1)}</td></tr>`}
 $('#board').innerHTML=h+'</table>'}
function end(){const t=[0,1].map(p=>card()?tot(p):dtot(p)),rv=G.mode=='rev',w=t[0]==t[1]?-1:(t[0]>t[1])!=rv?0:1;
 [0,1].forEach(p=>{if(!(G.ai&&p==1))saveScore(G.mode,G.n[p],t[p])});
 $('#endc').innerHTML=`<h1>${w<0?'🤝 Tasapeli!':'🏆 '+G.n[w]+' voittaa!'}</h1><table><tr><td>${G.n[0]}</td><td><b>${t[0]}</b></td></tr><tr><td>${G.n[1]}</td><td><b>${t[1]}</b></td></tr></table>
 <div class="fact">🌌 <b>Avaruusfakta:</b><br>${FACTS[Math.floor(Math.random()*FACTS.length)]}</div>
 <button class="big" onclick="$('#end').hidden=true;show('menu')">Uusi peli</button><button style="width:100%" onclick="showHS()">🏆 Huippupisteet</button>`;
 $('#end').hidden=false}
async function saveScore(mode,name,score){try{const l=JSON.parse(localStorage.getItem('ys')||'[]');l.push({mode,name,score,date:new Date().toLocaleDateString('fi-FI')});localStorage.setItem('ys',JSON.stringify(l))}catch(y){}}
let hsData={},hsMode='classic';
function hsRender(){const l=hsData[hsMode]||[];$('#hsl').innerHTML=l.length?'<table>'+l.map((e,i)=>`<tr><td>${i+1}.</td><td>${e.name.replace(/</g,'&lt;')}</td><td><b>${e.score}</b></td><td><small>${e.date}</small></td></tr>`).join('')+'</table>':'Ei vielä tuloksia.'}
async function showHS(){hsData={};
 try{JSON.parse(localStorage.getItem('ys')||'[]').forEach(e=>(hsData[e.mode]=hsData[e.mode]||[]).push(e))}catch(e){}
 ['classic','duel','free','rev'].forEach(m=>hsData[m]=(hsData[m]||[]).sort((a,b)=>m=='rev'?a.score-b.score:b.score-a.score).slice(0,20));hsRender();$('#hs').hidden=false}
seg('#hst',v=>{hsMode=v;hsRender()});$('#hsb').onclick=showHS;$('#hsx').onclick=()=>$('#hs').hidden=true;
</script></body></html>"""

if __name__ == "__main__":
    srv = ThreadingHTTPServer(("0.0.0.0", PORT), H)
    print(f"🚀 Avaruus-Yatzy käynnissä:\n  Tällä koneella: http://localhost:{PORT}\n  Puhelimella (sama wifi): http://{lan_ip()}:{PORT}\n  Lopeta: Ctrl+C")
    if "PORT" not in os.environ:
        threading.Timer(0.8, lambda: webbrowser.open(f"http://localhost:{PORT}")).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nNähdään avaruudessa!")
