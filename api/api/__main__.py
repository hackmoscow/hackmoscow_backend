import os
import logging
from .app import create_app
from utils.db import get_db_engine, get_db_session_factory, create_tables


def configure_logging():
    # Enable logging
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.DEBUG)


def main():
    configure_logging()
    SQLALCHEMY_DATABASE_URI = os.environ['SQLALCHEMY_DATABASE_URI']
    engine = get_db_engine(SQLALCHEMY_DATABASE_URI)
    db_session_factory = get_db_session_factory(engine)
    create_tables(engine)
    app = create_app(db_session_factory)
    app.run(port=8000, host="0.0.0.0")


if __name__ == '__main__':
    main()
