from PIL import ImageDraw


def draw_track(image, track_segments, origin_x, origin_y, project_fn, color='#e60000', width=3):
    draw = ImageDraw.Draw(image)

    for seg in track_segments:
        if len(seg.points) < 2:
            continue

        pixels = []
        for lat, lng in seg.points:
            px, py = project_fn(lat, lng)
            pixels.append((px - origin_x, py - origin_y))

        draw.line(pixels, fill=color, width=width, joint='curve')

    del draw
