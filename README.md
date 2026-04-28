# nakarte-map-exporter

Export annotated PNG map images from [nakarte.me](https://nakarte.me) track URLs.

Draw your route in nakarte, copy the URL, describe your annotations in a YAML config,
and get a high-resolution map image ready to print or share — no GPX export needed.

**Supported annotation types:** text labels, numbered waypoints, direction arrows.

---

## Installation

Requires **Python 3.9+**.

```bash
pip install git+https://github.com/Zararest/nakarte-labels.git
```

Or clone and install in editable mode for development:

```bash
git clone https://github.com/Zararest/nakarte-labels.git
cd nakarte-labels
pip install -e .
```

This installs two commands: `nakarte-init` and `nakarte-render`.

---

## Quick start

### Step 1 — nakarte.me (browser)

1. Draw or import your route.
2. Name waypoints directly in nakarte (`бивуак 4`, `обед`, etc.).
3. Copy the page URL from the address bar — the track is encoded in it.

### Step 2 — generate a YAML scaffold

```bash
nakarte-init --url 'https://nakarte.me/#m=14/50.27749/87.51100&l=Czt&nktl=KXVqIcleF26fAUjs_5X3pQ' \
             --scale 500 --dpi 300 --paper A4 --out config.yaml
```

Output:
```
Reading track from URL...
Track:   1 track(s), 1 segment(s), 247 points
Marks:   3 waypoint(s) → config marks (type: null)
Wrote config.yaml
```

### Step 3 — edit the config

Open `config.yaml` and set `type` for each mark you want rendered:

```yaml
map:
  url: "https://nakarte.me/#m=14/50.27749/87.51100&l=Czt&nktl=KXVqIcleF26fAUjs_5X3pQ"
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
Fetching tiles (zoom 14)... 24/24
Reading track from URL...
Drawing track (1 segment(s))...
Rendering 3 mark(s)...
Wrote map.png  (2000 × 1200 px)
```

---

## Config reference

### `export` section

| Field | Default | Description |
|-------|---------|-------------|
| `paper` | `A4` | Paper size: `A4` or `A3` |
| `orientation` | `portrait` | Page orientation: `portrait` or `landscape` |
| `scale` | `500` | **Map metres per image cm** — same unit as nakarte.me's export dialog.<br>Examples: `100` = 100 m/cm (1:10 000) · `500` = 500 m/cm (1:50 000) · `1000` = 1 km/cm (1:100 000) |
| `dpi` | `300` | Output resolution in DPI (300 = standard print quality) |

### `map` section

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `url` | yes | — | Full nakarte.me URL (used for zoom, center, and track data) |
| `center` | no | auto | Explicit map centre as `[lat, lng]`. If omitted, defaults to the track bounding box midpoint, or the coordinates from the URL if there is no track. |
| `width_px` | no | 2000 | Output image width (ignored when `export` section is present) |
| `height_px` | no | 1200 | Output image height (ignored when `export` section is present) |

#### Map centre priority

1. `map.center: [lat, lng]` — explicit override, always used when set.
2. Track bounding box midpoint — used when the URL contains a track and no explicit centre.
3. URL position — the `lat/lng` from the `#m=zoom/lat/lng` hash fragment.

### `style` section

| Field | Default | Description |
|-------|---------|-------------|
| `track_color` | `#e60000` | Track line color (CSS hex) |
| `track_width` | `3` | Track line width in pixels |
| `mark_size` | `1.0` | Scale multiplier for all marks — labels, numbered points, and arrows scale together. `2.0` = twice the default size. |

### Mark fields

| Field | Applies to | Description |
|-------|-----------|-------------|
| `lat`, `lng` | all | Coordinate (decimal degrees, WGS84) |
| `name` | all | Label text; preserved from nakarte waypoints |
| `type` | all | `label`, `numbered_point`, `direction_arrow`, or `null` (skip) |
| `color` | label, direction_arrow | CSS hex color |
| `offset` | label | `[dx, dy]` pixel nudge from the anchor point |
| `number` | numbered_point | Integer shown inside the circle |
| `bearing` | direction_arrow | Degrees clockwise from north (0–359) |

---

## URL format notes

nakarte.me stores track data directly in the URL hash. Two formats are supported:

- **`nktk=`** — track encoded inline in the URL (no server required)
- **`nktl=`** — track stored on nakarte's server, fetched automatically on init/render

If you use `nktl=` and get an authentication error, open nakarte.me in your browser
while logged in, or re-save the track to get an inline `nktk=` URL.

Currently only **single-track URLs** are fully supported. If the URL contains multiple
tracks, the first one is used for rendering and a warning is shown.

---

## Tile attribution

Map tiles are fetched from [OpenStreetMap](https://www.openstreetmap.org/).
© OpenStreetMap contributors, [ODbL](https://www.openstreetmap.org/copyright).

Please follow the [OSM tile usage policy](https://operations.osmfoundation.org/policies/tiles/) —
do not run batch exports at high frequency.

---

## License

[MIT](LICENSE)
