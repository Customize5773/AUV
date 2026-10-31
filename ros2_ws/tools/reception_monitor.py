"""Bounded callback-gap evidence; never changes freshness or control decisions."""
class ReceptionMonitor:
    def __init__(self):
        self.streams = {}
        self.gaps = []
        self.dropped_events = 0

    def record(self, topic, wall, sim):
        previous = self.streams.get(topic)
        if previous is None:
            self.streams[topic] = dict(count=1, wall=wall, sim=sim, max_wall_gap_s=0.)
            return
        gap = wall - previous['wall']
        previous['max_wall_gap_s'] = max(previous['max_wall_gap_s'], gap)
        if gap >= .1:
            event = dict(topic=topic, wall=wall, wall_gap_s=gap,
                         sim_before=previous['sim'], sim_after=sim)
            if len(self.gaps) < 1000:
                self.gaps.append(event)
            else:
                self.dropped_events += 1
        previous.update(count=previous['count']+1, wall=wall, sim=sim)

    def summary(self):
        return dict(streams={k:dict(v) for k,v in self.streams.items()},
                    gaps=list(self.gaps), dropped_events=self.dropped_events)
