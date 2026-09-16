"""Independent printer shape and palette; keep controls circular."""

def blend(hex_color,other,amount):
    rgb=[int(hex_color[i:i+2],16) for i in (1,3,5)]
    return '#'+''.join(f'{round(v*(1-amount)+other*amount):02x}' for v in rgb)

def css(c,g):
    base=c['color'];light=blend(base,255,.4);dark=blend(base,0,.18)
    rgb=[int(base[i:i+2],16)/255 for i in (1,3,5)]
    # Conservative contrasting label color for light/dark palettes.
    lum=sum(v*w for v,w in zip(rgb,(.2126,.7152,.0722)))
    label='#15191b' if lum>.52 else '#ffffff'
    slot=g['slot'];retro=c['style']=='retro'
    radius=34 if retro else 18
    extra='''
.machine .lid{border-radius:42px 42px 20px 20px}
.machine .lid-panel{border:2px solid var(--case-dark);box-shadow:inset 0 0 0 3px var(--case-light)}
.machine .controls{border-radius:8px;background:#a78f69;border:2px solid #6b5a44}
.machine .screen{background:#252b20;border-radius:2px}
.machine .label{font-family:ui-monospace,monospace;font-weight:bold;letter-spacing:5px}
.machine .vent{width:55px;background:repeating-linear-gradient(90deg,transparent 0 4px,#7f7058 4px 6px)}
.machine .lid:after{content:'';position:absolute;left:60px;right:60px;bottom:9px;height:5px;background:linear-gradient(90deg,#9a4937 0 33%,#c3914d 33% 66%,#687d67 66%)}
''' if retro else ''
    return f'''
:root{{--case:{base};--case-light:{light};--case-dark:{dark}}}
#furniture{{position:absolute;inset:0;z-index:5}}
.machine{{left:30px;top:12px;width:1380px;height:{slot}px}}
.machine .lid{{height:{slot-60}px;border-radius:{radius}px {radius}px 18px 18px;background:linear-gradient(150deg,var(--case-light),var(--case));border-color:var(--case-light)}}
.machine .lid-panel{{top:15px;height:{slot-111}px;border-radius:16px;background:var(--case);border-color:var(--case-dark);box-shadow:inset 0 1px 3px #00000015}}
.machine .seam{{top:{slot-82}px;background:var(--case-dark)}}
.machine .body{{inset:30px 0 0;border-radius:24px;background:linear-gradient(var(--case),var(--case-dark))}}
.machine .slot{{left:19px;width:1342px;top:{slot-36}px;height:26px}}
.machine .slot-lip{{left:31px;width:1318px;top:{slot-15}px;height:7px}}
.machine .label{{top:{(slot-194)/2+49}px;font-size:18px;letter-spacing:4px;color:{label}}}
.machine .controls{{top:{(slot-194)/2+28}px;height:64px}}
.machine .vent{{top:{slot-54}px;height:22px}}
#led{{width:16px;height:16px;right:25px;top:22px;background:#28dc65;box-shadow:0 0 12px #28dc6599}}
.tray{{left:30px;top:{slot-4}px;width:1380px;height:{g['design_height']-slot-g['margin']}px;clip-path:none;border-radius:0 0 20px 20px;background:linear-gradient(90deg,#bdc5ba,#d1d7cd 4%,#d1d7cd 96%,#bdc5ba);box-shadow:inset 0 0 0 2px #ffffff66}}
.ground-shadow{{left:30px;top:{slot}px;width:1380px;height:{g['design_height']-slot-g['margin']}px;background:transparent;border-radius:20px;box-shadow:0 8px 18px #382d1e14}}
.studio{{background:{c['background']}}}
{extra}
'''
