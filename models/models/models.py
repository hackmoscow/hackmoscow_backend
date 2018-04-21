import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, func
from geoalchemy2 import Geometry
from sqlalchemy.orm import relationship, backref
from utils import geo
from .base import Base


class Thread(Base):
    __tablename__ = 'threads'
    id = Column(Integer, primary_key=True)
    name = Column(String())
    location = Column(Geometry('POINT')) # lat lon
    messages = relationship('Message', backref=backref("thread_messages"), order_by="Message.created_at")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

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
