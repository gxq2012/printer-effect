from pathlib import Path
from .config import ending_duration

def plan(c):
    t=c['opening'];items=[];n=len(c['inputs'])
    for i,item in enumerate(c['inputs']):
        video=Path(item['path']).suffix.lower() in ('.mp4','.mov','.m4v')
        shot=t
        if c['style']=='instant':t+=.45
        end=t+item['print_seconds'];develop_end=end+(c['develop_seconds'] if c['style']=='instant' else 0);play_at=develop_end+c['printed_hold']
        move_at=play_at+(item.get('play_seconds',3) if video else 0)
        items.append({'index':i,'shot_at':shot,'develop_end':develop_end,'start':t,'print_end':end,'play_at':play_at,'move_at':move_at})
        t=move_at+(c['travel'] if n>1 else 0)
    return {'prints':items,'ending_start':t,'duration':round(t+ending_duration(c['ending'],n)+c['final_hold'],6)}
