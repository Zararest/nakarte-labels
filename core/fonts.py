from functools import lru_cache

from PIL import ImageFont

# Common bold TrueType font paths across Linux, macOS, Windows.
# DejaVu Sans has full Cyrillic coverage and is pre-installed on most Linux distros.
_CANDIDATES = [
    # Linux – DejaVu (most common)
    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    '/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf',
    '/usr/share/fonts/TTF/DejaVuSans-Bold.ttf',
    # Linux – Liberation (Red Hat / Fedora)
    '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
    '/usr/share/fonts/liberation/LiberationSans-Bold.ttf',
    # macOS
    '/System/Library/Fonts/Supplemental/Arial Bold.ttf',
    '/Library/Fonts/Arial Bold.ttf',
    '/System/Library/Fonts/Helvetica.ttc',
    # Windows
    'C:/Windows/Fonts/arialbd.ttf',
    'C:/Windows/Fonts/calibrib.ttf',
]


@lru_cache(maxsize=16)
def load_font(size):
    for path in _CANDIDATES:
        try:
            return ImageFont.truetype(path, size)
        except (IOError, OSError):
            continue
    # Pillow 10+ supports size= on the built-in bitmap font
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()
