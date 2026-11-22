import datetime as dt
import importlib.util
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from daily import next_slot, existing_upload
from clip_approved import validate


class ScheduleTests(unittest.TestCase):
    def test_eastern_slots_winter(self):
        now=dt.datetime(2026,11,23,10,17,tzinfo=dt.timezone.utc)
        self.assertEqual(next_slot('vicecity',0,now).hour,17)
        self.assertEqual(next_slot('vicecity',1,now).hour,23)
        self.assertEqual(next_slot('vicecity',2,now),dt.datetime(2026,11,24,2,tzinfo=dt.timezone.utc))
        self.assertEqual(next_slot('kidz',0,now).hour,20)

    def test_eastern_summer_and_weekend(self):
        now=dt.datetime(2027,6,5,10,17,tzinfo=dt.timezone.utc)
        self.assertEqual(next_slot('vicecity',0,now).hour,16)
        self.assertEqual(next_slot('kidz',0,now).hour,13)

    def test_original_weekend_generation_misses_same_day(self):
        now=dt.datetime(2026,11,28,14,17,tzinfo=dt.timezone.utc)
        self.assertEqual(next_slot('kidz',0,now).date(),dt.date(2026,11,29))

    def test_unapproved_clipping_rejected(self):
        with self.assertRaises(ValueError):
            validate({'media_url':'https://example.com/test.mp4','start_seconds':0,'end_seconds':30})
        with self.assertRaises(ValueError):
            validate({'media_url':'https://www.youtube.com/watch?v=test','rights_confirmed':True,'rights_note':'mine','end_seconds':30})

    def test_upload_marker_recovery(self):
        class Service:
            def playlistItems(self): return self
            def list(self,**kwargs): return self
            def execute(self): return {'items':[{'snippet':{'description':'Automation slot: example'},'contentDetails':{'videoId':'existing'}}]}
        channel={'contentDetails':{'relatedPlaylists':{'uploads':'list'}}}
        self.assertEqual(existing_upload(Service(),channel,'Automation slot: example'),'existing')
        self.assertIsNone(existing_upload(Service(),channel,'Automation slot: different'))

if __name__=='__main__':
    unittest.main()
