import os

from flask import Flask

from app.database import close_db, init_db


def create_app(config=None):
    app = Flask(__name__)

    db_path = os.path.join(app.instance_path, "data.db")
    app.config["DATABASE"] = db_path

    if config:
        app.config.update(config)

    os.makedirs(app.instance_path, exist_ok=True)

    init_db(app)
    app.teardown_appcontext(close_db)

    from app.routes import tables, rows
    app.register_blueprint(tables.bp)
    app.register_blueprint(rows.bp)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
