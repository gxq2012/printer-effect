#!/usr/bin/env python3
"""Build, preview and render local printer-effect animations."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from printer_effect.config import normalize, ConfigError
from printer_effect.engine import build, ROOT, HF_VERSION
from printer_effect.media import command


def doctor():
    result={'python':sys.version.split()[0],'commands':{},'packages':{},'gsap':False}
    for name in ('node','npm','npx','ffmpeg','ffprobe'):
        result['commands'][name]=shutil.which(name) is not None
    for name in ('PIL','pillow_heif'):result['packages'][name]=importlib.util.find_spec(name) is not None
    result['gsap']=(ROOT/'node_modules/gsap/dist/gsap.min.js').is_file()
    node_major=0
    if result['commands']['node']:
        node_major=int(command(['node','--version']).strip().lstrip('v').split('.')[0])
    result['node_22_or_newer']=node_major>=22
    result['ok']=all(result['commands'].values()) and result['packages']['PIL'] and result['gsap'] and node_major>=22
    result['help']='Install Node >=22, FFmpeg/ffprobe, pip install -r requirements.txt; then run setup. HEIC needs pillow-heif (or macOS sips).'
    return result


def task_config(args):
    raw={};base=Path.cwd()
    if args.config:
        cp=args.config.resolve();raw=json.loads(cp.read_text());base=cp.parent
    if args.inputs:raw['inputs']=[str(Path(p).expanduser().resolve()) for p in args.inputs]
    mapping={'aspect':'aspect_ratio','width':'content_width','camera_width':'camera_width','duration':'duration','ending':'ending',
             'style':'style','color':'color','background':'background','fit':'fit','feed':'feed',
             'fps':'fps','quality':'quality','cover':'cover','border':'paper_border',
             'machine_height':'machine_height','sound_volume':'sound_volume','sound_file':'sound_file'}
    for arg,key in mapping.items():
        val=getattr(args,arg,None)
        if val is not None:
            if arg in ('width','camera_width'):val=float(val.rstrip('%'))/100 if val.endswith('%') else float(val)
            if arg in ('cover','sound_file'):val=str(Path(val).expanduser().resolve())
            raw[key]=val
    if args.machine_height is not None and args.camera_width is None:raw.pop('camera_width',None)
    if args.color is not None:raw.pop('camera_appearance',None)
    if args.aspect:raw.pop('canvas',None)
    if args.duration is not None:
        raw.pop('print_seconds',None)
        for i in raw.get('inputs',[]):
            if isinstance(i,dict):i.pop('print_seconds',None)
    if args.no_timestamp:raw['timestamp']=False
    elif not args.config:raw.pop('timestamp_text',None)
    if args.silent:raw['sound']=False
    if args.source_audio:raw['source_audio']=True
    if args.no_cache:raw['cache']=False
    return normalize(raw,base)


def destination(path,revision):
    path=path.expanduser().resolve()
    if path.exists():
        if not revision:raise ConfigError(f'Output exists: {path}. Use --revision or another directory.')
        number=2
        while path.with_name(path.name+f'-v{number:03d}').exists():number+=1
        path=path.with_name(path.name+f'-v{number:03d}')
    return path


def logged(args,cwd,logname):
    logfile=cwd/logname
    try:
        with logfile.open('w') as log:
            subprocess.run(list(map(str,args)),cwd=cwd,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=1800)
    except (subprocess.CalledProcessError,subprocess.TimeoutExpired) as e:
        raise ConfigError(f'{args[0]} failed; see {logfile}\n'+logfile.read_text()[-2500:]) from e


def render_project(out,c):
    info=json.loads((out/'timing.json').read_text());points=[.1,info['duration']-.1]
    # Keep checks bounded for large batches; explicit first/middle/last print probes.
    events=info['prints'];sampled=[events[i] for i in sorted(set([0,len(events)//2,len(events)-1]))]
    for e in sampled:points += [(e['start']+e['print_end'])/2,e['print_end']+.05]
    at=','.join(str(round(t,3)) for t in sorted(set(points)) if 0<=t<info['duration'])
    logged(['npx','--yes',f'hyperframes@{HF_VERSION}','check','--snapshots','--at',at],out,'check.log')
    output=out/'renders/printer-effect.mp4'
    logged(['npx','--yes',f'hyperframes@{HF_VERSION}','render','--quality',c['quality'],
            '--fps',str(c['fps']),'--output',str(output)],out,'render.log')
    report=json.loads(command(['ffprobe','-v','error','-show_streams','-show_format','-of','json',output]))
    v=next(s for s in report['streams'] if s['codec_type']=='video')
    fps=v['r_frame_rate'].split('/');actual_fps=float(fps[0])/float(fps[1])
    if [v['width'],v['height']]!=c['canvas'] or abs(float(report['format']['duration'])-info['duration'])>.15 or abs(actual_fps-c['fps'])>.01:
        raise ConfigError('Rendered dimensions, fps or duration differ from configuration; inspect render.log')
    if c['sound'] and not any(s['codec_type']=='audio' for s in report['streams']):
        raise ConfigError('Requested printer sound but output has no audio stream')
    (out/'render-report.json').write_text(json.dumps({'width':v['width'],'height':v['height'],
        'fps':actual_fps,'duration':float(report['format']['duration']),'size':int(report['format']['size'])},indent=2))
    if c['export_cover']:
        command(['ffmpeg','-y','-v','error','-ss',max(0,info['duration']-.2),'-i',output,'-frames:v','1',out/'renders/cover.jpg'])
    return str(output)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('doctor',help='Check local dependencies without installing anything')
    sub.add_parser('setup',help='Install locked JavaScript dependency using npm ci')
    for cmd in ('build','render','preview'):
        p=sub.add_parser(cmd,help={'build':'Create a project','render':'Build, check and export MP4','preview':'Build and open local HyperFrames preview'}[cmd])
        p.add_argument('inputs',nargs='*');p.add_argument('--config',type=Path)
        p.add_argument('--output',type=Path,required=True);p.add_argument('--revision',action='store_true')
        p.add_argument('--aspect',choices=['4:3','9:16','1:1','3:4','16:9'])
        p.add_argument('--width',help='Content box width, e.g. 90%% or 0.9')
        p.add_argument('--duration',type=float);p.add_argument('--fps',type=int)
        p.add_argument('--ending',choices=['hold','row','grid','stack','flyout','snowflake'])
        p.add_argument('--style',choices=['modern','retro','instant']);p.add_argument('--color')
        p.add_argument('--background');p.add_argument('--fit',choices=['contain','cover'])
        p.add_argument('--feed',choices=['smooth','stepped']);p.add_argument('--border',type=float)
        p.add_argument('--camera-width',help='Instant camera width, e.g. 90%%');p.add_argument('--machine-height',type=float);p.add_argument('--cover')
        p.add_argument('--no-timestamp',action='store_true',help='Disable printed date/time postmark')
        p.add_argument('--silent',action='store_true');p.add_argument('--source-audio',action='store_true')
        p.add_argument('--sound-volume',type=float);p.add_argument('--sound-file')
        p.add_argument('--no-cache',action='store_true')
        p.add_argument('--quality',choices=['draft','standard','high'])
    args=parser.parse_args()
    try:
        if args.command=='doctor':
            d=doctor();print(json.dumps(d,indent=2));return 0 if d['ok'] else 1
        if args.command=='setup':
            if not shutil.which('npm'):raise ConfigError('Install Node >=22 with npm first')
            subprocess.run(['npm','ci','--ignore-scripts','--no-audit','--no-fund'],cwd=ROOT,check=True)
            print('JS dependency ready. Python dependencies: pip install -r requirements.txt');return 0
        d=doctor()
        if not d['ok']:raise ConfigError(d['help']+'\n'+json.dumps(d))
        c=task_config(args);out=destination(args.output,args.revision);out.parent.mkdir(parents=True,exist_ok=True)
        temp=Path(tempfile.mkdtemp(prefix='.printer-build-',dir=out.parent))
        cache=Path(os.environ.get('PRINTER_EFFECT_CACHE',str(Path.home()/'.cache/printer-effect')))
        try:
            report=build(c,temp,cache)
            temp.rename(out)
        except BaseException:
            shutil.rmtree(temp,ignore_errors=True);raise
        result={'project':str(out),'duration':report['duration'],'notes':report['notes']}
        if args.command=='render':result['video']=render_project(out,c)
        elif args.command=='preview':
            logged(['npx','--yes',f'hyperframes@{HF_VERSION}','check'],out,'check.log')
            subprocess.run(['npx','--yes',f'hyperframes@{HF_VERSION}','preview','--background'],cwd=out,check=True)
        print(json.dumps(result,ensure_ascii=False,indent=2));return 0
    except (ConfigError,ValueError,KeyError,OSError,subprocess.CalledProcessError) as e:
        print('Printer Effect error: '+str(e),file=sys.stderr);return 2

if __name__=='__main__':sys.exit(main())
