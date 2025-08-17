import os, re, json, hashlib, sqlite3, time
from datetime import datetime, timezone
from urllib.parse import urlparse
import httpx, feedparser, frontmatter, yaml
from slugify import slugify
import trafilatura
from ruamel.yaml import YAML

CFG = yaml.safe_load(open('scripts/config.yaml','r'))
DRAFTS = CFG['content']['drafts_dir']
POSTS = CFG['content']['posts_dir']
os.makedirs(DRAFTS, exist_ok=True)
os.makedirs(POSTS, exist_ok=True)
os.makedirs(os.path.dirname(CFG['store']['dedup_db']), exist_ok=True)

REVIEW = CFG['content'].get('review_required', True)

def db():
    conn = sqlite3.connect(CFG['store']['dedup_db'])
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS seen (id TEXT PRIMARY KEY, url TEXT, created_at INTEGER)")
    conn.commit()
    return conn

def norm_id(url):
    return hashlib.sha256(url.encode()).hexdigest()

def seen_before(conn, url):
    nid = norm_id(url)
    c = conn.cursor()
    c.execute("SELECT 1 FROM seen WHERE id=?", (nid,))
    if c.fetchone(): return True
    c.execute("INSERT INTO seen (id,url,created_at) VALUES (?,?,?)", (nid, url, int(time.time())))
    conn.commit()
    return False

def extract_text(url):
    try:
        downloaded = trafilatura.fetch_url(url, no_ssl=True)
        if not downloaded: return None
        text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
        return text
    except Exception:
        return None

def ollama_generate(prompt, model, temperature=0.7, top_p=0.9):
    payload = {
        "model": model,
        "prompt": prompt,
        "options": {"temperature": temperature, "top_p": top_p}
    }
    with httpx.stream("POST", "http://localhost:11434/api/generate", json=payload, timeout=120.0) as r:
        buf = ""
        for line in r.iter_lines():
            if not line: continue
            data = json.loads(line)
            if 'response' in data: buf += data['response']
        return buf

def build_prompt(source_url, outlet, text):
    date_iso = datetime.now(timezone.utc).isoformat()
    instr = open('prompts/news_post.txt','r').read()
    src = f"Source URL: {source_url}\nOutlet: {outlet}\n\nSource Text:\n{text}\n"
    return f"{instr}\n\nNow write the article for {date_iso}.\n\n{src}"

def parse_yaml_and_body(s):
    m = re.match(r'---\s*\n(.*?)\n---\s*\n(.*)', s, re.S)
    if not m:
        raise ValueError("Model output missing YAML front matter.")
    yml = YAML()
    meta = yml.load(m.group(1))
    body = m.group(2).strip()
    return meta, body

def write_post(meta, body, outlet, source_url):
    title = meta.get('title') or 'Untitled'
    date_slug = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    slug = slugify(title)[:80]
    fname = f"{date_slug}-{slug}.md"
    dst_dir = DRAFTS if REVIEW else POSTS
    path = os.path.join(dst_dir, fname)
    meta.setdefault('date', datetime.now(timezone.utc).isoformat())
    meta.setdefault('draft', REVIEW)
    meta.setdefault('source', {})
    meta['source']['url'] = source_url
    meta['source']['outlet'] = outlet
    meta.setdefault('canonical_url', f"{CFG['site']['base_url'].rstrip('/')}/posts/{date_slug.replace('-','/')}/{slug}/")
    meta.setdefault('cover', {'image':'', 'alt': title})
    post = frontmatter.Post(body, **meta)
    with open(path, 'w') as f:
        frontmatter.dump(post, f)
    print(f"Wrote {'draft' if REVIEW else 'post'}: {path}")


def main():
    conn = db()
    wrote = 0
    for feed in CFG['sources']['rss']:
        d = feedparser.parse(feed)
        for e in d.entries[:30]:
            url = e.get('link')
            title = e.get('title','')
            if not url: continue
            if any(k.lower() in title.lower() for k in CFG['sources']['blocklist_keywords']): continue
            if seen_before(conn, url): continue
            outlet = urlparse(url).netloc
            text = extract_text(url) or e.get('summary','')
            if not text or len(text) < 500: continue
            prompt = build_prompt(url, outlet, text[:6000])
            out = ollama_generate(prompt, CFG['ai']['model'], CFG['ai']['temperature'], CFG['ai']['top_p'])
            try:
                meta, body = parse_yaml_and_body(out)
            except Exception:
                # Fallback: wrap as simple post
                meta = {
                    "title": title[:60],
                    "description": f"Summary of {title}",
                    "categories": ["Tech"],
                    "tags": ["news"],
                    "seo": {"meta_title": title[:60], "meta_description": f"Summary of {title}"}
                }
                body = f"Source: {url}\n\n{out}"
            write_post(meta, body, outlet, url)
            wrote += 1
            if wrote >= CFG['content']['daily_target']:
                break
        if wrote >= CFG['content']['daily_target']:
            break
    print("Done.")

if __name__ == "__main__":
    main()
