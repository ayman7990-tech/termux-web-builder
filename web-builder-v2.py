#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
⚡ Web Builder v2.0 — النسخة الشاملة
"""
import json, re, time, threading, subprocess, urllib.request, urllib.error
import shutil, zipfile
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = 8000
HOME = Path.home()
KEY_FILE = HOME / ".secrets" / ".groq-key"
if not KEY_FILE.exists():
    KEY_FILE = HOME / ".groq-key"
BUILDS_DIR = HOME / "projects" / "generated-apps"
MODEL = "openai/gpt-oss-120b"

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    "Accept": "application/json",
}

def get_key():
    return KEY_FILE.read_text().strip() if KEY_FILE.exists() else ""

def ask_ai(idea, color_choice):
    key = get_key()
    if not key:
        return {"error": "مفتاح Groq مش موجود"}

    colors = {
        "1": ["#667eea", "#764ba2", "بنفسجي"],
        "2": ["#1f6feb", "#388bfd", "أزرق"],
        "3": ["#22c55e", "#10b981", "أخضر"],
        "4": ["#ef4444", "#dc2626", "أحمر"],
        "5": ["#f59e0b", "#f97316", "برتقالي"],
        "6": ["#ec4899", "#8b5cf6", "وردي"],
    }
    c1, c2, cname = colors.get(color_choice, colors["1"])

    prompt = (
        "أنت مبرمج محترف. ابنِ تطبيق ويب كامل بناءً على الفكرة: " + idea + "\n\n"
        "اللون الأساسي: " + c1 + " والثانوي: " + c2 + " (استخدمهم في التصميم)\n\n"
        "ارجع JSON فقط بالشكل ده:\n\n"
        "{\n"
        '  "name": "app-name-english",\n'
        '  "title": "عنوان عربي",\n'
        '  "description": "وصف عربي",\n'
        '  "html": "كود HTML كامل ملف واحد مع <style> و<script> جواه. بالعربي و dir=rtl. اللون الأساسي ' + c1 + ' والثانوي ' + c2 + '. يستخدم fetch على /api/items.",\n'
        '  "server": "كود Node.js Express كامل. فيه express.json() و express.static(public). مسارات: GET/POST/DELETE /api/items. يحفظ في data/items.json. يشتغل على port 3000."\n'
        "}\n\n"
        "قواعد:\n"
        "- html ملف واحد كامل\n"
        "- server كود express كامل\n"
        "- تصميم جميل وعصري ومناسب للموبايل\n"
        '- كل النصوص بالعربي و dir="rtl"\n'
    )

    url = "https://api.groq.com/openai/v1/chat/completions"
    body = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "أنت مبرمج محترف. ترجع JSON فقط."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 8000,
        "response_format": {"type": "json_object"}
    }).encode()

    headers = dict(HEADERS)
    headers["Authorization"] = "Bearer " + key
    req = urllib.request.Request(url, data=body, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            data = json.loads(r.read().decode())
            text = data["choices"][0]["message"]["content"]
            match = re.search(r'\{[\s\S]*\}', text)
            if match:
                return json.loads(match.group())
            return {"error": "الرد مش JSON"}
    except urllib.error.HTTPError as e:
        return {"error": "HTTP " + str(e.code) + ": " + e.read().decode()[:200]}
    except Exception as e:
        return {"error": "فشل: " + str(e)}

# ============================================
# إدارة المهام
# ============================================
jobs = {}
BUILDS_DIR.mkdir(parents=True, exist_ok=True)

def add_log(jid, msg):
    if jid not in jobs:
        jobs[jid] = {"status": "building", "log": [], "error": None, "folder": None}
    jobs[jid]["log"].append(msg)

def build(jid, idea, color_choice, do_github):
    add_log(jid, "🧠 بيسأل Groq...")
    result = ask_ai(idea, color_choice)

    if "error" in result:
        jobs[jid]["status"] = "error"
        jobs[jid]["error"] = result["error"]
        add_log(jid, "❌ " + result["error"])
        return

    name = re.sub(r'[^a-zA-Z0-9-]', '', result.get("name", "app"))[:25] or "app"
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    folder_name = "app-" + name + "-" + timestamp
    folder = BUILDS_DIR / folder_name

    add_log(jid, "📁 إنشاء: " + folder_name)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "public").mkdir(exist_ok=True)
    (folder / "data").mkdir(exist_ok=True)

    add_log(jid, "📝 كتابة server.js...")
    (folder / "server.js").write_text(result.get("server", ""), encoding="utf-8")

    add_log(jid, "🎨 كتابة index.html...")
    (folder / "public" / "index.html").write_text(result.get("html", ""), encoding="utf-8")

    # حفظ الميتاداتا
    meta = {
        "title": result.get("title", idea),
        "description": result.get("description", ""),
        "idea": idea,
        "color": color_choice,
        "created": datetime.now().isoformat(),
        "name": name,
        "folder": folder_name,
    }
    (folder / ".meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    (folder / "package.json").write_text(json.dumps({
        "name": name, "version": "1.0.0", "main": "server.js",
        "scripts": {"start": "node server.js"},
        "dependencies": {"express": "^4.18.0"}
    }, indent=2))

    (folder / "README.md").write_text(
        "# " + meta["title"] + "\n\n" + meta["description"] + "\n\n## التشغيل\n\nnpm install\nnode server.js\n",
        encoding="utf-8"
    )

    add_log(jid, "📦 تثبيت express...")
    subprocess.run("npm install express --silent", shell=True, cwd=str(folder),
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180)

    add_log(jid, "🚀 تشغيل السيرفر...")
    subprocess.Popen('cd "' + str(folder) + '" && nohup node server.js > server.log 2>&1 &', shell=True)
    time.sleep(3)

    if do_github:
        add_log(jid, "🐙 رفع على GitHub...")
        try:
            upload_github(folder, folder_name, jid)
        except Exception as e:
            add_log(jid, "⚠️ فشل الرفع: " + str(e))

    jobs[jid]["status"] = "done"
    jobs[jid]["folder"] = folder_name
    add_log(jid, "✅ تم!")

def upload_github(folder, name, jid):
    tf = HOME / ".config" / "termux-github" / "token.txt"
    if not tf.exists():
        add_log(jid, "⚠️ التوكن مش موجود")
        return
    token = tf.read_text().strip()
    if ':' not in token:
        return
    user, tok = token.split(':', 1)
    req = urllib.request.Request("https://api.github.com/user",
                                 headers={"Authorization": "token " + tok})
    with urllib.request.urlopen(req, timeout=10) as r:
        user = json.loads(r.read().decode()).get("login")
    if not (folder / ".git").exists():
        subprocess.run("git init && git branch -M main", shell=True, cwd=str(folder))
        subprocess.run('git config user.email "' + user + '@users.noreply.github.com"', shell=True, cwd=str(folder))
        subprocess.run('git config user.name "' + user + '"', shell=True, cwd=str(folder))
    subprocess.run("git add .", shell=True, cwd=str(folder))
    subprocess.run('git commit -m "Build: ' + name + '"', shell=True, cwd=str(folder))
    data = json.dumps({"name": name, "private": False}).encode()
    req = urllib.request.Request("https://api.github.com/user/repos", data=data,
                                 headers={"Authorization": "token " + tok, "Content-Type": "application/json"},
                                 method="POST")
    try:
        urllib.request.urlopen(req, timeout=15)
    except urllib.error.HTTPError as e:
        if e.code != 422:
            return
    push = "https://" + user + ":" + tok + "@github.com/" + user + "/" + name + ".git"
    subprocess.run("git remote remove origin", shell=True, cwd=str(folder))
    subprocess.run("git remote add origin https://github.com/" + user + "/" + name + ".git", shell=True, cwd=str(folder))
    subprocess.run("git push " + push + " main -u --force", shell=True, cwd=str(folder))
    subprocess.run("git remote set-url origin https://github.com/" + user + "/" + name + ".git", shell=True, cwd=str(folder))
    add_log(jid, "✅ https://github.com/" + user + "/" + name)

# ============================================
# قائمة التطبيقات
# ============================================
def list_apps():
    apps = []
    if not BUILDS_DIR.exists():
        return apps
    for folder in sorted(BUILDS_DIR.iterdir(), reverse=True):
        if not folder.is_dir():
            continue
        meta = {}
        meta_file = folder / ".meta.json"
        if meta_file.exists():
            try:
                meta = json.loads(meta_file.read_text())
            except:
                pass
        # حجم المجلد
        size = sum(f.stat().st_size for f in folder.rglob('*') if f.is_file())
        # هل السيرفر شغال؟
        running = (folder / "server.log").exists() and (folder / "node_modules").exists()
        apps.append({
            "folder": folder.name,
            "title": meta.get("title", folder.name),
            "description": meta.get("description", ""),
            "created": meta.get("created", ""),
            "size": size,
            "color": meta.get("color", "1"),
            "running": running,
        })
    return apps

def delete_app(folder_name):
    folder = BUILDS_DIR / folder_name
    if folder.exists() and folder.is_dir():
        # إيقاف السيرفر لو شغال
        subprocess.run("pkill -f '" + folder_name + "'", shell=True)
        shutil.rmtree(folder)
        return True
    return False

def export_app(folder_name):
    folder = BUILDS_DIR / folder_name
    if not folder.exists():
        return None
    zip_path = HOME / (folder_name + ".zip")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for f in folder.rglob('*'):
            if f.is_file() and 'node_modules' not in str(f):
                zf.write(f, f.relative_to(folder.parent))
    return zip_path

# ============================================
# HTML
# ============================================
HTML = """<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Web Builder v2.0</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,Arial,sans-serif;background:linear-gradient(135deg,#0a0a1a,#1a1a2e);color:#fff;min-height:100vh;padding:15px;line-height:1.6}
.c{max-width:900px;margin:0 auto}
.header{background:linear-gradient(135deg,#f55036,#ff8a00);padding:35px 20px;border-radius:20px;text-align:center;margin-bottom:20px}
.header h1{font-size:26px;margin-bottom:6px}
.header p{opacity:.95;font-size:14px}
.badge{display:inline-block;background:rgba(255,255,255,.2);padding:3px 10px;border-radius:10px;font-size:11px;margin-top:8px}
.card{background:#161b22;border:1px solid #30363d;border-radius:20px;padding:20px;margin-bottom:20px}
.card h2{font-size:16px;margin-bottom:15px;color:#ff8a00;display:flex;align-items:center;gap:8px}
label{display:block;font-size:13px;color:#8b949e;margin-bottom:6px;margin-top:10px}
textarea,select,input{width:100%;padding:12px;background:#0d1117;border:2px solid #30363d;border-radius:10px;color:#fff;font-size:14px;outline:none;font-family:inherit}
textarea:focus,select:focus,input:focus{border-color:#ff8a00}
textarea{resize:vertical;min-height:90px}
.btn{padding:14px;border:none;border-radius:12px;font-size:15px;font-weight:bold;cursor:pointer;width:100%;margin-top:15px;background:linear-gradient(135deg,#f55036,#ff8a00);color:#fff;font-family:inherit}
.btn:disabled{opacity:.5}
.btn-secondary{background:#238636;margin-top:8px}
.output{background:#0d1117;border:1px solid #30363d;border-radius:12px;padding:14px;font-family:monospace;font-size:12px;color:#79c0ff;direction:ltr;text-align:left;white-space:pre-wrap;word-break:break-all;max-height:300px;overflow-y:auto;margin-top:12px;display:none}
.output.show{display:block}
.app{background:#0d1117;border:1px solid #30363d;border-radius:12px;padding:14px;margin-bottom:10px;display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap}
.app-info{flex:1;min-width:200px}
.app-title{font-weight:bold;color:#ffd700;margin-bottom:4px}
.app-desc{font-size:12px;color:#8b949e;margin-bottom:4px}
.app-meta{font-size:11px;color:#64748b}
.app-actions{display:flex;gap:6px;flex-wrap:wrap}
.icon-btn{background:#21262d;border:1px solid #30363d;color:#fff;padding:8px 12px;border-radius:8px;cursor:pointer;font-size:14px;text-decoration:none;display:inline-flex;align-items:center}
.icon-btn:hover{background:#30363d}
.icon-btn.danger{background:#7f1d1d;border-color:#991b1b}
.icon-btn.success{background:#14532d;border-color:#166534}
.empty{text-align:center;padding:40px;color:#64748b}
.count-badge{background:rgba(255,138,0,.2);color:#ff8a00;padding:3px 10px;border-radius:10px;font-size:12px;margin-right:8px}
.toggle{display:flex;align-items:center;gap:8px;margin-top:10px;font-size:13px;color:#8b949e}
.toggle input{width:auto}
.footer{text-align:center;padding:20px;color:#64748b;font-size:12px}
</style>
</head>
<body>
<div class="c">
<div class="header">
<h1>⚡ Web Builder</h1>
<p>اكتب فكرتك، والتطبيق يتبني في ثواني</p>
<div class="badge">v2.0 الشاملة</div>
</div>

<div class="card">
<h2>💡 فكرتك</h2>
<textarea id="idea" placeholder="مثال: تطبيق آلة حاسبة بتصميم عصري"></textarea>
<label>اللون</label>
<select id="color">
<option value="1">🟣 بنفسجي</option>
<option value="2">🔵 أزرق</option>
<option value="3">🟢 أخضر</option>
<option value="4">🔴 أحمر</option>
<option value="5">🟠 برتقالي</option>
<option value="6">💗 وردي</option>
</select>
<label class="toggle"><input type="checkbox" id="github"> 🐙 ارفع على GitHub</label>
<button class="btn" id="btn" onclick="build()">⚡ ابنِ التطبيق</button>
<div class="output" id="out"></div>
</div>

<div class="card">
<h2>📦 التطبيقات المبنية <span class="count-badge" id="count">0</span></h2>
<button class="btn btn-secondary" onclick="loadApps()">🔄 تحديث القايمة</button>
<div id="apps" style="margin-top:15px">
<p class="empty">جاري التحميل...</p>
</div>
</div>

<div class="footer">⚡ Web Builder v2.0 — Groq + GPT-OSS-120B</div>
</div>

<script>
async function build(){
  var idea=document.getElementById('idea').value.trim();
  if(!idea){alert('اكتب فكرتك');return;}
  var color=document.getElementById('color').value;
  var github=document.getElementById('github').checked;
  document.getElementById('btn').disabled=true;
  document.getElementById('btn').textContent='جاري البناء...';
  document.getElementById('out').classList.add('show');
  document.getElementById('out').textContent='بيسأل Groq...';
  try{
    var r=await fetch('/api/build',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({idea:idea,color:color,github:github})});
    var d=await r.json();
    if(d.job_id) poll(d.job_id);
    else{document.getElementById('out').textContent='خطأ: '+(d.error||'فشل');reset();}
  }catch(e){document.getElementById('out').textContent='خطأ: '+e.message;reset();}
}
async function poll(id){
  try{
    var r=await fetch('/api/job/'+id);
    var j=await r.json();
    var o=document.getElementById('out');
    o.textContent=(j.log||[]).join('\\n');
    o.scrollTop=o.scrollHeight;
    if(j.status==='done'){o.textContent+='\\n\\n🎉 تم!';reset();loadApps();}
    else if(j.status==='error'){o.textContent+='\\n\\n❌ '+(j.error||'فشل');reset();}
    else setTimeout(function(){poll(id)},1500);
  }catch(e){setTimeout(function(){poll(id)},2000);}
}
function reset(){document.getElementById('btn').disabled=false;document.getElementById('btn').textContent='⚡ ابنِ التطبيق';}

async function loadApps(){
  try{
    var r=await fetch('/api/apps');
    var d=await r.json();
    var apps=d.apps||[];
    document.getElementById('count').textContent=apps.length;
    if(!apps.length){document.getElementById('apps').innerHTML='<p class="empty">📭 مفيش تطبيقات بعد</p>';return;}
    var html='';
    for(var i=0;i<apps.length;i++){
      var a=apps[i];
      var size=(a.size/1024).toFixed(1)+' KB';
      var date=a.created?a.created.substring(0,10):'';
      var runIcon=a.running?'🟢':'⚪';
      html+='<div class="app">';
      html+='<div class="app-info">';
      html+='<div class="app-title">'+runIcon+' '+a.title+'</div>';
      html+='<div class="app-desc">'+a.description+'</div>';
      html+='<div class="app-meta">📅 '+date+' | 📦 '+size+'</div>';
      html+='</div>';
      html+='<div class="app-actions">';
      html+='<a class="icon-btn success" href="http://localhost:3000" target="_blank">🌐</a>';
      html+='<button class="icon-btn" onclick="exportApp(\\''+a.folder+'\\')">📦</button>';
      html+='<button class="icon-btn danger" onclick="deleteApp(\\''+a.folder+'\\')">🗑️</button>';
      html+='</div>';
      html+='</div>';
    }
    document.getElementById('apps').innerHTML=html;
  }catch(e){document.getElementById('apps').innerHTML='<p class="empty">خطأ: '+e.message+'</p>';}
}

async function deleteApp(folder){
  if(!confirm('متأكد إنك عايز تمسح '+folder+'؟')) return;
  try{
    await fetch('/api/delete/'+folder,{method:'DELETE'});
    loadApps();
  }catch(e){alert('خطأ: '+e.message);}
}

async function exportApp(folder){
  window.open('/api/export/'+folder,'_blank');
}

loadApps();
setInterval(loadApps,15000);
</script>
</body>
</html>"""

# ============================================
# HTTP Handler
# ============================================
class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def _json(self, d, c=200):
        b = json.dumps(d, ensure_ascii=False).encode()
        self.send_response(c)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def _html(self, t):
        b = t.encode()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def _file(self, path, name):
        try:
            data = path.read_bytes()
            self.send_response(200)
            self.send_header('Content-Type', 'application/zip')
            self.send_header('Content-Disposition', 'attachment; filename="' + name + '"')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except:
            self.send_response(404); self.end_headers()

    def do_GET(self):
        if self.path in ('/', '/index.html'):
            self._html(HTML)
        elif self.path == '/api/apps':
            self._json({"apps": list_apps()})
        elif self.path.startswith('/api/export/'):
            name = self.path.split('/')[-1]
            zip_path = export_app(name)
            if zip_path and zip_path.exists():
                self._file(zip_path, name + ".zip")
            else:
                self._json({"error": "not found"}, 404)
        elif self.path.startswith('/api/job/'):
            i = self.path.split('/')[-1]
            self._json(jobs.get(i, {"error": "not found"}))
        else:
            self.send_response(404); self.end_headers()

    def do_DELETE(self):
        if self.path.startswith('/api/delete/'):
            name = self.path.split('/')[-1]
            ok = delete_app(name)
            self._json({"ok": ok})
        else:
            self.send_response(404); self.end_headers()

    def do_POST(self):
        if self.path == '/api/build':
            n = int(self.headers.get('Content-Length', 0))
            d = json.loads(self.rfile.read(n).decode())
            jid = str(int(time.time() * 1000))
            jobs[jid] = {"status": "building", "log": [], "error": None, "folder": None}
            t = threading.Thread(target=build, args=(jid, d.get('idea', ''), d.get('color', '1'), d.get('github', False)), daemon=True)
            t.start()
            self._json({"job_id": jid})
        else:
            self.send_response(404); self.end_headers()

# ============================================
# التشغيل
# ============================================
if __name__ == '__main__':
    if not get_key():
        print("❌ مفتاح Groq مش موجود!")
        print('اكتب: printf "%s" "gsk_..." > ~/.secrets/.groq-key')
        exit(1)
    print("")
    print("═══════════════════════════════════════════")
    print("⚡ Web Builder v2.0 — النسخة الشاملة")
    print("═══════════════════════════════════════════")
    print("📡 http://localhost:" + str(PORT))
    print("🤖 Model: " + MODEL)
    print("📁 Builds: " + str(BUILDS_DIR))
    print("═══════════════════════════════════════════")
    print("🛑 CTRL+C للإيقاف")
    print("")
    try:
        HTTPServer(('0.0.0.0', PORT), H).serve_forever()
    except KeyboardInterrupt:
        print("\n👋 وداعاً!")
