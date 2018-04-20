import json
import os
from flask import Flask, request, abort, Response, g, url_for, current_app
from .tasks import celery_app, add as task_add
from models import Result
from utils.db import close_db_session_on_flask_shutdown


def create_app(db_session_factory):
    app = Flask(__name__)
    app.secret_key = os.environ['API_SECRET_KEY']
    app.db_session = db_session_factory

    @app.teardown_appcontext
    def close_db_session(error):
        return close_db_session_on_flask_shutdown(app, g, error)

    @app.route('/add', methods=['POST'])
    def calculate():
        session = current_app.db_session()
        try:
            a, b = int(request.form.get('a', None)), int(request.form.get('b', None))
        except TypeError:
            abort(Response(
                response='Expected int params a, b',
                status=400))
        task_id = task_add.apply_async((a, b)).id

        # Notice we do not wait for the task to complete
        # We need to respond immediately or the HTTP request will time out.
        result = Result(task_id=task_id, result=None)
        session.add(result)
        session.commit()
        return Response(
            response=json.dumps({
                "task_id": task_id,
                "task_url": url_for("get_task_result", _external=True, task_id=task_id)
            })
        )

    @app.route('/task/<task_id>', methods=['GET'])
    def get_task_result(task_id):
        task_state = 'In processing'

        session = current_app.db_session()
        result = session.query(Result).filter_by(task_id=task_id).first()
        if not result:
            abort(404)
        if result.result:
            task_state = 'Done'
        return Response(
            response=json.dumps({'task_id': task_id, 'state': task_state, 'result': result.result}))

    return app
