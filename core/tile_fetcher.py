import asyncio
import io

import httpx
from PIL import Image

from core.tile_math import TILE_SIZE

TILE_URL = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
USER_AGENT = 'nakarte-map-exporter/1.0 (https://github.com/ivshumakov/nakarte-labels)'
MAX_CONCURRENT = 4


async def _fetch_all(zoom, tx_min, tx_max, ty_min, ty_max, on_progress=None):
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    results = {}

    async def fetch_one(client, tx, ty):
        url = TILE_URL.format(z=zoom, x=tx, y=ty)
        async with semaphore:
            r = await client.get(url)
            r.raise_for_status()
        img = Image.open(io.BytesIO(r.content)).convert('RGBA')
        results[(tx, ty)] = img
        if on_progress:
            on_progress(len(results), total)

    total = (tx_max - tx_min + 1) * (ty_max - ty_min + 1)
    async with httpx.AsyncClient(
        headers={'User-Agent': USER_AGENT},
        timeout=30,
        follow_redirects=True,
    ) as client:
        await asyncio.gather(*[
            fetch_one(client, tx, ty)
            for tx in range(tx_min, tx_max + 1)
            for ty in range(ty_min, ty_max + 1)
        ])

    return results


def fetch_and_stitch(zoom, tx_min, tx_max, ty_min, ty_max, on_progress=None):
    tiles = asyncio.run(_fetch_all(zoom, tx_min, tx_max, ty_min, ty_max, on_progress))

    w = (tx_max - tx_min + 1) * TILE_SIZE
    h = (ty_max - ty_min + 1) * TILE_SIZE
    canvas = Image.new('RGBA', (w, h))

    for (tx, ty), tile in tiles.items():
        canvas.paste(tile, ((tx - tx_min) * TILE_SIZE, (ty - ty_min) * TILE_SIZE))

    return canvas
