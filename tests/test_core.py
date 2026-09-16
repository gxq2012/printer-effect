import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from printer_effect.config import normalize,ConfigError,PRESETS
from printer_effect.layout import layout,pose,grid_positions
from printer_effect.timeline import plan
from printer_effect.media import normalize_image
ROOT=Path(__file__).resolve().parents[1]

class PrinterTests(unittest.TestCase):
    def test_exif_orientation_and_original_untouched(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/'photo.jpg';target=Path(d)/'normal.png'
            exif=Image.Exif();exif[274]=6
            Image.new('RGB',(80,40),'red').save(source,exif=exif)
            original=source.read_bytes()
            normalize_image(source,target)
            with Image.open(target) as im:self.assertEqual(im.size,(40,80))
            self.assertEqual(source.read_bytes(),original)
    def test_icc_transparency_preserved(self):
        from PIL import Image,ImageCms
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/'alpha.png';target=Path(d)/'normal.png'
            profile=ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
            Image.new('RGBA',(40,40),(100,120,140,80)).save(source,icc_profile=profile)
            normalize_image(source,target)
            with Image.open(target) as im:self.assertEqual(im.getpixel((0,0))[3],80)
    def config(self,**kw):
        return normalize(dict(inputs=[str(ROOT/'examples/media/card-01.png')],**kw))
    def test_duration_is_exact(self):
        for ending in ['hold','grid','stack','flyout','snowflake']:
            c=self.config(duration=15,ending=ending)
            self.assertAlmostEqual(plan(c)['duration'],15)
    def test_all_ratios_centered(self):
        for ratio in PRESETS:
            c=self.config(aspect_ratio=ratio)
            g=layout(c,[{'width':1200,'height':800}])
            self.assertEqual(g['tray_left'],g['machine_left'])
            self.assertEqual(g['tray_width'],g['machine_width'])
            card=g['cards'][0]
            self.assertAlmostEqual(card['left']+card['width']/2,720)
            self.assertLessEqual(card['top']+card['height'],g['design_height'])
    def test_exact_content_width_4x3(self):
        g=layout(self.config(aspect_ratio='4:3'),[{'width':1200,'height':800}])
        self.assertAlmostEqual(g['cards'][0]['actual_width_ratio'],.9)
    def test_tall_image_reports_actual_fit(self):
        g=layout(self.config(),[{'width':900,'height':1600}])
        self.assertLess(g['cards'][0]['actual_width_ratio'],.9)
    def test_invalid_numbers(self):
        for value in [True,float('nan'),float('inf'),-1]:
            with self.assertRaises(ConfigError):self.config(duration=value)
    def test_unknown_field(self):
        with self.assertRaises(ConfigError):self.config(duraton=15)
    def test_conflicting_timing(self):
        with self.assertRaises(ConfigError):self.config(duration=15,print_seconds=5)
    def test_invalid_paper_width(self):
        with self.assertRaises(ConfigError):layout(self.config(content_width=.94,paper_border=60),[{'width':1200,'height':800}])
    def test_missing_file(self):
        with self.assertRaises(ConfigError):normalize({'inputs':['missing-xyz.png']})
    def test_natural_sort_cover(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            for name in ['10.png','2.png','1.png','.hidden.png']:(p/name).touch()
            c=normalize({'inputs':[d],'cover':str(p/'2.png')})
            self.assertEqual([Path(i['path']).name for i in c['inputs']],['2.png','1.png','10.png'])
    def test_paginate_many(self):
        c=normalize({'inputs':[str(ROOT/'examples/media/card-01.png')]*20,'ending':'snowflake'})
        self.assertEqual(c['ending'],'grid')
        self.assertAlmostEqual(plan(c)['duration'],c['computed_duration'])
    def test_short_duration_rejected(self):
        with self.assertRaises(ConfigError):self.config(duration=2,ending='flyout')
    def test_grid_rotated_bounds(self):
        card={'width':1330,'height':2013,'left':55,'top':333}
        for angle in [-25,0,25]:
            p=pose(card,720,540,600,800,angle)
            import math
            r=math.radians(angle)
            self.assertLessEqual(p['scale']*(1330*abs(math.cos(r))+2013*abs(math.sin(r))),600.00001)
            self.assertLessEqual(p['scale']*(1330*abs(math.sin(r))+2013*abs(math.cos(r))),800.00001)
    def test_relative_paths(self):
        c=normalize({'inputs':['media/card-01.png']},ROOT/'examples')
        self.assertTrue(Path(c['inputs'][0]['path']).is_absolute())
    def test_custom_canvas_precedence(self):
        c=self.config(canvas=[1200,900],aspect_ratio='custom')
        self.assertEqual(c['canvas'],[1200,900])
    def test_play_after_print(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'test.mp4';p.touch()
            c=normalize({'inputs':[{'path':str(p),'play_seconds':3}],'duration':15})
            tm=plan(c);e=tm['prints'][0]
            self.assertGreater(e['play_at'],e['print_end'])
            self.assertAlmostEqual(e['move_at']-e['play_at'],3)
            self.assertAlmostEqual(tm['duration'],15)

if __name__=='__main__':unittest.main()
