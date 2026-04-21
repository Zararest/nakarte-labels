"""nakarte-render — render a nakarte map image from a YAML config."""

import sys

import click
import yaml

from core.gpx_parser import parse_gpx
from core.mark_renderer import render_marks
from core.tile_fetcher import fetch_and_stitch
from core.tile_math import TILE_SIZE, lat_lng_to_pixel
from core.track_renderer import draw_track
from core.url_parser import parse_nakarte_url


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

    url = map_cfg.get('url')
    if not url:
        click.echo('Error: config is missing map.url', err=True)
        sys.exit(1)

    width_px = map_cfg.get('width_px', 2000)
    height_px = map_cfg.get('height_px', 1200)
    track_color = style.get('track_color', '#e60000')
    track_width = style.get('track_width', 3)

    try:
        params = parse_nakarte_url(url)
    except ValueError as e:
        click.echo(f'Error parsing URL: {e}', err=True)
        sys.exit(1)

    zoom = params['zoom']
    cx, cy = lat_lng_to_pixel(params['lat'], params['lng'], zoom)

    # Canvas bounds in global pixel space
    origin_x = cx - width_px / 2
    origin_y = cy - height_px / 2

    # Tile range covering the canvas
    tx_min = int(origin_x // TILE_SIZE)
    ty_min = int(origin_y // TILE_SIZE)
    tx_max = int((origin_x + width_px - 1) // TILE_SIZE)
    ty_max = int((origin_y + height_px - 1) // TILE_SIZE)

    total = (tx_max - tx_min + 1) * (ty_max - ty_min + 1)

    def on_progress(done, _total):
        click.echo(f'\rFetching tiles (zoom {zoom})... {done}/{_total}', nl=False)

    click.echo(f'Fetching tiles (zoom {zoom})... 0/{total}', nl=False)
    stitched = fetch_and_stitch(zoom, tx_min, tx_max, ty_min, ty_max, on_progress=on_progress)
    click.echo()

    # Crop stitched image to exact canvas size
    stitch_ox = tx_min * TILE_SIZE
    stitch_oy = ty_min * TILE_SIZE
    crop_l = int(origin_x - stitch_ox)
    crop_t = int(origin_y - stitch_oy)
    canvas = stitched.crop((crop_l, crop_t, crop_l + width_px, crop_t + height_px)).convert('RGBA')

    def project(lat, lng):
        return lat_lng_to_pixel(lat, lng, zoom)

    gpx_file = map_cfg.get('gpx')
    if gpx_file:
        try:
            gpx_data = parse_gpx(gpx_file)
            click.echo('Drawing track...')
            draw_track(canvas, gpx_data.tracks, origin_x, origin_y, project,
                       color=track_color, width=track_width)
        except Exception as e:
            click.echo(f'Warning: could not draw track: {e}', err=True)

    active = [m for m in marks_cfg if m.get('type')]
    click.echo(f'Rendering {len(active)} mark(s)...')
    try:
        render_marks(canvas, marks_cfg, origin_x, origin_y, project)
    except ValueError as e:
        click.echo(f'Error: {e}', err=True)
        sys.exit(1)

    canvas.convert('RGB').save(out, 'PNG', optimize=True)
    click.echo(f'Wrote {out}  ({width_px} \u00d7 {height_px} px)')


if __name__ == '__main__':
    main()
