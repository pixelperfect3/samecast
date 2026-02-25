import random
from datetime import date, datetime, timezone

from sqlalchemy import func

from app import db
from app.models import Credit, OddOneOutRound, Person, Title

# Day 1 of OddOneOut
LAUNCH_DATE = date(2025, 2, 24)


def puzzle_number(target_date=None):
    """Return the puzzle number for a given date (Day 1 = launch date)."""
    if target_date is None:
        target_date = date.today()
    return (target_date - LAUNCH_DATE).days + 1


def get_or_generate_today():
    """Return 3 rounds for today, generating if needed."""
    today = date.today()
    rounds = (
        OddOneOutRound.query
        .filter_by(puzzle_date=today)
        .order_by(OddOneOutRound.round_number)
        .all()
    )
    if len(rounds) == 3:
        return rounds
    return generate_rounds_for_date(today)


def generate_rounds_for_date(target_date):
    """Auto-generate 3 rounds for a given date using cached titles."""
    # Find titles with enough cast members
    titles_with_cast = (
        db.session.query(Title.id, Title.title, Title.media_type)
        .join(Credit, Credit.title_id == Title.id)
        .filter(Title.credits_cached == True, Credit.credit_type == "cast")  # noqa: E712
        .group_by(Title.id)
        .having(func.count(Credit.id) >= 4)
        .all()
    )

    if len(titles_with_cast) < 4:
        raise ValueError("Not enough cached titles with 4+ cast to generate puzzles. Cache more titles first.")

    random.shuffle(titles_with_cast)
    used_title_ids = set()
    rounds = []

    for round_num in range(1, 4):
        round_row = _build_round(target_date, round_num, titles_with_cast, used_title_ids)
        if round_row is None:
            raise ValueError(f"Could not generate round {round_num} — not enough suitable titles.")
        rounds.append(round_row)
        db.session.add(round_row)

    db.session.commit()
    return rounds


def _build_round(target_date, round_number, titles_with_cast, used_title_ids):
    """Build a single round: pick a title, 3 cast, 1 outsider."""
    for title_id, title_name, media_type in titles_with_cast:
        if title_id in used_title_ids:
            continue

        # Get top-billed cast for this title
        cast = (
            Credit.query
            .filter_by(title_id=title_id, credit_type="cast")
            .order_by(Credit.display_order.asc())
            .limit(15)
            .all()
        )

        if len(cast) < 3:
            continue

        # Pick 3 actors from the cast
        chosen_cast = random.sample(cast[:min(len(cast), 10)], 3)
        cast_person_ids = {c.person_id for c in Credit.query.filter_by(title_id=title_id, credit_type="cast").all()}

        # Find an outsider from a different title
        outsider = _find_outsider(title_id, cast_person_ids, titles_with_cast, used_title_ids)
        if outsider is None:
            continue

        # Load person details
        person_ids = [c.person_id for c in chosen_cast] + [outsider.id]
        persons = {p.id: p for p in Person.query.filter(Person.id.in_(person_ids)).all()}

        used_title_ids.add(title_id)

        return OddOneOutRound(
            puzzle_date=target_date,
            round_number=round_number,
            title_id=title_id,
            title_name=title_name,
            actor_1_id=chosen_cast[0].person_id,
            actor_2_id=chosen_cast[1].person_id,
            actor_3_id=chosen_cast[2].person_id,
            outsider_id=outsider.id,
            actor_1_name=persons.get(chosen_cast[0].person_id, Person(name="?")).name,
            actor_2_name=persons.get(chosen_cast[1].person_id, Person(name="?")).name,
            actor_3_name=persons.get(chosen_cast[2].person_id, Person(name="?")).name,
            outsider_name=persons.get(outsider.id, Person(name="?")).name,
            actor_1_profile=persons.get(chosen_cast[0].person_id, Person()).profile_path,
            actor_2_profile=persons.get(chosen_cast[1].person_id, Person()).profile_path,
            actor_3_profile=persons.get(chosen_cast[2].person_id, Person()).profile_path,
            outsider_profile=persons.get(outsider.id, Person()).profile_path,
        )

    return None


def _find_outsider(target_title_id, cast_person_ids, titles_with_cast, used_title_ids):
    """Find an actor from a different title who is NOT in the target title's cast."""
    candidates = [t for t in titles_with_cast if t[0] != target_title_id]
    random.shuffle(candidates)

    for other_title_id, _, _ in candidates[:10]:
        other_cast = (
            Credit.query
            .filter_by(title_id=other_title_id, credit_type="cast")
            .order_by(Credit.display_order.asc())
            .limit(10)
            .all()
        )
        random.shuffle(other_cast)
        for credit in other_cast:
            if credit.person_id not in cast_person_ids:
                person = Person.query.get(credit.person_id)
                if person:
                    return person
    return None


def rounds_to_json(rounds):
    """Convert OddOneOutRound rows to a JSON-serializable list with shuffled actors."""
    result = []
    for r in rounds:
        actors = [
            {"id": r.actor_1_id, "name": r.actor_1_name, "profile": r.actor_1_profile},
            {"id": r.actor_2_id, "name": r.actor_2_name, "profile": r.actor_2_profile},
            {"id": r.actor_3_id, "name": r.actor_3_name, "profile": r.actor_3_profile},
            {"id": r.outsider_id, "name": r.outsider_name, "profile": r.outsider_profile},
        ]
        random.shuffle(actors)
        result.append({
            "round_number": r.round_number,
            "actors": actors,
            "title_name": r.title_name,
            "outsider_id": r.outsider_id,
            "outsider_name": r.outsider_name,
        })
    return result
