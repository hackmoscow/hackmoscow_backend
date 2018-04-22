import json
import os
from flask import Flask, request, abort, Response, g, url_for, current_app, redirect, render_template, \
    send_from_directory
from flask.views import MethodView
from models import Thread, Message, User
from utils.db import close_db_session_on_flask_shutdown
# from flask_login import LoginManager, login_user, login_required, current_user
from .schemas import thread_schema, message_schema, user_schema
from urllib.parse import urlparse, urljoin
from flask_cors import CORS


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc


def is_valid_location(text):
    if not text or not isinstance(text, str) or not ',' in text:
        return False
    try:
        lat, lon = text.split(',')
    except ValueError:
        return False

    return True


def get_user(session, pwd=None):
    # Trademarked IdiotAuth security
    if not pwd:
        return None
    return session.query(User).filter(User.password == pwd).first()


def create_app(db_session_factory):
    app = Flask(__name__, static_url_path='')
    app.secret_key = os.environ['API_SECRET_KEY']
    app.config['SECRET_KEY'] = os.environ['API_SECRET_KEY']
    app.db_session = db_session_factory

    app.cors = CORS(app, resources={r"*": {"origins": "*"}})

    # login_manager = LoginManager()
    # login_manager.login_view = "auth"
    # login_manager.session_protection = None
    # login_manager.init_app(app)

    # @login_manager.user_loader
    # def load_user(user_id):
    #    session = current_app.db_session()
    #    return session.query(User).filter(User.id == user_id).first()

    app.config['THREAD_DISTANCE'] = os.environ.get("THREAD_DISTANCE", 50)

    @app.teardown_appcontext
    def close_db_session(error):
        return close_db_session_on_flask_shutdown(app, g, error)

    class ThreadsAPI(MethodView):
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
            data = thread_schema.dump(thread).data
            return Response(
                response=json.dumps(data),
                status=201,
                mimetype='application/json'
            )

    class ThreadMessagesAPI(MethodView):
        def get(self, thread_id):
            session = current_app.db_session()
            thread = session.query(Thread).filter(Thread.id == thread_id).one()
            schema_dump = thread_schema.dump(thread).data
            messages = thread.messages
            schema_dump['messages'] = message_schema.dump(messages, many=True).data
            return Response(
                response=json.dumps(schema_dump),
                mimetype='application/json'
            )

        def post(self, thread_id):
            session = current_app.db_session()
            thread = session.query(Thread).filter(Thread.id == thread_id).first()
            if not thread:
                abort(404)
            data = request.json
            if not data or not is_valid_location(data.get('location')):
                abort(400)

            user = get_user(session, data.get('pwd'))
            if not user:
                abort(401)
            message = Message(text=data.get('text'))
            message.user = user
            thread.messages.append(message)
            session.add(message)
            session.add(thread)
            session.commit()
            return Response(
                response=json.dumps({'thread_id': thread.id, 'message_id': message.id}),
                status=201,
                mimetype='application/json'
            )

    class AuthAPI(MethodView):
        def post(self):
            data = request.json
            session = current_app.db_session()
            password = data.get('password', None)
            if not password:
                abort(400)
            user = session.query(User).filter(User.password == password).first()
            if not user:
                abort(401)
            return Response(
                response=json.dumps({'name': user.name}),
                status=201,
                mimetype='application/json'
            )

    class LikeAPI(MethodView):
        def post(self, thread_id):
            data = request.json
            session = current_app.db_session()
            user = get_user(session, data.get('pwd'))
            if not user:
                abort(401)
            thread = session.query(Thread).filter(Thread.id == thread_id).first()
            if not thread:
                abort(404)
            like = thread.like(session, user)
            if like:
                return Response(
                    response=json.dumps({"status": "liked"}),
                    status=201,
                    mimetype='application/json'
                )
            else:
                return Response(
                    response=json.dumps({"status": "unliked"}),
                    status=200,
                    mimetype='application/json'
                )

    class DislikeAPI(MethodView):
        def post(self, thread_id):
            data = request.json
            session = current_app.db_session()
            user = get_user(session, data.get('pwd'))
            if not user:
                abort(401)
            thread = session.query(Thread).filter(Thread.id == thread_id).first()
            if not thread:
                abort(404)
            like = thread.dislike(session, user)
            if like:
                return Response(
                    response=json.dumps({"status": "disliked"}),
                    status=201,
                    mimetype='application/json'
                )
            else:
                return Response(
                    response=json.dumps({"status": "undisliked"}),
                    status=200,
                    mimetype='application/json'
                )

    app.add_url_rule('/thread', view_func=ThreadsAPI.as_view('thread'))
    app.add_url_rule('/thread/<thread_id>', view_func=ThreadMessagesAPI.as_view('thread_messages'))
    app.add_url_rule('/thread/<thread_id>/like', view_func=LikeAPI.as_view('thread_likes'))
    app.add_url_rule('/thread/<thread_id>/dislike', view_func=DislikeAPI.as_view('thread_dislikes'))
    app.add_url_rule('/auth', view_func=AuthAPI.as_view('auth'))

    @app.route('/register', methods=['POST'])
    def register():
        data = request.json
        if not data or not data.get('password'):
            return abort(400)

        session = current_app.db_session()
        user = get_user(session, data.get('password'))
        if user:
            return Response(
                response=json.dumps({'name': user.name}),
                status=201,
                mimetype='application/json'
            )

        new_user = User(password=data['password'])
        session.add(new_user)
        session.commit()
        return Response(
            response=json.dumps({'name': new_user.name}),
            status=201,
            mimetype='application/json'
        )

    @app.route("/whoami", methods=['POST'])
    def whoami():
        data = request.json or {}
        session = current_app.db_session()
        user = get_user(session, data.get('pwd'))
        if not user:
            abort(401)
        return Response(response=json.dumps(user_schema.dump(user).data))

    @app.route('/')
    def index():
        return send_from_directory('front', 'index.html')

    # This crap is the only reason why frontend works, at all
    @app.route('/static/<path:path>')
    def serve_static(path):
        return send_from_directory('front', path)

    return app
