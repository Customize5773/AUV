"""Colour/shape candidates from camera pixels. No pose, world IDs or target coordinates."""
import math
import numpy as np

from sauvc_sim.gate_detection import decode_rgb, detect_gate


def components(mask, min_area=8):
    """8-connected components using row runs; preserves even one-pixel-wide flare poles."""
    parents, runs, previous = [], [], []

    def root(i):
        while parents[i] != i:
            parents[i] = parents[parents[i]]
            i = parents[i]
        return i

    previous_y = -2
    for y in np.flatnonzero(mask.any(axis=1)):
        y = int(y)
        if y != previous_y+1:
            previous = []
        previous_y = y
        edges = np.flatnonzero(np.diff(np.pad(mask[y].astype(np.int8), (1, 1))))
        current = []
        for left, right in zip(edges[::2], edges[1::2]):
            index = len(parents)
            parents.append(index)
            for a, b, other in previous:
                if a <= right and left <= b:
                    parents[root(other)] = root(index)
            current.append((int(left), int(right), index))
            runs.append((int(left), int(right), y, index))
        previous = current
    found = {}
    for left, right, y, index in runs:
        key = root(index)
        if key not in found:
            found[key] = [left, y, right, y+1, right-left]
        else:
            f = found[key]
            f[0], f[1], f[2], f[3] = min(f[0], left), min(f[1], y), max(f[2], right), max(f[3], y+1)
            f[4] += right-left
    return [dict(bbox=f[:4], area_px=f[4]) for f in found.values() if f[4] >= min_area]


def colour_masks(rgb):
    r, g, b = (rgb[:, :, i].astype(np.int16) for i in range(3))
    return {
        'orange': (r > 40) & (g > 15) & (g < r*.8) & (r > b*2) & (g > b*1.5),
        'red': (r > 35) & (r > g*1.4) & (r > b*1.4) & (np.abs(g-b) < r*.25),
        'green': (g > 30) & (g > r*1.6) & (g > b*1.2),
        'blue': (b > 35) & (b > r*1.8) & (b > g*1.5),
        'yellow': (r > 60) & (g > 35) & (g >= r*.8) & (r > b*2) & (g > b*2),
    }


def candidate(label, bbox, width, height, **extra):
    left, top, right, bottom = bbox
    cx, cy = (left+right-1)/2, (top+bottom-1)/2
    focal = width/(2*math.tan(1.22173/2))
    return dict(label=label, bbox=bbox, center_px=[cx, cy],
                error_normalized=[(cx-(width-1)/2)/(width/2), (cy-(height-1)/2)/(height/2)],
                bearing=-math.atan((cx-(width-1)/2)/focal),
                partial=left == 0 or top == 0 or right == width or bottom == height,
                **extra)


def striped_posts(parts):
    stacks = []
    for part in parts:
        l, t, r, b = part['bbox']
        if not 1 <= (b-t)/(r-l) <= 5:
            continue
        cx = (l+r)/2
        stack = next((s for s in stacks if abs((s['bbox'][0]+s['bbox'][2])/2-cx)
                      <= max(2, (r-l)/2)), None)
        if stack is None:
            stacks.append(dict(bbox=[l,t,r,b], stripes=1, area_px=part['area_px']))
        else:
            a = stack['bbox']
            stack['bbox'] = [min(l,a[0]),min(t,a[1]),max(r,a[2]),max(b,a[3])]
            stack['stripes'] += 1
            stack['area_px'] += part['area_px']
    return [s for s in stacks if s['stripes'] >= 2 and s['bbox'][3]-s['bbox'][1] >= 15]


def detect_objects(data, width, height, step, encoding='rgb8', camera='front', arena='finals'):
    if camera not in ('front', 'bottom') or arena not in ('qualification', 'finals'):
        raise ValueError('unknown camera or arena')
    rgb = decode_rgb(data, width, height, step, encoding)
    if rgb is None:
        return {'valid_image': False, 'detections': []}
    masks = colour_masks(rgb)
    detections = []
    if camera == 'front' and arena == 'qualification':
        gate = detect_gate(data, width, height, step, encoding)
        if gate:
            detections.append(candidate('qualification_gate', gate['bbox'], width, height,
                                        distance_estimate_m=gate['distance'], span_px=gate['span']))
    elif camera == 'front':
        # A one-pixel blue pole loses saturation under blur; recover only narrow,
        # tall local blue contrast, retaining the strict mask for other shapes.
        r,g,b=(rgb[:,:,i].astype(float) for i in range(3))
        blue_score=b-(r+g)/2
        contrast=np.zeros_like(blue_score)
        contrast[:,4:-4]=blue_score[:,4:-4]-(blue_score[:,:-8]+blue_score[:,8:])/2
        faint=(contrast>12)&(b>r*1.3)&(b>g*1.15)
        padded=np.pad(faint,((1,1),(0,0)))
        dilated=padded[:-2]|padded[1:-1]|padded[2:]
        padded=np.pad(dilated,((1,1),(0,0)))
        faint=padded[:-2]&padded[1:-1]&padded[2:]
        for part in components(faint):
            l,t,r,b=part['bbox'];h,w=b-t,r-l
            if (t>1 and b<height-1 and l>4 and r<width-4 and
                    h>=30 and w<=5 and h/w>=8 and part['area_px']/(h*w)>.45):
                masks['blue'][t:b,l:r]|=faint[t:b,l:r]
        parts = {colour: components(mask, 2 if colour in ('red','green') else 8)
                 for colour, mask in masks.items()}
        pairs = []
        for red in striped_posts(parts['red']):
            for green in striped_posts(parts['green']):
                a, b = red['bbox'], green['bbox']
                span = abs((a[0]+a[2]-b[0]-b[2])/2)
                overlap = min(a[3],b[3])-max(a[1],b[1])
                heights = (a[3]-a[1], b[3]-b[1])
                if span >= 15 and overlap > .5*min(heights) and min(heights) > .5*max(heights):
                    pairs.append((red['area_px']+green['area_px'], red, green, span))
        if pairs:
            _, red, green, span = max(pairs, key=lambda p: p[0])
            a, b = red['bbox'], green['bbox']
            box = [min(a[0],b[0]),min(a[1],b[1]),max(a[2],b[2]),max(a[3],b[3])]
            detections.append(candidate('navigation_gate', box, width, height,
                distance_estimate_m=width/(2*math.tan(1.22173/2))*1.55/span,
                span_px=span, stripe_count=[red['stripes'],green['stripes']]))
        bars=[p for p in parts['blue'] if p['bbox'][3]-p['bbox'][1]>=15 and
              (p['bbox'][3]-p['bbox'][1])/max(1,p['bbox'][2]-p['bbox'][0])>=4]
        square_pairs=[];square_parts=set()
        for i,first in enumerate(bars):
            for second in bars[i+1:]:
                a,b=first['bbox'],second['bbox']
                ha,hb=a[3]-a[1],b[3]-b[1];span=abs((a[0]+a[2]-b[0]-b[2])/2)
                overlap=min(a[3],b[3])-max(a[1],b[1])
                if min(ha,hb)>.8*max(ha,hb) and span>2*max(ha,hb) and overlap>.6*min(ha,hb):
                    square_pairs.append((ha+hb,first,second,span))
        if square_pairs:
            _,first,second,span=max(square_pairs,key=lambda p:p[0])
            a,b=first['bbox'],second['bbox'];marker_height=max(a[3]-a[1],b[3]-b[1])
            box=[min(a[0],b[0]),min(a[1],b[1]),max(a[2],b[2]),max(a[3],b[3])]
            for part in bars:
                l,t,r,b=part['bbox']
                if box[0]<=(l+r)/2<=box[2] and box[1]-marker_height*.25<=t<=box[3] and b<=box[3]+marker_height:
                    square_parts.add(id(part))
            detections.append(candidate('surfacing_square',box,width,height,span_px=span))
        for colour in ('orange','blue','red','yellow'):
            for part in parts[colour]:
                if colour=='blue' and id(part) in square_parts:continue
                l,t,r,b = part['bbox']
                if b-t >= 15 and (b-t)/(r-l) >= 5 and part['area_px']/((r-l)*(b-t)) > .45:
                    detections.append(candidate(colour+'_flare', part['bbox'], width, height,
                                                area_px=part['area_px']))
    elif arena == 'finals':
        # shortcut: round coloured regions are drum candidates, not proof of a physical drum.
        for colour in ('blue','red'):
            for part in components(masks[colour]):
                l,t,r,b = part['bbox']
                ratio, fill = (r-l)/(b-t), part['area_px']/((r-l)*(b-t))
                if min(r-l,b-t) >= 24 and .65 <= ratio <= 1.55 and .3 <= fill <= .9:
                    obj = candidate(colour+'_drum', part['bbox'], width, height,
                                    area_px=part['area_px'], fill_ratio=fill)
                    if not obj['partial']:
                        detections.append(obj)
    return {'valid_image': True, 'detections': detections}
