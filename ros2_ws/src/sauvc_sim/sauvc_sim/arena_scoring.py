"""SAUVC 2026/2027.2.1 attempt accounting, separate from strict training success."""
import math


class ArenaScore:
    def __init__(self, order, blue_drum=0, pinger_drum=None,edition='2026'):
        if pinger_drum is not None and (pinger_drum not in range(4) or pinger_drum == blue_drum):
            raise ValueError('pinger must be in a red drum')
        self.edition=edition
        self.square_ok=False
        self.order=list(order)
        self.blue_drum=blue_drum
        self.pinger_drum=pinger_drum
        self.started=None
        self.ended=None
        self.end_reason=None
        self.navigation=False
        self.flares=[]
        self.first_payload=None
        self.acquisition=None
        self.retrieval_crossing=False
        self.retrieved=False
        self.penalties=0
        self.pool_touches=0
        self.pool_seconds=0.
        self.active=set()
        self.last_contact_time=None
        self.entries=[]

    def award(self, kind, t, **data):
        if self.ended is not None: return
        if kind=='navigation':
            if self.edition=='2026' and self.navigation and self.acquisition is not None:self.retrieval_crossing=True
            self.navigation=True
        elif kind=='flare' and self.navigation and data['label'] not in self.flares:
            self.flares.append(data['label'])
        elif kind=='payload' and self.navigation and self.first_payload is None:
            # Latch the first released ball even if it misses every drum.
            self.first_payload=data['ball_id']
        elif kind=='acquisition' and self.navigation and data['ball_id']==self.first_payload and self.acquisition is None:
            self.acquisition=data['drum']
        elif kind=='target_zone_exit' and self.acquisition is not None:
            self.retrieval_crossing=True
        elif kind=='retrieval':
            self.retrieved=bool(self.retrieval_crossing and data['ball_id']==self.first_payload and data['held'])
        else: return
        self.entries.append(dict(event=kind,time=t,**data))

    def contacts(self, t, kinds):
        if self.ended is not None: return
        kinds=set(kinds)
        if self.last_contact_time is not None and 'pool' in self.active:
            self.pool_seconds+=max(0.,t-self.last_contact_time)
        for kind in sorted(kinds-self.active):
            self.penalties+=2 if kind=='gate' else 5
            if kind=='pool': self.pool_touches+=1
            self.entries.append(dict(event='contact',kind=kind,time=t))
        self.active=kinds
        self.last_contact_time=t
        if self.pool_seconds>10 or self.pool_touches>=5: self.finish(t,'automatic_abort')

    def finish(self, t, reason, square=False):
        if self.ended is not None: return
        if not math.isfinite(t): raise ValueError('nonfinite end time')
        self.ended=t
        self.end_reason=reason
        self.square_ok=bool(self.edition=='2027' and self.navigation and reason=='surface' and square)

    def result(self):
        nav=15 if self.navigation else 0
        acquisition=0 if self.acquisition is None else (30 if self.acquisition==self.blue_drum else
                      50 if self.acquisition==self.pinger_drum else 10)
        flare=20*len(self.flares)
        ordered=60 if self.flares==self.order else 0
        retrieval=60 if self.retrieved and self.acquisition is not None else 0
        elapsed=max(0.,self.ended-self.started) if self.ended is not None and self.started is not None else None
        other=acquisition>0 or flare>0 or retrieval>0
        timing=max(0.,900-elapsed)*.03 if elapsed is not None and nav and other else 0.
        surface=5 if self.end_reason=='surface' else 0
        square=20 if self.square_ok else 0
        return dict(rulebook='2027.2.1' if self.edition=='2027' else '2026 v6.1.0',final=self.ended is not None,end_reason=self.end_reason,
                    run_time_s=elapsed,navigation=nav,target_acquisition=acquisition,
                    communication_localization=flare,flare_order_bonus=ordered,target_reacquisition=retrieval,
                    surface_bonus=surface,surfacing_square_bonus=square,timing_bonus=timing,penalty_points=self.penalties,
                    pool_contact_seconds=self.pool_seconds,pool_contact_episodes=self.pool_touches,
                    attempt_total=nav+acquisition+flare+ordered+retrieval+surface+square+timing-self.penalties,
                    inspection_bonus_included=False,entries=self.entries)
