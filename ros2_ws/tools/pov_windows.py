"""Manage only X11 image viewer windows belonging to the supplied launchers."""
# shortcut: X11 only; add another backend when Wayland GUI testing is required.
import ctypes
import ctypes.util
import re
import subprocess


def viewer_command(camera):
    if camera not in ('front','bottom'):raise ValueError('unknown camera')
    return ['bash','tools/ros.sh','python','tools/pov_viewer.py',camera]


def owned_windows(viewers,titles=('SAUVC POV front','SAUVC POV bottom')):
    if not viewers:return []
    owned={v.pid for v in viewers}
    pairs=[tuple(map(int,line.split())) for line in subprocess.check_output(['ps','-eo','pid=,ppid='],text=True).splitlines()]
    while True:
        expanded=owned|{pid for pid,parent in pairs if parent in owned}
        if expanded==owned:break
        owned=expanded
    tree=subprocess.check_output(['xwininfo','-root','-tree'],text=True)
    result=[]
    names='|'.join(re.escape(t) for t in titles)
    for window in re.findall(r'^\s*(0x[0-9a-f]+) "(?:'+names+r')":.*',tree,re.M):
        prop=subprocess.check_output(['xprop','-id',window,'_NET_WM_PID'],text=True)
        match=re.search(r'=\s*(\d+)',prop)
        if match and int(match[1]) in owned:result.append(int(window,16))
    return result


class Data(ctypes.Union):
    _fields_=[('b',ctypes.c_char*20),('s',ctypes.c_short*10),('l',ctypes.c_long*5)]


class Message(ctypes.Structure):
    _fields_=[('type',ctypes.c_int),('serial',ctypes.c_ulong),('send_event',ctypes.c_int),
              ('display',ctypes.c_void_p),('window',ctypes.c_ulong),('message_type',ctypes.c_ulong),
              ('format',ctypes.c_int),('data',Data)]


class Event(ctypes.Union):
    _fields_=[('message',Message),('pad',ctypes.c_long*24)]


def send(windows,atom,values):
    if not windows:return
    lib=ctypes.CDLL(ctypes.util.find_library('X11'))
    lib.XOpenDisplay.argtypes=[ctypes.c_char_p];lib.XOpenDisplay.restype=ctypes.c_void_p
    lib.XDefaultRootWindow.argtypes=[ctypes.c_void_p];lib.XDefaultRootWindow.restype=ctypes.c_ulong
    lib.XInternAtom.argtypes=[ctypes.c_void_p,ctypes.c_char_p,ctypes.c_int];lib.XInternAtom.restype=ctypes.c_ulong
    lib.XSendEvent.argtypes=[ctypes.c_void_p,ctypes.c_ulong,ctypes.c_int,ctypes.c_long,ctypes.POINTER(Event)]
    lib.XFlush.argtypes=[ctypes.c_void_p];lib.XCloseDisplay.argtypes=[ctypes.c_void_p]
    display=lib.XOpenDisplay(None)
    if not display:raise RuntimeError('X11 display unavailable')
    try:
        root=lib.XDefaultRootWindow(display);message_type=lib.XInternAtom(display,atom.encode(),0)
        for window,data in zip(windows,values):
            event=Event();event.message=Message(33,0,1,display,window,message_type,32,Data())
            for i,value in enumerate(data):event.message.data.l[i]=value
            if not lib.XSendEvent(display,root,0,(1<<19)|(1<<20),ctypes.byref(event)):raise RuntimeError('X11 event rejected')
        lib.XFlush(display)
    finally:lib.XCloseDisplay(display)


def arrange(viewers):
    windows=owned_windows(viewers)
    if len(windows)!=len(viewers):return []
    root=subprocess.check_output(['xwininfo','-root'],text=True)
    width=int(re.search(r'Width:\s+(\d+)',root)[1]);height=int(re.search(r'Height:\s+(\d+)',root)[1])
    send(windows,'_NET_MOVERESIZE_WINDOW',[[2<<12|15<<8, int(width*.63)+10,40+i*(height//2),int(width*.35),(height-220)//2] for i in range(len(windows))])
    return windows



def close_simulator_gui(process):
    windows=owned_windows([process],titles=('Gazebo',))
    send(windows,'_NET_CLOSE_WINDOW',[[0,1,0,0,0] for _ in windows])
    if windows:
        try:process.wait(timeout=8)
        except subprocess.TimeoutExpired:pass
    return bool(windows)
