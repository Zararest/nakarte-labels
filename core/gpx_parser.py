from dataclasses import dataclass, field

import gpxpy


@dataclass
class WaypointPoint:
    lat: float
    lng: float
    name: str


@dataclass
class TrackSegment:
    name: str
    points: list = field(default_factory=list)  # list of (lat, lng) tuples


@dataclass
class GPXData:
    waypoints: list = field(default_factory=list)  # list[WaypointPoint]
    tracks: list = field(default_factory=list)      # list[TrackSegment]


def parse_gpx(gpx_file_path):
    with open(gpx_file_path, 'r', encoding='utf-8') as f:
        gpx = gpxpy.parse(f)

    waypoints = []

    for wpt in gpx.waypoints:
        waypoints.append(WaypointPoint(lat=wpt.latitude, lng=wpt.longitude, name=wpt.name or ''))

    tracks = []
    for trk in gpx.tracks:
        for seg in trk.segments:
            points = []
            for pt in seg.points:
                points.append((pt.latitude, pt.longitude))
                if pt.name:
                    waypoints.append(WaypointPoint(lat=pt.latitude, lng=pt.longitude, name=pt.name))
            tracks.append(TrackSegment(name=trk.name or '', points=points))

    return GPXData(waypoints=waypoints, tracks=tracks)
