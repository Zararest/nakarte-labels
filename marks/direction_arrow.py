import math

from PIL import ImageDraw

from marks.base import Mark

_LENGTH = 30
_HEAD_LEN = 10
_HEAD_ANGLE = math.radians(25)


class DirectionArrow(Mark):
    def __init__(self, lat, lng, name, bearing=0, color='#e60000', **kwargs):
        super().__init__(lat, lng, name)
        self.bearing = bearing
        self.color = color

    def render(self, image, pixel_x, pixel_y):
        draw = ImageDraw.Draw(image)
        s = self.size_scale

        length   = _LENGTH   * s
        head_len = _HEAD_LEN * s
        line_w   = max(1, round(2 * s))

        angle = math.radians(self.bearing)
        dx = math.sin(angle) * length
        dy = -math.cos(angle) * length  # screen y increases downward

        ex, ey = pixel_x + dx, pixel_y + dy
        draw.line([(pixel_x, pixel_y), (ex, ey)], fill=self.color, width=line_w)

        # Arrowhead – two lines fanning back from the tip
        back = angle + math.pi
        left = (
            ex + head_len * math.sin(back - _HEAD_ANGLE),
            ey - head_len * math.cos(back - _HEAD_ANGLE),
        )
        right = (
            ex + head_len * math.sin(back + _HEAD_ANGLE),
            ey - head_len * math.cos(back + _HEAD_ANGLE),
        )
        draw.polygon([(ex, ey), left, right], fill=self.color)
        del draw
