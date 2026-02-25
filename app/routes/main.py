import json

from flask import Blueprint, Response, render_template, request

from app.models import Suggestion
from app.services.comparison import find_shared

main_bp = Blueprint("main", __name__)

SITEMAP_XML = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://samecast.com/</loc><changefreq>weekly</changefreq><priority>1.0</priority></url>
  <url><loc>https://samecast.com/oddoneout</loc><changefreq>daily</changefreq><priority>0.9</priority></url>
</urlset>"""

ROBOTS_TXT = """User-agent: *
Allow: /
Disallow: /search/
Disallow: /images/

Sitemap: https://samecast.com/sitemap.xml
"""


@main_bp.route("/sitemap.xml")
def sitemap():
    return Response(SITEMAP_XML, mimetype="application/xml")


@main_bp.route("/robots.txt")
def robots():
    return Response(ROBOTS_TXT, mimetype="text/plain")


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
