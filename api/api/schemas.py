from models import Thread, Message
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
        """Deserialize value. Concrete :class:`Field` classes should implement this method.

        :param value: The value to be deserialized.
        :param str attr: The attribute/key in `data` to be deserialized.
        :param dict data: The raw input data passed to the `Schema.load`.
        :raise ValidationError: In case of formatting or validation failure.
        :return: The deserialized value.

        .. versionchanged:: 2.0.0
            Added ``attr`` and ``data`` parameters.
        """
        if value is None:
            return value

        if ',' in value:
            lat, lon = value.split(',')
            return geo.make_point_geometry(lat, lon)
        return WKTElement(value)


class ThreadSchema(ModelSchema):
    location = GeographySerializationField(attribute='location')

    class Meta:
        fields = ("id", "name", "location", "created_at")
        model = Thread
        model_converter = GeoConverter


class MessageSchema(ModelSchema):
    class Meta:
        fields = ("text", "created_at")
        model = Message


thread_schema = ThreadSchema()
message_schema = MessageSchema()
