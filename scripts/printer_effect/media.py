"""Local media normalization and cache. Originals are never overwritten."""
import array
import hashlib
import json
import math
import shutil
import subprocess
import sys
import wave
from pathlib import Path
from .config import ConfigError

VIDEO={'.mp4','.mov','.m4v'}

def command(args):
    try:
        result=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=600,check=True)
        return result.stdout
    except FileNotFoundError as e: raise ConfigError(f'Missing command: {args[0]}; run doctor') from e
    except subprocess.TimeoutExpired as e: raise ConfigError(f'{args[0]} timed out after 10 minutes') from e
    except subprocess.CalledProcessError as e: raise ConfigError(f'{args[0]} failed: {e.stderr[-1600:]}') from e

def probe(path):
    data=json.loads(command(['ffprobe','-v','error','-show_streams','-show_format','-of','json',path]))
    v=next((s for s in data['streams'] if s['codec_type']=='video'),None)
    if not v: raise ConfigError(f'No visual stream: {path}')
    w,h=v['width'],v['height']
    rotation=next((s.get('rotation',0) for s in v.get('side_data_list',[]) if 'rotation' in s),0)
    rotation=float(v.get('tags',{}).get('rotate',rotation))
    if round(rotation)%180: w,h=h,w
    return {'width':w,'height':h,'duration':float(data.get('format',{}).get('duration',0)),
            'audio':any(s['codec_type']=='audio' for s in data['streams'])}

def key_for(path, settings):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    h.update(json.dumps(settings,sort_keys=True).encode())
    return h.hexdigest()

def normalize_image(source,target):
    from PIL import Image, ImageOps, ImageCms
    if source.suffix.lower() in ('.heic','.heif'):
        try:
            from pillow_heif import register_heif_opener
            register_heif_opener()
        except ImportError:
            if sys.platform=='darwin' and shutil.which('sips'):
                command(['sips','-s','format','png',source,'--out',target])
                source=target
            else: raise ConfigError('HEIC needs pillow-heif. Install requirements.txt and retry.')
    try:
        with Image.open(source) as im:
            im=ImageOps.exif_transpose(im)
            icc=im.info.get('icc_profile')
            if icc:
                import io
                alpha=im.getchannel('A') if im.mode=='RGBA' else None
                try:
                    im=ImageCms.profileToProfile(im,ImageCms.ImageCmsProfile(io.BytesIO(icc)),
                        ImageCms.createProfile('sRGB'),outputMode='RGB')
                except (ValueError,ImageCms.PyCMSError): im=im.convert('RGB')
                if alpha is not None: im.putalpha(alpha)
            if im.mode not in ('RGB','RGBA'): im=im.convert('RGB')
            im.thumbnail((4096,4096),Image.Resampling.LANCZOS)
            im.save(target,format='PNG',icc_profile=ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes())
    except OSError as e: raise ConfigError(f'Cannot decode image {source.name}: {e}') from e

def mechanical(target,duration):
    rate=24000;samples=array.array('h')
    for i in range(round(duration*rate)):
        t=i/rate;env=max(0,min(1,t/.06,(duration-t)/.1))
        gate=.35+.65*(math.sin(2*math.pi*4*t)>-.4)
        v=(.1*math.sin(2*math.pi*110*t)+.035*math.sin(2*math.pi*430*t)+.018*math.sin(2*math.pi*1733*t))*env*gate
        samples.append(round(32767*v))
    if sys.byteorder!='little':samples.byteswap()
    with wave.open(str(target),'wb') as f:
        f.setparams((1,2,rate,0,'NONE','not compressed'));f.writeframes(samples.tobytes())

def prepare(c,timing,assets,cache_dir):
    media=[];cache_dir.mkdir(parents=True,exist_ok=True)
    for i,(item,tm) in enumerate(zip(c['inputs'],timing['prints'])):
        source=Path(item['path']);video=source.suffix.lower() in VIDEO
        name=f'input-{i:03d}'+('.mp4' if video else '.png');target=assets/name
        original_name=f'original-{i:03d}{source.suffix.lower()}'
        shutil.copy2(source,assets/original_name)
        if not video:
            key=key_for(source,{'normalizer':2});cached=cache_dir/(key+'.png')
            if c['cache'] and cached.exists(): shutil.copy2(cached,target)
            else:
                normalize_image(source,target)
                if c['cache']:shutil.copy2(target,cached)
            from PIL import Image
            with Image.open(target) as im:w,h=im.size
            data={'width':w,'height':h,'audio':False}
        else:
            data=probe(source);crop=item.get('crop');start=item.get('media_start',0);play=item.get('play_seconds',3)
            if start>=data['duration']:raise ConfigError(f'media_start exceeds video duration: {source.name}')
            vf=[]
            if crop:
                cw,ch,x,y=crop
                if x+cw>data['width'] or y+ch>data['height']:raise ConfigError('crop exceeds oriented video dimensions')
                vf.append('crop='+':'.join(map(str,crop)));data.update(width=cw,height=ch)
            vf += [f'trim=start={start}:duration={play}','setpts=PTS-STARTPTS',f'fps={c["fps"]}',
                f'tpad=start_mode=clone:start_duration={tm["play_at"]}:stop_mode=clone:stop_duration={timing["duration"]}',
                'scale=trunc(iw/2)*2:trunc(ih/2)*2']
            settings={'vf':vf,'duration':timing['duration'],'fps':c['fps'],'normalizer':2}
            cached=cache_dir/(key_for(source,settings)+'.mp4')
            if c['cache'] and cached.exists():shutil.copy2(cached,target)
            else:
                command(['ffmpeg','-y','-v','error','-i',source,'-vf',','.join(vf),'-t',timing['duration'],
                    '-an','-r',c['fps'],'-c:v','libx264','-pix_fmt','yuv420p','-crf','18','-movflags','+faststart',target])
                if c['cache']:shutil.copy2(target,cached)
            if abs(probe(target)['duration']-timing['duration'])>1/c['fps']+.05:
                raise ConfigError('Prepared video length is incorrect; retry with --no-cache')
            if c['source_audio'] and data['audio']:
                audio_name=f'source-{i:03d}.wav'
                command(['ffmpeg','-y','-v','error','-i',source,'-vn','-af',
                    f'atrim=start={start}:duration={play},asetpts=PTS-STARTPTS,apad',
                    '-t',play,'-ar','48000',assets/audio_name])
                data['audio_name']=audio_name
        data.update(name=name,original=original_name,video=video);media.append(data)
        if c['sound']:
            duration=item['print_seconds'];sound=assets/f'print-{i:03d}.wav'
            if c.get('sound_file'):
                command(['ffmpeg','-y','-v','error','-stream_loop','-1','-i',c['sound_file'],'-t',duration,
                    '-af',f'afade=t=in:d=0.06,afade=t=out:st={max(0,duration-.1)}:d=0.1','-ar','24000',sound])
            else:mechanical(sound,duration)
    return media
