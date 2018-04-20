import os
from flask import Flask, redirect, url_for, g
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from models import Result
from utils.db import close_db_session_on_flask_shutdown


def create_app(db_session_factory):
    """
    Application factory
    """

    app = Flask(__name__)
    app.secret_key = os.environ['ADMIN_SECRET_KEY']
    app.db_session = db_session_factory
    app.admin = Admin(app, name=app.name, template_mode='bootstrap3')

    app.admin.add_view(ModelView(Result, app.db_session))

    @app.route("/")
    def index():
        return redirect(url_for('admin.index'))

    @app.teardown_appcontext
    def close_db_session(error):
        close_db_session_on_flask_shutdown(app, g, error)

    return app
