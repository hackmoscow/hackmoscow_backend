from models import Thread, Message, User
from marshmallow_sqlalchemy import ModelSchema, ModelConverter
from marshmallow import post_load, fields
from utils import geo
from geoalchemy2 import Geometry
from geoalchemy2.elements import WKTElement
from geoalchemy2.shape import to_shape


class GeoConverter(ModelConverter):
    SQLA_TYPE_MAPPING = ModelConverter.SQLA_TYPE_MAPPING.copy()
    SQLA_TYPE_MAPPING.update({
        Geometry: fields.Str
    })


class GeographySerializationField(fields.String):
    def _serialize(self, value, attr, obj):
        if value is None:
            return value
        shply_geom = to_shape(value)
        return shply_geom.to_wkt()

    def _deserialize(self, value, attr, data):
        if value is None:
            return value

        if ',' in value:
            lat, lon = value.split(',')
            return geo.make_point_geometry(lat, lon)
        return WKTElement(value)


class CountSerializationField(fields.Number):
    def _serialize(self, value, attr, obj):
        return len(value) if value else 0


class MessageSchema(ModelSchema):
    class Meta:
        fields = ("author", "text", "created_at")
        model = Message


class ThreadSchema(ModelSchema):
    location = GeographySerializationField(attribute='location')
    likes = CountSerializationField(attribute='likes', dump_only=True)
    dislikes = CountSerializationField(attribute='dislikes', dump_only=True)

    class Meta:
        fields = ("id", "name", "location", "created_at", "likes", "dislikes")
        model = Thread
        model_converter = GeoConverter


class UserSchema(ModelSchema):
    class Meta:
        fields = ('name',)
        model = User


thread_schema = ThreadSchema()
message_schema = MessageSchema()
user_schema = UserSchema()
