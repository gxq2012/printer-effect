#!/usr/bin/env python3
"""Generate redistributable synthetic test cards; no private media."""
from pathlib import Path
from PIL import Image,ImageDraw
p=Path(__file__).resolve().parents[1]/'examples/media';p.mkdir(parents=True,exist_ok=True)
for i,size in enumerate([(1200,800),(800,1200),(900,900),(1200,800)]):
    im=Image.new('RGB',size,[(224,227,211),(210,226,233),(231,209,194),(226,214,235)][i]);d=ImageDraw.Draw(im)
    w,h=size;d.ellipse((w*.6,h*.1,w*.86,h*.1+w*.26),fill=(221,167,87))
    d.polygon([(0,h*.85),(w*.38,h*.32),(w*.78,h),(0,h)],fill=(66,106,106))
    d.polygon([(w*.26,h),(w*.78,h*.44),(w,h*.75),(w,h)],fill=(97,135,116))
    d.rectangle((15,15,w-16,h-16),outline=(255,255,255),width=10)
    d.text((35,35),f'PRINTER EFFECT / SAMPLE {i+1}',fill=(25,35,35),font_size=30)
    im.save(p/f'card-{i+1:02d}.png')
print(p)
