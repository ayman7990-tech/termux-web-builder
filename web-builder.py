#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, re, time, threading, subprocess, urllib.request, urllib.error
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = 8000
HOME = Path.home()
KEY_FILE = HOME / ".groq-key"
MODEL = "openai/gpt-oss-120b"

# User-Agent مهم جداً لتجاوز حماية Cloudflare
HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "ar,en;q=0.9",
}

def get_key():
    return KEY_FILE.read_text().strip() if KEY_FILE.exists() else ""

def ask_ai(idea):
    key = get_key()
    if not key:
        return {"error": "مفتاح Groq مش موجود"}
    
    prompt = (
        "أنت مبرمج محترف. ابنِ تطبيق ويب كامل بناءً على الفكرة: " + idea + "\n\n"
        "ارجع JSON فقط بالشكل ده (بدون أي كلام قبله أو بعده):\n\n"
        "{\n"
        '  "name": "app-name-english",\n'
        '  "title": "عنوان عربي",\n'
        '  "description": "وصف عربي",\n'
        '  "html": "كود HTML كامل ملف واحد مع style و script جواه. بالعربي و dir=rtl. يستخدم fetch على /api/items.",\n'
        '  "server": "كود Node.js Express كامل. فيه express.json() و express.static public. مسارات: GET POST DELETE /api/items. يحفظ في data/items.json. يشتغل على port 3000."\n'
        "}\n\n"
        "قواعد:\n"
        "- html ملف واحد كامل\n"
        "- server كود express كامل\n"
        "- تصميم جميل وعصري\n"
        '- كل النصوص بالعربي و dir="rtl"\n'
    )
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    body = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "أنت مبرمج محترف. ترجع JSON فقط."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.6,
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
        err_body = e.read().decode()[:200]
        return {"error": "HTTP " + str(e.code) + ": " + err_body}
    except Exception as e:
        return {"error": "فشل: " + str(e)}

jobs = {}

def add_log(jid, msg):
    if jid not in jobs:
        jobs[jid] = {"status": "building", "log": [], "error": None, "folder": None}
    jobs[jid]["log"].append(msg)

def build(jid, idea):
    add_log(jid, "🧠 بيسأل Groq (" + MODEL + ")...")
    result = ask_ai(idea)
    if "error" in result:
        jobs[jid]["status"] = "error"
        jobs[jid]["error"] = result["error"]
        add_log(jid, "❌ " + result["error"])
        return
    name = re.sub(r'[^a-zA-Z0-9-]', '', result.get("name", "app"))[:25] or "app"
    folder = HOME / ("built-" + name + "-" + str(int(time.time()) % 10000))
    add_log(jid, "📁 إنشاء: " + folder.name)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "public").mkdir(exist_ok=True)
    (folder / "data").mkdir(exist_ok=True)
    add_log(jid, "📝 كتابة server.js...")
    (folder / "server.js").write_text(result.get("server", ""), encoding="utf-8")
    add_log(jid, "🎨 كتابة index.html...")
    (folder / "public" / "index.html").write_text(result.get("html", ""), encoding="utf-8")
    (folder / "package.json").write_text(json.dumps({
        "name": name, "version": "1.0.0", "main": "server.js",
        "scripts": {"start": "node server.js"},
        "dependencies": {"express": "^4.18.0"}
    }, indent=2))
    add_log(jid, "📦 تثبيت express...")
    subprocess.run("npm install express --silent", shell=True, cwd=str(folder),
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180)
    add_log(jid, "🚀 تشغيل السيرفر...")
    subprocess.Popen('cd "' + str(folder) + '" && nohup node server.js > server.log 2>&1 &', shell=True)
    time.sleep(3)
    jobs[jid]["status"] = "done"
    jobs[jid]["folder"] = folder.name
    add_log(jid, "✅ تم! افتح http://localhost:3000")

HTML = """<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Web Builder</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,Arial,sans-serif;background:linear-gradient(135deg,#0a0a1a,#1a1a2e);color:#fff;min-height:100vh;padding:15px;line-height:1.6}
.c{max-width:800px;margin:0 auto}
.header{background:linear-gradient(135deg,#f55036,#ff8a00);padding:30px 20px;border-radius:20px;text-align:center;margin-bottom:20px}
.header h1{font-size:24px;margin-bottom:6px}
.header p{opacity:.95;font-size:13px}
.card{background:#161b22;border:1px solid #30363d;border-radius:20px;padding:20px;margin-bottom:20px}
.card h2{font-size:16px;margin-bottom:12px;color:#ff8a00}
textarea{width:100%;padding:12px;background:#0d1117;border:2px solid #30363d;border-radius:10px;color:#fff;font-size:14px;outline:none;resize:vertical;min-height:100px}
textarea:focus{border-color:#ff8a00}
.btn{padding:14px;border:none;border-radius:12px;font-size:16px;font-weight:bold;cursor:pointer;width:100%;margin-top:15px;background:linear-gradient(135deg,#f55036,#ff8a00);color:#fff}
.btn:disabled{opacity:.5}
.output{background:#0d1117;border:1px solid #30363d;border-radius:12px;padding:14px;font-family:monospace;font-size:12px;color:#79c0ff;direction:ltr;text-align:left;white-space:pre-wrap;word-break:break-all;max-height:350px;overflow-y:auto;margin-top:12px;display:none}
.output.show{display:block}
.link{display:block;text-align:center;padding:14px;background:linear-gradient(135deg,#238636,#2ea043);color:#fff;text-decoration:none;border-radius:12px;font-weight:bold;margin-top:12px;display:none}
.link.show{display:block}
.footer{text-align:center;padding:20px;color:#64748b;font-size:12px}
</style>
</head>
<body>
<div class="c">
<div class="header"><h1>Web Builder</h1><p>اكتب فكرتك، والتطبيق يتبني في ثواني</p></div>
<div class="card">
<h2>💡 فكرتك</h2>
<textarea id="idea" placeholder="مثال: تطبيق آلة حاسبة بتصميم عصري"></textarea>
<button class="btn" id="btn" onclick="build()">⚡ ابنِ التطبيق</button>
<div class="output" id="out"></div>
<a class="link" id="openLink" href="http://localhost:3000" target="_blank">🌐 افتح التطبيق</a>
</div>
<div class="footer">Groq + gpt-oss-120b — Termux</div>
</div>
<script>
async function build(){
  var idea=document.getElementById('idea').value.trim();
  if(!idea){alert('اكتب فكرتك');return;}
  document.getElementById('btn').disabled=true;
  document.getElementById('btn').textContent='جاري البناء...';
  document.getElementById('out').classList.add('show');
  document.getElementById('out').textContent='بيسأل Groq...';
  document.getElementById('openLink').classList.remove('show');
  try{
    var r=await fetch('/api/build',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({idea:idea})});
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
    if(j.status==='done'){o.textContent+='\\n\\nتم!';document.getElementById('openLink').classList.add('show');reset();}
    else if(j.status==='error'){o.textContent+='\\n\\nخطأ: '+(j.error||'فشل');reset();}
    else setTimeout(function(){poll(id)},1500);
  }catch(e){setTimeout(function(){poll(id)},2000);}
}
function reset(){document.getElementById('btn').disabled=false;document.getElementById('btn').textContent='⚡ ابنِ التطبيق';}
</script>
</body>
</html>"""

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _j(self, d, c=200):
        b = json.dumps(d, ensure_ascii=False).encode()
        self.send_response(c)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(b)))
        self.end_headers()
        self.wfile.write(b)
    def _h(self, t):
        b = t.encode()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(b)))
        self.end_headers()
        self.wfile.write(b)
    def do_GET(self):
        if self.path in ('/', '/index.html'):
            self._h(HTML)
        elif self.path == '/api/jobs':
            self._j({"jobs": jobs})
        elif self.path.startswith('/api/job/'):
            i = self.path.split('/')[-1]
            self._j(jobs.get(i, {"error": "not found"}))
        else:
            self.send_response(404); self.end_headers()
    def do_POST(self):
        if self.path == '/api/build':
            n = int(self.headers.get('Content-Length', 0))
            d = json.loads(self.rfile.read(n).decode())
            jid = str(int(time.time() * 1000))
            jobs[jid] = {"status": "building", "log": [], "error": None, "folder": None}
            threading.Thread(target=build, args=(jid, d.get('idea', '')), daemon=True).start()
            self._j({"job_id": jid})
        else:
            self.send_response(404); self.end_headers()

if __name__ == '__main__':
    if not get_key():
        print("❌ مفتاح Groq مش موجود!")
        print('اكتب: printf "%s" "gsk_..." > ~/.groq-key')
        exit(1)
    print("=" * 50)
    print("⚡ Web Builder — النسخة النهائية")
    print("=" * 50)
    print("📡 http://localhost:" + str(PORT))
    print("🤖 Model: " + MODEL)
    print("🌐 User-Agent: مضاف (لتجاوز Cloudflare)")
    print("=" * 50)
    HTTPServer(('0.0.0.0', PORT), H).serve_forever()
