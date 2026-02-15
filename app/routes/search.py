from flask import Blueprint, render_template, request

from app.services.tmdb import TMDBClient

search_bp = Blueprint("search", __name__)


@search_bp.route("/autocomplete")
def autocomplete():
    query = request.args.get("q", "").strip()
    slot = request.args.get("slot", "1")
    if len(query) < 2:
        return ""

    client = TMDBClient()
    results = client.search_multi(query)[:8]
    return render_template("partials/search_results.html", results=results, slot=slot)


@search_bp.route("/select")
def select():
    title_id = request.args.get("id")
    media_type = request.args.get("media_type")
    title = request.args.get("title", "")
    year = request.args.get("year", "")
    poster_path = request.args.get("poster_path", "")
    slot = request.args.get("slot", "1")

    return render_template(
        "partials/selected_title.html",
        title_id=title_id,
        media_type=media_type,
        title=title,
        year=year,
        poster_path=poster_path,
        slot=slot,
    )
