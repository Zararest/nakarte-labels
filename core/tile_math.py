import math

TILE_SIZE = 256


def lat_lng_to_tile(lat, lng, zoom):
    n = 2 ** zoom
    lat_rad = math.radians(lat)
    tile_x = int((lng + 180) / 360 * n)
    tile_y = int((1 - math.log(math.tan(lat_rad) + 1 / math.cos(lat_rad)) / math.pi) / 2 * n)
    return tile_x, tile_y


def lat_lng_to_pixel(lat, lng, zoom, tile_size=TILE_SIZE):
    n = 2 ** zoom
    lat_rad = math.radians(lat)
    x = (lng + 180) / 360 * n * tile_size
    y = (1 - math.log(math.tan(lat_rad) + 1 / math.cos(lat_rad)) / math.pi) / 2 * n * tile_size
    return x, y
