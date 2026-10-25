"""Draw detector output with NumPy; these pixels never feed the detector."""
import numpy as np
from sauvc_sim.gate_detection import decode_rgb

# Five-bit rows of a small ASCII font avoid native imaging dependencies.
FONT = {
    'A': (14,17,17,31,17,17,17), 'B': (30,17,17,30,17,17,30),
    'C': (14,17,16,16,16,17,14), 'D': (30,17,17,17,17,17,30),
    'E': (31,16,16,30,16,16,31), 'F': (31,16,16,30,16,16,16),
    'G': (14,17,16,23,17,17,14), 'H': (17,17,17,31,17,17,17),
    'I': (14,4,4,4,4,4,14), 'J': (7,2,2,2,18,18,12),
    'K': (17,18,20,24,20,18,17), 'L': (16,16,16,16,16,16,31),
    'M': (17,27,21,21,17,17,17), 'N': (17,25,21,19,17,17,17),
    'O': (14,17,17,17,17,17,14), 'P': (30,17,17,30,16,16,16),
    'Q': (14,17,17,17,21,18,13), 'R': (30,17,17,30,20,18,17),
    'S': (15,16,16,14,1,1,30), 'T': (31,4,4,4,4,4,4),
    'U': (17,17,17,17,17,17,14), 'V': (17,17,17,17,17,10,4),
    'W': (17,17,17,21,21,21,10), 'X': (17,17,10,4,10,17,17),
    'Y': (17,17,10,4,4,4,4), 'Z': (31,1,2,4,8,16,31),
    '_': (0,0,0,0,0,0,31), '-': (0,0,0,31,0,0,0),
    ' ': (0,0,0,0,0,0,0),
}


def text(image, label, x, y):
    height, width = image.shape[:2]
    x, y = max(0, min(x, width-len(label)*6)), max(0, min(y, height-9))
    image[y:min(height,y+9), x:min(width,x+len(label)*6)] = 0
    for i, char in enumerate(label.upper()):
        left = x+i*6
        if left >= width:
            break
        rows = np.array(FONT.get(char, FONT[' ']), dtype=np.uint8)
        mask = (rows[:, None] >> np.arange(4,-1,-1)) & 1
        region = image[y:y+7, left:min(width,left+5)]
        region[mask[:region.shape[0], :region.shape[1]].astype(bool)] = 255


def annotate(data, width, height, step, encoding, detections):
    rgb = decode_rgb(data, width, height, step, encoding)
    if rgb is None:
        return None
    image = rgb.copy()
    for obj in detections:
        left, top, right, bottom = obj['bbox']
        image[top:min(top+2,bottom), left:right] = (255,0,255)
        image[max(top,bottom-2):bottom, left:right] = (255,0,255)
        image[top:bottom, left:min(left+2,right)] = (255,0,255)
        image[top:bottom, max(left,right-2):right] = (255,0,255)
        cx, cy = (int(round(v)) for v in obj['center_px'])
        image[max(0,cy-4):min(height,cy+5), cx:cx+1] = 255
        image[cy:cy+1, max(0,cx-4):min(width,cx+5)] = 255
        text(image, obj['label'], left, top-10)
    return image.tobytes()


def unavailable_image(message):
    image = np.zeros((480,640,3), dtype=np.uint8)
    text(image, message, 12, 12)
    return image.tobytes()
