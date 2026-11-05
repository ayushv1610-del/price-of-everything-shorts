import unittest
from unittest.mock import patch
import jungle_cartoon as cartoon

class ActionAttentionTests(unittest.TestCase):
 def test_all_characters_follow_prop_through_scene_boundaries(self):
  for setting,position in [('kite',lambda i,p:cartoon.kite_position(i,7,p)),('ball',cartoon.ball_position)]:
   for i in range(3,7):
    for p in (0,.25,.5,.75,1):
     for kind in ('golu','tara','mithu'):
      self.assertEqual(cartoon.attention_target(setting,i,7,p,'tara',kind),position(i,p))

 def test_dialogue_attention_is_preserved_before_action(self):
  self.assertEqual(cartoon.attention_target('ball',1,7,.5,'tara','tara'),(402,515))
  self.assertEqual(cartoon.attention_target('ball',1,7,.5,'tara','golu'),(365,831))
  self.assertEqual(cartoon.attention_target('rain',5,7,.5,'golu','tara'),(150,776))

 def test_frame_passes_moving_target_to_every_character(self):
  scene={'setting':'ball','speaker':'tara','narration':'गेंद नीचे आई।','caption':'गेंद मिली!'}
  with patch.object(cartoon,'friend') as friend,patch.object(cartoon,'text_panel'),patch.object(cartoon,'font',return_value=None),patch('PIL.ImageDraw.ImageDraw.text'):
   cartoon.frame(scene,3,7,.5)
  self.assertEqual(friend.call_count,3)
  for call in friend.call_args_list:self.assertEqual(call.kwargs['target'],cartoon.ball_position(3,.5))
