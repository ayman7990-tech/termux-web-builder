import os
import json

PROJECT_NAME = "dalil-khadamat-masr"

DATA = {
  "government": [
    {"name": "Boabet Masr El Rakamia", "url": "egypt.gov.eg"},
    {"name": "Wazarat El Dakhilia", "url": "moi.gov.eg"},
    {"name": "Maslahat El Daraeb", "url": "tax.gov.eg"},
    {"name": "El Niyaba El Ama", "url": "pp.gov.eg"},
    {"name": "El Markazi Lel Ehsa", "url": "capmas.gov.eg"},
    {"name": "El Hayaa Lel Estethmar", "url": "gafi.gov.eg"}
  ],
  "education": [
    {"name": "Bank El Maarefa", "url": "ekb.eg"},
    {"name": "Madrastna Plus", "url": "madrastna.eg"},
    {"name": "Hesas Masr", "url": "hesasmasr.eg"},
    {"name": "Wazarat El Tarbia", "url": "moe.gov.eg"},
    {"name": "Wazarat El Taalim El Aly", "url": "mohe.gov.eg"}
  ],
  "companies": [
    {"name": "Vodafone", "codes": "*2000# - *888#", "note": "Taaked men el tatbeeq el rasmi"},
    {"name": "Orange", "codes": "#100# - #400#", "note": "Fi tatbeeq My Orange"},
    {"name": "e&", "codes": "*566#", "note": "Qesm El orod fi tatbeeq My e&"},
    {"name": "WE", "codes": "*600#", "note": "Oula tasgeel tedi hedia ghaliban"}
  ],
  "tips": [
    "La yojad internet magani daem bil hadud",
    "El mawaqe el hukumia wel taalimia magania daeman",
    "Ehtarez men ay kod aw tatbeeq ghair rasmi",
    "La todkhal bayanat hasasa fi Wi-Fi el ama",
    "Estakhdem *155# lel ghai el khadamat el ghair marghuba"
  ]
}

FILES = {
    "README.md": "# Dalil El Khadamat El Magania\nMasr — data updated 2026",
    "data.json": json.dumps(DATA, ensure_ascii=False, indent=2),
    "index.html": """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>دليل الخدمات المجانية</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <header><h1>دليل الخدمات المجانية في مصر</h1></header>
  <main>
    <section><h2>حكومية</h2><ul id="gov-list"></ul></section>
    <section><h2>تعليمية</h2><ul id="edu-list"></ul></section>
    <section><h2>شركات الاتصالات</h2><ul id="comp-list"></ul></section>
    <section><h2>نصائح</h2><ul id="tips-list"></ul></section>
  </main>
  <script src="script.js"></script>
</body>
</html>""",
    "style.css": """*{margin:0;padding:0;box-sizing:border-box}
body{max-width:700px;margin:0 auto;padding:1rem;background:#f8f9fa}
section{background:#fff;padding:1rem;margin:1rem 0;border-radius:8px}
h2{color:#1e40af;margin-bottom:.5rem}
li{padding:.3rem 0;border-bottom:1px solid #eee}""",
    "script.js": """fetch('data.json')
.then(r=>r.json())
.then(d=>{
  d.government.forEach(i=>{const l=document.createElement('li');l.innerHTML=`<a href="https://${i.url}">${i.name}</a>`;document.getElementById('gov-list').appendChild(l)})
  d.education.forEach(i=>{const l=document.createElement('li');l.innerHTML=`<a href="https://${i.url}">${i.name}</a>`;document.getElementById('edu-list').appendChild(l)})
  d.companies.forEach(i=>{const l=document.createElement('li');l.innerHTML=`<b>${i.name}</b> | ${i.codes}<br><small>${i.note}</small>`;document.getElementById('comp-list').appendChild(l)})
  d.tips.forEach(t=>{const l=document.createElement('li');l.textContent=t;document.getElementById('tips-list').appendChild(l)})
})"""
}

def main():
    if not os.path.exists(PROJECT_NAME): os.mkdir(PROJECT_NAME)
    for n,c in FILES.items():
        with open(os.path.join(PROJECT_NAME,n),'w',encoding='utf-8') as f:f.write(c)
        print(f"Created: {n}")
    print("✅ Done! Folder:", PROJECT_NAME)

if __name__=="__main__": main()
