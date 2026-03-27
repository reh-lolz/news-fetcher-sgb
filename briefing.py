"""
Tägliches Reha-Branchenbriefing
Fetched via RSS → Zusammenfassung via Claude → Post in Craft Daily Note
"""

import os
import json
import datetime
import httpx
import feedparser

# ─── RSS Feeds ────────────────────────────────────────────────────────────────

FEEDS = [
    ("BfW / Berufsförderungswerk",
     "https://news.google.com/rss/search?q=Berufsf%C3%B6rderungswerk&hl=de&gl=DE&ceid=DE:de"),
    ("BBW / Berufsbildungswerk",
     "https://news.google.com/rss/search?q=Berufsbildungswerk+Rehabilitation&hl=de&gl=DE&ceid=DE:de"),
    ("WfbM / Werkstatt",
     "https://news.google.com/rss/search?q=Werkstatt+behinderte+Menschen+WfbM&hl=de&gl=DE&ceid=DE:de"),
    ("Eingliederungshilfe NRW",
     "https://news.google.com/rss/search?q=Eingliederungshilfe+NRW+BTHG&hl=de&gl=DE&ceid=DE:de"),
    ("SGB IX Reform",
     "https://news.google.com/rss/search?q=SGB+IX+Rehabilitation+Reform+2025&hl=de&gl=DE&ceid=DE:de"),
    ("Sozialwirtschaft Träger",
     "https://news.google.com/rss/search?q=Sozialwirtschaft+Tr%C3%A4ger+Finanzierung+2025&hl=de&gl=DE&ceid=DE:de"),
]

# ─── Config ───────────────────────────────────────────────────────────────────

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
CRAFT_TOKEN       = os.environ.get("CRAFT_TOKEN", "")
CRAFT_SPACE_ID    = os.environ.get("CRAFT_SPACE_ID", "d3cb873f-6399-61d7-2be9-24b48a8f6b75")
MAX_ITEMS_PER_FEED = 4
MAX_TOTAL_ITEMS    = 20

# ─── Fetch ────────────────────────────────────────────────────────────────────

def fetch_news() -> list[dict]:
    items = []
    seen_titles = set()

    for label, url in FEEDS:
        try:
            feed = feedparser.parse(url)
            count = 0
            for entry in feed.entries:
                title = entry.get("title", "").strip()
                if not title or title in seen_titles:
                    continue
                seen_titles.add(title)
                items.append({
                    "category": label,
                    "title": title,
                    "summary": entry.get("summary", "")[:400],
                    "link": entry.get("link", ""),
                    "published": entry.get("published", ""),
                })
                count += 1
                if count >= MAX_ITEMS_PER_FEED:
                    break
            print(f"  [{label}] {count} items")
        except Exception as e:
            print(f"  [{label}] Fehler: {e}")

    return items[:MAX_TOTAL_ITEMS]


# ─── Summarize ────────────────────────────────────────────────────────────────

def summarize(items: list[dict]) -> str:
    today = datetime.date.today().strftime("%d.%m.%Y")
    weekday = datetime.date.today().strftime("%A")

    news_text = "\n\n".join([
        f"[{item['category']}] {item['title']}\n{item['summary']}\n→ {item['link']}"
        for item in items
    ])

    payload = {
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 1800,
        "system": (
            "Du bist ein präziser Branchenanalyst für den deutschen Sozial- und Rehabilitationssektor. "
            "Dein Briefing geht an einen GF eines BfW/Eingliederungshilfe-Verbunds in NRW. "
            "Ton: sachlich, direkt, strategisch relevant. Keine Füllsätze."
        ),
        "messages": [{
            "role": "user",
            "content": f"""Erstelle ein tägliches Briefing ({weekday}, {today}) aus diesen News-Treffern.

Struktur exakt so:

## 📋 Reha & Eingliederungshilfe — {today}

### Top-Entwicklungen
(Die 2–3 relevantesten Items. Je 2 Sätze + Link. Nur wenn wirklich relevant.)

### Strategischer Kontext
(1 Absatz: Was bedeutet das für Träger wie BfW / BBW / WfbM / Eingliederungshilfe NRW?)

### Weitere Meldungen
(Restliche Items als kompakte Bullet-Liste mit Link)

---
*Quellen: Google News RSS | Generiert automatisch*

NEWS:
{news_text}

Wenn keine relevanten News vorhanden: Schreib kurz "Heute keine branchenrelevanten Meldungen." — kein Filler."""
        }]
    }

    resp = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json=payload,
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["content"][0]["text"]


# ─── Post to Craft via MCP ────────────────────────────────────────────────────

def post_to_craft(markdown: str) -> bool:
    """
    Sendet das Briefing via Craft MCP HTTP-Endpoint an die Daily Note.
    CRAFT_TOKEN = der Token aus deiner MCP-URL (siehe README)
    """
    if not CRAFT_TOKEN:
        print("⚠️  Kein CRAFT_TOKEN gesetzt — überspringe Craft.")
        return False

    today_iso = datetime.date.today().isoformat()
    mcp_url   = f"https://mcp.craft.do/links/{CRAFT_TOKEN}/mcp"

    # MCP JSON-RPC: tools/call → markdown_add auf Daily Note
    body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "markdown_add",
            "arguments": {
                "markdown": markdown,
                "position": "end",
                "date": today_iso,
            }
        }
    }

    try:
        resp = httpx.post(
            mcp_url,
            json=body,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        if resp.status_code == 200:
            print(f"✅ Craft Daily Note aktualisiert ({today_iso})")
            return True
        else:
            print(f"⚠️  Craft MCP Fehler {resp.status_code}: {resp.text[:200]}")
            return False
    except Exception as e:
        print(f"⚠️  Craft Post fehlgeschlagen: {e}")
        return False


# ─── Fallback: Artifact speichern ─────────────────────────────────────────────

def save_artifact(markdown: str):
    today = datetime.date.today().isoformat()
    os.makedirs("briefings", exist_ok=True)
    path = f"briefings/{today}.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write(markdown)
    print(f"📁 Gespeichert als {path}")


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Reha Briefing ===")

    print("\n1. News fetchen...")
    items = fetch_news()
    print(f"   → {len(items)} Items gesamt")

    if not items:
        print("   Keine Items gefunden. Abbruch.")
        exit(0)

    print("\n2. Zusammenfassung via Claude...")
    briefing = summarize(items)
    print(briefing[:300] + "...")

    print("\n3. In Craft Daily Note posten...")
    posted = post_to_craft(briefing)

    print("\n4. Als Datei sichern...")
    save_artifact(briefing)

    print("\n=== Done ===")
