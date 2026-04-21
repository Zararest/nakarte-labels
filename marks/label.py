from PIL import ImageDraw

from core.fonts import load_font
from marks.base import Mark


class Label(Mark):
    def __init__(self, lat, lng, name, color='#e60000', offset=None, **kwargs):
        super().__init__(lat, lng, name)
        self.color = color
        self.offset = offset or [0, 0]

    def render(self, image, pixel_x, pixel_y):
        draw = ImageDraw.Draw(image)
        font = load_font(14)
        draw.text(
            (pixel_x + self.offset[0], pixel_y + self.offset[1]),
            self.name,
            fill=self.color,
            font=font,
        )
        del draw
