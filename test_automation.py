import json, tempfile, unittest, time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch, MagicMock
import numpy as np
import engine,store,story_feed,language_qa
import test_system
class AutomationTests(unittest.TestCase):
 def test_encoded_hindi_verification_rejects_silence_or_wrong_text(self):
  expected='मेरी गेंद पेड़ पर फँस गई है।'
  for actual,passed in [(expected,True),('',False),('आज मौसम बहुत अच्छा है।',False)]:
   recognizer=MagicMock();recognizer.transcribe.return_value=([SimpleNamespace(text=actual)],None)
   report=language_qa.verify_samples(np.zeros(16000,dtype='float32'),[{'narration':expected}],[1],recognizer)
   self.assertEqual(report['passed'],passed)
   self.assertNotIn('initial_prompt',recognizer.transcribe.call_args.kwargs)
 def test_every_line_must_be_understood(self):
  text='गोलू और तारा आज ढोल बजा रहे हैं।'
  recognizer=MagicMock();recognizer.transcribe.side_effect=[([SimpleNamespace(text=text)],None),([],None)]
  self.assertFalse(language_qa.verify_samples(np.zeros(32000,dtype='float32'),[{'narration':text}]*2,[1,1],recognizer)['passed'])
 def test_feed_schema_and_duplicate_scripts(self):
  feed=json.loads(Path('story_feed.json').read_text())
  plans=story_feed.validate(feed)
  self.assertEqual(len(plans),len(feed))
  self.assertTrue(all(p['automated_language_review'] and p['made_for_kids'] for p in plans))
  duplicate=dict(feed[0],id='hi-renamed-duplicate')
  with self.assertRaises(ValueError):story_feed.validate([feed[0],duplicate])
  feed[0]['scenes'][0]['setting']='remote-code'
  with self.assertRaises(ValueError):story_feed.validate(feed)
 def test_feed_offline_fallback_and_bounded_size(self):
  with tempfile.TemporaryDirectory() as tmp,patch.object(story_feed,'ROOT',Path(tmp)),patch.object(story_feed,'_last_fetch',None),patch('urllib.request.urlopen',side_effect=OSError('offline')):
   self.assertGreater(len(story_feed.plans(refresh=True)),0)
 def test_language_gate_cannot_be_bypassed_by_publication_flag(self):
  p=story_feed.plans()[0]
  self.assertFalse(engine.publishable(p,{'dialogue_validated':True}))
  self.assertTrue(engine.publishable(p,{'dialogue_validated':True,'language_validated':True}))

class SchedulingTests(unittest.TestCase):
 setUp=test_system.SystemTests.setUp
 tearDown=test_system.SystemTests.tearDown
 def test_empty_supply_does_not_consume_daily_slot(self):
  store.set_setting('daily_enabled',True)
  with patch.dict('os.environ',{'SHORTS_CONTENT_MODE':'cartoon','SHORTS_FEED_ENABLED':'1'}),patch.object(engine,'datetime') as clock,patch.object(engine,'enqueue_next',return_value=(None,False)):
   clock.now.return_value=SimpleNamespace(hour=10,date=lambda:SimpleNamespace(isoformat=lambda:'2026-10-30'))
   engine.tick();engine.tick()
  self.assertIsNone(store.setting('last_scheduled_v2'))
  with store.database() as c:self.assertEqual(c.execute("SELECT count(*) FROM events WHERE action='story_supply_empty'").fetchone()[0],1)
 def test_daily_feed_slot_survives_restart_and_catches_up(self):
  store.set_setting('daily_enabled',True)
  with patch.dict('os.environ',{'SHORTS_CONTENT_MODE':'cartoon','SHORTS_FEED_ENABLED':'1'}),patch.object(engine,'datetime') as clock,patch('story_feed.plans',return_value=story_feed.plans()),patch.object(engine,'render',return_value={'dialogue_validated':True,'language_validated':True}):
   clock.now.return_value=SimpleNamespace(hour=10,date=lambda:SimpleNamespace(isoformat=lambda:'2026-10-30'))
   engine.tick();engine.recover();engine.tick()
   self.assertEqual(store.setting('last_scheduled_v2'),'2026-10-30')
   with store.database() as c:self.assertEqual(c.execute('SELECT count(*) FROM jobs').fetchone()[0],1)
 def test_renamed_script_cannot_republish(self):
  plans=story_feed.plans();engine.enqueue(plans[0],'story:old-id')
  with patch.dict('os.environ',{'SHORTS_CONTENT_MODE':'cartoon','SHORTS_FEED_ENABLED':'1'}),patch('story_feed.plans',return_value=plans[:1]):
   self.assertEqual(engine.enqueue_next(),(None,False))

 def test_atomic_slot_prevents_duplicate_when_marker_lost(self):
  plans=story_feed.plans()
  first,_=engine.enqueue(plans[0],'story:'+plans[0]['topic'],scheduled_date='2026-10-30')
  second,created=engine.enqueue(plans[1],'story:'+plans[1]['topic'],scheduled_date='2026-10-30')
  self.assertEqual(first,second);self.assertFalse(created)

 def test_confirmed_remote_id_is_retained_on_verification_failure(self):
  engine.enqueue(story_feed.plans()[0],'story:pending')
  with store.database() as c:jid=c.execute('SELECT id FROM jobs').fetchone()[0]
  engine.remember_upload(jid,'remote123')
  with store.database() as c:
   c.execute("UPDATE jobs SET status='upload_unknown' WHERE id=?",(jid,))
  api=MagicMock();api.videos.return_value.list.return_value.execute.return_value={'items':[{'status':{'privacyStatus':'public'}}]}
  with patch('youtube.client',return_value=api),patch.object(engine,'_last_reconcile',None):engine.reconcile_known_uploads()
  with store.database() as c:row=c.execute('SELECT status,youtube_id FROM jobs').fetchone()
  self.assertEqual(tuple(row),('published','remote123'))

 def test_daily_failed_story_falls_back_but_never_unknown_upload(self):
  plans=story_feed.plans()
  first,_=engine.enqueue(plans[0],'story:'+plans[0]['topic'],scheduled_date='2026-10-30')
  with store.database() as c:c.execute("UPDATE jobs SET status='upload_unknown' WHERE id=?",(first,))
  self.assertFalse(engine.enqueue(plans[1],'story:'+plans[1]['topic'],scheduled_date='2026-10-30')[1])
  with store.database() as c:c.execute("UPDATE jobs SET status='failed' WHERE id=?",(first,))
  second,created=engine.enqueue(plans[1],'story:'+plans[1]['topic'],scheduled_date='2026-10-30')
  self.assertTrue(created);self.assertNotEqual(first,second)
  with store.database() as c:c.execute("UPDATE jobs SET status='failed' WHERE id=?",(second,))
  third,_=engine.enqueue(plans[2],'story:'+plans[2]['topic'],scheduled_date='2026-10-30')
  with store.database() as c:c.execute("UPDATE jobs SET status='failed' WHERE id=?",(third,))
  self.assertFalse(engine.enqueue(plans[3],'story:'+plans[3]['topic'],scheduled_date='2026-10-30')[1])
