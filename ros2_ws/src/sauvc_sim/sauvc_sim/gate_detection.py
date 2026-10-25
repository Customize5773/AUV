"""Orange striped gate detection from RGB frames; no world coordinates."""
import math
import numpy as np


def decode_rgb(data, width, height, step, encoding='rgb8'):
    if encoding not in ('rgb8', 'bgr8') or width <= 0 or height <= 0 or step < width * 3:
        return None
    try:
        rgb = np.frombuffer(data, dtype=np.uint8).reshape(height, step)[:, :width * 3]
        rgb = rgb.reshape(height, width, 3)
    except (ValueError, TypeError, BufferError):
        return None
    if encoding == 'bgr8':
        rgb = rgb[:, :, ::-1]
    return rgb


def detect_gate(data, width, height, step, encoding='rgb8'):
    rgb = decode_rgb(data, width, height, step, encoding)
    if rgb is None:
        return None
    r, g, b = (rgb[:, :, i].astype(np.int16) for i in range(3))
    # The reverse side is shaded; colour ratios survive the lower brightness.
    mask = (r > 70) & (g > 25) & (g < r * .8) & (r > b * 2) & (g > b * 1.5)
    columns = np.flatnonzero(mask.sum(axis=0) >= 5)
    if not len(columns):
        return None
    groups = np.split(columns, np.flatnonzero(np.diff(columns) > 3) + 1)
    # The two strongest vertical stripe stacks must lie on opposite gate posts.
    groups = sorted(groups, key=lambda c: mask[:, c].sum(), reverse=True)[:2]
    if len(groups) != 2:
        return None
    left, right = sorted(float(c.mean()) for c in groups)
    span = right - left
    if span < 15 or any(mask[:, c].any(axis=1).sum() < 10 for c in groups):
        return None
    focal = width / (2 * math.tan(1.22173 / 2))
    chosen = np.concatenate(groups)
    ys = np.flatnonzero(mask[:, chosen].any(axis=1))
    return {'bearing': -math.atan(((left + right) / 2 - (width - 1) / 2) / focal),
            'distance': focal * 1.55 / span, 'span': span,
            'center': (left + right) / 2,
            'bbox': [int(chosen.min()), int(ys.min()), int(chosen.max())+1, int(ys.max())+1]}
