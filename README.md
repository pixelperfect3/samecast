# SameCast

Discover shared cast & crew between any two movies or TV shows.

**Live at [samecast.com](https://samecast.com)**

## Project Status

### Infrastructure

| Component | Details |
|-----------|---------|
| **Domain** | `samecast.com` — purchased via Cloudflare |
| **DNS** | Cloudflare (CNAME to Render) |
| **Hosting** | Render — $7/month Individual plan |
| **Persistent Disk** | 1 GB mounted at `/opt/render/project/src/instance` — SQLite DB survives restarts |
| **SSL** | Auto-provisioned by Render (Let's Encrypt) |
| **Repo** | [github.com/pixelperfect3/samecast](https://github.com/pixelperfect3/samecast) (private) |

### Stack

| Layer | Choice |
|-------|--------|
| Backend | Flask (Python) |
| Frontend | Jinja2 + HTMX + Tailwind CSS + DaisyUI |
| Database | SQLite with Flask-SQLAlchemy |
| Movie API | TMDB (The Movie Database) |
| WSGI Server | Gunicorn (2 workers) |

### Completed Milestones

1. **Project Scaffolding** — Flask app factory, config, base template, wsgi entry point
2. **Database Models** — Title, Person, Credit models with relationships and indexes
3. **TMDB API Integration** — TMDBClient with search, movie/TV details, aggregate credits
4. **Search & Autocomplete UI** — HTMX-powered search with poster thumbnails, two-slot selection
5. **Comparison Logic** — Set intersection of cast/crew, sorted by billing order and department
6. **Caching Layer** — DB cache with 7-day TTL, upsert on miss, no API calls on hit
7. **Image Handling** — Proxy routes that download from TMDB CDN, cache locally, fallback to redirect
8. **UI Polish** — Cupcake/synthwave theme toggle, CSS animations, responsive layout, TMDB attribution
9. **Deployment** — render.yaml, runtime.txt, Cloudflare DNS, persistent disk

### Features

- Search any movie or TV show with live autocomplete
- Compare two titles to find shared actors, directors, writers, and crew
- Results sorted by billing order (cast) and department priority (crew)
- Person cards show roles in both titles side by side
- Dark/light theme toggle (persisted in localStorage)
- DB caching — repeated comparisons are instant (no API calls)
- Image caching with TMDB CDN fallback
- Responsive design (mobile, tablet, desktop)

## Local Development

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Add your TMDB API key
flask --app wsgi run --debug --port 5050
```

Port 5000 is blocked by AirPlay Receiver on macOS — use port 5050.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `TMDB_API_KEY` | API key from [themoviedb.org](https://www.themoviedb.org/settings/api) |
| `SECRET_KEY` | Flask secret key (auto-generated on Render) |
| `DATABASE_URL` | SQLite connection string (default: `sqlite:///samecast.db`) |

## Deploy to Render

1. Push to GitHub
2. Connect repo on [render.com](https://render.com)
3. Set `TMDB_API_KEY` in environment variables
4. Add persistent disk (1 GB) mounted at `/opt/render/project/src/instance`
5. Deploy
