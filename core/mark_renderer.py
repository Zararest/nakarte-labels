from marks.label import Label
from marks.numbered_point import NumberedPoint
from marks.direction_arrow import DirectionArrow

_MARK_CLASSES = {
    'label': Label,
    'numbered_point': NumberedPoint,
    'direction_arrow': DirectionArrow,
}


def _build_mark(cfg):
    mark_type = cfg.get('type')
    if not mark_type:
        return None
    cls = _MARK_CLASSES.get(mark_type)
    if cls is None:
        raise ValueError(f"Unknown mark type: {mark_type!r}. Valid types: {list(_MARK_CLASSES)}")
    return cls(**cfg)


def render_marks(image, marks_config, origin_x, origin_y, project_fn):
    rendered = 0
    for cfg in marks_config:
        mark = _build_mark(cfg)
        if mark is None:
            continue
        px, py = project_fn(mark.lat, mark.lng)
        mark.render(image, int(px - origin_x), int(py - origin_y))
        rendered += 1
    return rendered
