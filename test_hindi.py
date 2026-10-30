import unittest, os, tempfile
from unittest.mock import patch, MagicMock
from pathlib import Path
from cartoon_stories import STORIES, plan_for_story
import kokoro_voice
class HindiTests(unittest.TestCase):
 def test_next_episode_is_new_hindi_cast_and_held(self):
  p=plan_for_story(STORIES[0])
  self.assertEqual(p['language'],'hi');self.assertEqual(p['cast'],'jungle-friends')
  self.assertFalse(p['publication_ready']);self.assertTrue(p['language_review_required'])
  self.assertEqual({s['speaker'] for s in p['scenes']},{'golu','tara','mithu'})
  self.assertTrue(all(any('\u0900'<=c<='\u097f' for c in s['narration']) for s in p['scenes']))
 def test_hindi_never_uses_an_english_voice(self):
  for speaker,language,text in [('fox','hi','नमस्ते'),('golu','en','Hello'),('golu','hi','Namaste')]:
   with self.assertRaises(ValueError):kokoro_voice.synthesize(text,speaker,'/tmp/never.wav',language)
 def test_synthesis_selects_hindi_phonemizer_and_voice(self):
  fake=MagicMock();fake.create.return_value=([.1]*24000,24000)
  with patch.object(kokoro_voice,'_ENGINE',fake),patch('soundfile.write'),patch('dialogue.inspect_voice',return_value={'duration':1}):
   kokoro_voice.synthesize('मेरी लाल पतंग कहाँ गई?','golu','unused.wav','hi')
  self.assertEqual(fake.create.call_args.kwargs['lang'],'hi')
  self.assertEqual(fake.create.call_args.kwargs['voice'],'hm_omega')
 def test_missing_or_rejected_voice_fails_before_media_work(self):
  import renderer
  for voice in [None,'flite','unknown']:
   with patch.object(renderer,'run') as run:
    with self.assertRaises(ValueError):renderer.render({'voice_engine':voice},'/tmp/never-rendered-short')
    run.assert_not_called()
if __name__=='__main__':unittest.main()

