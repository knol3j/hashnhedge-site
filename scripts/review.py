#!/usr/bin/env python3
import os, subprocess, shutil, yaml
CFG = yaml.safe_load(open('scripts/config.yaml','r'))
DRAFTS = CFG['content']['drafts_dir']
POSTS = CFG['content']['posts_dir']
EDITOR = os.environ.get('EDITOR','nano')

def list_drafts():
  return sorted([os.path.join(DRAFTS,f) for f in os.listdir(DRAFTS) if f.endswith('.md')])

def approve(path):
  with open(path,'r') as f:
    data = f.read().replace("\ndraft: true","\ndraft: false")
  with open(path,'w') as f:
    f.write(data)
  slug = os.path.basename(path)
  target = os.path.join(POSTS, slug)
  os.makedirs(POSTS, exist_ok=True)
  shutil.move(path, target)
  print(f"Approved -> {target}")

def main():
  ds = list_drafts()
  for p in ds:
    print(f"\nReviewing: {p}\n")
    subprocess.call([EDITOR, p])
    ans = input("Approve and publish? y/N: ").strip().lower()
    if ans == 'y':
      approve(p)

if __name__ == "__main__":
  main()
