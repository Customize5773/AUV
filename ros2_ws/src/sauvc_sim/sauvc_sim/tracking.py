"""Short image-space tracks, never publish predicted objects as current detections."""
import math


class Tracker:
    def __init__(self):
        self.tracks = {}
        self.next_id = 1
        self.last_stamp = None

    def clear(self):
        self.tracks.clear()
        self.last_stamp = None

    def update(self, objects, stamp):
        if not math.isfinite(stamp):
            self.clear()
            return []
        if self.last_stamp is not None and stamp <= self.last_stamp:
            if stamp < self.last_stamp:
                self.clear()
            else:
                return []
        self.last_stamp = stamp
        self.tracks = {i:t for i,t in self.tracks.items() if stamp-t['stamp'] <= .7}
        pairs = []
        for j, obj in enumerate(objects):
            for i, track in self.tracks.items():
                if track['label'] != obj['label']:
                    continue
                dt = stamp-track['stamp']
                predicted = [track['center'][k]+track['velocity'][k]*dt for k in (0,1)]
                distance = math.dist(predicted, obj['center_px'])
                if distance <= 90:
                    pairs.append((distance,j,i))
        assignments, used = {}, set()
        for _,j,i in sorted(pairs):
            if j not in assignments and i not in used:
                assignments[j] = i
                used.add(i)
        result = []
        for j,obj in enumerate(objects):
            i = assignments.get(j)
            old = self.tracks.get(i)
            if old is None:
                i = self.next_id
                self.next_id += 1
            center = obj['center_px']
            dt = stamp-old['stamp'] if old else 1.
            velocity = [(center[k]-old['center'][k])/dt if old else 0. for k in (0,1)]
            hits = old['hits']+1 if old else 1
            self.tracks[i] = dict(label=obj['label'],center=center,velocity=velocity,
                                  stamp=stamp,hits=hits)
            result.append(dict(obj,track_id=i,track_hits=hits,confirmed=hits>=3))
        return result
