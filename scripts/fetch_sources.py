#!/usr/bin/env python3
import yaml, sqlite3, sys, os
import feedparser
from urllib.parse import urlparse
from pathlib import Path
import requests_cache

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "sources.yml"
VAR = ROOT / "var"
VAR.mkdir(parents=True, exist_ok=True)
CACHE_DIR = VAR / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
DB = VAR / "seen.db"

requests_cache.install_cache(str(CACHE_DIR / 'http'), expire_after=3600)

conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute(
    """
    CREATE TABLE IF NOT EXISTS items (
      id INTEGER PRIMARY KEY,
      url TEXT UNIQUE,
      title TEXT,
      source TEXT,
      published TEXT,
      added_at TEXT DEFAULT CURRENT_TIMESTAMP,
      used INTEGER DEFAULT 0
    )
    """
)

cfg = yaml.safe_load(DATA.read_text())
feeds = [f['url'] for cat in cfg['categories'].values() for f in cat]

added = 0
for feed in feeds:
    d = feedparser.parse(feed)
    for e in d.entries:
        url = e.get('link')
        title = e.get('title')
        published = e.get('published', '')
        if not url:
            continue
        try:
            cur.execute(
                "INSERT OR IGNORE INTO items(url,title,source,published) VALUES(?,?,?,?)",
                (url, title, urlparse(feed).netloc, published),
            )
            if cur.rowcount:
                added += 1
        except Exception:
            pass

conn.commit()
print(f"Fetched feeds. New items added: {added}")

