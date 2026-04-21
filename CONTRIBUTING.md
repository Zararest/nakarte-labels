# Contributing

Contributions are welcome. Please open an issue first to discuss what you would like to change.

## Setup

```bash
git clone https://github.com/ivshumakov/nakarte-labels.git
cd nakarte-labels
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e .
```

## Adding a new mark type

1. Create `marks/your_type.py` subclassing `Mark` from `marks/base.py`.
2. Implement the `render(self, image, pixel_x, pixel_y)` method.
3. Register the new class in `core/mark_renderer.py` → `_MARK_CLASSES`.
4. Document the new fields in `README.md`.

## Code style

- Standard library imports first, then third-party, then local.
- No unnecessary comments — name things clearly instead.
- Keep dependencies minimal; avoid adding new ones unless truly necessary.

## Pull requests

- One logical change per PR.
- Describe *why*, not just *what*.
