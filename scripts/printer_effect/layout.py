"""Geometry in one 1440-wide design plane; no printer scaleY."""
import math
from .config import ConfigError

def layout(c, media):
    W,H=c['canvas'];vh=H*1440/W;slot=c['machine_height'];n=len(media)
    border=c['paper_border'];content=1440*c['content_width'];paper=content+2*(border+1)
    # Printer opening is 1342px wide. Reject invalid combinations before rendering.
    if paper>1338: raise ConfigError('content_width + paper_border exceeds the output slot; reduce either value')
    instant=c['style']=='instant'
    if instant:
        slot=c['machine_height']*620/650+24
        paper=min(paper,c['machine_height']*724/650-12)
        content=paper-2*(border+1)
    margin=6 if vh<=1080 else 24
    row_h=min(190,vh*.1) if n>1 else 0
    extra=55 if instant else 0
    lifting=instant and n==1
    layout_slot=min(slot,100) if lifting else slot
    max_h=vh-layout_slot-row_h-2*margin-2*(border+1)-extra
    if max_h<120: raise ConfigError('Not enough room below printer; use a taller canvas or smaller machine_height')
    cards=[]
    for m in media:
        image_h=min(max_h,content*m['height']/m['width'])
        actual_w=min(content,image_h*m['width']/m['height']) if c['fit']=='contain' else content
        ph=image_h+2*(border+1)+extra
        card_width=actual_w+2*(border+1) if instant and c['fit']=='contain' else paper
        cards.append({'width':card_width,'height':ph,'left':(1440-card_width)/2,'top':slot,
                      'content_height':image_h,'actual_width_ratio':actual_w/1440})
    lift=max(0,slot+max(card['height'] for card in cards)+2*margin-vh) if lifting else 0
    return {'camera_lift':lift,'width':W,'height':H,'design_height':vh,'slot':slot,'margin':margin,
            'row_height':row_h,'machine_left':30,'machine_width':1380,
            'tray_left':30,'tray_width':1380,'cards':cards}

def pose(card,cx,cy,max_w,max_h,rotation=0):
    # Fit ROTATED bounds, not merely the unrotated rectangle.
    r=math.radians(rotation);w,h=card['width'],card['height']
    scale=min(max_w/(abs(w*math.cos(r))+abs(h*math.sin(r))),
              max_h/(abs(w*math.sin(r))+abs(h*math.cos(r))))
    sw,sh=w*scale,h*scale
    return {'x':cx-(sw*math.cos(r)-sh*math.sin(r))/2-card['left'],
            'y':cy-(sw*math.sin(r)+sh*math.cos(r))/2-card['top'],
            'scale':scale,'rotation':rotation}

def grid_positions(cards,vh):
    n=len(cards);best=None
    for cols in range(1,n+1):
        rows=math.ceil(n/cols);cw=1320/cols;ch=(vh-120)/rows
        score=min(min((cw-24)/c['width'],(ch-24)/c['height']) for c in cards)
        if best is None or score>best[0]: best=(score,cols,rows,cw,ch)
    _,cols,rows,cw,ch=best;result=[]
    for i,card in enumerate(cards):
        row=i//cols;count=min(cols,n-row*cols)
        cx=720+(i%cols-(count-1)/2)*cw;cy=60+(row+.5)*ch
        result.append(pose(card,cx,cy,cw-24,ch-24))
    return result
