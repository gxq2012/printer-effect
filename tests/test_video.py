"""Integration regression: actual frozen frames, motion, duration and source audio."""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from printer_effect.config import normalize
from printer_effect.timeline import plan
from printer_effect.media import prepare,probe,command

@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'FFmpeg integration test')
class VideoTests(unittest.TestCase):
    def test_video_freezes_then_plays(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);source=p/'motion.mp4';assets=p/'assets';assets.mkdir()
            command(['ffmpeg','-y','-v','error','-f','lavfi','-i','testsrc2=size=160x120:rate=24:duration=2',
                     '-f','lavfi','-i','sine=frequency=440:duration=2','-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac',source])
            c=normalize({'inputs':[str(source)],'duration':10,'fps':24,'sound':False,'source_audio':True})
            tm=plan(c);m=prepare(c,tm,assets,p/'cache')[0];v=assets/m['name']
            self.assertAlmostEqual(probe(v)['duration'],10,places=1)
            self.assertTrue((assets/m['audio_name']).is_file())
            def frame(t):
                return subprocess.check_output(['ffmpeg','-v','error','-ss',str(t),'-i',str(v),'-frames:v','1',
                    '-vf','scale=40:30','-pix_fmt','gray','-f','rawvideo','-'])
            start=tm['prints'][0]['play_at']
            a,b=frame(.5),frame(start-.2)
            self.assertEqual(len(a),1200)
            self.assertLess(sum(abs(x-y) for x,y in zip(a,b))/len(a),1)
            a,b=frame(start+.3),frame(start+1.2)
            self.assertGreater(sum(abs(x-y) for x,y in zip(a,b))/len(a),3)
