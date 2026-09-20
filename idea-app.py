#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, json, subprocess, shutil, re, time
from pathlib import Path
from datetime import datetime

HOME = Path.home()

def ask(msg, default=""):
    if default:
        v = input(f"❓ {msg} [{default}]: ").strip()
        return v if v else default
    return input(f"❓ {msg}: ").strip()

def run(cmd, cwd=None):
    try:
        r = subprocess.run(cmd, shell=True, cwd=cwd,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120)
        return r.returncode == 0
    except:
        return False

CATS = {
    "notes":    {"kw": ["ملاحظات","مذكرة","دفتر"], "name": "تطبيق ملاحظات", "icon": "📝", "fields": ["العنوان","المحتوى"], "prefix": "notes"},
    "todo":     {"kw": ["مهام","مهمة","todo"], "name": "قائمة مهام", "icon": "✅", "fields": ["العنوان","الوصف"], "prefix": "todo"},
    "books":    {"kw": ["كتب","كتاب","مكتبة"], "name": "مكتبة كتب", "icon": "📚", "fields": ["العنوان","المؤلف"], "prefix": "library"},
    "expenses": {"kw": ["مصاريف","مصروف","فلوس"], "name": "متتبع مصاريف", "icon": "💰", "fields": ["الوصف","المبلغ"], "prefix": "expenses"},
    "contacts": {"kw": ["جهات","أرقام","contacts"], "name": "دفتر جهات", "icon": "📞", "fields": ["الاسم","الرقم"], "prefix": "contacts"},
    "custom":   {"kw": [], "name": "مشروع مخصص", "icon": "🎨", "fields": ["العنوان","الوصف"], "prefix": "app"},
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

def folder_name(idea, cat):
    n = re.sub(r'[^\w\s]', '', idea).strip().replace(' ', '-')[:25]
    if not n or re.search(r'[\u0600-\u06FF]', n):
        n = cat["prefix"] + "-" + datetime.now().strftime("%H%M")
    return n.lower()

SERVER = '''const express = require('express');
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

def make_html(cat, idea):
    fields_input = ""
    for f in cat["fields"]:
        if f in ["الوصف", "المحتوى"]:
            fields_input += '<textarea name="' + f + '" placeholder="' + f + '..." rows="3" required></textarea>\n'
        else:
            fields_input += '<input type="text" name="' + f + '" placeholder="' + f + '..." required>\n'

    field1 = cat["fields"][0]
    field2 = cat["fields"][1] if len(cat["fields"]) > 1 else ""

    html = '''<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>''' + cat["name"] + '''</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Arial,sans-serif;background:linear-gradient(135deg,#0f0c29,#24243e);color:#fff;min-height:100vh;padding:20px}
.c{max-width:800px;margin:0 auto}
.header{background:linear-gradient(135deg,#667eea,#764ba2);padding:35px 20px;border-radius:20px;text-align:center;margin-bottom:20px}
.header h1{font-size:28px;margin-bottom:8px}
.header p{opacity:.9;font-size:14px}
.card{background:rgba(255,255,255,.05);border-radius:16px;padding:20px;margin-bottom:16px;border:1px solid rgba(255,255,255,.1)}
.card h2{font-size:16px;margin-bottom:14px;color:#a78bfa}
input,textarea{width:100%;padding:12px;border-radius:10px;border:1px solid rgba(255,255,255,.1);background:rgba(0,0,0,.3);color:#fff;font-family:inherit;font-size:14px;margin-bottom:10px}
input:focus,textarea:focus{outline:none;border-color:#667eea}
button{padding:14px;border-radius:10px;border:none;background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;font-weight:bold;cursor:pointer;font-size:15px;width:100%;font-family:inherit}
button:active{transform:scale(.98)}
.item{background:rgba(0,0,0,.3);padding:14px;border-radius:10px;margin-bottom:10px;display:flex;justify-content:space-between;align-items:center;gap:10px}
.info{flex:1}
.item h3{font-size:16px;margin-bottom:6px}
.item p{font-size:13px;color:#94a3b8;margin:2px 0}
.del{background:#ef4444;padding:8px 12px;border-radius:8px;cursor:pointer;font-size:12px;color:#fff;border:none}
.empty{text-align:center;padding:40px;color:#64748b}
.footer{text-align:center;padding:20px;color:#64748b;font-size:12px}
</style>
</head>
<body>
<div class="c">
<div class="header">
<h1>''' + cat["icon"] + " " + cat["name"] + '''</h1>
<p>''' + idea + '''</p>
</div>
<div class="card">
<h2>➕ إضافة جديد</h2>
<form id="f" onsubmit="add(event)">
''' + fields_input + '''
<button type="submit">➕ إضافة</button>
</form>
</div>
<div class="card">
<h2>📋 القائمة</h2>
<div id="list">جاري التحميل...</div>
</div>
<div class="footer">تم بناؤه تلقائياً — Termux 2026</div>
</div>
<script>
async function load() {
  const r = await fetch('/api/items');
  const items = await r.json();
  const el = document.getElementById('list');
  if (!items.length) {
    el.innerHTML = '<div class="empty">📭 مفيش عناصر</div>';
    return;
  }
  el.innerHTML = items.map(item => {
    const t = item["''' + field1 + '''"] || "بدون عنوان";
    const c = item["''' + field2 + '''"] || "";
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
    return html

def main():
    print("\n" + "="*55)
    print("  🤖 مساعد بناء المشاريع")
    print("="*55 + "\n")
    print("اكتب فكرة مشروعك بالعربي:")
    print()
    idea = input("❓ الفكرة: ").strip()
    if not idea:
        print("❌ الفكرة مطلوبة!")
        return
    cat = analyze(idea)
    print(f"\n✅ النوع: {cat['icon']} {cat['name']}")
    ans = input("هنبني؟ (y/n) [y]: ").strip().lower() or "y"
    if ans == "n":
        print("اتلغى")
        return
    print("\n📁 إنشاء المشروع...")
    name = folder_name(idea, cat)
    folder = HOME / name
    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir(parents=True)
    (folder / "public").mkdir()
    (folder / "data").mkdir()
    print(f"✅ {name}/")
    print("⚙️ server.js...")
    (folder / "server.js").write_text(SERVER, encoding='utf-8')
    pkg = {"name": name, "version": "1.0.0", "main": "server.js",
           "scripts": {"start": "node server.js"},
           "dependencies": {"express": "^4.18.0"}}
    (folder / "package.json").write_text(json.dumps(pkg, indent=2))
    print("🎨 index.html...")
    (folder / "public" / "index.html").write_text(make_html(cat, idea), encoding='utf-8')
    (folder / "README.md").write_text("# " + cat["name"] + "\n\n" + idea + "\n", encoding='utf-8')
    (folder / ".gitignore").write_text("node_modules/\n*.log\n")
    print("📦 تثبيت express...")
    run("npm install express --silent", cwd=folder)
    print("🚀 تشغيل السيرفر...")
    subprocess.Popen('cd "' + str(folder) + '" && nohup node server.js > server.log 2>&1 &', shell=True)
    time.sleep(3)
    print("🌐 فتح المتصفح...")
    time.sleep(1)
    subprocess.run('termux-open-url "http://localhost:3000"', shell=True)
    print("\n" + "="*55)
    print("  🎉 تم!")
    print("="*55 + "\n")
    print("📁 ~/" + name + "/")
    print("🌐 http://localhost:3000")
    print("🛑 pkill -f '" + name + "/server.js'\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nاتلغى")
    except Exception as e:
        print("\n❌ خطأ: " + str(e))
