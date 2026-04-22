import asyncio
import io

import httpx
from PIL import Image

from core.tile_math import TILE_SIZE

USER_AGENT = 'nakarte-map-exporter/1.0 (https://github.com/Zararest/nakarte-labels)'
MAX_CONCURRENT = 4
_RETRY_STATUSES = {429, 500, 502, 503, 504}
_MAX_RETRIES = 5


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


async def _fetch_layer(client, semaphore, tile_url_tpl, zoom, tx_min, tx_max, ty_min, ty_max):
    """Fetch all tiles for one layer, return dict {(tx, ty): Image}."""
    tiles = {}

    async def fetch_one(tx, ty):
        url = tile_url_tpl.format(z=zoom, x=tx, y=ty)
        try:
            img = await _fetch_tile(client, semaphore, url)
            tiles[(tx, ty)] = img
        except Exception:
            # Missing/failed tiles are left transparent
            pass

    await asyncio.gather(*[
        fetch_one(tx, ty)
        for tx in range(tx_min, tx_max + 1)
        for ty in range(ty_min, ty_max + 1)
    ])
    return tiles


def _stitch(tiles, tx_min, tx_max, ty_min, ty_max):
    w = (tx_max - tx_min + 1) * TILE_SIZE
    h = (ty_max - ty_min + 1) * TILE_SIZE
    canvas = Image.new('RGBA', (w, h))
    for (tx, ty), tile in tiles.items():
        canvas.paste(tile, ((tx - tx_min) * TILE_SIZE, (ty - ty_min) * TILE_SIZE))
    return canvas


async def _fetch_all_layers(tile_url_tpls, zoom, tx_min, tx_max, ty_min, ty_max, on_progress):
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    total = (tx_max - tx_min + 1) * (ty_max - ty_min + 1) * len(tile_url_tpls)
    done = 0

    async with httpx.AsyncClient(
        headers={'User-Agent': USER_AGENT},
        timeout=30,
        follow_redirects=True,
    ) as client:
        base = None
        for tpl in tile_url_tpls:
            tiles = await _fetch_layer(client, semaphore, tpl, zoom, tx_min, tx_max, ty_min, ty_max)
            done += (tx_max - tx_min + 1) * (ty_max - ty_min + 1)
            if on_progress:
                on_progress(done, total)

            layer_img = _stitch(tiles, tx_min, tx_max, ty_min, ty_max)
            if base is None:
                base = layer_img
            else:
                base = Image.alpha_composite(base, layer_img)

    return base


def fetch_and_stitch(zoom, tx_min, tx_max, ty_min, ty_max, tile_url_tpls=None, on_progress=None):
    from core.layers import REGISTRY
    if tile_url_tpls is None:
        tile_url_tpls = [REGISTRY['O']]

    result = asyncio.run(
        _fetch_all_layers(tile_url_tpls, zoom, tx_min, tx_max, ty_min, ty_max, on_progress)
    )
    return result
