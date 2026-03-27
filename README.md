# Reha Briefing Bot

Täglicher Branchennewsletter für BfW / BBW / WfbM / Eingliederungshilfe NRW.  
Läuft als GitHub Action, postet in die Craft Daily Note.

---

## Setup (10 Minuten)

### 1. Repo anlegen

```bash
# Neues privates Repo auf github.com anlegen, dann lokal:
git clone https://github.com/DEIN-USERNAME/reha-briefing
cd reha-briefing
mkdir -p .github/workflows briefings
# Dateien aus diesem Setup reinkopieren
git add . && git commit -m "init" && git push
```

### 2. GitHub Secrets setzen

Geh zu: `github.com/DEIN-USERNAME/reha-briefing` → **Settings → Secrets and variables → Actions → New repository secret**

| Secret Name        | Wert | Wo herbekommen |
|--------------------|------|----------------|
| `ANTHROPIC_API_KEY` | `sk-ant-...` | console.anthropic.com → API Keys |
| `CRAFT_TOKEN`       | Siehe unten | Craft MCP-URL |

### 3. Craft Token herausfinden

Deine Craft MCP-URL lautet:
```
https://mcp.craft.do/links/AVXlma9KSYy/mcp
```

Der Token ist der Teil zwischen `/links/` und `/mcp/` — also:
```
AVXlma9KSYy
```

Das ist dein `CRAFT_TOKEN`.

> **Hinweis:** Falls dieser Token nicht funktioniert (MCP-Links haben manchmal eingeschränkte Schreibrechte), gibt es einen Fallback: Das Briefing wird trotzdem als Markdown-Datei im `briefings/`-Ordner des Repos gespeichert und ist dort täglich abrufbar.

### 4. Testen

Nach dem Push:  
`github.com/DEIN-USERNAME/reha-briefing` → **Actions → Tägliches Reha Briefing → Run workflow**

---

## Läuft automatisch

Mo–Fr, 06:00 Uhr MEZ. Output:
- ✅ Craft Daily Note (Ende des Tages-Eintrags)
- ✅ `briefings/YYYY-MM-DD.md` im Repo als Backup

---

## Kosten

| Komponente | Kosten |
|------------|--------|
| GitHub Actions | kostenlos (2.000 min/Monat) |
| Claude Haiku (~1.800 tokens/Tag) | ~$0.30–0.50/Monat |

---

## Themen anpassen

In `briefing.py` → `FEEDS`-Liste ergänzen oder kürzen.  
Keywords in den Google News URLs nach Bedarf ändern.
