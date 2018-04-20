import os
import pytest
from api.app import create_app
from utils.db import get_db_engine, get_db_session_factory, create_tables
from models import Base


@pytest.yield_fixture(scope="function")
def engine():
    connection_string = os.environ['TEST_SQLALCHEMY_DATABASE_URI']
    engine = get_db_engine(connection_string)
    yield engine


@pytest.yield_fixture(scope="function")
def connection(engine):
    connection = engine.connect()
    transaction = connection.begin()
    Base.metadata.create_all(bind=engine)
    yield connection
    transaction.close()
    connection.close()


@pytest.yield_fixture(scope="function")
def session_factory(connection):
    db_session_factory = get_db_session_factory(connection)
    yield db_session_factory
    db_session_factory.remove()


@pytest.yield_fixture(scope="function")
def session(session_factory):
    session = session_factory()
    session.expire_on_commit = False
    yield session
    session.close()


@pytest.yield_fixture
def app(session_factory):
    app = create_app(session_factory)
    yield app


@pytest.yield_fixture
def client(app):
    with app.test_client() as client:
        yield client
