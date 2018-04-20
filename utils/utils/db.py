from flask import g
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


def get_db_engine(db_uri):
    engine = create_engine(db_uri, convert_unicode=True)
    return engine


def get_db_session_factory(engine):
    session_maker = sessionmaker(autocommit=False, autoflush=False)
    session_maker.configure(bind=engine)
    db_session_factory = scoped_session(session_maker)
    return db_session_factory


def create_tables(engine):
    from models import Base
    Base.metadata.create_all(bind=engine)


def close_db_session_on_flask_shutdown(app, g, error):
    """Closes the database again at the end of the request."""
    if app.db_session:
        try:
            app.db_session.commit()
        except:
            app.db_session.rollback()
            raise
        finally:
            app.db_session.remove()
    if hasattr(g, 'db_session'):
        g.db_session.remove()
