"""Map nakarte.me layer codes to XYZ tile URL templates.

nakarte encodes active layers as a string of single characters in the URL
hash parameter `l=`.  Each character is one layer; multiple layers are
composited in order (first = bottom / base layer).

Tile URL templates use {z}, {x}, {y} placeholders.

For layer codes not in REGISTRY we attempt
  https://tiles.nakarte.me/{code}/{z}/{x}/{y}
which covers most of nakarte's own-hosted layers (Russian topo maps, etc.).
If that also fails, the layer is skipped with a warning.
"""

import click

# Definitively known public tile servers, no API key required.
REGISTRY = {
    'O': 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
    'C': 'https://tile-cyclosm.openstreetmap.fr/cyclosm/{z}/{x}/{y}.png',
}

# nakarte hosts its own raster tiles (Russian topo, etc.) at this base URL.
# Most single-character layer codes map directly to a path component there.
_NAKARTE_TILES = 'https://tiles.nakarte.me/{code}/{z}/{x}/{y}'

# Layers that require third-party API keys and cannot be fetched without them.
_REQUIRES_KEY = {'G', 'S', 'A', 'B'}  # Google, Bing satellite, etc.


def resolve_layers(layer_codes):
    """Return a list of tile URL templates for the given layer code characters.

    Skips layers that require an API key (with a warning).
    Falls back to nakarte's tile server for unknown codes.
    Falls back to OSM if everything else is unavailable.
    """
    urls = []
    for code in layer_codes:
        if not code.strip():
            continue
        if code in _REQUIRES_KEY:
            click.echo(
                f"  Layer '{code}' requires an API key and will be skipped.",
                err=True,
            )
            continue
        if code in REGISTRY:
            urls.append(REGISTRY[code])
        else:
            # Try nakarte's own tile server — covers Russian topo, overlays, etc.
            urls.append(_NAKARTE_TILES.format(code=code, z='{z}', x='{x}', y='{y}'))

    if not urls:
        click.echo('  No usable layers found; falling back to OpenStreetMap.', err=True)
        urls.append(REGISTRY['O'])

    return urls


def parse_layer_codes(l_param):
    """Split the nakarte `l=` parameter value into individual layer codes."""
    return list(l_param) if l_param else ['O']
