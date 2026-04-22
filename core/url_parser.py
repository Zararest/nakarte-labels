from urllib.parse import urlparse


def parse_nakarte_url(url):
    """Parse a nakarte.me URL, return dict with zoom, lat, lng, layers, nktk, nktl."""
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

    return {
        'zoom': int(m_parts[0]),
        'lat': float(m_parts[1]),
        'lng': float(m_parts[2]),
        'layers': params.get('l', 'O').split(','),
        'nktk': params.get('nktk'),  # inline base64 track data
        'nktl': params.get('nktl'),  # server-stored track id
    }


def extract_tracks(url_params):
    """Decode all track data referenced by a parsed URL param dict.

    Returns a list of TrackData. Raises RuntimeError / PermissionError on
    network or auth failures when fetching nktl tracks.
    """
    from core.nktk_parser import fetch_nktl, parse_nktk_sequence

    tracks = []
    if url_params.get('nktk'):
        tracks.extend(parse_nktk_sequence(url_params['nktk']))
    if url_params.get('nktl'):
        tracks.extend(fetch_nktl(url_params['nktl']))
    return tracks
