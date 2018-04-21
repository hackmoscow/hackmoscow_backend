from sqlalchemy import Column, Integer, String, func
from geoalchemy2 import Geometry
from utils import geo
from sqlalchemy import func
from .base import Base


class Thread(Base):
    __tablename__ = 'threads'
    id = Column(Integer, primary_key=True)
    name = Column(String())
    location = Column(Geometry('POINT')) # lat lon

    @classmethod
    def get_near_location(cls, session, lat, lon, max_distance):
        geometry = geo.make_point_geometry(lat, lon)
        threads = session.query(cls).filter(func.ST_DWithin(cls.location, geometry, max_distance)).all()
        return threads