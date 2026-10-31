"""Locate observed stalls; labels deliberately retain uncertainty within each layer."""
import json
from pathlib import Path


def load(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def largest_gap(rows,start,end,field='wall_s'):
    pairs=[(a,b) for a,b in zip(rows,rows[1:]) if a['wall_s']<=end and b['wall_s']>=start]
    if not pairs:return dict(seconds=None)
    a,b=max(pairs,key=lambda p:p[1][field]-p[0][field])
    return dict(seconds=b[field]-a[field],before=a,after=b)


def diagnose(native,ros,checker,start,end):
    def stream(rows,topic):return [p for p in rows if p.get('topic')==topic]
    gaps={name:largest_gap(rows,start,end) for name,rows in {
        'native_sensor':stream(native,'sensors'),'native_telemetry':stream(native,'dynamics/telemetry'),
        'ros_sensor':stream(ros,'sensors'),'ros_telemetry':stream(ros,'dynamics/telemetry'),
        'ros_health':stream(ros,'state/health'),
        'native_heartbeat':[p for p in native if p['kind']=='heartbeat'],
        'ros_heartbeat':[p for p in ros if p['kind']=='heartbeat']}.items()}
    def gap(name):return gaps[name]['seconds']
    health=[p for p in stream(ros,'state/health') if start<=p['wall_s']<=end]
    ages=[p['sensor_age_wall_s'] for p in health if 'sensor_age_wall_s' in p]
    peak_age=max(ages,default=None)
    packets=[p for p in stream(native,'dynamics/telemetry') if start<=p['wall_s']<=end]
    publish=max((p.get('sensor_publish_duration_s',0.) for p in packets),default=None)
    checker_gap=max((p['wall_gap_s'] for p in checker.get('reception',{}).get('gaps',[])
                     if p['topic']=='health' and p['wall']>=start and p['wall']-p['wall_gap_s']<=end),default=0.)
    label='inconclusive'
    required=('native_sensor','native_telemetry','ros_sensor','ros_health','native_heartbeat','ros_heartbeat')
    if all(gap(k) is not None for k in required) and peak_age is not None:
        if gap('native_heartbeat')>.3:label='native_observer_delay'
        elif gap('ros_heartbeat')>.3 and checker_gap<.15 and peak_age<.3 and gap('native_sensor')<.3:
            label='ros_observer_delay'
        elif publish is not None and publish>.3:label='native_publish_blocking'
        elif gap('native_sensor')>.3 and gap('ros_sensor')>.3:
            g=gaps['native_telemetry'];a=g.get('before',{});b=g.get('after',{})
            if b.get('sensor_sequence',0)-a.get('sensor_sequence',0)==1 and b.get('producer_wall_s',0)-a.get('producer_wall_s',0)>.3:
                label='producer_or_simulation_stall'
            else:label='native_transport_or_cli_delay'
        elif gap('native_sensor')<.3 and gap('ros_sensor')>.3 and peak_age>.3:
            label='bridge_or_ros_transport_delay'
        elif gap('native_sensor')<.3 and gap('ros_sensor')<.3 and (gap('ros_health')>.3 or peak_age>.3):
            label='estimator_or_subscription_stall'
        elif gap('ros_sensor')<.3 and gap('ros_health')<.3 and peak_age<.3:
            label='no_stale_sensor_event'
    # Validate the common monotonic clock basis rather than assuming matching epochs.
    latency=[p['wall_s']-p['producer_wall_s'] for p in packets if 'producer_wall_s' in p]
    clock_ok=bool(latency) and min(latency)>=-.005 and min(latency)<.1
    if not clock_ok:label='inconclusive_clock_or_probe'
    return dict(classification=label,start_wall_s=start,end_wall_s=end,gaps=gaps,
                max_estimator_sensor_age_s=peak_age,max_sensor_publish_duration_s=publish,
                checker_health_gap_s=checker_gap,producer_native_min_delay_s=min(latency,default=None),clock_basis_valid=clock_ok)
