import json
from datetime import date

from flask import Blueprint, render_template, request

from app.models import OddOneOutRound
from app.services.puzzle import get_or_generate_today, puzzle_number, rounds_to_json

oddoneout_bp = Blueprint("oddoneout", __name__, template_folder="../templates")


@oddoneout_bp.route("/")
def index():
    """Serve today's OddOneOut puzzle."""
    try:
        rounds = get_or_generate_today()
    except ValueError as e:
        return render_template("partials/error.html", message=str(e)), 500

    today = date.today()
    rounds_json = rounds_to_json(rounds)

    return render_template(
        "oddoneout.html",
        rounds_json=json.dumps(rounds_json),
        puzzle_num=puzzle_number(today),
        puzzle_date=today.isoformat(),
    )


@oddoneout_bp.route("/guess", methods=["POST"])
def guess():
    """Handle a guess for a single round."""
    puzzle_date = request.form.get("puzzle_date")
    round_number = request.form.get("round_number", type=int)
    guessed_id = request.form.get("guessed_id", type=int)

    if not all([puzzle_date, round_number, guessed_id]):
        return render_template("partials/error.html", message="Missing parameters."), 400

    round_row = OddOneOutRound.query.filter_by(
        puzzle_date=puzzle_date,
        round_number=round_number,
    ).first()

    if not round_row:
        return render_template("partials/error.html", message="Round not found."), 404

    correct = guessed_id == round_row.outsider_id

    # Find the guessed actor's name
    guessed_name = None
    for aid, aname in [
        (round_row.actor_1_id, round_row.actor_1_name),
        (round_row.actor_2_id, round_row.actor_2_name),
        (round_row.actor_3_id, round_row.actor_3_name),
        (round_row.outsider_id, round_row.outsider_name),
    ]:
        if aid == guessed_id:
            guessed_name = aname
            break

    return render_template(
        "partials/oddoneout_result.html",
        correct=correct,
        guessed_name=guessed_name,
        outsider_name=round_row.outsider_name,
        outsider_id=round_row.outsider_id,
        title_name=round_row.title_name,
        round_number=round_number,
    )
