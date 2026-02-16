from datetime import datetime, timezone

from app import db
from app.models import Title, Person, Credit
from app.services.tmdb import TMDBClient


def get_title_with_credits(title_id, media_type):
    """
    Get title details and credits, using DB cache when available.
    Returns the same dict format as TMDBClient.get_movie/tv_details().
    """
    title_id = int(title_id)

    # Check cache
    title = Title.query.get(title_id)
    if title and title.credits_cached:
        current_year = datetime.now(timezone.utc).year
        if title.release_year is None or title.release_year < current_year:
            return _load_from_db(title)
        # Current/future year — re-fetch for fresh data

    # Cache miss — fetch from TMDB
    client = TMDBClient()
    if media_type == "movie":
        details = client.get_movie_details(title_id)
    else:
        details = client.get_tv_details(title_id)

    _save_to_db(details)
    return details


def _save_to_db(details):
    """Upsert title, persons, and credits into the database."""
    now = datetime.now(timezone.utc)
    title_id = details["id"]

    # Upsert title
    title = Title.query.get(title_id)
    if title:
        title.title = details["title"]
        title.media_type = details["media_type"]
        title.release_year = details["release_year"]
        title.overview = details["overview"]
        title.poster_path = details["poster_path"]
        title.credits_cached = True
        title.cached_at = now
    else:
        title = Title(
            id=title_id,
            media_type=details["media_type"],
            title=details["title"],
            release_year=details["release_year"],
            overview=details["overview"],
            poster_path=details["poster_path"],
            credits_cached=True,
            cached_at=now,
        )
        db.session.add(title)

    # Delete old credits for this title (full refresh)
    Credit.query.filter_by(title_id=title_id).delete()

    # Upsert persons and insert credits
    all_credits = []
    for entry in details.get("cast", []):
        _upsert_person(entry, now)
        all_credits.append(Credit(
            title_id=title_id,
            person_id=entry["person_id"],
            credit_type="cast",
            character=entry.get("character", ""),
            display_order=entry.get("display_order", 999),
        ))

    for entry in details.get("crew", []):
        _upsert_person(entry, now)
        all_credits.append(Credit(
            title_id=title_id,
            person_id=entry["person_id"],
            credit_type="crew",
            job=entry.get("job", ""),
            department=entry.get("department", ""),
        ))

    db.session.add_all(all_credits)
    db.session.commit()


def _upsert_person(entry, now):
    """Insert or update a person record."""
    person_id = entry["person_id"]
    person = Person.query.get(person_id)
    if person:
        person.name = entry["name"]
        person.profile_path = entry.get("profile_path")
        person.known_for_department = entry.get("known_for_department")
        person.cached_at = now
    else:
        person = Person(
            id=person_id,
            name=entry["name"],
            profile_path=entry.get("profile_path"),
            known_for_department=entry.get("known_for_department"),
            cached_at=now,
        )
        db.session.add(person)


def _load_from_db(title):
    """Load title details and credits from the database into the standard dict format."""
    credits = Credit.query.filter_by(title_id=title.id).all()

    cast = []
    crew = []
    for c in credits:
        person = Person.query.get(c.person_id)
        if not person:
            continue
        entry = {
            "person_id": person.id,
            "name": person.name,
            "profile_path": person.profile_path,
            "known_for_department": person.known_for_department,
            "credit_type": c.credit_type,
        }
        if c.credit_type == "cast":
            entry["character"] = c.character or ""
            entry["display_order"] = c.display_order or 999
            cast.append(entry)
        else:
            entry["job"] = c.job or ""
            entry["department"] = c.department or ""
            crew.append(entry)

    cast.sort(key=lambda x: x.get("display_order", 999))

    return {
        "id": title.id,
        "media_type": title.media_type,
        "title": title.title,
        "release_year": title.release_year,
        "overview": title.overview,
        "poster_path": title.poster_path,
        "cast": cast,
        "crew": crew,
    }
