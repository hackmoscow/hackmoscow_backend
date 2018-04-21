import json
import os
from flask import Flask, request, abort, Response, g, url_for, current_app
from flask.views import MethodView
from models import Thread
from utils.db import close_db_session_on_flask_shutdown
from .schemas import thread_schema, message_schema
from flask import jsonify


def is_valid_location(text):
    if not text or not isinstance(text, str) or not ',' in text:
        return False
    try:
        lat, lon = text.split(',')
    except ValueError:
        return False

    return True


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
            if not is_valid_location(location):
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
            if not data or not is_valid_location(data.get('location')):
                abort(400)
            thread = thread_schema.load(data, session=session).data
            session.add(thread)
            session.commit()
            return Response(
                response=json.dumps({'thread_id': thread.id}),
                status=201,
                mimetype='application/json'
            )

    class MessagesAPI(MethodView):
        def get(self, thread_id):
            session = current_app.db_session()
            thread = session.query(Thread).filter(Thread.id == thread_id).one()
            messages = thread.messages
            data = message_schema.dump(messages, many=True).data
            return Response(
                response=json.dumps(data),
                mimetype='application/json'
            )

        def post(self, thread_id):
            session = current_app.db_session()
            thread = session.query(Thread).filter(Thread.id == thread_id).one()
            session = current_app.db_session()
            data = request.json
            if not data or not is_valid_location(data.get('location')):
                abort(400)

            # TODO CHECK USER IS WITHIN DISTANCE TO POST TO THREAD
            message = message_schema.load(data, session=session).data
            thread.messages.append(message)
            session.add(message)
            session.add(thread)
            session.commit()
            return Response(
                response=json.dumps({'thread_id': thread.id, 'message_id': message.id}),
                status=201,
                mimetype='application/json'
            )

    app.add_url_rule('/thread', view_func=ThreadAPI.as_view('thread'))
    app.add_url_rule('/thread/<thread_id>', view_func=MessagesAPI.as_view('thread_messages'))

    return app
