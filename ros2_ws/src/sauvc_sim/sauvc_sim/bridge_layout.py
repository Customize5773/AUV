"""Isolate high-volume camera transport without changing topics or QoS."""


def bridge_groups(entries, layout):
    if layout=='single':return {'sauvc_bridge':list(entries)}
    if layout!='isolated':raise ValueError('unknown bridge layout')
    images=[row for row in entries if row['ros_type_name']=='sensor_msgs/msg/Image']
    critical=[row for row in entries if row['ros_type_name']!='sensor_msgs/msg/Image']
    return {'sauvc_bridge':critical,'sauvc_camera_bridge':images}


def camera_qos(entries):
    result={}
    for row in entries:
        if row['ros_type_name']=='sensor_msgs/msg/Image':
            prefix='qos_overrides.'+row['ros_topic_name']+'.publisher.'
            result.update({prefix+'reliability':'best_effort',prefix+'history':'keep_last',prefix+'depth':1})
    return result


def water_camera_bridges(entries):
    result=[]
    for row in entries:
        camera=next((name for name in ('front','bottom') if row['ros_topic_name']==f'/sauvc/camera_{name}/image_raw'),None)
        if camera:
            prefix=f'/sauvc/optics/{camera}'
            result.extend([{**row,'ros_topic_name':prefix+'/rgb','gz_topic_name':prefix+'/image'},
                           {**row,'ros_topic_name':prefix+'/depth','gz_topic_name':prefix+'/depth_image'}])
        else:result.append(dict(row))
    return result
