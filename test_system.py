import os, tempfile, json, unittest
from pathlib import Path
from unittest.mock import patch
os.environ['SHORTS_WORKER_ENABLED']='0'
os.environ['SHORTS_COOKIE_SECURE']='0'
import store, app, engine
from catalog import CATALOG,plan_for
from fastapi.testclient import TestClient
class SystemTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)/'output';self.root.mkdir()
  self.patches=[patch.object(store,'DB',str(Path(self.tmp.name)/'test.db')),patch.object(store,'ROOT',self.root),patch.object(app,'ROOT',self.root),patch.object(engine,'ROOT',self.root),patch.object(app,'TOKEN','test-secret')]
  for p in self.patches:p.start()
  self.client=TestClient(app.app);self.auth={'Authorization':'Bearer test-secret'}
  store.set_setting('daily_enabled',False)
 def tearDown(self):
  for p in reversed(self.patches):p.stop()
  self.tmp.cleanup()
 def test_auth_and_health(self):
  self.assertEqual(self.client.get('/api/jobs').status_code,401)
  self.assertEqual(self.client.post('/api/produce',json={}).status_code,401)
  self.assertEqual(self.client.get('/health').json()['publishing_enabled'],False)
  self.assertEqual(self.client.get('/ready').status_code,200)
  self.assertEqual(self.client.post('/api/login',json={'token':'bad'}).status_code,401)
  self.assertEqual(self.client.post('/api/login',json={'token':'test-secret'}).status_code,200)
  self.assertEqual(self.client.get('/api/jobs').status_code,200)
  self.assertEqual(self.client.post('/api/produce',json={},headers={'Origin':'https://evil.example'}).status_code,403)
 def test_unique_and_catalog_exhaustion(self):
  ids=[engine.enqueue_next()[0] for _ in CATALOG]
  self.assertEqual(len(set(ids)),len(CATALOG));self.assertEqual(engine.enqueue_next(),(None,False))
  self.assertFalse(engine.enqueue(plan_for(CATALOG[0]),'topic:'+CATALOG[0]['slug'])[1])
 def test_render_retry_and_recovery(self):
  jid,_=engine.enqueue_next()
  with patch.object(engine,'render',side_effect=RuntimeError('test encoder failure')):
   for _ in range(3):self.assertTrue(engine.tick())
  self.assertEqual(app.get_job(jid)['status'],'failed')
  self.assertEqual(app.get_job(jid)['attempts'],3)
  self.assertEqual(self.client.post(f'/api/jobs/{jid}/retry',json={},headers=self.auth).status_code,200)
  with store.database() as c:c.execute("UPDATE jobs SET status='rendering'")
  engine.recover();self.assertEqual(app.get_job(jid)['status'],'queued')
  with store.database() as c:c.execute("UPDATE jobs SET status='uploading'")
  engine.recover();self.assertEqual(app.get_job(jid)['status'],'upload_unknown')
 def test_no_public_endpoint_or_unapproved_upload(self):
  jid,_=engine.enqueue_next()
  self.assertEqual(self.client.post(f'/api/jobs/{jid}/upload-private',json={},headers=self.auth).status_code,409)
  self.assertEqual(self.client.post(f'/api/jobs/{jid}/publish',json={},headers=self.auth).status_code,404)
  self.assertEqual(self.client.get(f'/api/jobs/{jid}/assets/google-token.json',headers=self.auth).status_code,404)
 def test_daily_idempotency(self):
  store.set_setting('daily_enabled',True)
  with patch.object(engine,'render',return_value={'test':True}):
   engine.tick();engine.tick()
  self.assertEqual(len(self.client.get('/api/jobs',headers=self.auth).json()),1)
 def test_research_required(self):
  with self.assertRaises(ValueError):engine.enqueue({'fact_checked':False},'bad')
 def test_google_state_is_single_use_and_pkce_enabled(self):
  import youtube
  with patch.dict(os.environ,{'GOOGLE_CLIENT_ID':'test-client','GOOGLE_CLIENT_SECRET':'test-secret','SHORTS_PUBLIC_URL':'https://studio.example'}):
   f=youtube.flow();url,state=f.authorization_url()
   self.assertTrue(f.code_verifier);self.assertIn('code_challenge=',url)
  with self.assertRaises(ValueError):youtube.callback('invalid-state','code')
  with store.database() as c:c.execute('INSERT INTO settings VALUES(?,?)',('oauth:expired',json.dumps({'expires':0,'verifier':'x'})))
  with self.assertRaises(ValueError):youtube.callback('expired','code')
  with store.database() as c:self.assertIsNone(c.execute("SELECT value FROM settings WHERE key='oauth:expired'").fetchone())
 def test_third_interrupted_attempt_becomes_failed(self):
  jid,_=engine.enqueue_next()
  with store.database() as c:c.execute("UPDATE jobs SET status='rendering',attempts=3")
  engine.recover();self.assertEqual(app.get_job(jid)['status'],'failed')
 def test_legacy_draft_preserved(self):
  r=self.client.post('/api/drafts',headers=self.auth,json={'title':'Legacy draft','script':'A draft remains available without overwriting earlier content.'})
  self.assertEqual(r.status_code,201);self.assertEqual(len(self.client.get('/api/drafts',headers=self.auth).json()),1)
if __name__=='__main__':unittest.main()
