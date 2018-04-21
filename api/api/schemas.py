from models import Thread
from marshmallow_sqlalchemy import ModelSchema, ModelConverter
from marshmallow import post_load, fields
from utils import geo
from geoalchemy2 import Geometry
from geoalchemy2.elements import WKTElement


class GeoConverter(ModelConverter):
    SQLA_TYPE_MAPPING = ModelConverter.SQLA_TYPE_MAPPING.copy()
    SQLA_TYPE_MAPPING.update({
        Geometry: fields.Str
    })


class GeographySerializationField(fields.String):
    def _serialize(self, value, attr, obj):
        if value is None:
            return value
        else:
            if attr == 'location':
                return {'latitude': db.session.scalar(geo_funcs.ST_X(value)),
                        'longitude': db.session.scalar(geo_funcs.ST_Y(value))}
            else:
                return None

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
        else:
            if attr == 'location':
                return WKTElement(
                    'POINT({0} {1})'.format(str(value.get('longitude')), str(value.get('latitude'))))
            else:
                return None


class ThreadSchema(ModelSchema):
    location = GeographySerializationField(attribute='location')

    class Meta:
        model = Thread
        model_converter = GeoConverter

    @post_load
    def make_user(self, data):
        if not data.get('location') and data.get('lat') and data.get('long'):
            lat = data.get('lat')
            lon = data.get('lon')
            data['location'] = geo.make_point_geometry(lat, lon)
            del data['lat']
            del data['lon']
        return Thread(**data)


thread_schema = ThreadSchema()
