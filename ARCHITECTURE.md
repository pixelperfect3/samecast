# SameCast Architecture

A detailed guide to how SameCast works — from user interaction to API calls, caching, and rendering.

---

## System Overview

```mermaid
graph TB
    User([User Browser])

    subgraph Cloudflare
        CF[Cloudflare DNS/Proxy]
    end

    subgraph Render["Render (Starter Tier)"]
        Gunicorn[Gunicorn WSGI<br/>2 workers]
        Flask[Flask App]
        SQLite[(SQLite DB<br/>instance/samecast.db)]
        ImageCache[Local Image Cache<br/>static/images/]
    end

    subgraph External
        TMDB_API[TMDB API<br/>api.themoviedb.org/3]
        TMDB_CDN[TMDB Image CDN<br/>image.tmdb.org/t/p]
    end

    User <-->|HTTPS| CF
    CF <-->|HTTPS| Gunicorn
    Gunicorn --> Flask
    Flask <-->|Read/Write| SQLite
    Flask <-->|Read/Write| ImageCache
    Flask -->|API calls| TMDB_API
    Flask -->|Image download| TMDB_CDN
    User -.->|Redirect fallback| TMDB_CDN
```

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | HTMX 2.0 | AJAX without writing JS — partial HTML swaps |
| **Styling** | Tailwind CSS + DaisyUI | Utility-first CSS with component library |
| **Backend** | Flask 3.1 | Python web framework |
| **ORM** | Flask-SQLAlchemy | Database models and queries |
| **Database** | SQLite | Persistent local storage on Render disk |
| **WSGI Server** | Gunicorn | Production server with 2 workers |
| **External API** | TMDB API v3 | Movie/TV data source |
| **DNS/CDN** | Cloudflare | DNS proxy, SSL termination |
| **Hosting** | Render | Starter tier ($7/month) |

---

## Project Structure

```
app/
├── __init__.py              # App factory, CLI commands
├── config.py                # Environment-based configuration
├── models.py                # SQLAlchemy models (Title, Person, Credit, Suggestion)
├── routes/
│   ├── main.py              # GET /  and  GET /compare
│   ├── search.py            # GET /search/autocomplete  and  GET /search/select
│   └── images.py            # GET /images/poster/<file>  and  GET /images/profile/<file>
├── services/
│   ├── tmdb.py              # TMDB API client wrapper
│   ├── cache.py             # DB caching layer (permanent, year-aware)
│   └── comparison.py        # Shared cast/crew set-intersection logic
├── templates/
│   ├── base.html            # Layout: floating theme toggle, footer
│   ├── index.html           # Homepage: search boxes, suggestions, results area
│   └── partials/
│       ├── search_results.html   # Autocomplete dropdown items
│       ├── selected_title.html   # Selected title card with hidden fields
│       ├── comparison.html       # Shared cast/crew result cards
│       └── error.html            # Error alert banner
└── static/
    ├── css/custom.css        # Animations, transitions, theme styles
    └── images/
        ├── posters/          # Cached poster images (w500)
        └── profiles/         # Cached profile photos (w185)
```

---

## Database Schema

```mermaid
erDiagram
    TITLES {
        int id PK "TMDB ID (not auto-increment)"
        string media_type "movie | tv"
        string title
        int release_year
        text overview
        string poster_path
        bool poster_cached
        bool credits_cached
        datetime cached_at
    }

    PERSONS {
        int id PK "TMDB person ID"
        string name
        string profile_path
        bool profile_cached
        string known_for_department
        datetime cached_at
    }

    CREDITS {
        int id PK "Auto-increment"
        int title_id FK
        int person_id FK
        string credit_type "cast | crew"
        string character "Cast only"
        string job "Crew only (e.g. Director)"
        string department "Crew only (e.g. Directing)"
        int display_order "Billing order"
    }

    SUGGESTIONS {
        int id PK "Auto-increment"
        string title_1
        string title_2
        bool active "Default true"
        datetime created_at
    }

    TITLES ||--o{ CREDITS : "has many"
    PERSONS ||--o{ CREDITS : "has many"
```

**Indexes on `credits`:**
- `ix_credit_title_person` — composite on `(title_id, person_id)` for finding shared people
- `ix_credit_person` — on `person_id` for person-centric queries

---

## User Flow: Full Comparison

```mermaid
sequenceDiagram
    actor User
    participant Browser
    participant HTMX
    participant Flask
    participant Cache as Cache Layer
    participant DB as SQLite
    participant TMDB as TMDB API

    Note over User,TMDB: Phase 1 — Page Load
    User->>Browser: Visit samecast.com
    Browser->>Flask: GET /
    Flask->>DB: Query active Suggestions
    DB-->>Flask: Suggestion rows
    Flask-->>Browser: index.html + suggestions JSON

    Note over User,TMDB: Phase 2 — Search (always live)
    User->>Browser: Type "Breaking Bad"
    Browser->>HTMX: input event (400ms debounce)
    HTMX->>Flask: GET /search/autocomplete?q=breaking+bad&slot=1
    Flask->>TMDB: GET /search/multi?query=breaking+bad
    TMDB-->>Flask: Search results (movies + TV)
    Flask-->>HTMX: search_results.html partial
    HTMX-->>Browser: Swap into #dropdown-1

    Note over User,TMDB: Phase 3 — Select Title
    User->>Browser: Click "Breaking Bad"
    Browser->>HTMX: Click event
    HTMX->>Flask: GET /search/select?id=1396&media_type=tv&title=Breaking+Bad&slot=1
    Flask-->>HTMX: selected_title.html partial (card + hidden fields)
    HTMX-->>Browser: Swap into #selected-1
    Browser->>Browser: checkCompareButton() — still disabled (need slot 2)

    Note over User,TMDB: Phase 4 — Select Second Title
    User->>Browser: Search & select "Malcolm in the Middle" in slot 2
    Browser->>Browser: checkCompareButton() — ENABLED

    Note over User,TMDB: Phase 5 — Compare
    User->>Browser: Click "Compare"
    Browser->>HTMX: Submit form
    HTMX->>Flask: GET /compare?title_id_1=1396&media_type_1=tv&title_id_2=2004&media_type_2=tv

    Flask->>Cache: get_title_with_credits(1396, "tv")
    Cache->>DB: SELECT * FROM titles WHERE id=1396
    alt Cache HIT (< 7 days old)
        DB-->>Cache: Title + Credits rows
        Cache-->>Flask: Cached details
    else Cache MISS or STALE
        Cache->>TMDB: GET /tv/1396?append_to_response=aggregate_credits
        TMDB-->>Cache: Full details + cast + crew
        Cache->>DB: UPSERT title, persons, credits
        Cache-->>Flask: Fresh details
    end

    Flask->>Cache: get_title_with_credits(2004, "tv")
    Note over Cache: Same cache check for title 2

    Flask->>Flask: find_shared() — set intersection
    Flask-->>HTMX: comparison.html partial
    HTMX-->>Browser: Swap into #results
    Browser-->>User: Shared cast & crew cards with staggered animation
```

---

## Caching Strategy

```mermaid
flowchart TD
    A[get_title_with_credits called] --> B{Title in DB?}
    B -->|No| D[Fetch from TMDB API]
    B -->|Yes| C{credits_cached<br/>= True?}
    C -->|No| D
    C -->|Yes| E{release_year<br/>>= current year?}
    E -->|Yes| D[Fetch from TMDB API]
    E -->|No| F[Load from DB]

    D --> G[Save to DB]
    G --> H[Upsert Title row]
    G --> I[Delete old Credits]
    G --> J[Upsert Person rows]
    G --> K[Insert new Credit rows]
    H & I & J & K --> L[Return details]
    F --> L

    style D fill:#f96,stroke:#333
    style F fill:#6f6,stroke:#333
```

**Key design decisions:**
- **Search autocomplete always hits TMDB** — ensures fresh, complete results
- **Comparison uses DB cache** — avoids redundant API calls for previously compared titles
- **Cache is permanent for past titles** — movie/TV credits don't change after release
- **Current/future year titles always re-fetch** — credits may be incomplete before release
- **Manual refresh via CLI** — `flask cache refresh <title_id>` clears cache for any title
- **Full credit refresh on cache miss** — deletes all old credits, re-inserts (avoids stale data)

---

## Image Proxy Flow

```mermaid
flowchart TD
    A["Browser requests<br/>/images/poster/abc123.jpg"] --> B{File exists in<br/>static/images/posters/?}
    B -->|Yes| C[send_file from disk]
    B -->|No| D["Download from TMDB CDN<br/>image.tmdb.org/t/p/w500/abc123.jpg"]
    D --> E{Download OK?}
    E -->|Yes| F[Save to disk cache]
    F --> C
    E -->|No| G["Redirect browser<br/>to TMDB CDN URL"]

    style C fill:#6f6,stroke:#333
    style G fill:#ff6,stroke:#333
```

**Image sizes used:**
| Type | Route | TMDB Size | Typical File |
|------|-------|-----------|-------------|
| Poster thumbnail | Autocomplete dropdown | `w92` | ~5 KB |
| Poster | Selected card & results | `w500` | ~100-200 KB |
| Profile photo | Result cards | `w185` | ~50-100 KB |

---

## HTMX Interaction Pattern

SameCast uses HTMX for all dynamic interactions — no client-side JavaScript framework needed.

```mermaid
flowchart LR
    subgraph Browser
        Input1[Search Input #1]
        Drop1[Dropdown #1]
        Sel1[Selected Card #1]
        Input2[Search Input #2]
        Drop2[Dropdown #2]
        Sel2[Selected Card #2]
        Btn[Compare Button]
        Results[Results Area]
    end

    subgraph Server["Flask Routes"]
        AC["/search/autocomplete"]
        SL["/search/select"]
        CMP["/compare"]
    end

    Input1 -->|"hx-get, 400ms debounce"| AC
    AC -->|"HTML partial"| Drop1
    Drop1 -->|"click → hx-get"| SL
    SL -->|"HTML partial"| Sel1

    Input2 -->|"hx-get, 400ms debounce"| AC
    AC -->|"HTML partial"| Drop2
    Drop2 -->|"click → hx-get"| SL
    SL -->|"HTML partial"| Sel2

    Btn -->|"hx-get (form submit)"| CMP
    CMP -->|"HTML partial"| Results
```

**How HTMX replaces a traditional SPA:**
- Each server response is an HTML fragment, not JSON
- `hx-target` specifies which DOM element to update
- `hx-swap="innerHTML"` replaces the target's content
- `hx-trigger` controls when requests fire (input changes, clicks, form submit)
- `hx-indicator` shows/hides a loading spinner during requests

---

## Comparison Algorithm

```mermaid
flowchart TD
    A[Title 1 Credits] --> B["Build lookup dict<br/>cast_1 = {person_id: credit}"]
    C[Title 2 Credits] --> D["Build lookup dict<br/>cast_2 = {person_id: credit}"]

    B & D --> E["shared_cast_ids =<br/>cast_1.keys() ∩ cast_2.keys()"]

    A --> F["crew_1 = {person_id: credit}"]
    C --> G["crew_2 = {person_id: credit}"]

    F & G --> H["shared_crew_ids =<br/>crew_1.keys() ∩ crew_2.keys()"]

    E --> I["Remove duplicates:<br/>shared_crew_ids -= shared_cast_ids"]
    H --> I

    I --> J["Build shared_cast list<br/>with roles from both titles"]
    I --> K["Build shared_crew list<br/>with jobs from both titles"]

    J --> L["Sort by billing order<br/>(lower = more prominent)"]
    K --> M["Sort by department priority<br/>Directing → Writing → Production → ..."]

    L & M --> N["Return result with<br/>title metadata + shared people"]
```

**Department sort priority:** Directing > Writing > Production > Sound > Camera > Art > ... > Other

---

## TV vs Movie Credits: A Key Difference

TMDB structures credits differently for movies and TV shows. This is one of the trickiest parts of the codebase.

```mermaid
flowchart LR
    subgraph Movie["Movie Credit (flat)"]
        MC["credits.cast[i]"]
        MC --> MChar["character: 'Bruce Wayne'"]
    end

    subgraph TV["TV Credit (nested)"]
        TC["aggregate_credits.cast[i]"]
        TC --> Roles["roles: [...]"]
        Roles --> R1["{ character: 'Walter White',<br/>episode_count: 62 }"]
        Roles --> R2["{ character: 'Mr. Lambert',<br/>episode_count: 1 }"]
    end

    subgraph Normalized["Normalized Output"]
        N["character: 'Walter White / Mr. Lambert'"]
    end

    MChar --> Normalized
    R1 & R2 -->|"join with ' / '"| Normalized
```

The same pattern applies to crew: movies have a single `job` field, TV shows have a `jobs` array.

---

## Theme System

```mermaid
flowchart TD
    A[Page Load] --> B{localStorage.theme<br/>== 'synthwave'?}
    B -->|Yes| C["Set html[data-theme]='synthwave'<br/>Show moon icon"]
    B -->|No| D["Set html[data-theme]='cupcake'<br/>Show sun icon"]

    E[User clicks toggle] --> F{Current theme?}
    F -->|cupcake| G["Switch to synthwave<br/>Save to localStorage"]
    F -->|synthwave| H["Switch to cupcake<br/>Save to localStorage"]
```

**Themes:**
- **Cupcake** (light) — warm pastels, soft shadows
- **Synthwave** (dark) — neon colors, dark background

DaisyUI handles all component color changes automatically via CSS variables tied to `data-theme`.

---

## Suggestion Rotation

```mermaid
stateDiagram-v2
    [*] --> LoadJSON: Page loads
    LoadJSON --> PickRandom: Parse suggestions array
    PickRandom --> Visible: Show random suggestion

    state "Every 60 seconds" as Timer {
        Visible --> FadeOut: Remove .suggestion-visible<br/>Add .suggestion-hidden
        FadeOut --> SwapText: After 500ms timeout
        SwapText --> FadeIn: Advance index, update textContent
        FadeIn --> Visible: Remove .suggestion-hidden<br/>Add .suggestion-visible
    }

    note right of LoadJSON
        All suggestions embedded as JSON
        at page render time.
        No HTMX polling needed.
    end note
```

---

## Deployment Architecture

```mermaid
flowchart TD
    subgraph Dev["Local Development"]
        DevFlask["flask run --debug --port 5050"]
        DevDB[(instance/samecast.db)]
        DevImages[static/images/]
    end

    subgraph GitHub
        Repo["github.com/pixelperfect3/samecast"]
    end

    subgraph Render["Render (Production)"]
        Build["Build: pip install -r requirements.txt"]
        Run["gunicorn wsgi:app --workers 2"]
        ProdDB[(Persistent Disk<br/>instance/samecast.db)]
        ProdImages[Persistent Disk<br/>static/images/]
    end

    subgraph Cloudflare
        DNS["DNS: samecast.com"]
        SSL["SSL Termination"]
    end

    Dev -->|git push| Repo
    Repo -->|Auto-deploy on push| Build
    Build --> Run
    Run <--> ProdDB
    Run <--> ProdImages
    DNS --> SSL --> Run

    style Cloudflare fill:#f5a623,stroke:#333,color:#000
    style Render fill:#46e3b7,stroke:#333,color:#000
```

**Environment variables on Render:**
- `TMDB_API_KEY` — set manually in dashboard
- `SECRET_KEY` — auto-generated by Render
- `FLASK_ENV` — `production`
- `DATABASE_URL` — `sqlite:///samecast.db`

---

## Request Routing Summary

| Method | Path | Handler | Returns | Cached? |
|--------|------|---------|---------|---------|
| GET | `/` | `main.index` | Full HTML page | No |
| GET | `/compare` | `main.compare` | HTML partial (results) | DB cache for TMDB data |
| GET | `/search/autocomplete` | `search.autocomplete` | HTML partial (dropdown) | Never (always live) |
| GET | `/search/select` | `search.select` | HTML partial (card) | No |
| GET | `/images/poster/<file>` | `images.poster` | Image file | Disk cache |
| GET | `/images/profile/<file>` | `images.profile` | Image file | Disk cache |

---

## CLI Commands

```bash
# Seed 10 starter suggestions (idempotent — safe to re-run)
flask --app wsgi suggestions seed

# Add a custom suggestion pair
flask --app wsgi suggestions add 'Goodfellas' 'The Sopranos'

# List all suggestions with status
flask --app wsgi suggestions list
```
