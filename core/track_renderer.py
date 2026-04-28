import math

from PIL import ImageDraw


def draw_track(image, track_segments, origin_x, origin_y, project_fn, color='#e60000', width=3):
    """Draw track segments with uniform perpendicular width at all angles.

    PIL's line() measures width in axis-aligned pixels, making diagonal
    segments appear thinner.  Instead we draw each segment as a rotated
    rectangle (width measured perpendicular to the line) and place a
    filled circle at every vertex for smooth round joins and end-caps.
    """
    draw = ImageDraw.Draw(image)
    r = width / 2

    for seg in track_segments:
        if len(seg.points) < 2:
            continue

        pixels = []
        for lat, lng in seg.points:
            px, py = project_fn(lat, lng)
            pixels.append((px - origin_x, py - origin_y))

        for i in range(len(pixels) - 1):
            x1, y1 = pixels[i]
            x2, y2 = pixels[i + 1]

            dx = x2 - x1
            dy = y2 - y1
            length = math.hypot(dx, dy)
            if length == 0:
                continue

            # Perpendicular offset vector of length r
            nx = -dy / length * r
            ny =  dx / length * r

            # Rotated rectangle enclosing the segment
            draw.polygon([
                (x1 + nx, y1 + ny),
                (x2 + nx, y2 + ny),
                (x2 - nx, y2 - ny),
                (x1 - nx, y1 - ny),
            ], fill=color)

        # Round caps and joins: circle at every vertex
        for x, y in pixels:
            draw.ellipse([x - r, y - r, x + r, y + r], fill=color)

    del draw
