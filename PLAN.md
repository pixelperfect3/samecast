# SameCast - Implementation Plan

## Context

Build **SameCast** (samecast.com) — a website where users enter two movies or TV shows and discover which actors, directors, writers, and crew they share. The user is new to web development and prefers Python. The UI should feel smooth and whimsical with autocomplete and images.

## Chosen Stack

| Layer | Choice |
|-------|--------|
| **Backend** | Flask (Python) |
| **Frontend** | Jinja2 + HTMX + Tailwind CSS + DaisyUI |
| **Database** | SQLite with Flask-SQLAlchemy |
| **Movie API** | TMDB (The Movie Database) — free, 50 req/sec |
| **Hosting** | Render (free tier) |
| **WSGI Server** | Gunicorn |

## Project Structure

```
samecast/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── config.py                # Configuration (env vars, DB, TMDB settings)
│   ├── models.py                # SQLAlchemy models (Title, Person, Credit)
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── main.py              # Index page + compare endpoint
│   │   ├── search.py            # Autocomplete + selection (HTMX partials)
│   │   └── images.py            # Image proxy/serving with TMDB fallback
│   ├── services/
│   │   ├── __init__.py
│   │   ├── tmdb.py              # TMDB API client wrapper
│   │   ├── cache.py             # DB cache layer (check DB before API)
│   │   └── comparison.py        # Set intersection logic for shared cast/crew
│   ├── templates/
│   │   ├── base.html            # Base layout (navbar, footer, CDN links)
│   │   ├── index.html           # Main page with two search boxes
│   │   └── partials/
│   │       ├── search_results.html   # Autocomplete dropdown items
│   │       ├── selected_title.html   # Selected movie/show card
│   │       ├── comparison.html       # Shared cast/crew results grid
│   │       └── error.html            # Error message
│   └── static/
│       └── css/custom.css       # Animations, transitions
├── .env.example
├── .gitignore
├── requirements.txt
├── render.yaml                  # Render deployment config
├── wsgi.py                      # Gunicorn entry point
└── README.md
```

## Database Schema

**Title** — movies and TV shows (PK = TMDB ID)
- `id`, `media_type`, `title`, `release_year`, `overview`, `poster_path`, `poster_cached`, `credits_cached`, `cached_at`

**Person** — actors and crew (PK = TMDB person ID)
- `id`, `name`, `profile_path`, `profile_cached`, `known_for_department`, `cached_at`

**Credit** — junction table (autoincrement PK, allows multiple roles per person per title)
- `id`, `title_id` (FK), `person_id` (FK), `credit_type` (cast/crew), `character`, `job`, `department`, `display_order`

## Implementation Milestones

Each milestone produces a working state pushed to GitHub.

### Milestone 1: Project Scaffolding
- Flask app factory (`app/__init__.py`), config, basic route, base template
- `requirements.txt`: Flask, Flask-SQLAlchemy, requests, python-dotenv, gunicorn
- `.gitignore`, `.env.example`, `wsgi.py`, `README.md`
- **Verify**: `flask --app wsgi run --debug` shows "SameCast" at localhost:5000

### Milestone 2: Database Models
- Define `Title`, `Person`, `Credit` models in `app/models.py`
- Relationships, indexes on `(title_id, person_id)` and `person_id`
- **Verify**: Insert test data via `flask shell`, query it back

### Milestone 3: TMDB API Integration
- `app/services/tmdb.py` — `TMDBClient` class with methods:
  - `search_multi(query)` — search movies + TV shows together
  - `get_movie_details(id)` / `get_tv_details(id)` — details with credits appended
  - `get_image_url(path, size)` — construct full TMDB image URL
- Uses `search/multi` endpoint (movies + TV in one call)
- Uses `aggregate_credits` for TV shows (all seasons combined)
- Uses `append_to_response=credits` to fetch details + credits in one API call
- **Verify**: Hit `/test-search?q=breaking+bad` and get JSON results

### Milestone 4: Search & Autocomplete UI
- `app/routes/search.py` — `/search/autocomplete` and `/search/select` endpoints returning HTML partials
- Two search input boxes with HTMX (`hx-get`, `hx-trigger="input changed delay:400ms"`)
- Clicking a result populates a selected-title card and sets hidden form fields
- Compare button enables when both titles are selected
- CDN includes: HTMX, Tailwind CSS, DaisyUI
- **Verify**: Type a movie name, see dropdown, click to select, repeat for second box

### Milestone 5: Comparison Logic
- `app/services/comparison.py` — `find_shared()` function
- Fetches credits for both titles, builds `{person_id: data}` dicts for cast and crew
- Set intersection: `shared_ids = cast1_ids & cast2_ids`
- Returns shared people with their roles in each title
- `/compare` route returns `partials/comparison.html` with actor/crew cards
- **Verify**: Compare "The Dark Knight" and "Inception" — should show Cillian Murphy, Christopher Nolan, Hans Zimmer, etc.

### Milestone 6: Caching Layer
- `app/services/cache.py` — `get_title_with_credits()` function
- Check SQLite first (by TMDB ID + `credits_cached` flag + 7-day TTL)
- On cache miss: fetch from TMDB, upsert Title/Person/Credit records, commit
- On cache hit: load from DB (no API call)
- Search autocomplete always hits TMDB (results should be fresh)
- Update `comparison.py` to use cache layer instead of direct TMDB calls
- **Verify**: Compare same titles twice — second time is faster (no API calls)

### Milestone 7: Image Handling
- `app/services/images.py` — download images from TMDB to local filesystem
- `app/routes/images.py` — `/images/poster/<filename>` and `/images/profile/<filename>`
- Fallback pattern: if not cached locally, redirect to TMDB CDN
- Update templates to use `/images/` routes instead of direct TMDB URLs
- **Verify**: Images load (via redirect initially, then locally after caching)

### Milestone 8: UI Polish
- DaisyUI `cupcake` theme (whimsical, warm) with `synthwave` dark mode toggle
- CSS animations: fade-slide-in for HTMX content, staggered card reveals, card hover lift, dropdown scale-in
- Gradient text heading, loading spinners/dots, image fade-in on load
- Responsive grid layout (single column on mobile, two columns on desktop)
- Sticky navbar, TMDB attribution in footer
- Placeholder images for missing photos
- **Verify**: Test on mobile viewport, toggle theme, check all animations

### Milestone 9: Deployment to Render
- `render.yaml` with build/start commands, env var placeholders
- `runtime.txt` specifying Python 3.12
- Production config (DEBUG=false, generated SECRET_KEY)
- Push to GitHub, connect to Render, set TMDB_API_KEY in dashboard
- **Verify**: App works at `https://samecast.onrender.com`

## Pre-requisites (User Action Required)

1. **TMDB API Key**: Sign up free at https://www.themoviedb.org/signup, go to Settings > API > Create > Developer, copy the v3 API key
2. **GitHub Account**: For version control and Render deployment
3. **Render Account**: Sign up free at https://render.com with GitHub

## Verification Plan

1. **Local dev**: Run `flask --app wsgi run --debug`, test full flow (search > select > compare)
2. **Caching**: Compare same titles twice, verify DB has records via `flask shell`
3. **Edge cases**: Same title in both boxes (error), no shared results (friendly message), TMDB API down (error handling)
4. **Responsive**: Test in browser at mobile/tablet/desktop widths
5. **Production**: Deploy to Render, test the public URL end-to-end
