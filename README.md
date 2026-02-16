# SameCast

Discover shared cast & crew between any two movies or TV shows.

## Local Development

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Add your TMDB API key
flask --app wsgi run --debug --port 5050
```

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
4. Deploy

## Stack

Flask, SQLAlchemy, HTMX, Tailwind CSS, DaisyUI, TMDB API
