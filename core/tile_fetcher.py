import asyncio
import io

import click
import httpx
from PIL import Image

from core.tile_math import TILE_SIZE

USER_AGENT = 'nakarte-map-exporter/1.0 (https://github.com/Zararest/nakarte-labels)'
MAX_CONCURRENT = 4
_RETRY_STATUSES = {429, 500, 502, 503, 504}
_MAX_RETRIES = 5


def _tile_url(tpl, zoom, tx, ty, is_tms):
    """Format a tile URL template, applying TMS y-flip when needed."""
    y = (2 ** zoom - 1 - ty) if is_tms else ty
    return tpl.format(z=zoom, x=tx, y=y)


async def _fetch_tile(client, semaphore, url):
    delay = 1.0
    for attempt in range(_MAX_RETRIES):
        async with semaphore:
            r = await client.get(url)
        if r.status_code not in _RETRY_STATUSES:
            r.raise_for_status()
            return Image.open(io.BytesIO(r.content)).convert('RGBA')
        if attempt < _MAX_RETRIES - 1:
            await asyncio.sleep(delay)
            delay *= 2
        else:
            r.raise_for_status()


async def _fetch_layer(client, semaphore, title, url_tpl, is_tms,
                       zoom, tx_min, tx_max, ty_min, ty_max):
    """Fetch all tiles for one layer. Returns (tiles_dict, failed_count)."""
    tiles = {}
    failed = 0

    async def fetch_one(tx, ty):
        nonlocal failed
        url = _tile_url(url_tpl, zoom, tx, ty, is_tms)
        try:
            img = await _fetch_tile(client, semaphore, url)
            tiles[(tx, ty)] = img
        except Exception:
            failed += 1

    await asyncio.gather(*[
        fetch_one(tx, ty)
        for tx in range(tx_min, tx_max + 1)
        for ty in range(ty_min, ty_max + 1)
    ])

    loaded = (tx_max - tx_min + 1) * (ty_max - ty_min + 1) - failed
    if failed:
        click.echo(
            f"\n  Layer '{title}': {loaded}/{loaded + failed} tiles loaded"
            f" ({failed} failed — URL: {url_tpl!r})",
            err=True,
        )
    return tiles, failed


def _stitch(tiles, tx_min, tx_max, ty_min, ty_max):
    w = (tx_max - tx_min + 1) * TILE_SIZE
    h = (ty_max - ty_min + 1) * TILE_SIZE
    canvas = Image.new('RGBA', (w, h))
    for (tx, ty), tile in tiles.items():
        canvas.paste(tile, ((tx - tx_min) * TILE_SIZE, (ty - ty_min) * TILE_SIZE))
    return canvas


async def _fetch_all_layers(layer_defs, zoom, tx_min, tx_max, ty_min, ty_max, on_progress):
    """layer_defs: list of (title, url_template, is_tms)"""
    from core.layers import REGISTRY

    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    tiles_per_layer = (tx_max - tx_min + 1) * (ty_max - ty_min + 1)
    total = tiles_per_layer * len(layer_defs)
    done = 0

    async with httpx.AsyncClient(
        headers={'User-Agent': USER_AGENT},
        timeout=30,
        follow_redirects=True,
    ) as client:
        base = None
        all_failed = True

        for title, url_tpl, is_tms in layer_defs:
            tiles, failed = await _fetch_layer(
                client, semaphore, title, url_tpl, is_tms,
                zoom, tx_min, tx_max, ty_min, ty_max,
            )
            done += tiles_per_layer
            if on_progress:
                on_progress(done, total)

            if tiles_per_layer - failed > 0:
                all_failed = False

            layer_img = _stitch(tiles, tx_min, tx_max, ty_min, ty_max)
            base = layer_img if base is None else Image.alpha_composite(base, layer_img)

        if all_failed:
            osm_title, osm_url, osm_tms = REGISTRY['O']
            click.echo('\n  All layers failed — falling back to OpenStreetMap.', err=True)
            tiles, failed = await _fetch_layer(
                client, semaphore, osm_title, osm_url, osm_tms,
                zoom, tx_min, tx_max, ty_min, ty_max,
            )
            base = _stitch(tiles, tx_min, tx_max, ty_min, ty_max)

    return base


def fetch_and_stitch(zoom, tx_min, tx_max, ty_min, ty_max, layer_defs=None, on_progress=None):
    """layer_defs: list of (title, url_template, is_tms). Defaults to OSM."""
    from core.layers import REGISTRY
    if layer_defs is None:
        layer_defs = [REGISTRY['O']]

    return asyncio.run(
        _fetch_all_layers(layer_defs, zoom, tx_min, tx_max, ty_min, ty_max, on_progress)
    )
