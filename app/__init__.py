from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


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

    return app
