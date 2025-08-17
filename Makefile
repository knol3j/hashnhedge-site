SHELL := /bin/bash
VENV := .venv
run:
	@hugo server -D --disableFastRender --bind 0.0.0.0
serve: run

deps:
	@test -d $(VENV) || python3 -m venv $(VENV)
	@source $(VENV)/bin/activate && pip install -r scripts/requirements.txt

# Existing combined generator (kept for compatibility)
generate:
	@source $(VENV)/bin/activate && python scripts/fetch_and_generate.py || true

# New pipeline targets
fetch:
	@source $(VENV)/bin/activate && python scripts/fetch_sources.py

draft:
	@source $(VENV)/bin/activate && python scripts/generate_post.py

calendar:
	@source $(VENV)/bin/activate && python scripts/build_calendar.py

review:
	@source $(VENV)/bin/activate && python scripts/review.py || true

build:
	@hugo --minify

publish:
	@git add .
	@git commit -m "content: publish updates" || true
	@git push origin main
