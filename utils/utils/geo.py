from geoalchemy2.elements import WKTElement


def make_point_geometry(lat, lon):
    return WKTElement(f'POINT ({lat} {lon})')
