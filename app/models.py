from datetime import datetime, timezone
from app import db


class Title(db.Model):
    __tablename__ = "titles"

    id = db.Column(db.Integer, primary_key=True, autoincrement=False)  # TMDB ID
    media_type = db.Column(db.String(10), nullable=False)  # "movie" or "tv"
    title = db.Column(db.String(500), nullable=False)
    release_year = db.Column(db.Integer)
    overview = db.Column(db.Text)
    poster_path = db.Column(db.String(200))
    poster_cached = db.Column(db.Boolean, default=False)
    credits_cached = db.Column(db.Boolean, default=False)
    cached_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    credits = db.relationship("Credit", back_populates="title", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Title {self.id}: {self.title} ({self.media_type})>"


class Person(db.Model):
    __tablename__ = "persons"

    id = db.Column(db.Integer, primary_key=True, autoincrement=False)  # TMDB person ID
    name = db.Column(db.String(300), nullable=False)
    profile_path = db.Column(db.String(200))
    profile_cached = db.Column(db.Boolean, default=False)
    known_for_department = db.Column(db.String(100))
    cached_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    credits = db.relationship("Credit", back_populates="person", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Person {self.id}: {self.name}>"


class Credit(db.Model):
    __tablename__ = "credits"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title_id = db.Column(db.Integer, db.ForeignKey("titles.id"), nullable=False)
    person_id = db.Column(db.Integer, db.ForeignKey("persons.id"), nullable=False)
    credit_type = db.Column(db.String(10), nullable=False)  # "cast" or "crew"
    character = db.Column(db.String(500))  # for cast
    job = db.Column(db.String(200))  # for crew (e.g. "Director")
    department = db.Column(db.String(100))  # for crew (e.g. "Directing")
    display_order = db.Column(db.Integer)

    title = db.relationship("Title", back_populates="credits")
    person = db.relationship("Person", back_populates="credits")

    __table_args__ = (
        db.Index("ix_credit_title_person", "title_id", "person_id"),
        db.Index("ix_credit_person", "person_id"),
    )

    def __repr__(self):
        return f"<Credit {self.person_id} in {self.title_id} ({self.credit_type})>"
