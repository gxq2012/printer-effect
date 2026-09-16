"""Instant-camera case, fixed-proportion geometry and original shutter sound."""
import math,array,wave
from .themes import blend

def artwork(c,assets):
    if c['camera_appearance']=='photo':return '<img class="camera-photo" src="assets/instant-camera-photo.png" alt="Instant camera">'
    return (assets/'instant-camera.svg').read_text().replace('VAR_LIGHT',blend(c['color'],255,.48)).replace('VAR_BASE',c['color']).replace('VAR_DARK',blend(c['color'],0,.24))

def css(c,g):
    h=c['machine_height'];w=h*1000/650;left=(1440-w)/2
    photo=c['camera_appearance']=='photo'
    led_left=75.3 if photo else 80.4;led_top=50.4 if photo else 44.6
    return f'''
#furniture{{position:absolute;inset:0;z-index:5}}
.machine{{position:absolute;left:{left}px;top:24px;width:{w}px;height:{h}px;transform-origin:50% 50%}}
.machine .camera-photo{{width:100%;height:100%;object-fit:contain;display:block}}
.machine svg{{width:100%;height:100%;display:block;overflow:visible}}
.tray,.ground-shadow{{opacity:0!important}}
#led{{left:{led_left}%;top:{led_top}%;width:1.8%;height:2.8%;background:#28dc65}}
#camera-flare{{position:absolute;left:11%;top:12%;width:28%;height:24%;background:radial-gradient(white,#fffde3 35%,transparent 72%);opacity:0;filter:blur(6px);pointer-events:none}}
.studio{{background:{c['background']}}}
.card{{padding-bottom:{c['paper_border']+55}px!important}}
'''

def shutter(path):
    rate=24000;samples=array.array('h');state=37
    for i in range(round(.35*rate)):
        t=i/rate;state=(1664525*state+1013904223)&0xffffffff
        noise=state/2147483648-1
        envelope=math.exp(-t*100)+(.65*math.exp(-(t-.09)*75) if t>=.09 else 0)
        v=.42*envelope*(.8*noise+.2*math.sin(2*math.pi*850*t))
        samples.append(round(32767*v))
    import sys
    if sys.byteorder!='little':samples.byteswap()
    with wave.open(str(path),'wb') as f:
        f.setparams((1,2,rate,0,'NONE','not compressed'));f.writeframes(samples.tobytes())
