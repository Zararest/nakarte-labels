"""Decoder for nakarte.me nktk (inline) and nktl (server-stored) track URL parameters.

nktk= — URL-safe Base64 track data embedded in the URL hash.
nktl= — Track ID; the binary nktk sequence is fetched from tracks.nakarte.me.

Each value may contain multiple tracks separated by '/'.
"""

import base64
from dataclasses import dataclass, field

import httpx

ARC_UNIT = ((1 << 24) - 1) / 360  # ≈ 46603.375
_TRACKS_SERVER = 'https://tracks.nakarte.me'
_USER_AGENT = 'nakarte-map-exporter/1.0 (https://github.com/Zararest/nakarte-labels)'


@dataclass
class TrackData:
    name: str = ''
    segments: list = field(default_factory=list)  # list[list[tuple[lat, lng]]]
    waypoints: list = field(default_factory=list)  # list[tuple[lat, lng, name]]


# ---------------------------------------------------------------------------
# URL-safe Base64

def _b64decode(s):
    s = s.strip().replace('\n', '').replace('\r', '').replace('\t', '').replace(' ', '')
    s = s.replace('-', '+').replace('_', '/')
    s += '=' * (-len(s) % 4)
    return base64.b64decode(s)


# ---------------------------------------------------------------------------
# Nakarte custom variable-length signed integer (versions 1-3)

def _unpack_num(data, pos):
    b0 = data[pos]
    if b0 < 128:
        return b0 - 64, pos + 1
    b1 = data[pos + 1]
    if b1 < 128:
        n = (b0 & 0x7F) | (b1 << 7)
        return n - 8192, pos + 2
    b2 = data[pos + 2]
    if b2 < 128:
        n = (b0 & 0x7F) | ((b1 & 0x7F) << 7) | (b2 << 14)
        return n - 1048576, pos + 3
    b3 = data[pos + 3]
    n = (b0 & 0x7F) | ((b1 & 0x7F) << 7) | ((b2 & 0x7F) << 14) | (b3 << 21)
    return n - 268435456, pos + 4


# ---------------------------------------------------------------------------
# Minimal protobuf wire-format parser (version 4)

def _varint(data, pos):
    n, shift = 0, 0
    while True:
        b = data[pos]; pos += 1
        n |= (b & 0x7F) << shift
        if not (b & 0x80):
            return n, pos
        shift += 7


def _zz(n):
    return (n >> 1) ^ -(n & 1)


def _packed_sint32(payload):
    values, pos = [], 0
    while pos < len(payload):
        n, pos = _varint(payload, pos)
        values.append(_zz(n))
    return values


def _tag(data, pos):
    t, pos = _varint(data, pos)
    return t >> 3, t & 7, pos


def _ld(data, pos):
    n, pos = _varint(data, pos)
    return data[pos:pos + n], pos + n


def _parse_waypoint_pb(data):
    lat = lon = 0
    name = ''
    pos = 0
    while pos < len(data):
        fn, wt, pos = _tag(data, pos)
        if wt == 0:
            v, pos = _varint(data, pos)
            if fn == 1:
                lat = _zz(v)
            elif fn == 2:
                lon = _zz(v)
        elif wt == 2:
            payload, pos = _ld(data, pos)
            if fn == 3:
                name = payload.decode('utf-8')
    return lat, lon, name


def _parse_waypoints_pb(data):
    mid_lat = mid_lon = 0
    raw_wps = []
    pos = 0
    while pos < len(data):
        fn, wt, pos = _tag(data, pos)
        if wt == 0:
            v, pos = _varint(data, pos)
            if fn == 1:
                mid_lat = _zz(v)
            elif fn == 2:
                mid_lon = _zz(v)
        elif wt == 2:
            payload, pos = _ld(data, pos)
            if fn == 3:
                raw_wps.append(_parse_waypoint_pb(payload))
    return mid_lat, mid_lon, raw_wps


def _parse_segment_pb(data):
    lats, lons = [], []
    pos = 0
    while pos < len(data):
        fn, wt, pos = _tag(data, pos)
        if wt == 2:
            payload, pos = _ld(data, pos)
            if fn == 1:
                lats = _packed_sint32(payload)
            elif fn == 2:
                lons = _packed_sint32(payload)
    return lats, lons


def _parse_track_pb(data):
    name = ''
    seg_payloads = []
    wp_payload = None
    pos = 0
    while pos < len(data):
        fn, wt, pos = _tag(data, pos)
        if wt == 2:
            payload, pos = _ld(data, pos)
            if fn == 1:
                name = payload.decode('utf-8')
            elif fn == 2:
                seg_payloads.append(payload)
            elif fn == 3:
                wp_payload = payload
    return name, seg_payloads, wp_payload


def _parse_trackview_pb(data):
    track_payload = None
    pos = 0
    while pos < len(data):
        fn, wt, pos = _tag(data, pos)
        if wt == 2:
            payload, pos = _ld(data, pos)
            if fn == 2:
                track_payload = payload
        elif wt == 0:
            _, pos = _varint(data, pos)  # skip View int32/bool fields

    if track_payload is None:
        return TrackData()

    name, seg_payloads, wp_payload = _parse_track_pb(track_payload)
    td = TrackData(name=name)

    for seg_payload in seg_payloads:
        dlats, dlons = _parse_segment_pb(seg_payload)
        lat_acc = lon_acc = 0
        points = []
        for dlat, dlon in zip(dlats, dlons):
            lat_acc += dlat
            lon_acc += dlon
            points.append((lat_acc / ARC_UNIT, lon_acc / ARC_UNIT))
        if points:
            td.segments.append(points)

    if wp_payload:
        mid_lat, mid_lon, raw_wps = _parse_waypoints_pb(wp_payload)
        for wlat, wlon, wname in raw_wps:
            td.waypoints.append(
                ((wlat + mid_lat) / ARC_UNIT, (wlon + mid_lon) / ARC_UNIT, wname)
            )

    return td


# ---------------------------------------------------------------------------
# Legacy format (versions 1-3)

def _parse_nktk_legacy(data, pos, version):
    try:
        n, pos = _unpack_num(data, pos)
        name = data[pos:pos + n].decode('utf-8', errors='replace')
        pos += n

        seg_count, pos = _unpack_num(data, pos)
        segments = []
        for _ in range(seg_count):
            pt_count, pos = _unpack_num(data, pos)
            x = y = 0
            points = []
            for _ in range(pt_count):
                dx, pos = _unpack_num(data, pos)
                dy, pos = _unpack_num(data, pos)
                x += dx
                y += dy
                points.append((y / ARC_UNIT, x / ARC_UNIT))  # lat, lng
            segments.append(points)

        # color + ticks (v1+) — skip
        try:
            _, pos = _unpack_num(data, pos)
            _, pos = _unpack_num(data, pos)
        except Exception:
            pass

        # hidden flag (v3+) — skip
        if version >= 3:
            try:
                _, pos = _unpack_num(data, pos)
            except Exception:
                pass

        waypoints = []
        if version >= 2:
            try:
                wp_count, pos = _unpack_num(data, pos)
                if wp_count > 0:
                    mid_x, pos = _unpack_num(data, pos)
                    mid_y, pos = _unpack_num(data, pos)
                    for _ in range(wp_count):
                        n, pos = _unpack_num(data, pos)
                        wp_name = data[pos:pos + n].decode('utf-8', errors='replace')
                        pos += n
                        _, pos = _unpack_num(data, pos)  # symbol — skip
                        dx, pos = _unpack_num(data, pos)
                        dy, pos = _unpack_num(data, pos)
                        waypoints.append(
                            ((dy + mid_y) / ARC_UNIT, (dx + mid_x) / ARC_UNIT, wp_name)
                        )
            except Exception:
                pass

        return TrackData(name=name, segments=segments, waypoints=waypoints)
    except Exception:
        return TrackData(name='corrupt track')


# ---------------------------------------------------------------------------
# Public API

def parse_nktk_fragment(s):
    """Decode a single URL-safe Base64 nktk fragment."""
    try:
        data = _b64decode(s)
    except Exception:
        return TrackData(name='corrupt track')

    version, pos = _unpack_num(data, 0)

    if version in (1, 2, 3):
        return _parse_nktk_legacy(data, pos, version)
    if version == 4:
        return _parse_trackview_pb(data[pos:])
    return TrackData(name=f'unsupported version {version}')


def parse_nktk_sequence(s):
    """Decode a '/'-separated nktk sequence string."""
    return [parse_nktk_fragment(part) for part in s.split('/') if part.strip()]


def fetch_nktl(track_id):
    """Fetch a track from nakarte's track server and return decoded TrackData list."""
    url = f'{_TRACKS_SERVER}/track/{track_id}'
    try:
        r = httpx.get(url, headers={'User-Agent': _USER_AGENT}, timeout=15, follow_redirects=True)
        r.raise_for_status()
    except httpx.HTTPStatusError as e:
        code = e.response.status_code
        if code in (401, 403):
            raise PermissionError(
                f'Track {track_id!r} is private or requires a login session. '
                'Open nakarte.me in the browser and keep the session active, '
                'or use a URL whose track is stored inline (nktk= parameter).'
            ) from e
        raise RuntimeError(f'Server returned HTTP {code} for track {track_id!r}') from e
    except httpx.RequestError as e:
        raise RuntimeError(f'Network error fetching track {track_id!r}: {e}') from e

    return parse_nktk_sequence(r.text)
