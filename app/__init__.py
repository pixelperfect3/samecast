import click
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

STARTER_SUGGESTIONS = [
    ("Game of Thrones", "The Crown"),
    ("The Dark Knight", "Inception"),
    ("Arrested Development", "Ozark"),
    ("The Departed", "Gangs of New York"),
    ("The Office", "The Morning Show"),
    ("Oppenheimer", "Interstellar"),
    ("Breaking Bad", "Malcolm in the Middle"),
    ("Goodfellas", "The Sopranos"),
    ("Succession", "The Big Short"),
    ("The Grand Budapest Hotel", "The French Dispatch"),
]


def create_app():
    app = Flask(__name__)
    app.config.from_object("app.config.Config")

    db.init_app(app)

    from app.routes.main import main_bp
    from app.routes.search import search_bp
    from app.routes.images import images_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(search_bp, url_prefix="/search")
    app.register_blueprint(images_bp, url_prefix="/images")

    with app.app_context():
        from app import models  # noqa: F401
        db.create_all()

    _register_cli(app)

    return app


def _register_cli(app):
    from app.models import Suggestion

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
