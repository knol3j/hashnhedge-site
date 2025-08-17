#!/usr/bin/env python3
import csv, datetime as dt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DATA.mkdir(parents=True, exist_ok=True)
CAL = DATA / "calendar.csv"

start = dt.date.today()
rows = []
for i in range(30):
    d = start + dt.timedelta(days=i)
    rows.append({"date": d.isoformat(), "slug": f"daily-seo-brief-{d.isoformat()}", "type": "news"})

with CAL.open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["date","slug","type"])
    w.writeheader()
    for r in rows:
        w.writerow(r)

print(f"Wrote {CAL}")

