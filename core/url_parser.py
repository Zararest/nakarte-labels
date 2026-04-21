from urllib.parse import urlparse


def parse_nakarte_url(url):
    """Parse a nakarte.me URL, return dict with zoom, lat, lng, layers."""
    parsed = urlparse(url)
    fragment = parsed.fragment

    params = {}
    for part in fragment.split('&'):
        if '=' in part:
            key, value = part.split('=', 1)
            params[key] = value

    if 'm' not in params:
        raise ValueError("URL is missing the 'm' parameter (zoom/lat/lng)")

    m_parts = params['m'].split('/')
    if len(m_parts) != 3:
        raise ValueError(f"Invalid 'm' parameter: {params['m']!r}")

    zoom = int(m_parts[0])
    lat = float(m_parts[1])
    lng = float(m_parts[2])
    layers = params.get('l', 'O').split(',')

    return {'zoom': zoom, 'lat': lat, 'lng': lng, 'layers': layers}
