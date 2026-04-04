# BET Deck Builder — Deployment Guide

## Was ist das?

Ein kleiner Python-Service der outline.json entgegennimmt und eine .pptx im BET Corporate Design zurückgibt. Läuft auf Railway.

## Dateien im Repo

```
main.py              ← FastAPI Server (POST /build)
build_deck.py        ← PPTX-Generator (aus dem Skill)
Master_Ergebnis.pptx ← BET Template
requirements.txt     ← Python Dependencies
Dockerfile           ← Container-Config
railway.toml         ← Railway-Config
```

## Deployment auf Railway (Schritt für Schritt)

### 1. GitHub Repo erstellen

1. Geh auf github.com → "New repository"
2. Name: `bet-build-service`
3. Private repo
4. NICHT "Add README" anklicken — leer lassen
5. "Create repository"

### 2. Dateien hochladen

Option A — Per Drag & Drop:
1. Öffne das leere Repo auf GitHub
2. Klick "uploading an existing file"
3. Ziehe ALLE Dateien aus diesem Ordner rein (main.py, build_deck.py, Master_Ergebnis.pptx, requirements.txt, Dockerfile, railway.toml, .gitignore)
4. "Commit changes"

Option B — Per Terminal (wenn Git installiert ist):
```bash
cd bet-build-service
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/DEIN_USERNAME/bet-build-service.git
git push -u origin main
```

### 3. Railway mit GitHub verbinden

1. Geh auf railway.com → Dashboard
2. Klick "New Project"
3. Wähle "Deploy from GitHub repo"
4. Wähle `bet-build-service`
5. Railway erkennt den Dockerfile automatisch und startet den Build

### 4. Umgebungsvariable setzen

1. In Railway: Klick auf deinen Service → "Variables"
2. Füge hinzu:
   - `BUILD_SECRET` = ein beliebiges Passwort (z.B. `mein-geheimes-token-123`)
   - Das brauchst du später im Dify HTTP-Request-Node als Bearer Token

### 5. Domain aktivieren

1. In Railway: Service → "Settings" → "Networking"
2. Klick "Generate Domain"
3. Du bekommst eine URL wie: `bet-build-service-production.up.railway.app`
4. Notiere diese URL!

### 6. Testen

Öffne im Browser:
```
https://DEINE-RAILWAY-URL/health
```

Sollte zeigen: `{"status": "ok", "template_exists": true}`

Dann teste den Build mit curl oder Postman:
```bash
curl -X POST https://DEINE-RAILWAY-URL/build \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer mein-geheimes-token-123" \
  -d '{
    "title": "Test Präsentation",
    "subtitle": "Funktionstest",
    "footer": "BET | April 2026",
    "slides": [
      {
        "layout": 2,
        "title": "Erste Ergebnisfolie",
        "body": ["Punkt 1", "Punkt 2", "→ Fazit: Es funktioniert!"]
      }
    ]
  }' \
  --output test.pptx
```

Wenn eine test.pptx heruntergeladen wird → Alles funktioniert!

## Dify-Konfiguration (nächster Schritt)

Nach erfolgreichem Test konfigurieren wir den HTTP-Request-Node in Dify:
- URL: `https://DEINE-RAILWAY-URL/build`
- Method: POST
- Header: `Authorization: Bearer DEIN_BUILD_SECRET`
- Body: Das outline.json aus dem vorherigen LLM-Node
