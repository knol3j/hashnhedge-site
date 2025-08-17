#!/usr/bin/env python3
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MODEL = "qwen2.5:7b-instruct"
TEMP = "0.3"

PROMPT = f"""You are an SEO news editor.
Inputs: a list of source headlines and links with snippets.
Tasks:
1) Summarize top 3-6 items with neutral tone.
2) Add a 'What this means for SEOs' section with actionable takeaways.
3) Write an SEO title (<=60 chars) and meta description (<=155 chars).
Output JSON with keys: title, description, sections (markdown), bullets (list), takeaways (list).
"""

def ollama_run(prompt: str, model: str = MODEL):
    proc = subprocess.run(["ollama", "run", model], input=prompt.encode(), stdout=subprocess.PIPE)
    return proc.stdout.decode()

if __name__ == "__main__":
    sources_blob = sys.stdin.read()
    out = ollama_run(PROMPT + "\n\nSources:\n" + sources_blob)
    print(out)

