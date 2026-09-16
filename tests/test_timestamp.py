import unittest,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from printer_effect.config import normalize,ConfigError
ROOT=Path(__file__).resolve().parents[1]
class TimestampTests(unittest.TestCase):
 def config(self,**kw):return normalize(dict(inputs=[str(ROOT/'examples/media/card-01.png')],**kw))
 def test_generated_local_time_and_reproducible_override(self):
  c=self.config();self.assertTrue(c['timestamp'])
  self.assertRegex(c['timestamp_text'],r'^\d{4}\.\d{2}\.\d{2}\|\d{2}:\d{2}:\d{2}$')
  self.assertEqual(self.config(timestamp_text=c['timestamp_text'])['timestamp_text'],c['timestamp_text'])
 def test_disable_and_invalid_values(self):
  self.assertFalse(self.config(timestamp=False)['timestamp'])
  with self.assertRaises(ConfigError):self.config(timestamp='yes')
  with self.assertRaises(ConfigError):self.config(timestamp_text=100)

 def test_legacy_offset_converts_to_beijing_without_label(self):
  c=self.config(timestamp_text='2026.09.15|20:00:00|UTC+0000')
  self.assertEqual(c['timestamp_text'],'2026.09.16|04:00:00')
 def test_default_ignores_host_timezone(self):
  import os,time
  from datetime import datetime,timezone,timedelta
  from unittest.mock import patch
  with patch.dict(os.environ,{'TZ':'America/Los_Angeles'}):
   if hasattr(time,'tzset'):time.tzset()
   try:
    c=self.config();actual=datetime.strptime(c['timestamp_text'],'%Y.%m.%d|%H:%M:%S').replace(tzinfo=timezone(timedelta(hours=8)))
    self.assertLess(abs((actual-datetime.now(timezone.utc)).total_seconds()),2)
   finally:
    pass
  if hasattr(time,'tzset'):time.tzset()
