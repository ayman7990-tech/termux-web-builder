#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, json, subprocess, shutil, re, time, socket, threading
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = 8000
HOME = Path.home()
JOBS_FILE = HOME / "builder-jobs.json"

CATS = {
    "notes":    {"kw": ["ملاحظات","مذكرة","دفتر"], "name": "ملاحظات", "fields": ["العنوان","المحتوى"]},
    "todo":     {"kw": ["مهام","مهمة","todo"], "name": "مهام", "fields": ["العنوان","الوصف"]},
    "books":    {"kw": ["كتب","كتاب","مكتبة"], "name": "مكتبة كتب", "fields": ["العنوان","المؤلف"]},
    "expenses": {"kw": ["مصاريف","مصروف","فلوس"], "name": "مصاريف", "fields": ["الوصف","المبلغ"]},
    "contacts": {"kw": ["جهات","أرقام"], "name": "جهات اتصال", "fields": ["الاسم","الرقم"]},
    "custom":   {"kw": [], "name": "مخصص", "fields": ["العنوان","الوصف"]},
}

def analyze(idea):
    low = idea.lower()
    best = "custom"; best_score = 0
    for k, c in CATS.items():
        if k == "custom": continue
        score = sum(1 for w in c["kw"] if w in low)
        if score > best_score:
            best_score = score; best = k
    return CATS[best]

SERVER_JS = '''const express = require('express');
const fs = require('fs');
const path = require('path');
const app = express();
const PORT = 3000;
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static('public'));
const DIR = './data';
if (!fs.existsSync(DIR)) fs.mkdirSync(DIR);
const FILE = path.join(DIR, 'items.json');
if (!fs.existsSync(FILE)) fs.writeFileSync(FILE, '[]');
function load() { try { return JSON.parse(fs.readFileSync(FILE, 'utf8')); } catch(e) { return []; } }
function save(items) { fs.writeFileSync(FILE, JSON.stringify(items, null, 2)); }
app.get('/api/items', (req, res) => res.json(load()));
app.post('/api/items', (req, res) => {
  const items = load();
  items.push({ id: Date.now(), ...req.body, createdAt: new Date().toISOString() });
  save(items);
  res.json({ ok: true });
});
app.delete('/api/items/:id', (req, res) => {
  save(load().filter(i => i.id != req.params.id));
  res.json({ ok: true });
});
app.listen(PORT, '0.0.0.0', () => console.log('Running on http://localhost:' + PORT));
'''

def make_html(name, desc, fields, color):
    fields_input = ""
    for f in fields:
        if f in ["الوصف", "المحتوى"]:
            fields_input += '<textarea name="' + f + '" placeholder="' + f + '..." rows="3" required></textarea>\n'
        else:
            fields_input += '<input type="text" name="' + f + '" placeholder="' + f + '..." required>\n'
    f1 = fields[0]
    f2 = fields[1] if len(fields) > 1 else ""
    c1, c2 = color
    return '''<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>''' + name + '''</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Arial,sans-serif;background:linear-gradient(135deg,#0f0c29,#24243e);color:#fff;min-height:100vh;padding:20px}
.c{max-width:800px;margin:0 auto}
.header{background:linear-gradient(135deg,''' + c1 + ',''' + c2 + ''');padding:35px 20px;border-radius:20px;text-align:center;margin-bottom:20px}
.header h1{font-size:28px;margin-bottom:8px}
.header p{opacity:.9;font-size:14px}
.card{background:rgba(255,255,255,.05);border-radius:16px;padding:20px;margin-bottom:16px;border:1px solid rgba(255,255,255,.1)}
.card h2{font-size:16px;margin-bottom:14px;color:''' + c1 + '''}
input,textarea{width:100%;padding:12px;border-radius:10px;border:1px solid rgba(255,255,255,.1);background:rgba(0,0,0,.3);color:#fff;font-family:inherit;font-size:14px;margin-bottom:10px}
input:focus,textarea:focus{outline:none;border-color:''' + c1 + '''}
button{padding:14px;border-radius:10px;border:none;background:linear-gradient(135deg,''' + c1 + ',''' + c2 + ''');color:#fff;font-weight:bold;cursor:pointer;font-size:15px;width:100%;font-family:inherit}
button:active{transform:scale(.98)}
.item{background:rgba(0,0,0,.3);padding:14px;border-radius:10px;margin-bottom:10px;display:flex;justify-content:space-between;align-items:center;gap:10px}
.info{flex:1}
.item h3{font-size:16px;margin-bottom:6px}
.item p{font-size:13px;color:#94a3b8;margin:2px 0}
.del{background:#ef4444;padding:8px 12px;border-radius:8px;cursor:pointer;font-size:12px;color:#fff;border:none}
.empty{text-align:center;padding:40px;color:#64748b}
.count{background:rgba(255,255,255,.1);padding:4px 12px;border-radius:12px;font-size:12px;margin-right:8px}
.footer{text-align:center;padding:20px;color:#64748b;font-size:12px}
</style>
</head>
<body>
<div class="c">
<div class="header">
<h1>''' + name + '''</h1>
<p>''' + desc + '''</p>
</div>
<div class="card">
<h2>➕ إضافة جديد</h2>
<form id="f" onsubmit="add(event)">
''' + fields_input + '''
<button type="submit">➕ إضافة</button>
</form>
</div>
<div class="card">
<h2>📋 القائمة <span class="count" id="count">0</span></h2>
<div id="list">جاري التحميل...</div>
</div>
<div class="footer">تم بناؤه تلقائياً — Termux 2026</div>
</div>
<script>
async function load() {
  const r = await fetch('/api/items');
  const items = await r.json();
  const el = document.getElementById('list');
  document.getElementById('count').textContent = items.length;
  if (!items.length) { el.innerHTML = '<div class="empty">📭 مفيش عناصر</div>'; return; }
  el.innerHTML = items.map(item => {
    const t = item["''' + f1 + '''"] || "بدون عنوان";
    const c = item["''' + f2 + '''"] || "";
    return '<div class="item"><div class="info"><h3>' + t + '</h3><p>' + c + '</p></div><button class="del" onclick="del(' + item.id + ')">🗑️</button></div>';
  }).join('');
}
async function add(e) {
  e.preventDefault();
  const data = {};
  new FormData(e.target).forEach((v,k) => data[k] = v);
  await fetch('/api/items', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(data)});
  e.target.reset();
  load();
}
async function del(id) {
  if (!confirm('متأكد؟')) return;
  await fetch('/api/items/' + id, {method:'DELETE'});
  load();
}
load();
</script>
</body>
</html>
'''

jobs = {}

def load_jobs():
    global jobs
    try:
        if JOBS_FILE.exists(): jobs = json.loads(JOBS_FILE.read_text())
    except: jobs = {}

def save_jobs():
    try: JOBS_FILE.write_text(json.dumps(jobs, ensure_ascii=False, indent=2))
    except: pass

def add_log(job_id, msg):
    if job_id not in jobs:
        jobs[job_id] = {"status": "building", "log": [], "folder": None, "error": None}
    jobs[job_id]["log"].append(msg)
    save_jobs()

def build_project(job_id, idea, name, desc, fields, color, do_github):
    try:
        cat = analyze(idea)
        folder_name = re.sub(r'[^\w\s-]', '', name).strip().replace(' ', '-')[:30]
        if not folder_name or re.search(r'[\u0600-\u06FF]', folder_name):
            folder_name = cat.get("prefix", "app") + "-" + datetime.now().strftime("%H%M")
        folder = HOME / folder_name
        add_log(job_id, f"📁 إنشاء المجلد: {folder_name}")
        if folder.exists(): shutil.rmtree(folder)
        folder.mkdir(parents=True)
        (folder / "public").mkdir()
        (folder / "data").mkdir()
        add_log(job_id, "⚙️ كتابة server.js...")
        (folder / "server.js").write_text(SERVER_JS, encoding='utf-8')
        pkg = {"name": folder_name, "version": "1.0.0", "main": "server.js",
               "scripts": {"start": "node server.js"},
               "dependencies": {"express": "^4.18.0"}}
        (folder / "package.json").write_text(json.dumps(pkg, indent=2))
        add_log(job_id, "🎨 كتابة index.html...")
        (folder / "public" / "index.html").write_text(make_html(name, desc, fields, color), encoding='utf-8')
        readme = f"# {name}\n\n{desc}\n\n## التشغيل\n\ncd ~/{folder_name}\nnpm install\nnode server.js\n"
        (folder / "README.md").write_text(readme, encoding='utf-8')
        (folder / ".gitignore").write_text("node_modules/\n*.log\n")
        add_log(job_id, "📦 تثبيت express...")
        subprocess.run("npm install express --silent", shell=True, cwd=str(folder), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180)
        add_log(job_id, "🚀 تشغيل السيرفر...")
        subprocess.Popen(f'cd "{folder}" && nohup node server.js > server.log 2>&1 &', shell=True)
        time.sleep(3)
        if do_github:
            add_log(job_id, "🐙 رفع على GitHub...")
            upload_github(folder, folder_name, job_id)
        add_log(job_id, f"✅ تم! http://localhost:3000")
        jobs[job_id]["status"] = "done"
        jobs[job_id]["folder"] = folder_name
        save_jobs()
    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)
        add_log(job_id, f"❌ خطأ: {e}")

def upload_github(folder, name, job_id):
    import urllib.request, urllib.error
    token_file = HOME / ".config" / "termux-github" / "token.txt"
    if not token_file.exists():
        add_log(job_id, "⚠️ التوكن مش موجود")
        return
    token = token_file.read_text().strip()
    if ':' not in token:
        add_log(job_id, "⚠️ التوكن غلط")
        return
    req = urllib.request.Request("https://api.github.com/user", headers={"Authorization": f"token {token}"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            user = json.loads(r.read().decode()).get("login")
    except:
        add_log(job_id, "⚠️ فشل الاتصال")
        return
    if not (folder / ".git").exists():
        subprocess.run("git init && git branch -M main", shell=True, cwd=str(folder))
        subprocess.run(f'git config user.email "{user}@users.noreply.github.com"', shell=True, cwd=str(folder))
        subprocess.run(f'git config user.name "{user}"', shell=True, cwd=str(folder))
    subprocess.run("git add .", shell=True, cwd=str(folder))
    subprocess.run(f'git commit -m "Initial commit: {name}"', shell=True, cwd=str(folder))
    data = json.dumps({"name": name, "private": False, "auto_init": False}).encode()
    req = urllib.request.Request("https://api.github.com/user/repos", data=data,
                                 headers={"Authorization": f"token {token}", "Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as r: pass
    except urllib.error.HTTPError as e:
        if e.code != 422:
            add_log(job_id, f"⚠️ فشل: {e.code}")
            return
    push_url = f"https://{user}:{token}@github.com/{user}/{name}.git"
    subprocess.run(f'git remote remove origin', shell=True, cwd=str(folder))
    subprocess.run(f'git remote add origin https://github.com/{user}/{name}.git', shell=True, cwd=str(folder))
    subprocess.run(f'git push {push_url} main -u --force', shell=True, cwd=str(folder))
    subprocess.run(f'git remote set-url origin https://github.com/{user}/{name}.git', shell=True, cwd=str(folder))
    add_log(job_id, f"✅ https://github.com/{user}/{name}")

HTML = '''<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>🤖 Smart Builder</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{--bg:#0a0a1a;--card:#161b22;--border:#30363d;--text:#fff;--muted:#8b949e;--green:#22c55e;--blue:#58a6ff;--red:#ef4444}
body{font-family:system-ui,-apple-system,Arial,sans-serif;background:var(--bg);color:var(--text);min-height:100vh;padding:15px;line-height:1.6;font-size:15px}
.c{max-width:800px;margin:0 auto}
.header{background:linear-gradient(135deg,#667eea,#764ba2);padding:35px 20px;border-radius:20px;text-align:center;margin-bottom:20px}
.header h1{font-size:26px;margin-bottom:8px}
.header p{opacity:.95;font-size:14px}
.card{background:var(--card);border:1px solid var(--border);border-radius:20px;padding:20px;margin-bottom:20px}
.card h2{font-size:17px;margin-bottom:15px;color:#a78bfa;display:flex;align-items:center;gap:10px}
label{display:block;font-size:13px;color:var(--muted);margin-bottom:6px;margin-top:10px}
input,textarea,select{width:100%;padding:12px 15px;background:#0d1117;border:2px solid var(--border);border-radius:10px;color:#fff;font-family:inherit;font-size:14px;outline:none}
input:focus,textarea:focus,select:focus{border-color:#667eea}
textarea{resize:vertical;min-height:70px}
.btn{padding:14px 24px;border:none;border-radius:12px;font-size:15px;font-weight:bold;cursor:pointer;font-family:inherit;transition:all .2s;display:inline-flex;align-items:center;justify-content:center;gap:8px;width:100%;margin-top:15px}
.btn:active{transform:scale(.97)}
.btn-primary{background:linear-gradient(135deg,#238636,#2ea043);color:#fff}
.btn:disabled{opacity:.5;cursor:not-allowed}
.toggle{display:flex;align-items:center;gap:10px;margin-top:12px;font-size:14px}
.toggle input{width:auto}
.output{background:#0d1117;border:1px solid var(--border);border-radius:12px;padding:16px;font-family:'Courier New',monospace;font-size:13px;color:#79c0ff;direction:ltr;text-align:left;white-space:pre-wrap;word-break:break-all;max-height:400px;overflow-y:auto;line-height:1.6;display:none;margin-top:15px}
.output.show{display:block}
.jobs-list{max-height:300px;overflow-y:auto}
.job{padding:12px;background:#0d1117;border-radius:10px;margin-bottom:8px;font-size:13px}
.job .name{font-weight:bold;color:#5eead4}
.job .status{font-size:11px;color:var(--muted);margin-top:4px}
.footer{text-align:center;padding:20px;color:var(--muted);font-size:12px}
</style>
</head>
<body>
<div class="c">
<div class="header"><h1>🤖 Smart Builder</h1><p>اكتب فكرة المشروع، وهو يبنيه تلقائياً</p></div>
<div class="card">
<h2>💡 الفكرة</h2>
<label>اكتب فكرتك بالعربي</label>
<textarea id="idea" placeholder="مثال: تطبيق ملاحظاتي الشخصية" rows="2"></textarea>
<label>اسم المشروع (اختياري)</label>
<input type="text" id="name" placeholder="مثال: ملاحظاتي">
<label>الوصف (اختياري)</label>
<input type="text" id="desc" placeholder="مثال: تطبيق بسيط لإدارة ملاحظاتي">
<label>اللون</label>
<select id="color">
<option value="1">🟣 بنفسجي (افتراضي)</option>
<option value="2">🔵 أزرق</option>
<option value="3">🟢 أخضر</option>
<option value="4">🔴 أحمر</option>
<option value="5">🟠 برتقالي</option>
</select>
<label class="toggle"><input type="checkbox" id="github"> 🐙 ارفع على GitHub</label>
<button class="btn btn-primary" id="buildBtn" onclick="build()">🚀 ابنِ المشروع</button>
</div>
<div class="card" id="progressCard" style="display:none">
<h2>⏳ جاري البناء</h2>
<div class="output show" id="output"></div>
</div>
<div class="card"><h2>📜 المشاريع</h2><div class="jobs-list" id="jobsList"><p style="color:#8b949e">لا يوجد مشاريع بعد</p></div></div>
<div class="footer">🤖 Smart Builder — Termux 2026</div>
</div>
<script>
async function build() {
    const idea = document.getElementById('idea').value.trim();
    if (!idea) { alert('اكتب الفكرة أول'); return; }
    const name = document.getElementById('name').value.trim() || idea;
    const desc = document.getElementById('desc').value.trim() || idea;
    const colorChoice = document.getElementById('color').value;
    const github = document.getElementById('github').checked;
    document.getElementById('buildBtn').disabled = true;
    document.getElementById('buildBtn').textContent = '⏳ جاري البناء...';
    document.getElementById('progressCard').style.display = 'block';
    document.getElementById('output').textContent = '⏳ جاري التحليل...\\n';
    try {
        const res = await fetch('/api/build', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({idea, name, desc, color: colorChoice, github}) });
        const data = await res.json();
        if (data.job_id) { pollJob(data.job_id); } else { document.getElementById('output').textContent = '❌ ' + (data.error || 'فشل'); resetBtn(); }
    } catch (e) { document.getElementById('output').textContent = '❌ ' + e.message; resetBtn(); }
}
async function pollJob(jobId) {
    try {
        const res = await fetch('/api/job/' + jobId);
        const job = await res.json();
        const out = document.getElementById('output');
        out.textContent = (job.log || []).join('\\n');
        out.scrollTop = out.scrollHeight;
        if (job.status === 'done') { out.textContent += '\\n\\n🎉 تم! الرابط: http://localhost:3000'; resetBtn(); loadJobs(); }
        else if (job.status === 'error') { out.textContent += '\\n\\n❌ ' + (job.error || 'فشل'); resetBtn(); loadJobs(); }
        else { setTimeout(() => pollJob(jobId), 1000); }
    } catch (e) { setTimeout(() => pollJob(jobId), 2000); }
}
function resetBtn() { document.getElementById('buildBtn').disabled = false; document.getElementById('buildBtn').textContent = '🚀 ابنِ المشروع'; }
async function loadJobs() {
    try {
        const res = await fetch('/api/jobs'); const data = await res.json();
        const el = document.getElementById('jobsList'); const keys = Object.keys(data.jobs || {});
        if (!keys.length) { el.innerHTML = '<p style="color:#8b949e">لا يوجد مشاريع بعد</p>'; return; }
        el.innerHTML = keys.map(k => { const j = data.jobs[k]; const status = j.status === 'done' ? '✅' : j.status === 'error' ? '❌' : '⏳'; return '<div class="job"><div class="name">' + status + ' ' + (j.folder || k) + '</div><div class="status">' + j.status + '</div></div>'; }).join('');
    } catch (e) {}
}
loadJobs(); setInterval(loadJobs, 10000);
</script>
</body>
</html>
'''

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _json(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def _html(self, html):
        body = html.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html': self._html(HTML)
        elif self.path == '/api/jobs':
            load_jobs()
            self._json({"jobs": jobs})
        elif self.path.startswith('/api/job/'):
            job_id = self.path.split('/')[-1]
            load_jobs()
            if job_id in jobs: self._json(jobs[job_id])
            else: self._json({"error": "not found"}, 404)
        else:
            self.send_response(404); self.end_headers()
    def do_POST(self):
        if self.path == '/api/build':
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode('utf-8')
            try:
                data = json.loads(body)
                idea = data.get('idea', '')
                name = data.get('name', idea)
                desc = data.get('desc', idea)
                color_choice = data.get('color', '1')
                do_github = data.get('github', False)
                color_map = {"1": ["#667eea", "#764ba2"], "2": ["#1f6feb", "#388bfd"], "3": ["#22c55e", "#10b981"], "4": ["#ef4444", "#dc2626"], "5": ["#f59e0b", "#f97316"]}
                color = color_map.get(color_choice, color_map["1"])
                cat = analyze(idea)
                fields = cat["fields"]
                job_id = str(int(time.time() * 1000))
                jobs[job_id] = {"status": "building", "log": [], "folder": None, "error": None}
                save_jobs()
                t = threading.Thread(target=build_project, args=(job_id, idea, name, desc, fields, color, do_github))
                t.daemon = True
                t.start()
                self._json({"job_id": job_id})
            except Exception as e:
                self._json({"error": str(e)}, 500)
        else:
            self.send_response(404); self.end_headers()

def main():
    load_jobs()
    server = HTTPServer(('0.0.0.0', PORT), Handler)
    print("=" * 50)
    print("🤖 Smart Builder Web")
    print("=" * 50)
    print(f"✅ يعمل على: http://localhost:{PORT}")
    print("🛑 CTRL+C للإيقاف")
    print("=" * 50)
    try: server.serve_forever()
    except KeyboardInterrupt: print("\n👋 وداعاً!")

if __name__ == '__main__':
    main()
