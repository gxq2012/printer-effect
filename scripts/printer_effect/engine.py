"""Composition authoring. Builds artifacts; never uploads or publishes."""
import html
import json
import math
import shutil
from pathlib import Path
from . import __version__
from . import instant
from .layout import layout, pose, grid_positions
from .timeline import plan
from .media import prepare
from .themes import css as theme_css
from .config import ConfigError, PHOTO_ASSETS

ROOT=Path(__file__).resolve().parents[2]
ASSETS=ROOT/'assets'
HF_VERSION='0.8.40'

def set_pose(js,selector,p,t,duration=None):
    props=dict(p)
    if duration is None:
        js.append(f'tl.set({json.dumps(selector)},{json.dumps(props)},{t});')
    else:
        props.update(duration=duration,ease='power2.inOut')
        js.append(f'tl.to({json.dumps(selector)},{json.dumps(props)},{t});')

def endings(js,c,g,tm):
    cards=g['cards'];n=len(cards);mode=c['ending'];vh=g['design_height']
    if mode in ('hold','row'):return
    start=tm['ending_start']+.8
    js.append(f"tl.to(['#furniture','.tray','.ground-shadow'],{{opacity:0,y:{-g.get('camera_lift',0)-40},duration:.8,ease:'power2.inOut'}},{start});")
    release=start+.8
    js.append(f"tl.set('#photo-layer',{{clipPath:'inset(0px 0px 0px 0px)'}},{release});")
    if mode=='flyout':
        for i,card in enumerate(cards):
            at=release+i*3.2
            set_pose(js,f'#card-{i}',{'zIndex':100+i},at)
            target=pose(card,720,vh/2,1296,vh-120,0)
            # Lift, then settle: actual subject travel rather than a static zoom.
            lifted=pose(card,760,vh*.47,1150,vh-160,-4)
            set_pose(js,f'#card-{i}',lifted,at,.85)
            set_pose(js,f'#card-{i}',target,at+.85,.55)
            if i<n-1:set_pose(js,f'#card-{i}',dict(target,x=target['x']-1600,opacity=0),at+2.55,.65)
        return
    if mode=='grid' and n>12:
        for page,offset in enumerate(range(0,n,12)):
            at=release+page*4
            for i in range(n):set_pose(js,f'#card-{i}',{'opacity':0},at)
            group=cards[offset:offset+12]
            for j,p in enumerate(grid_positions(group,vh)):
                i=offset+j;set_pose(js,f'#card-{i}',dict(p,opacity=1),at,1)
        return
    if mode=='grid':targets=grid_positions(cards,vh)
    elif mode=='stack':
        targets=[pose(card,720+(i-(n-1)/2)*10,vh/2+(i-(n-1)/2)*8,
                      1100,vh-160,((i*7)%17)-8) for i,card in enumerate(cards)]
    else:
        targets=[]
        for i,card in enumerate(cards):
            if i==0:
                targets.append(pose(card,720,vh/2,620 if n>1 else 1200,vh*(.4 if n>1 else .85)))
            else:
                a=-math.pi/2+(i-1)*2*math.pi/max(1,n-1)
                targets.append(pose(card,720+460*math.cos(a),vh/2+vh*.31*math.sin(a),
                    440 if n<=6 else 300,vh*.28,[-5,12,20,15,-10,6,-14,-20,-12,9][(i-1)%10]))
    for i,p in enumerate(targets):
        set_pose(js,f'#card-{i}',{'zIndex':1000 if mode=='snowflake' and i==0 else 20+i},release)
        set_pose(js,f'#card-{i}',p,release+i*.07,2.4)

def build(c,out,cache_dir):
    assets=out/'assets';assets.mkdir(parents=True);(out/'renders').mkdir()
    gsap=ROOT/'node_modules/gsap/dist/gsap.min.js'
    if not gsap.is_file():raise ConfigError('GSAP dependency missing. Run: python3 scripts/cli.py setup')
    shutil.copy2(gsap,assets/'gsap.min.js')
    if c['style']=='instant' and c['camera_appearance']=='photo':shutil.copy2(ASSETS/PHOTO_ASSETS[c['color']],assets/'instant-camera-photo.png')
    timing=plan(c);media=prepare(c,timing,assets,cache_dir);g=layout(c,media)
    total=timing['duration'];cards=[];audio=[];js=['const tl=gsap.timeline({paused:true});']
    for i,(item,mt,card,m) in enumerate(zip(c['inputs'],timing['prints'],g['cards'],media)):
        t=mt['start'];dur=item['print_seconds'];ph=card['height']
        visual=(f'<video id="video-{i}" src="assets/{m["name"]}" data-start="0" data-duration="{total}" '
                f'data-track-index="{i+2}" muted playsinline preload="auto"></video>') if m['video'] else f'<img src="assets/{m["name"]}" alt="Photo {i+1}">'
        stamp=''
        if c['timestamp']:
            lines=c['timestamp_text'].split('|')[:2]
            textlines=''.join(f'<text x="85" y="{77+j*24}" text-anchor="middle" font-family="monospace" font-size="{14 if j<2 else 10}" fill="#304b60">{html.escape(line)}</text>' for j,line in enumerate(lines))
            stamp=f'<svg class="postmark" viewBox="0 0 220 160" aria-label="Print timestamp"><rect x="10" y="8" width="150" height="142" rx="10" fill="#fffdf3" fill-opacity=".86" stroke="#304b60" stroke-width="2" stroke-dasharray="3 4"/><circle cx="85" cy="80" r="60" fill="none" stroke="#304b60" stroke-width="2"/><circle cx="85" cy="80" r="55" fill="none" stroke="#304b60" stroke-width="1"/><text x="85" y="45" text-anchor="middle" font-family="sans-serif" font-size="12" letter-spacing="2" fill="#304b60">PRINTED</text>{textlines}<path d="M145 60q16 -8 32 0t32 0 M145 72q16 -8 32 0t32 0 M145 84q16 -8 32 0t32 0" fill="none" stroke="#304b60" stroke-width="2"/></svg>'
        cards.append(f'<div id="card-{i}" class="card" data-layout-allow-overflow style="left:{card["left"]}px;top:{g["slot"]}px;width:{card["width"]}px;height:{ph}px;padding:{c["paper_border"]}px">{visual}{stamp}</div>')
        set_pose(js,f'#card-{i}',{'opacity':0,'y':-ph},0)
        set_pose(js,f'#card-{i}',{'opacity':1},t)
        if c['style']=='instant':
            visual_selector=f'#card-{i} img, #card-{i} video, #card-{i} .postmark'
            set_pose(js,visual_selector,{'opacity':0},0)
            set_pose(js,visual_selector,{'opacity':1},mt['print_end'],c['develop_seconds'])
            if c['flash']:
                set_pose(js,'#camera-flare',{'opacity':1},mt['shot_at'])
                set_pose(js,'#camera-flare',{'opacity':0},mt['shot_at']+.06,.22)
            set_pose(js,'.machine',{'scale':.993},mt['shot_at'],.07)
            set_pose(js,'.machine',{'scale':1},mt['shot_at']+.07,.18)
            if c['sound']:
                instant.shutter(assets/f'shutter-{i:03d}.wav')
                audio.append(f'<audio id="shutter-{i}" src="assets/shutter-{i:03d}.wav" data-start="{mt["shot_at"]}" data-duration="0.35" data-track-index="3" data-volume="{c["sound_volume"]}"></audio>')
        lift=g.get('camera_lift',0)
        if c['feed']=='smooth':
            if lift:
                js.append(f"tl.to('#furniture',{{y:{-lift},duration:{dur},ease:'sine.inOut'}},{t});")
                js.append(f"tl.to('#photo-layer',{{clipPath:'inset({g['slot']-lift}px 0px 0px 0px)',duration:{dur},ease:'sine.inOut'}},{t});")
            js.append(f"tl.to('#card-{i}',{{y:{-lift},duration:{dur},ease:'sine.inOut'}},{t});")
        else:
            steps=max(8,round(dur*3))
            for j in range(steps):
                if lift:
                    shift=lift*(j+1)/steps
                    js.append(f"tl.to('#furniture',{{y:{-shift},duration:{dur/steps*.91},ease:'sine.inOut'}},{t+j*dur/steps});")
                    js.append(f"tl.to('#photo-layer',{{clipPath:'inset({g['slot']-shift}px 0px 0px 0px)',duration:{dur/steps*.91},ease:'sine.inOut'}},{t+j*dur/steps});")
                js.append(f"tl.to('#card-{i}',{{y:{-ph*(1-(j+1)/steps)-lift*(j+1)/steps},duration:{dur/steps*.91},ease:'sine.inOut'}},{t+j*dur/steps});")
        js.append(f"tl.fromTo('#progress',{{scaleX:0}},{{scaleX:1,duration:{dur},ease:'none',immediateRender:false}},{t});")
        set_pose(js,'#led',{'backgroundColor':'#28dc65','opacity':1,'boxShadow':'0 0 12px #28dc6599'},t)
        for k in range(math.ceil(dur/c['blink_period'])):
            for phase,alpha in ((0,1),(c['blink_period']/2,.18)):
                at=t+k*c['blink_period']+phase;bd=min(.16,t+dur-at)
                if bd>0:js.append(f"tl.to('#led',{{opacity:{alpha},duration:{bd},ease:'sine.inOut'}},{at});")
        set_pose(js,'#led',{'backgroundColor':c['complete_color'],'opacity':1,'boxShadow':f'0 0 14px {c["complete_color"]}99'},t+dur)
        if c['sound']:
            audio.append(f'<audio id="sound-{i}" src="assets/print-{i:03d}.wav" data-start="{t}" data-duration="{dur}" data-track-index="1" data-volume="{c["sound_volume"]}"></audio>')
        if 'audio_name' in m:
            audio.append(f'<audio id="source-sound-{i}" src="assets/{m["audio_name"]}" data-start="{mt["play_at"]}" data-duration="{item.get("play_seconds",3)}" data-track-index="2" data-volume="1"></audio>')
        if len(media)>1:
            # Large batches stage as an overlapping stack; ending uses readable pages.
            cell=1320/min(len(media),12);column=i%12
            sc=min(cell*.88/card['width'],(g['row_height']-12)/ph)
            rx=60+cell*(column+.5)-card['width']*sc/2;ry=g['design_height']-g['row_height']+8
            set_pose(js,f'#card-{i}',{'x':rx-card['left'],'y':ry-g['slot'],'scale':sc},mt['move_at'],c['travel'])
    endings(js,c,g,timing)
    js.append('window.__timelines=window.__timelines||{};window.__timelines.main=tl;')
    W,H=c['canvas'];vh=g['design_height'];pos=c['position']
    css=(ASSETS/'printer.css').read_text()+theme_css(c,g)+(instant.css(c,g) if c['style']=='instant' else '')+f'''
html,body,#main{{width:{W}px;height:{H}px}}
#main{{position:relative;overflow:hidden}}
#scene{{position:absolute;width:1440px;height:{vh}px;transform:scale({W/1440});transform-origin:0 0}}
#photo-layer{{position:absolute;inset:0;z-index:4;clip-path:inset({g['slot']}px 0px 0px 0px)}}
.card{{position:absolute;box-sizing:border-box;background:#fff;border:1px solid #e4ded1;border-radius:3px;box-shadow:0 16px 30px #40372933;opacity:0;transform-origin:0 0}}
.postmark{{position:absolute;right:2%;bottom:1%;width:25%;max-width:220px;height:auto;transform:rotate(-8deg);pointer-events:none}}
.card img,.card video{{display:block;width:100%;height:100%;object-fit:{c['fit']};object-position:{pos[0]*100}% {pos[1]*100}%;background:white}}
'''
    machine=(ASSETS/'machine.html').read_text().replace('PHOTO / 01',f'{"MEMORY" if c["style"]=="retro" else "PHOTO"} / {len(media):02d}')
    if c['style']=='instant':machine='<div class="machine">'+instant.artwork(c,ASSETS)+'<div id="led"></div><div id="camera-flare"></div></div>'
    document=f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>{html.escape(c['title'])}</title><script src="assets/gsap.min.js"></script><style>{css}</style></head><body><div id="main" data-composition-id="main" data-start="0" data-duration="{total}" data-width="{W}" data-height="{H}"><div id="scene" class="clip" data-start="0" data-duration="{total}" data-track-index="0"><div class="studio"></div><div class="ground-shadow"></div><div class="tray"></div><div id="furniture">{machine}</div><div id="photo-layer">{''.join(cards)}</div></div>{''.join(audio)}</div><script>{''.join(js)}</script></body></html>'''
    (out/'index.html').write_text(document)
    (out/'timing.json').write_text(json.dumps(timing,indent=2))
    report={'version':__version__,'canvas':c['canvas'],'duration':total,'fps':c['fps'],
        'style':c['style'],'color':c['color'],'ending':c['ending'],'geometry':g,'notes':c['notes']}
    for i,card in enumerate(g['cards']):
        if card['actual_width_ratio']<c['content_width']-.005:
            report['notes'].append(f'Photo {i+1}: complete image uses {card["actual_width_ratio"]:.1%} of canvas width; paper area requested {c["content_width"]:.1%}. No cropping.')
    (out/'layout-report.json').write_text(json.dumps(report,indent=2))
    saved={k:v for k,v in c.items() if k not in ('computed_duration','notes')}
    saved['inputs']=[dict(item,path='assets/'+m['original']) for item,m in zip(c['inputs'],media)]
    if 'duration' in saved:
        saved.pop('print_seconds',None)
        for item in saved['inputs']:item.pop('print_seconds',None)
    if c.get('sound_file'):
        sf=Path(c['sound_file']);shutil.copy2(sf,assets/('custom-sound'+sf.suffix.lower()))
        saved['sound_file']='assets/custom-sound'+sf.suffix.lower()
    (out/'printer-config.json').write_text(json.dumps(saved,ensure_ascii=False,indent=2))
    (out/'package.json').write_text(json.dumps({'private':True,'type':'module','scripts':{
        'check':f'npx --yes hyperframes@{HF_VERSION} check',
        'render':f'npx --yes hyperframes@{HF_VERSION} render --fps {c["fps"]} --quality {c["quality"]}',
        'preview':f'npx --yes hyperframes@{HF_VERSION} preview'}},indent=2))
    (out/'BRIEF.md').write_text('---\nworkflow: general-video\nflow: automation\nstoryboard: no\n---\n'
        +f'Printer Effect {__version__}; {W}x{H}; {total:.2f}s; {c["style"]}; {c["ending"]}.\n'
        +'See printer-config.json for editable parameters and layout-report.json for actual fit.\n')
    return report
