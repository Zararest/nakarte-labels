"""Geometric helpers for track and waypoint data."""


def bounding_box(tracks):
    """Return (min_lat, max_lat, min_lng, max_lng) covering all track points.

    tracks — list of TrackData objects (from nktk_parser).
    Raises ValueError if no points are found.
    """
    lats, lngs = [], []
    for track in tracks:
        for seg in track.segments:
            for lat, lng in seg:
                lats.append(lat)
                lngs.append(lng)
        for lat, lng, _ in track.waypoints:
            lats.append(lat)
            lngs.append(lng)

    if not lats:
        raise ValueError('No track points found — cannot compute bounding box.')

    return min(lats), max(lats), min(lngs), max(lngs)


def bbox_center(tracks):
    """Return (lat, lng) at the centre of the track bounding box."""
    min_lat, max_lat, min_lng, max_lng = bounding_box(tracks)
    return (min_lat + max_lat) / 2, (min_lng + max_lng) / 2
