import datetime
import enum
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Enum, func
from geoalchemy2 import Geometry
from sqlalchemy.orm import relationship, backref
from flask_login import UserMixin
from utils import geo
from .base import Base


class Thread(Base):
    __tablename__ = 'threads'
    id = Column(Integer, primary_key=True)
    name = Column(String())
    location = Column(Geometry('POINT'))  # lat lon
    messages = relationship('Message', backref=backref("thread_messages"), order_by="Message.created_at")
    likes = relationship('Like', backref=backref("thread_likes"))
    dislikes = relationship('Dislike', backref=backref("thread_dislikes"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    def like(self, session, user):
        for like in self.likes:
            if like.thread == self and like.user == user:
                session.delete(like)
                return None  # unlike
        like = Like()
        like.thread = self
        like.user = user
        session.add(like)
        self.likes.append(like)
        session.add(self)
        for dislike in self.dislikes:
            if dislike.thread == self and dislike.user == user:
                session.delete(dislike)
        session.commit()
        return like

    def dislike(self, session, user):
        for dislike in self.dislikes:
            if dislike.thread == self and dislike.user == user:
                session.delete(dislike)
                return None  # undislike
        dislike = Dislike()
        dislike.thread = self
        dislike.user = user
        session.add(dislike)
        self.dislikes.append(dislike)
        session.add(self)
        for like in self.likes:
            if like.thread == self and like.user == user:
                session.delete(like)
        session.commit()
        return dislike

    @classmethod
    def get_near_location(cls, session, lat, lon, max_distance):
        geometry = geo.make_point_geometry(lat, lon)
        threads = session.query(cls).filter(func.ST_DWithin(cls.location, geometry, max_distance)).all()
        return threads


class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    text = Column(Text)
    thread_id = Column(Integer, ForeignKey("threads.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Like(Base):
    __tablename__ = 'likes'
    id = Column(Integer, primary_key=True)
    thread_id = Column(Integer, ForeignKey("threads.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    thread = relationship("Thread")
    user = relationship("User")


class Dislike(Base):
    __tablename__ = 'dislikes'
    id = Column(Integer, primary_key=True)
    thread_id = Column(Integer, ForeignKey("threads.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    thread = relationship("Thread")
    user = relationship("User")


def default_name(user):
    return user.password + 'abcd'


class User(UserMixin, Base):
    __tablename__ = 'users'

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.name not in kwargs:
            self.name = self.__table__.c.name.default.arg(self)

    id = Column(Integer, primary_key=True)
    password = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=True, default=default_name)

    def __repr__(self):
        return self.password
