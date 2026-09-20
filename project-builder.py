#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, json, subprocess, shutil
from pathlib import Path

G='\033[92m'; R='\033[91m'; Y='\033[93m'; B='\033[94m'; C='\033[96m'; N='\033[0m'
def s(m): print(f"{B}[STEP]{N} {m}")
def ok(m): print(f"{G}[OK]{N} {m}")
def er(m): print(f"{R}[ERR]{N} {m}")
def inf(m): print(f"{Y}[INFO]{N} {m}")
def ask(m): return input(f"{C}❓ {m}{N}\n> ").strip()

HOME = Path.home()

TEMPLATES = {
    "notes": {"name": "تطبيق الملاحظات", "desc": "تطبيق ويب لإدارة الملاحظات", "tech": ["Node.js","Express","JSON"], "folder": "notes-app", "run": "node server.js", "port": 3000},
    "todo": {"name": "قائمة المهام", "desc": "تطبيق متقدم لإدارة المهام", "tech": ["Node.js","Express","PWA"], "folder": "todo-app", "run": "node server.js", "port": 3000},
    "library": {"name": "مكتبة الكتب", "desc": "نظام إدارة وقراءة الكتب", "tech": ["Python","HTML"], "folder": "my-library", "run": "python server.py", "port": 5000},
    "organizer": {"name": "منظم الملفات", "desc": "تنظيم تلقائي للملفات", "tech": ["Python"], "folder": "file-organizer", "run": "python server.py", "port": 5000},
    "directory": {"name": "دليل الخدمات", "desc": "دليل شامل للخدمات", "tech": ["Node.js","JSON"], "folder": "services-directory", "run": "node server.js", "port": 3000},
    "iot": {"name": "تحكم IoT", "desc": "تحكم في ESP32 من المتصفح", "tech": ["Node.js","PWA"], "folder": "esp32-hub", "run": "node server.js", "port": 3000},
    "bot": {"name": "بوت تيليجرام", "desc": "بوت ذكي بكل المميزات", "tech": ["Python"], "folder": "my-bot", "run": "python bot.py", "port": None},
    "custom": {"name": "مشروع مخصص", "desc": "مشروع جديد من اختيارك", "tech": ["Node.js","HTML"], "folder": "my-project", "run": "node server.js", "port": 3000},
}

def run_cmd(cmd, cwd=None, check=False):
    r = subprocess.run(cmd, shell=True, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if r.returncode != 0 and check:
        er(f"فشل: {cmd}")
        if r.stderr: print(r.stderr[-300:])
        return None
    return r.stdout.strip()

def exists(c): return shutil.which(c) is not None

def choose_template():
    print(f"\n{G}{'='*55}{N}")
    print(f"{G}  🤖 مساعد بناء المشاريع التلقائي{N}")
    print(f"{G}{'='*55}{N}\n")
    print(f"{C}🎯 اختر نوع مشروعك:{N}\n")
    keys = list(TEMPLATES.keys())
    for i, key in enumerate(keys, 1):
        t = TEMPLATES[key]
        print(f"  {G}{i}{N}. {t['name']} - {Y}{t['desc']}{N}")
        print(f"     📦 {', '.join(t['tech'])}\n")
    while True:
        choice = ask(f"اختار رقم (1-{len(keys)})")
        try:
            n = int(choice) - 1
            if 0 <= n < len(keys): return TEMPLATES[keys[n]]
        except: pass
        er("رقم غلط")

def check_requirements(template):
    print(f"\n{B}{'='*55}{N}")
    print(f"{B}  🔍 1. فحص الأدوات{N}")
    print(f"{B}{'='*55}{N}\n")
    needed = []
    if "Node" in template["tech"]: needed.append("node")
    if "Python" in template["tech"]: needed.append("python")
    needed.append("git")
    missing = []
    for tool in needed:
        if exists(tool): ok(f"{tool}: موجود")
        else: er(f"{tool}: مش موجود"); missing.append(tool)
    return len(missing) == 0

def create_structure(template):
    print(f"\n{B}{'='*55}{N}")
    print(f"{B}  📁 2. إنشاء الهيكل{N}")
    print(f"{B}{'='*55}{N}\n")
    folder = HOME / template["folder"]
    if folder.exists():
        ans = ask(f"المجلد موجود: {folder.name} — أستبدله؟ (y/n)")
        if ans.lower() == 'y': shutil.rmtree(folder)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "public").mkdir(exist_ok=True)
    (folder / "data").mkdir(exist_ok=True)
    ok(f"المجلد: {folder.name}")
    return folder

def write_server_js(folder, template):
    if "Node" not in template["tech"]: return
    s("كتابة server.js...")
    server = '''const express = require('express');
const fs = require('fs');
const app = express();
const PORT = 3000;

app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static('public'));

const DATA = './data/items.json';
if (!fs.existsSync(DATA)) fs.writeFileSync(DATA, '[]');

app.get('/api/items', (req, res) => {
  try { res.json(JSON.parse(fs.readFileSync(DATA, 'utf8'))); }
  catch (e) { res.json([]); }
});

app.post('/api/items', (req, res) => {
  const items = JSON.parse(fs.readFileSync(DATA, 'utf8'));
  items.push({ id: Date.now(), ...req.body });
  fs.writeFileSync(DATA, JSON.stringify(items, null, 2));
  res.json({ ok: true });
});

app.listen(PORT, '0.0.0.0', () => {
  console.log('Running on http://localhost:' + PORT);
});
'''
    (folder / "server.js").write_text(server, encoding='utf-8')
    ok("server.js")
    pkg = {"name": template["folder"], "version": "1.0.0", "main": "server.js",
           "scripts": {"start": "node server.js"}, "dependencies": {"express": "^4.18.0"}}
    (folder / "package.json").write_text(json.dumps(pkg, indent=2))
    ok("package.json")

def write_server_py(folder, template):
    if "Python" not in template["tech"]: return
    s("كتابة server.py...")
    server = '''#!/usr/bin/env python3
import os, json
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

PORT = 5000
DATA_FILE = Path(__file__).parent / "data" / "items.json"
DATA_FILE.parent.mkdir(exist_ok=True)
if not DATA_FILE.exists(): DATA_FILE.write_text("[]")

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        if self.path == '/':
            html = (Path(__file__).parent / "public" / "index.html").read_text(encoding='utf-8')
            body = html.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == '/api/items':
            body = DATA_FILE.read_text(encoding='utf-8').encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

print(f"Running on http://localhost:{PORT}")
HTTPServer(('0.0.0.0', PORT), Handler).serve_forever()
'''
    (folder / "server.py").write_text(server, encoding='utf-8')
    ok("server.py")

def write_index_html(folder, template):
    s("كتابة index.html...")
    html = '''<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>''' + template["name"] + '''</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Arial,Tahoma,sans-serif;background:#0f0f1a;color:#fff;min-height:100vh;padding:20px}
.c{max-width:800px;margin:0 auto}
.header{background:linear-gradient(135deg,#667eea,#764ba2);padding:35px 20px;border-radius:20px;text-align:center;margin-bottom:20px}
.header h1{font-size:28px;margin-bottom:8px}
.header p{opacity:.9;font-size:14px}
.card{background:#1a1a2e;border-radius:16px;padding:20px;margin-bottom:16px;border:1px solid #2a2a40}
.card h2{font-size:16px;margin-bottom:14px;color:#a78bfa}
input,textarea{width:100%;padding:12px;border-radius:10px;border:1px solid #2a2a40;background:#0d1117;color:#fff;font-family:inherit;font-size:14px;margin-bottom:10px}
button{padding:14px;border-radius:10px;border:none;background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;font-weight:bold;cursor:pointer;font-size:15px;width:100%}
.item{background:#0d1117;padding:14px;border-radius:10px;margin-bottom:10px}
.item h3{font-size:16px;margin-bottom:6px}
.item p{font-size:13px;color:#94a3b8}
</style>
</head>
<body>
<div class="c">
<div class="header"><h1>''' + template["name"] + '''</h1><p>''' + template["desc"] + '''</p></div>
<div class="card"><h2>➕ إضافة</h2>
<form id="addForm" onsubmit="addItem(event)">
<input type="text" name="title" placeholder="العنوان..." required>
<textarea name="content" placeholder="المحتوى..." rows="2"></textarea>
<button type="submit">إضافة</button>
</form></div>
<div class="card"><h2>📋 القائمة</h2><div id="items">جاري التحميل...</div></div>
</div>
<script>
function loadItems() {
  fetch('/api/items').then(r => r.json()).then(items => {
    const el = document.getElementById('items');
    if (!items.length) { el.innerHTML = '<p>مفيش عناصر</p>'; return; }
    el.innerHTML = items.map(i => `<div class="item"><h3>${i.title}</h3><p>${i.content||''}</p></div>`).join('');
  });
}
function addItem(e) {
  e.preventDefault();
  const form = e.target;
  fetch('/api/items', {method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({title: form.title.value, content: form.content.value})
  }).then(() => { form.reset(); loadItems(); });
}
loadItems();
</script>
</body>
</html>
'''
    (folder / "public" / "index.html").write_text(html, encoding='utf-8')
    ok("index.html")

def write_readme(folder, template):
    s("كتابة README.md...")
    readme = f"# {template['name']}\n\n{template['desc']}\n\n## التقنيات\n\n"
    readme += "\n".join(f"- {t}" for t in template['tech'])
    readme += f"\n\n## التشغيل\n\n```bash\ncd ~/{template['folder']}\n{template['run']}\n```\n"
    (folder / "README.md").write_text(readme, encoding='utf-8')
    ok("README.md")

def write_gitignore(folder):
    s("كتابة .gitignore...")
    content = "node_modules/\n__pycache__/\n*.pyc\n.env\ntoken.txt\n*.log\n"
    (folder / ".gitignore").write_text(content)
    ok(".gitignore")

def install_deps(folder, template):
    if "Node" not in template["tech"]: return
    print(f"\n{B}{'='*55}{N}")
    print(f"{B}  📦 3. تثبيت الحزم{N}")
    print(f"{B}{'='*55}{N}\n")
    if not (folder / "node_modules").exists():
        s("npm install...")
        run_cmd("npm install express --silent", cwd=folder)
        ok("express مثبت")

def test_project(folder, template):
    print(f"\n{B}{'='*55}{N}")
    print(f"{B}  ✅ 4. اختبار{N}")
    print(f"{B}{'='*55}{N}\n")
    inf(f"للتشغيل: cd ~/{template['folder']} && {template['run']}")
    if template["port"]:
        inf(f"افتح: http://localhost:{template['port']}")

def upload_to_github(folder, template):
    print(f"\n{B}{'='*55}{N}")
    print(f"{B}  🐙 5. رفع على GitHub{N}")
    print(f"{B}{'='*55}{N}\n")
    ans = ask("عايز ترفعه على GitHub؟ (y/n) [n]")
    if ans.lower() != 'y':
        inf("تم التخطي")
        return
    token_file = HOME / ".config" / "termux-github" / "token.txt"
    if not token_file.exists():
        er("التوكن مش موجود")
        return
    token = token_file.read_text().strip()
    if ':' not in token:
        er("التوكن غلط")
        return
    import urllib.request, urllib.error
    req = urllib.request.Request("https://api.github.com/user", headers={"Authorization": f"token {token}"})
    try:
        with urllib.request.urlopen(req) as r:
            user = json.loads(r.read().decode()).get("login")
        ok(f"مرحباً {user}")
    except Exception as e:
        er(f"فشل: {e}")
        return
    s("تهيئة Git...")
    if not (folder / ".git").exists():
        run_cmd("git init && git branch -M main", cwd=folder)
        run_cmd(f'git config user.email "{user}@users.noreply.github.com"', cwd=folder)
        run_cmd(f'git config user.name "{user}"', cwd=folder)
    run_cmd("git add .", cwd=folder)
    run_cmd(f'git commit -m "Initial commit: {template["name"]}"', cwd=folder)
    ok("Commit")
    repo_name = template["folder"]
    s(f"إنشاء المستودع '{repo_name}'...")
    data = json.dumps({"name": repo_name, "private": False, "auto_init": False}).encode()
    req = urllib.request.Request("https://api.github.com/user/repos", data=data,
        headers={"Authorization": f"token {token}", "Content-Type": "application/json"},
        method="POST")
    try:
        with urllib.request.urlopen(req) as r:
            ok("المستودع جاهز")
    except urllib.error.HTTPError as e:
        if e.code != 422:
            er(f"فشل: {e}")
            return
    s("رفع الملفات...")
    push_url = f"https://{user}:{token}@github.com/{user}/{repo_name}.git"
    run_cmd('git remote remove origin 2>/dev/null', cwd=folder)
    run_cmd(f'git remote add origin https://github.com/{user}/{repo_name}.git', cwd=folder)
    run_cmd(f'git push {push_url} main -u --force 2>&1', cwd=folder)
    ok("تم الرفع")
    run_cmd(f'git remote set-url origin https://github.com/{user}/{repo_name}.git', cwd=folder)
    print(f"\n{G}✅ https://github.com/{user}/{repo_name}{N}\n")

def main():
    try:
        template = choose_template()
        print(f"\n{G}المشروع:{N} {template['name']}")
        confirm = ask("تمام؟ (y/n) [y]")
        if confirm.lower() == 'n':
            inf("اتلغى"); return
        if not check_requirements(template):
            er("ثبت المتطلبات"); return
        folder = create_structure(template)
        if "Node" in template["tech"]: write_server_js(folder, template)
        if "Python" in template["tech"]: write_server_py(folder, template)
        write_index_html(folder, template)
        write_readme(folder, template)
        write_gitignore(folder)
        install_deps(folder, template)
        test_project(folder, template)
        upload_to_github(folder, template)
        print(f"\n{G}{'='*55}{N}")
        print(f"{G}  🎉 تم!{N}")
        print(f"{G}{'='*55}{N}\n")
        print(f"📁 ~/{template['folder']}/")
        print(f"🚀 cd ~/{template['folder']} && {template['run']}")
        if template["port"]:
            print(f"🌐 http://localhost:{template['port']}")
        print()
    except KeyboardInterrupt:
        print(f"\n{R}اتلغى{N}")

if __name__ == "__main__":
    main()
