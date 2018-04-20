import time
import os
from celery import Celery
from models import Result
from utils.db import get_db_engine, get_db_session_factory

RABBITMQ_URL = os.environ['RABBITMQ_URL']

celery_app = Celery(broker=RABBITMQ_URL,
                    backend=RABBITMQ_URL)


def store_task_result(task_id, result):
    engine = get_db_engine(os.environ['SQLALCHEMY_DATABASE_URI'])
    db_session_factory = get_db_session_factory(engine)
    session = db_session_factory()
    try:
        result_object = session.query(Result).filter_by(task_id=task_id).one()
        result_object.result = str(result)
        session.add(result_object)
        session.commit()
    finally:
        session.close()


@celery_app.task
def add(x, y):
    # Counting is hard
    time.sleep(3)
    result = x + y
    store_task_result(add.request.id, result)
    return result
