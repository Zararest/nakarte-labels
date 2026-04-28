"""nakarte-render — render a nakarte map image from a YAML config."""

import sys

import click
import yaml
from PIL import Image

from core.export_params import resolve_export
from core.layers import resolve_layers
from core.mark_renderer import render_marks
from core.tile_fetcher import fetch_and_stitch
from core.tile_math import TILE_SIZE, lat_lng_to_pixel
from core.track_renderer import draw_track
from core.track_utils import bbox_center
from core.url_parser import extract_tracks, parse_nakarte_url


def _to_seg_objects(tracks):
    class _Seg:
        def __init__(self, pts):
            self.points = pts
    return [_Seg(seg) for t in tracks for seg in t.segments]


@click.command()
@click.argument('config', type=click.Path(exists=True))
@click.option('--out', default='map.png', show_default=True, help='Output PNG path.')
def main(config, out):
    """Render a nakarte map image from a YAML config."""
    with open(config, 'r', encoding='utf-8') as f:
        cfg = yaml.safe_load(f)

    map_cfg = cfg.get('map', {})
    style = cfg.get('style', {})
    marks_cfg = cfg.get('marks', [])
    export_cfg = cfg.get('export')

    url = map_cfg.get('url')
    if not url:
        click.echo('Error: config is missing map.url', err=True)
        sys.exit(1)

    track_color = style.get('track_color', '#e60000')
    track_width = style.get('track_width', 3)
    mark_size   = style.get('mark_size', 1.0)

    try:
        url_params = parse_nakarte_url(url)
    except ValueError as e:
        click.echo(f'Error parsing URL: {e}', err=True)
        sys.exit(1)

    # --- Load track (needed for center and drawing) ---
    tracks = []
    has_track = url_params.get('nktk') or url_params.get('nktl')
    if has_track:
        click.echo('Reading track from URL...')
        try:
            tracks = extract_tracks(url_params)
        except (PermissionError, RuntimeError) as e:
            click.echo(f'Warning: could not load track: {e}', err=True)

    # --- Determine map centre ---
    explicit_center = map_cfg.get('center')
    if explicit_center:
        center_lat, center_lng = explicit_center
    elif tracks:
        center_lat, center_lng = bbox_center(tracks)
        click.echo(f'Centre: track bounding box ({center_lat:.5f}, {center_lng:.5f})')
    else:
        center_lat, center_lng = url_params['lat'], url_params['lng']
        click.echo(f'Centre: URL position ({center_lat:.5f}, {center_lng:.5f})')

    # --- Resolve export parameters ---
    try:
        width_px, height_px, zoom = resolve_export(map_cfg, export_cfg, center_lat)
    except ValueError as e:
        click.echo(f'Error in export config: {e}', err=True)
        sys.exit(1)

    if zoom is None:
        zoom = url_params['zoom']

    # --- Resolve layers ---
    layer_codes = url_params.get('layer_codes', ['O'])
    layer_defs = resolve_layers(layer_codes)  # list of (title, url_tpl, is_tms)
    titles = ', '.join(t for t, _, _ in layer_defs)
    click.echo(f'Layers: {"".join(layer_codes)!r}  →  {titles}')

    # --- Tile bounds ---
    cx, cy = lat_lng_to_pixel(center_lat, center_lng, zoom)
    origin_x = cx - width_px / 2
    origin_y = cy - height_px / 2

    tx_min = int(origin_x // TILE_SIZE)
    ty_min = int(origin_y // TILE_SIZE)
    tx_max = int((origin_x + width_px - 1) // TILE_SIZE)
    ty_max = int((origin_y + height_px - 1) // TILE_SIZE)

    total_tiles = (tx_max - tx_min + 1) * (ty_max - ty_min + 1) * len(layer_defs)

    def on_progress(done, _total):
        click.echo(f'\rFetching tiles... {done}/{_total}', nl=False)

    click.echo(f'Fetching tiles (zoom {zoom}, {total_tiles} tile request(s))... 0/{total_tiles}',
               nl=False)
    stitched = fetch_and_stitch(zoom, tx_min, tx_max, ty_min, ty_max,
                                layer_defs=layer_defs, on_progress=on_progress)
    click.echo()

    # Crop to exact canvas size
    stitch_ox = tx_min * TILE_SIZE
    stitch_oy = ty_min * TILE_SIZE
    crop_l = int(origin_x - stitch_ox)
    crop_t = int(origin_y - stitch_oy)
    canvas = stitched.crop((crop_l, crop_t, crop_l + width_px, crop_t + height_px)).convert('RGBA')

    def project(lat, lng):
        return lat_lng_to_pixel(lat, lng, zoom)

    if tracks:
        segs = _to_seg_objects(tracks)
        click.echo(f'Drawing track ({len(segs)} segment(s))...')
        draw_track(canvas, segs, origin_x, origin_y, project,
                   color=track_color, width=track_width)

    active = [m for m in marks_cfg if m.get('type')]
    click.echo(f'Rendering {len(active)} mark(s)...')
    try:
        render_marks(canvas, marks_cfg, origin_x, origin_y, project, size_scale=mark_size)
    except ValueError as e:
        click.echo(f'Error: {e}', err=True)
        sys.exit(1)

    # Flatten onto white before saving: transparent pixels (failed tiles, empty areas)
    # become white instead of black when converting RGBA → RGB.
    background = Image.new('RGBA', canvas.size, (255, 255, 255, 255))
    background.alpha_composite(canvas)
    background.convert('RGB').save(out, 'PNG', optimize=True)
    click.echo(f'Wrote {out}  ({width_px} \u00d7 {height_px} px)')


if __name__ == '__main__':
    main()
