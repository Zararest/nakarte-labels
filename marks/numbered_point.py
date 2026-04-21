from PIL import ImageDraw

from core.fonts import load_font
from marks.base import Mark

_FILL = '#1a56db'
_TEXT = 'white'
_RADIUS = 9


class NumberedPoint(Mark):
    def __init__(self, lat, lng, name, number=1, **kwargs):
        super().__init__(lat, lng, name)
        self.number = number

    def render(self, image, pixel_x, pixel_y):
        draw = ImageDraw.Draw(image)
        r = _RADIUS
        draw.ellipse([pixel_x - r, pixel_y - r, pixel_x + r, pixel_y + r], fill=_FILL)

        font = load_font(12)
        text = str(self.number)
        bb = draw.textbbox((0, 0), text, font=font)
        tw, th = bb[2] - bb[0], bb[3] - bb[1]
        draw.text((pixel_x - tw // 2, pixel_y - th // 2), text, fill=_TEXT, font=font)
        del draw
