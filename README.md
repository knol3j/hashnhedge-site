# Hash n Hedge – Hugo + PaperMod

This is the Hash n Hedge news site powered by Hugo and the PaperMod theme.

Local development
- make run        # runs `hugo server -D --disableFastRender`
- make serve      # alias for run
- make build      # runs `hugo --minify`

Daily content pipeline (local AI)
- make deps       # set up Python venv and install requirements
- make fetch      # fetch RSS sources into var/seen.db (SQLite)
- make draft      # generate today's Daily SEO Brief at content/news/YYYY/MM/slug/index.md
- make calendar   # generate data/calendar.csv for 30 days

Advertising & SEO
- Update params.ads in config/_default/hugo.toml with your AdSense client_id.
- Enable ads via params.ads.enabled=true or export ADS_ENABLED=1 for local testing.
- In-article ad shortcode: {{< ad_in_article slot="YOUR_SLOT" >}}
- static/ads.txt must contain your publisher ID entry.
- NewsArticle JSON-LD is auto-included on news section pages.

Cloudflare Pages deployment (recommended)
1) Connect this repository in Cloudflare Pages.
2) Settings:
   - Framework: Hugo
   - Build command: hugo
   - Output directory: public
   - Environment variable: HUGO_VERSION=0.146.0
3) Add the custom domain (hashnhedge.com) and follow DNS instructions.

Hugo config notes
- baseURL: https://hashnhedge.com/
- Pagination: [pagination].pagerSize = 12
- Theme: PaperMod (see themes/PaperMod)
