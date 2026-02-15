import os

import requests
from flask import Blueprint, send_file, redirect, current_app

images_bp = Blueprint("images", __name__)

POSTER_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "images", "posters")
PROFILE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "images", "profiles")


@images_bp.route("/poster/<path:filename>")
def poster(filename):
    return _serve_image(filename, POSTER_DIR, "w500")


@images_bp.route("/profile/<path:filename>")
def profile(filename):
    return _serve_image(filename, PROFILE_DIR, "w185")


def _serve_image(filename, cache_dir, size):
    """Serve image from local cache, or download from TMDB and cache it."""
    local_path = os.path.join(cache_dir, filename)

    if os.path.exists(local_path):
        return send_file(local_path)

    # Try to download and cache
    tmdb_url = f"{current_app.config['TMDB_IMAGE_BASE_URL']}/{size}/{filename}"
    try:
        resp = requests.get(tmdb_url, timeout=5, stream=True)
        resp.raise_for_status()

        os.makedirs(cache_dir, exist_ok=True)
        with open(local_path, "wb") as f:
            for chunk in resp.iter_content(1024):
                f.write(chunk)

        return send_file(local_path)
    except Exception:
        # Fallback: redirect to TMDB CDN
        return redirect(tmdb_url)
