# nakarte-map-exporter

Export annotated PNG map images from [nakarte.me](https://nakarte.me) GPX tracks.

Draw your route in nakarte, export a GPX file, describe your annotations in a YAML config, and get a high-resolution map image ready to print or share.

**Supported annotation types:** text labels, numbered waypoints, direction arrows.

---

## Installation

Requires **Python 3.9+**.

```bash
pip install git+https://github.com/ivshumakov/nakarte-labels.git
```

Or clone and install in editable mode for development:

```bash
git clone https://github.com/ivshumakov/nakarte-labels.git
cd nakarte-labels
pip install -e .
```

This installs two commands: `nakarte-init` and `nakarte-render`.

---

## Quick start

### Step 1 — nakarte.me (browser)

1. Draw or import your route.
2. Name waypoints directly in nakarte (`бивуак 4`, `обед`, etc.).
3. **File → Export → GPX** — save as `track.gpx`.
4. Copy the page URL from the address bar.

### Step 2 — generate a YAML scaffold

```bash
nakarte-init track.gpx --url "https://nakarte.me/#m=12/67.84/33.51&l=T" --out config.yaml
```

Output:
```
Parsed track.gpx:
  3 waypoint(s) → marks (type: null)
  1 track segment(s) with 247 points
Wrote config.yaml
```

### Step 3 — edit the config

Open `config.yaml` and set `type` for each mark you want rendered:

```yaml
map:
  url: "https://nakarte.me/#m=12/67.842/33.512&l=T"
  gpx: "/path/to/track.gpx"
  width_px: 2000
  height_px: 1200

style:
  track_color: "#e60000"
  track_width: 3

marks:
  - lat: 67.8530
    lng: 33.4880
    name: "бивуак 4"
    type: label
    color: "#e60000"
    offset: [8, -4]

  - lat: 67.8421
    lng: 33.5124
    name: "point 18"
    type: numbered_point
    number: 18

  - lat: 67.8445
    lng: 33.5010
    name: "head north"
    type: direction_arrow
    bearing: 0
    color: "#e60000"
```

### Step 4 — render

```bash
nakarte-render config.yaml --out map.png
```

Output:
```
Fetching tiles (zoom 12)... 24/24
Drawing track...
Rendering 3 mark(s)...
Wrote map.png  (2000 × 1200 px)
```

---

## Config reference

### `map` section

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `url` | yes | — | Full nakarte.me URL (used for zoom and center) |
| `gpx` | no | — | Path to the GPX file (needed to draw the track line) |
| `width_px` | no | 2000 | Output image width |
| `height_px` | no | 1200 | Output image height |

### `style` section

| Field | Default | Description |
|-------|---------|-------------|
| `track_color` | `#e60000` | Track line color (CSS hex) |
| `track_width` | `3` | Track line width in pixels |

### Mark fields

| Field | Applies to | Description |
|-------|-----------|-------------|
| `lat`, `lng` | all | Coordinate (decimal degrees, WGS84) |
| `name` | all | Label text; preserved from GPX |
| `type` | all | `label`, `numbered_point`, `direction_arrow`, or `null` (skip) |
| `color` | label, direction_arrow | CSS hex color |
| `offset` | label | `[dx, dy]` pixel nudge from the anchor point |
| `number` | numbered_point | Integer shown inside the circle |
| `bearing` | direction_arrow | Degrees clockwise from north (0–359) |

---

## Tile attribution

Map tiles are fetched from [OpenStreetMap](https://www.openstreetmap.org/).
© OpenStreetMap contributors, [ODbL](https://www.openstreetmap.org/copyright).

Please follow the [OSM tile usage policy](https://operations.osmfoundation.org/policies/tiles/) — do not run batch exports at high frequency.

---

## License

[MIT](LICENSE)
