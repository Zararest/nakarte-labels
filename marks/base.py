from abc import ABC, abstractmethod


class Mark(ABC):
    def __init__(self, lat, lng, name, **kwargs):
        self.lat = lat
        self.lng = lng
        self.name = name

    @abstractmethod
    def render(self, image, pixel_x, pixel_y):
        """Draw this mark onto *image* at the given canvas pixel coordinates."""
