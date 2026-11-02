import json,math,tempfile,unittest,wave
from pathlib import Path
from unittest.mock import patch
import numpy as np
from PIL import Image
import renderer

class PacingTests(unittest.TestCase):
 def test_timing_keeps_complete_lines_and_overall_minimum(self):
  for fps in (24,30):
   for count in range(3,13):
    for speech in (.3,1,2.3,3.1,5):
     duration=renderer.scene_frames(speech,count,fps)/fps
     self.assertGreaterEqual(duration,speech+.22-1e-8)
     self.assertGreaterEqual(duration*count,12)
     self.assertAlmostEqual(duration*fps,round(duration*fps))
 def test_short_lines_lose_padding_but_long_lines_keep_breath(self):
  self.assertEqual(renderer.scene_frames(1,5,30),72)
  self.assertEqual(renderer.scene_frames(4,5,30),127)
  for invalid in (-1,float('nan'),float('inf')):
   with self.assertRaises(ValueError):renderer.scene_frames(invalid,5,30)
 def test_real_mux_preserves_all_five_dialogue_intervals(self):
  def voice(text,speaker,path,language):
   rate=24000;t=np.arange(rate)/rate
   samples=(np.sin(2*np.pi*440*t)*6000).astype('<i2')
   with wave.open(str(path),'wb') as w:
    w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate);w.writeframes(samples.tobytes())
   return {'duration':1,'rms':.12}
  plan={'voice_engine':'kokoro','language':'hi','sources':[],'title':'Pacing integration',
        'scenes':[{'speaker':'golu','narration':'नमस्ते दोस्त','caption':'नमस्ते'}]*5}
  with tempfile.TemporaryDirectory() as tmp,patch('kokoro_voice.synthesize',side_effect=voice),patch.object(renderer,'W',72),patch.object(renderer,'H',128),patch.object(renderer,'FPS',30),patch.object(renderer,'frame',return_value=Image.new('RGB',(72,128),'blue')):
   qa=renderer.render(plan,Path(tmp))
   self.assertTrue(qa['full_decode']);self.assertEqual(qa['voice_lines'],5)
   self.assertGreaterEqual(qa['duration'],12);self.assertLess(qa['duration'],12.3)
   self.assertEqual(len(qa['encoded_audio_rms']),5)
   self.assertTrue(all(level>.003 for level in qa['encoded_audio_rms']))
   metadata=renderer.probe(Path(tmp)/'video.mp4')
   audio=next(s for s in metadata['streams'] if s['codec_type']=='audio')
   self.assertGreaterEqual(float(audio['duration']),11.9)
   subtitles=(Path(tmp)/'captions.srt').read_text()
   self.assertIn('00:00:12,000',subtitles)
