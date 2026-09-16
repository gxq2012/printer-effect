"""Validated public configuration; no media writes or network calls."""
from datetime import datetime, timezone, timedelta
import math
import re
from pathlib import Path

PRESETS = {'4:3': [1920,1440], '3:4': [1440,1920], '1:1': [1440,1440],
           '16:9': [1920,1080], '9:16': [1440,2560]}
EXTENSIONS = {'.png','.jpg','.jpeg','.webp','.heic','.heif','.tif','.tiff','.mp4','.mov','.m4v'}
COLORS = {'ivory':'#eee9df', 'mint':'#c1d6c7', 'pink':'#e8bdc7', 'blue':'#b5cce2',
          'black':'#353b42', 'silver':'#bcc3cc', 'cream':'#e5d2a6', 'red':'#a94f48'}
COLORS.update({'white':'#f3f3ef','matcha':'#b8cba0','light-blue':'#b5cce2',
 '白色':'#f3f3ef','粉色':'#e8bdc7','抹茶':'#b8cba0','淡蓝色':'#b5cce2'})
PHOTO_ASSETS = {COLORS[k]: 'instant-camera-'+k+'.png' for k in ('white','pink','matcha','light-blue')}
PHOTO_ASSETS[COLORS['ivory']]='instant-camera-photo.png'
KEYS = {'version','title','inputs','cover','canvas','aspect_ratio','content_width','paper_border',
        'machine_height','opening','printed_hold','travel','final_hold','print_seconds','duration',
        'ending','sound','sound_volume','sound_file','fps','style','color','background','fit',
        'position','feed','complete_color','blink_period','quality','source_audio','cache',
        'export_cover','notes','develop_seconds','flash','camera_appearance','camera_width','timestamp','timestamp_text'}

class ConfigError(ValueError):
    pass

def number(value, key, low, high):
    if isinstance(value, bool) or not isinstance(value, (int,float)) or not math.isfinite(value):
        raise ConfigError(f'{key}: expected a finite number')
    if not low <= value <= high:
        raise ConfigError(f'{key}: expected {low}..{high}, got {value}')
    return value

def color(value, key):
    value = COLORS.get(value, value)
    if not isinstance(value,str) or not re.fullmatch(r'#[0-9a-fA-F]{6}',value):
        raise ConfigError(f'{key}: use a named color {list(COLORS)} or #RRGGBB')
    return value

def natural(path):
    return tuple((1,int(s)) if s.isdigit() else (0,s.lower()) for s in re.split(r'(\d+)',path.name))

def path_value(value, base):
    p = Path(value).expanduser()
    return (p if p.is_absolute() else base/p).resolve()

def ending_duration(ending, n):
    if ending in ('hold','row'): return 0
    if ending == 'flyout': return 1.6 + n*3.2
    if ending == 'grid' and n > 12: return 1.6 + math.ceil(n/12)*4
    return 1.6 + 2.4 + (n-1)*.07

def normalize(raw, base=None):
    base = Path(base or '.').resolve()
    if not isinstance(raw,dict): raise ConfigError('Config must be an object')
    unknown = set(raw)-KEYS
    if unknown: raise ConfigError(f'Unknown configuration keys: {sorted(unknown)}')
    c = dict(raw)
    if c.get('version',1) != 1: raise ConfigError('Unsupported config version; expected 1')
    c['version']=1
    ratio=c.get('aspect_ratio','9:16')
    if 'canvas' not in c and ratio not in PRESETS: raise ConfigError(f'aspect_ratio: choose {list(PRESETS)}')
    canvas=c.get('canvas',PRESETS.get(ratio))
    if not isinstance(canvas,list) or len(canvas)!=2: raise ConfigError('canvas: expected [width,height]')
    for v in canvas:
        number(v,'canvas',320,4096)
        if int(v)!=v or v%2: raise ConfigError('canvas: dimensions must be even integers')
    c['canvas']=list(map(int,canvas))
    if max(canvas)/min(canvas)>3: raise ConfigError('canvas: aspect ratios beyond 3:1 are unsupported')
    c['aspect_ratio']=ratio if ratio in PRESETS and PRESETS[ratio]==canvas else f'{canvas[0]}x{canvas[1]}'
    for key,default,choices in [('style','modern',('modern','retro','instant')),
        ('fit','contain',('contain','cover')),('feed','stepped',('smooth','stepped')),
        ('quality','high',('draft','standard','high'))]:
        c[key]=c.get(key,default)
        if c[key] not in choices: raise ConfigError(f'{key}: choose {choices}')
    c['color']=color(c.get('color','cream' if c['style']=='retro' else 'ivory'),'color')
    c['camera_appearance']=c.get('camera_appearance','photo' if c['color'] in PHOTO_ASSETS else 'rendered')
    if c['camera_appearance'] not in ('photo','rendered'):raise ConfigError('camera_appearance: photo or rendered')
    if c['style']=='instant' and c['camera_appearance']=='photo' and c['color'] not in PHOTO_ASSETS:raise ConfigError('No photo asset for this color; choose camera_appearance rendered')
    c['background']=color(c.get('background','#eee9df'),'background')
    c['complete_color']=color(c.get('complete_color','#ee3838'),'complete_color')
    c['title']=c.get('title','Photo Printer')
    if not isinstance(c['title'],str) or len(c['title'])>150: raise ConfigError('title: expected <=150 characters')
    defaults={'content_width':(.9,.2,.94),'paper_border':(4 if canvas[0]>=canvas[1] else 16,0,60),
        'machine_height':((360 if canvas[0]>=canvas[1] else 842.4) if c['style']=='instant' else (194 if canvas[0]>=canvas[1] else 333),194,900 if c['style']=='instant' else 400),
        'develop_seconds':(2.5 if c['style']=='instant' else 0,0,15),'opening':(.6,0,10),'printed_hold':(.5,0,30),'travel':(.75,.2,5),
        'final_hold':(3,0,60),'sound_volume':(.55,0,1),'fps':(30,15,60),'blink_period':(.54,.3,3)}
    for key,(default,low,high) in defaults.items(): c[key]=number(c.get(key,default),key,low,high)
    if 'camera_width' in c:
        if c['style']!='instant': raise ConfigError('camera_width applies to instant cameras only')
        c['machine_height']=number(c['camera_width'],'camera_width',.25,.96)*1440*.65
    if int(c['fps'])!=c['fps']: raise ConfigError('fps must be an integer')
    for key,default in [('sound',True),('source_audio',False),('cache',True),('export_cover',True),('flash',True),('timestamp',True)]:
        c[key]=c.get(key,default)
        if not isinstance(c[key],bool): raise ConfigError(f'{key}: expected true/false')
    c['timestamp_text']=c.get('timestamp_text',datetime.now(timezone(timedelta(hours=8))).strftime('%Y.%m.%d|%H:%M:%S'))
    if not isinstance(c['timestamp_text'],str) or len(c['timestamp_text'])>100:raise ConfigError('timestamp_text: expected <=100 characters')
    if re.fullmatch(r'\d{4}\.\d{2}\.\d{2}\|\d{2}:\d{2}:\d{2}\|UTC[+-]\d{4}',c['timestamp_text']):
        c['timestamp_text']=datetime.strptime(c['timestamp_text'],'%Y.%m.%d|%H:%M:%S|UTC%z').astimezone(timezone(timedelta(hours=8))).strftime('%Y.%m.%d|%H:%M:%S')
    pos=c.get('position',[.5,.5])
    if not isinstance(pos,list) or len(pos)!=2: raise ConfigError('position: expected [x,y] in 0..1')
    c['position']=[number(v,'position',0,1) for v in pos]
    inputs=c.get('inputs',[])
    if isinstance(inputs,str): inputs=[inputs]
    if not isinstance(inputs,list): raise ConfigError('inputs: expected a list of files or directories')
    expanded=[]
    for entry in inputs:
        item={'path':entry} if isinstance(entry,str) else entry
        if not isinstance(item,dict) or 'path' not in item: raise ConfigError('Each input needs a path')
        extra=set(item)-{'path','print_seconds','play_seconds','media_start','crop'}
        if extra: raise ConfigError(f'Unknown input keys: {sorted(extra)}')
        p=path_value(item['path'],base)
        if p.is_dir():
            if len(item)>1: raise ConfigError('Per-item settings require a file, not a directory')
            expanded.extend({'path':str(f.resolve())} for f in sorted(p.iterdir(),key=natural)
                if not f.name.startswith('.') and f.is_file() and f.suffix.lower() in EXTENSIONS)
        else: expanded.append(dict(item,path=str(p)))
    if not 1<=len(expanded)<=100: raise ConfigError('Provide 1..100 supported media files')
    for item in expanded:
        p=Path(item['path'])
        if not p.is_file(): raise ConfigError(f'Input does not exist: {p}')
        if p.suffix.lower() not in EXTENSIONS: raise ConfigError(f'Unsupported input: {p.suffix}')
        for key,low,high in [('print_seconds',.5,120),('play_seconds',.1,120),('media_start',0,86400)]:
            if key in item: number(item[key],key,low,high)
        if 'crop' in item:
            if p.suffix.lower() not in ('.mp4','.mov','.m4v'): raise ConfigError('crop applies to video; use fit/position for images')
            crop=item['crop']
            if not isinstance(crop,list) or len(crop)!=4: raise ConfigError('crop: [width,height,x,y]')
            for v in crop:
                number(v,'crop',0,65536)
                if int(v)!=v: raise ConfigError('crop: integer pixels required')
            if min(crop[:2])<=0: raise ConfigError('crop width and height must be positive')
    cover=c.get('cover')
    if cover:
        cp=str(path_value(cover,base))
        idx=next((i for i,v in enumerate(expanded) if v['path']==cp),None)
        if idx is None: raise ConfigError('cover must identify a file already in inputs')
        expanded.insert(0,expanded.pop(idx))
    c.pop('cover',None)
    n=len(expanded)
    ending=c.get('ending','hold' if n==1 else 'snowflake')
    if ending=='collage': ending='snowflake'
    if ending not in ('hold','row','snowflake','grid','stack','flyout'): raise ConfigError('Invalid ending')
    if ending=='hold' and n>1: raise ConfigError('Multiple inputs: use row, grid, stack, snowflake or flyout')
    c['notes']=[]
    if n>12 and ending in ('snowflake','row','stack'):
        ending='grid';c['notes'].append('More than 12 photos: switched to paginated grid for readability.')
    c['ending']=ending
    print_times=[item.get('print_seconds',c.get('print_seconds',8 if n==1 else (4.8 if i==0 else 2.4))) for i,item in enumerate(expanded)]
    for v in print_times: number(v,'print_seconds',.5,120)
    video_time=sum(item.get('play_seconds',3) for item in expanded if Path(item['path']).suffix.lower() in ('.mp4','.mov','.m4v'))
    fixed=c['opening']+n*(.45+c['develop_seconds'] if c['style']=='instant' else 0)+n*c['printed_hold']+(n*c['travel'] if n>1 else 0)+video_time+c['final_hold']+ending_duration(ending,n)
    if 'duration' in c:
        target=number(c['duration'],'duration',1,1800)
        if 'print_seconds' in raw or any('print_seconds' in i for i in expanded):
            raise ConfigError('Use duration OR print_seconds, not both')
        available=target-fixed
        if available<n*.5: raise ConfigError(f'duration too short; minimum {fixed+n*.5:.2f}s for these scenes')
        # Give every item a minimum readable print interval, then distribute the remainder.
        weights=sum(print_times)
        print_times=[.5+(available-.5*n)*v/weights for v in print_times]
    for item,v in zip(expanded,print_times): item['print_seconds']=v
    c['inputs']=expanded
    c['computed_duration']=fixed+sum(print_times)
    if c.get('sound_file'):
        p=path_value(c['sound_file'],base)
        if not p.is_file(): raise ConfigError(f'sound_file does not exist: {p}')
        c['sound_file']=str(p)
    return c
