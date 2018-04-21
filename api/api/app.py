import json
import os
from flask import Flask, request, abort, Response, g, url_for, current_app
from flask.views import MethodView
from models import Thread
from utils.db import close_db_session_on_flask_shutdown
from .schemas import thread_schema
from flask import jsonify

def create_app(db_session_factory):
    app = Flask(__name__)
    app.secret_key = os.environ['API_SECRET_KEY']
    app.db_session = db_session_factory

    app.config['THREAD_DISTANCE'] = os.environ.get("THREAD_DISTANCE", 100)  # meters

    @app.teardown_appcontext
    def close_db_session(error):
        return close_db_session_on_flask_shutdown(app, g, error)

    class ThreadAPI(MethodView):
        def get(self):
            location = request.args.get('location')  # lat,lon
            if not location:
                abort(400)

            lat, lon = location.split(',')
            session = current_app.db_session()
            threads = Thread.get_near_location(session, lat, lon, app.config['THREAD_DISTANCE'])
            data = thread_schema.dump(threads, many=True).data
            return Response(
                response=json.dumps(data),
                mimetype='application/json'
            )

        def post(self):
            session = current_app.db_session()
            data = request.json
            if not data or not data.get('location') or len(data.get('location').split(',')) != 2:
                abort(400)
            thread = thread_schema.load(data, session=session).data
            session.add(thread)
            session.commit()
            return Response(
                response=json.dumps({'thread_id': thread.id}),
                status=201,
                mimetype='application/json'
            )


    app.add_url_rule('/thread', view_func=ThreadAPI.as_view('thread'))

    return app
