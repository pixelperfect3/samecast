import click
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

STARTER_SUGGESTIONS = [
    ("Game of Thrones", "The Crown"),
    ("The Dark Knight", "Inception"),
    ("Arrested Development", "Veep"),
    ("The Departed", "Gangs of New York"),
    ("The Office", "The Morning Show"),
    ("Oppenheimer", "Interstellar"),
    ("Breaking Bad", "Malcolm in the Middle"),
    ("Goodfellas", "The Sopranos"),
    ("Succession", "The Big Short"),
    ("The Grand Budapest Hotel", "The French Dispatch"),
    ("Dilwale Dulhania Le Jayenge", "Kuch Kuch Hota Hai"),
    ("Law & Order", "The Wire"),
]


def create_app():
    app = Flask(__name__)
    app.config.from_object("app.config.Config")

    db.init_app(app)

    from app.routes.main import main_bp
    from app.routes.search import search_bp
    from app.routes.images import images_bp
    from app.routes.oddoneout import oddoneout_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(search_bp, url_prefix="/search")
    app.register_blueprint(images_bp, url_prefix="/images")
    app.register_blueprint(oddoneout_bp, url_prefix="/oddoneout")

    with app.app_context():
        from app import models  # noqa: F401
        db.create_all()

    _register_cli(app)

    return app


def _register_cli(app):
    from datetime import date, timedelta

    from app.models import OddOneOutRound, Suggestion, Title

    @app.cli.group()
    def suggestions():
        """Manage homepage suggestions."""

    @suggestions.command()
    def seed():
        """Insert starter suggestion pairs (idempotent)."""
        added = 0
        for t1, t2 in STARTER_SUGGESTIONS:
            exists = Suggestion.query.filter_by(title_1=t1, title_2=t2).first()
            if not exists:
                db.session.add(Suggestion(title_1=t1, title_2=t2))
                added += 1
        db.session.commit()
        click.echo(f"Added {added} suggestion(s) ({len(STARTER_SUGGESTIONS) - added} already existed).")

    @suggestions.command()
    @click.argument("title_1")
    @click.argument("title_2")
    def add(title_1, title_2):
        """Add a new suggestion pair."""
        db.session.add(Suggestion(title_1=title_1, title_2=title_2))
        db.session.commit()
        click.echo(f"Added: '{title_1}' & '{title_2}'")

    @suggestions.command("list")
    def list_suggestions():
        """List all suggestions."""
        rows = Suggestion.query.order_by(Suggestion.id).all()
        if not rows:
            click.echo("No suggestions found. Run 'flask suggestions seed' to add starters.")
            return
        for s in rows:
            status = "active" if s.active else "inactive"
            click.echo(f"  [{s.id}] {s.title_1}  &  {s.title_2}  ({status})")

    @app.cli.group()
    def cache():
        """Manage the title/credits cache."""

    @cache.command()
    @click.argument("title_id", type=int)
    def refresh(title_id):
        """Clear cached credits for a title so it re-fetches from TMDB on next comparison."""
        title = Title.query.get(title_id)
        if not title:
            click.echo(f"Title {title_id} not found in cache.")
            return
        title.credits_cached = False
        db.session.commit()
        click.echo(f"Cleared cache for: {title.title} ({title.release_year})")

    @cache.command("list")
    def list_cache():
        """List all cached titles."""
        rows = Title.query.order_by(Title.cached_at.desc()).all()
        if not rows:
            click.echo("No titles cached.")
            return
        click.echo(f"  {'ID':>8}  {'Type':>5}  {'Year':>4}  Title")
        click.echo(f"  {'─'*8}  {'─'*5}  {'─'*4}  {'─'*40}")
        for t in rows:
            year = t.release_year or "?"
            click.echo(f"  {t.id:>8}  {t.media_type:>5}  {year:>4}  {t.title}")
        click.echo(f"\n  {len(rows)} title(s) cached.")

    # --- OddOneOut game commands ---

    @app.cli.group()
    def game():
        """Manage OddOneOut daily puzzles."""

    @game.command()
    @click.option("--days", default=7, help="Number of days to generate ahead.")
    def seed(days):
        """Generate puzzles for the next N days (default 7)."""
        from app.services.puzzle import generate_rounds_for_date

        today = date.today()
        created = 0
        for i in range(days):
            target = today + timedelta(days=i)
            existing = OddOneOutRound.query.filter_by(puzzle_date=target).count()
            if existing >= 3:
                click.echo(f"  {target}  — already has {existing} round(s), skipping.")
                continue
            try:
                generate_rounds_for_date(target)
                created += 1
                click.echo(f"  {target}  — generated 3 rounds.")
            except ValueError as e:
                click.echo(f"  {target}  — ERROR: {e}")
        click.echo(f"\nDone. Created puzzles for {created} day(s).")

    @game.command()
    @click.option("--force", is_flag=True, help="Overwrite existing rounds.")
    def curated(force):
        """Insert curated puzzles (idempotent). All data is baked in."""
        from app.services.puzzle_data import CURATED_ROUNDS

        added = 0
        replaced = 0
        skipped = 0
        for entry in CURATED_ROUNDS:
            existing = OddOneOutRound.query.filter_by(
                puzzle_date=date.fromisoformat(entry["puzzle_date"]),
                round_number=entry["round_number"],
            ).first()
            if existing:
                if force:
                    db.session.delete(existing)
                    db.session.flush()
                    replaced += 1
                else:
                    skipped += 1
                    continue
            row = OddOneOutRound(
                puzzle_date=date.fromisoformat(entry["puzzle_date"]),
                round_number=entry["round_number"],
                title_id=entry["title_id"],
                title_name=entry["title_name"],
                actor_1_id=entry["actor_1_id"],
                actor_2_id=entry["actor_2_id"],
                actor_3_id=entry["actor_3_id"],
                outsider_id=entry["outsider_id"],
                actor_1_name=entry["actor_1_name"],
                actor_2_name=entry["actor_2_name"],
                actor_3_name=entry["actor_3_name"],
                outsider_name=entry["outsider_name"],
                actor_1_profile=entry.get("actor_1_profile"),
                actor_2_profile=entry.get("actor_2_profile"),
                actor_3_profile=entry.get("actor_3_profile"),
                outsider_profile=entry.get("outsider_profile"),
            )
            db.session.add(row)
            added += 1
        db.session.commit()
        msg = f"Added {added} curated round(s)"
        if replaced:
            msg += f", replaced {replaced}"
        if skipped:
            msg += f" ({skipped} already existed)"
        click.echo(msg + ".")

    @game.command("list")
    def list_puzzles():
        """List upcoming puzzles."""
        rows = (
            OddOneOutRound.query
            .filter(OddOneOutRound.puzzle_date >= date.today())
            .order_by(OddOneOutRound.puzzle_date, OddOneOutRound.round_number)
            .all()
        )
        if not rows:
            click.echo("No upcoming puzzles. Run 'flask game seed' to generate some.")
            return
        current_date = None
        for r in rows:
            if r.puzzle_date != current_date:
                current_date = r.puzzle_date
                click.echo(f"\n  {current_date}:")
            click.echo(
                f"    R{r.round_number}: {r.title_name} — "
                f"{r.actor_1_name}, {r.actor_2_name}, {r.actor_3_name} "
                f"(outsider: {r.outsider_name})"
            )

    @game.command()
    @click.argument("puzzle_date")
    @click.argument("round_num", type=int)
    @click.argument("title_id", type=int)
    @click.argument("title_name")
    @click.argument("a1", type=int)
    @click.argument("a2", type=int)
    @click.argument("a3", type=int)
    @click.argument("outsider", type=int)
    def add(puzzle_date, round_num, title_id, title_name, a1, a2, a3, outsider):
        """Manually add a curated round. Date format: YYYY-MM-DD."""
        from app.models import Person

        target = date.fromisoformat(puzzle_date)
        persons = {p.id: p for p in Person.query.filter(Person.id.in_([a1, a2, a3, outsider])).all()}

        row = OddOneOutRound(
            puzzle_date=target,
            round_number=round_num,
            title_id=title_id,
            title_name=title_name,
            actor_1_id=a1,
            actor_2_id=a2,
            actor_3_id=a3,
            outsider_id=outsider,
            actor_1_name=persons.get(a1, Person(name="Unknown")).name,
            actor_2_name=persons.get(a2, Person(name="Unknown")).name,
            actor_3_name=persons.get(a3, Person(name="Unknown")).name,
            outsider_name=persons.get(outsider, Person(name="Unknown")).name,
            actor_1_profile=getattr(persons.get(a1), "profile_path", None),
            actor_2_profile=getattr(persons.get(a2), "profile_path", None),
            actor_3_profile=getattr(persons.get(a3), "profile_path", None),
            outsider_profile=getattr(persons.get(outsider), "profile_path", None),
        )
        db.session.add(row)
        db.session.commit()
        click.echo(f"Added round {round_num} for {target}: {title_name}")
