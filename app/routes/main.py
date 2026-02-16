import json

from flask import Blueprint, render_template, request

from app.models import Suggestion
from app.services.comparison import find_shared

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    rows = Suggestion.query.filter_by(active=True).all()
    suggestions_json = json.dumps([s.to_dict() for s in rows])
    return render_template("index.html", suggestions_json=suggestions_json)


@main_bp.route("/compare")
def compare():
    title_id_1 = request.args.get("title_id_1")
    media_type_1 = request.args.get("media_type_1")
    title_id_2 = request.args.get("title_id_2")
    media_type_2 = request.args.get("media_type_2")

    if not all([title_id_1, media_type_1, title_id_2, media_type_2]):
        return render_template("partials/error.html", message="Please select two titles to compare.")

    if title_id_1 == title_id_2 and media_type_1 == media_type_2:
        return render_template("partials/error.html", message="Please pick two different titles!")

    try:
        result = find_shared(title_id_1, media_type_1, title_id_2, media_type_2)
    except Exception:
        return render_template("partials/error.html",
                               message="Something went wrong fetching data. Please try again.")

    return render_template("partials/comparison.html", **result)
