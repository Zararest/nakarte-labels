"""Map nakarte.me layer codes to tile sources.

nakarte stores active layers as a single string in the `l=` URL parameter.
Codes are 1–4 characters long and are packed without separators, so parsing
requires a greedy longest-match against the known code table.

Each REGISTRY entry is a (title, tile_url_template, is_tms) tuple:
  tile_url_template — supports {z}, {x}, {y} in any position/separator
  is_tms            — True when the tile server uses TMS (y-axis inverted)
"""

import click

# ---------------------------------------------------------------------------
# Registry of known nakarte layer codes → (title, tile_url_template, is_tms)
# ---------------------------------------------------------------------------
REGISTRY = {
    # OpenStreetMap family
    'O':   ('OpenStreetMap',
            'https://tile.openstreetmap.org/{z}/{x}/{y}.png', False),
    'Otm': ('OpenTopoMap',
            'https://a.tile.opentopomap.org/{z}/{x}/{y}.png', False),
    'Co':  ('CyclOSM',
            'https://a.tile-cyclosm.openstreetmap.fr/cyclosm/{z}/{x}/{y}.png', False),

    # Russian topographic maps — tiles.nakarte.me, TMS convention (y-axis flipped)
    'D':   ('Topo 10km',  'https://a.tiles.nakarte.me/topo10000/{z}/{x}/{y}', True),
    'C':   ('Topo 1km',   'https://a.tiles.nakarte.me/topo1000/{z}/{x}/{y}',  True),
    'B':   ('Topo 500m',  'https://a.tiles.nakarte.me/topo500/{z}/{x}/{y}',   True),
    'T25': ('Topo 250m',  'https://a.tiles.nakarte.me/topo250/{z}/{x}/{y}',   True),

    # GGC (Soviet military maps) — tiles.nakarte.me, TMS convention (y-axis flipped)
    'N':   ('GGC 2km',   'https://a.tiles.nakarte.me/ggc2000/{z}/{x}/{y}',  True),
    'J':   ('GGC 1km',   'https://a.tiles.nakarte.me/ggc1000/{z}/{x}/{y}',  True),
    'F':   ('GGC 500m',  'https://a.tiles.nakarte.me/ggc500/{z}/{x}/{y}',   True),
    'K':   ('GGC 250m',  'https://a.tiles.nakarte.me/ggc250/{z}/{x}/{y}',   True),

    # mapy.cz (served via nakarte CORS proxy, dash-separated coordinates)
    'Czt': ('mapy.cz tourist', 'https://proxy.nakarte.me/mapy/turist-en/{z}-{x}-{y}', False),
    'Czw': ('mapy.cz winter',  'https://proxy.nakarte.me/mapy/winter-en-down/{z}-{x}-{y}', False),

    # Norway
    'Np': ('Norway paper map',
           'https://cache.kartverket.no/v1/wmts/1.0.0/toporaster/default/webmercator/{z}/{y}/{x}.png',
           False),
    'Nm': ('Norway topo',
           'https://cache.kartverket.no/v1/wmts/1.0.0/topo/default/webmercator/{z}/{y}/{x}.png',
           False),
}

# Layers that need third-party API keys and cannot be fetched publicly.
_REQUIRES_KEY = {'G', 'Gh', 'L', 'P', 'S', 'Y', 'I', 'E'}

# Known codes sorted longest-first for greedy matching.
_CODES_BY_LENGTH = sorted(REGISTRY, key=len, reverse=True)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_layer_codes(l_param):
    """Parse the nakarte `l=` value into a list of layer codes.

    Codes are 1–4 characters, packed without separators.  We match greedily
    from left to right, always trying the longest known code first.
    """
    if not l_param:
        return ['O']

    codes = []
    rest = l_param
    while rest:
        for code in _CODES_BY_LENGTH:
            if rest.startswith(code):
                codes.append(code)
                rest = rest[len(code):]
                break
        else:
            # Unknown prefix — consume one character and continue.
            codes.append(rest[0])
            rest = rest[1:]
    return codes


def resolve_layers(layer_codes):
    """Return a list of (title, url_template, is_tms) for the given codes.

    Skips API-key-only layers with a warning.  Falls back to OSM when
    nothing else is available.
    """
    result = []
    for code in layer_codes:
        if code in _REQUIRES_KEY:
            click.echo(f"  Layer '{code}' requires an API key — skipped.", err=True)
            continue
        if code in REGISTRY:
            result.append(REGISTRY[code])
        else:
            click.echo(f"  Layer '{code}' is not yet supported — skipped.", err=True)

    if not result:
        click.echo('  No usable layers — falling back to OpenStreetMap.', err=True)
        result.append(REGISTRY['O'])

    return result
