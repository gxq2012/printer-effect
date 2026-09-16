import sys,unittest,tempfile,wave
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from printer_effect.config import normalize,PRESETS,ConfigError
from printer_effect.timeline import plan
from printer_effect.layout import layout
from printer_effect.instant import shutter
ROOT=Path(__file__).resolve().parents[1]
class InstantTests(unittest.TestCase):
 def config(self,**kw):return normalize(dict(inputs=[str(ROOT/'examples/media/card-01.png')],style='instant',**kw))
 def test_capture_development_and_video_sequence(self):
  with tempfile.TemporaryDirectory() as d:
   v=Path(d)/'source.mp4';v.touch()
   c=normalize({'style':'instant','inputs':[{'path':str(v),'play_seconds':3}],'duration':18})
   t=plan(c);e=t['prints'][0]
   self.assertAlmostEqual(e['start']-e['shot_at'],.45)
   self.assertAlmostEqual(e['develop_end']-e['print_end'],2.5)
   self.assertGreater(e['play_at'],e['develop_end'])
   self.assertEqual(t['duration'],18)
 def test_slot_and_page_bounds_all_ratios(self):
  for ratio in PRESETS:
   c=self.config(aspect_ratio=ratio);g=layout(c,[{'width':1000,'height':1500}]);card=g['cards'][0]
   self.assertLessEqual(card['width'],c['machine_height']*724/650)
   self.assertLessEqual(card['top']+card['height']-g.get('camera_lift',0),g['design_height'])
 def test_insufficient_development_budget(self):
  with self.assertRaises(ConfigError):self.config(duration=3)
 def test_shutter_audio_not_silent(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'click.wav';shutter(p)
   with wave.open(str(p)) as f:
    self.assertAlmostEqual(f.getnframes()/f.getframerate(),.35)
    self.assertTrue(any(f.readframes(f.getnframes())))

 def test_wider_portrait_and_explicit_width(self):
  c=self.config();self.assertAlmostEqual(c['machine_height']/0.65/1440,.9)
  c=self.config(camera_width=.8);self.assertAlmostEqual(c['machine_height']/0.65/1440,.8)
  with self.assertRaises(ConfigError):self.config(camera_width=1.1)
 def test_pastel_photo_assets(self):
  from printer_effect.config import PHOTO_ASSETS
  from PIL import Image
  for name in ['pink','white','matcha','light-blue','粉色','白色','抹茶','淡蓝色']:
   c=self.config(color=name);self.assertEqual(c['camera_appearance'],'photo')
   with Image.open(ROOT/'assets'/PHOTO_ASSETS[c['color']]) as im:
    self.assertEqual(im.mode,'RGBA');self.assertEqual(im.getchannel('A').getextrema(),(0,255))

 def test_landscape_film_has_no_wide_empty_sides(self):
  c=self.config(aspect_ratio='4:3',camera_width=.9)
  card=layout(c,[{'width':1600,'height':1067}])['cards'][0]
  self.assertAlmostEqual((card['width']-2*(c['paper_border']+1))/card['content_height'],1600/1067)

 def test_large_camera_paper_matches_slot_and_lifts(self):
  c=self.config(aspect_ratio='4:3',camera_width=.9)
  g=layout(c,[{'width':1600,'height':1067}]);card=g['cards'][0]
  self.assertGreater(card['width'],c['machine_height']/0.65*.7)
  self.assertGreater(g['camera_lift'],300)
  self.assertLessEqual(card['top']+card['height']-g['camera_lift'],g['design_height'])
