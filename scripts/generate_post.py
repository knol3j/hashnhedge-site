#!/usr/bin/env python3
import sqlite3, datetime as dt, json, os
from pathlib import Path
import frontmatter, yaml, requests, bs4
from slugify import slugify
import subprocess

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content" / "news"
CONTENT.mkdir(parents=True, exist_ok=True)
VAR = ROOT / "var"
DB = VAR / "seen.db"

def pick_items(limit=6, days=2):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute(
        "SELECT url,title,source,published FROM items WHERE used=0 ORDER BY COALESCE(published, added_at) DESC LIMIT ?",
        (limit,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows

def collect_snippets(items):
    out = []
    for url, title, source, published in items:
        out.append(f"- {title} ({url})")
    return "\n".join(out)

def summarize(sources_blob: str) -> dict:
    proc = subprocess.run(["python3", str(ROOT / "scripts" / "summarize.py")], input=sources_blob.encode(), stdout=subprocess.PIPE)
    text = proc.stdout.decode()
    try:
        # Model may return JSON or Markdown with JSON fenced; try to locate JSON
        start = text.find('{')
        end = text.rfind('}')
        js = json.loads(text[start:end+1])
        return js
    except Exception:
        # Fallback minimal structure
        return {
            "title": "Daily SEO Brief",
            "description": "Top SEO updates today.",
            "sections": text,
            "bullets": [],
            "takeaways": []
        }

def write_post(payload: dict, date: dt.date, sources_list):
    slug = slugify(payload.get("title") or f"daily-seo-brief-{date.isoformat()}")
    post_dir = CONTENT / str(date.year) / f"{date.month:02d}" / slug
    post_dir.mkdir(parents=True, exist_ok=True)
    md_path = post_dir / "index.md"
    fm = {
        "title": payload.get("title", f"Daily SEO Brief: {date.isoformat()}"),
        "description": payload.get("description", "Top SEO updates today."),
        "date": dt.datetime.combine(date, dt.time(13,0)).isoformat() + "Z",
        "tags": ["news","seo"],
        "draft": False,
        "sources": [{"title": s[1], "url": s[0]} for s in sources_list],
        "author": "Hash n Hedge",
    }
    body = ""
    if payload.get("sections"):
        body += payload["sections"] + "\n\n"
    if payload.get("takeaways"):
        body += "## What this means for SEOs\n\n" + "\n".join([f"- {t}" for t in payload["takeaways"]]) + "\n\n"
    body += "## Sources\n\n" + "\n".join([f"- [{title}]({url})" for (url,title,_,_) in sources_list]) + "\n"

    post = frontmatter.Post(body, **fm)
    md_path.write_bytes(frontmatter.dumps(post).encode())
    return md_path

if __name__ == "__main__":
    today = dt.date.today()
    items = pick_items()
    if not items:
        print("No items available. Run scripts/fetch_sources.py first.")
        raise SystemExit(0)
    blob = collect_snippets(items)
    summary = summarize(blob)
    path = write_post(summary, today, items)
    # Mark items as used
    conn = sqlite3.connect(DB); cur = conn.cursor()
    for (url, *_rest) in items:
        cur.execute("UPDATE items SET used=1 WHERE url=?", (url,))
    conn.commit(); conn.close()
    print(f"Wrote {path}")

