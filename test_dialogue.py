import math,tempfile,wave,struct,unittest
from pathlib import Path
from dialogue import inspect_voice,prepare_dialogue,DialogueError
class DialogueTests(unittest.TestCase):
 def audio(self,kind):
  p=Path(self.tmp.name)/'voice.wav'
  with wave.open(str(p),'wb') as w:
   w.setparams((1,2,16000,0,'NONE','not compressed'))
   vals=[0 if kind=='silent' else 32767 if kind=='clipped' else int(4000*math.sin(i*.15)) for i in range(16000)]
   w.writeframes(struct.pack('<'+'h'*len(vals),*vals))
  return p
 def setUp(self):self.tmp=tempfile.TemporaryDirectory()
 def tearDown(self):self.tmp.cleanup()
 def test_rejects_silent_audio(self):
  with self.assertRaisesRegex(DialogueError,'silent'):inspect_voice(self.audio('silent'))
 def test_rejects_clipping(self):
  with self.assertRaisesRegex(DialogueError,'clipped'):inspect_voice(self.audio('clipped'))
 def test_accepts_decodable_non_silent_pcm(self):
  self.assertEqual(inspect_voice(self.audio('tone'))['duration'],1)
 def test_missing_voice_never_falls_back(self):
  with self.assertRaisesRegex(DialogueError,'no fallback'):prepare_dialogue([{'speaker':'fox','narration':'Hello!'}],{})
 def test_old_robotic_provider_is_rejected(self):
  with self.assertRaisesRegex(DialogueError,'Rejected'):prepare_dialogue([{'speaker':'fox','narration':'Hello!'}],{'0':{'provider':'flite','text':'Hello!','path':str(self.audio('tone'))}})
