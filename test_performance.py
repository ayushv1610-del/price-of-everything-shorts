import os,unittest
from unittest.mock import MagicMock,patch
import performance,store,engine
from catalog import CATALOG,plan_for
import test_system

class PerformanceTests(unittest.TestCase):
    setUp=test_system.SystemTests.setUp
    tearDown=test_system.SystemTests.tearDown
    def seed(self):
        jid,_=engine.enqueue(plan_for(CATALOG[0]),'metrics-test')
        with store.database() as c:c.execute("UPDATE jobs SET status='published',youtube_id='public1' WHERE id=?",(jid,))
    def test_public_statistics_are_read_only_and_throttled(self):
        self.seed();api=MagicMock()
        api.videos.return_value.list.return_value.execute.return_value={'items':[{'id':'public1','snippet':{'channelId':'owner'},'status':{'privacyStatus':'public'},'statistics':{'viewCount':'0','likeCount':'2'}}]}
        with patch.dict(os.environ,{'YOUTUBE_CHANNEL_ID':'owner'}),patch('youtube.client',return_value=api):
            performance.refresh();performance.refresh()
        data=performance.summary()
        self.assertEqual(data['views_reported'],0)
        self.assertEqual(data['videos'][0]['comments'],None)
        self.assertFalse(data['retention_available'])
        api.videos.return_value.list.assert_called_once()
        api.videos.return_value.insert.assert_not_called()
        with store.database() as c:self.assertEqual(c.execute('SELECT status FROM jobs').fetchone()[0],'published')
    def test_private_and_foreign_results_never_exposed(self):
        self.seed();api=MagicMock()
        api.videos.return_value.list.return_value.execute.return_value={'items':[{'id':'public1','snippet':{'channelId':'foreign'},'status':{'privacyStatus':'public'},'statistics':{'viewCount':'999'}}]}
        with patch.dict(os.environ,{'YOUTUBE_CHANNEL_ID':'owner'}),patch('youtube.client',return_value=api):performance.refresh()
        self.assertEqual(performance.summary()['videos'],[])
        self.assertEqual(performance.summary()['status'],'partial')
    def test_failure_keeps_dated_measurement_and_marks_unavailable(self):
        self.seed();store.set_setting('public_performance',{'status':'ok','checked_at':1,'views_reported':14})
        with patch.dict(os.environ,{'YOUTUBE_CHANNEL_ID':'owner'}),patch('youtube.client',side_effect=RuntimeError('secret must not be stored')):performance.refresh()
        self.assertEqual(performance.summary()['views_reported'],14)
        self.assertEqual(performance.summary()['status'],'unavailable')
        self.assertNotIn('secret',str(performance.summary()))
