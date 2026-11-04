import unittest
from jungle_cartoon import kite_position,branch_bend,ball_position

class MotionContinuityTests(unittest.TestCase):
 def test_release_and_every_later_scene_share_boundary_positions(self):
  for total in (4,5,6,7,12):
   for index in range(total-1):
    self.assertEqual(kite_position(index,total,1),kite_position(index+1,total,0))
 def test_tail_has_one_forward_flight_without_rewinding(self):
  for total in (5,6,7):
   positions=[kite_position(index,total,p/20) for index in range(4,total) for p in range(21)]
   self.assertEqual(positions[0],(292,695));self.assertEqual(positions[-1],(240,510))
   for a,b in zip(positions,positions[1:]):
    self.assertGreaterEqual(a[0],b[0]);self.assertGreaterEqual(a[1],b[1])
 def test_branch_settles_without_scene_cut_jump(self):
  for setting in ('kite','ball'):
   for index in range(6):self.assertEqual(branch_bend(setting,index,1),branch_bend(setting,index+1,0))
   self.assertEqual(branch_bend(setting,3,1),200)
   self.assertEqual(branch_bend(setting,4,1),0)
  for setting in ('rain','mango','drum'):
   for index in range(7):self.assertEqual(branch_bend(setting,index,.5),0)

 def test_ball_falls_rebounds_and_stays_still(self):
  for i in range(6):
   a,b=ball_position(i,1),ball_position(i+1,0)
   self.assertAlmostEqual(a[0],b[0]);self.assertAlmostEqual(a[1],b[1])
  self.assertLess(ball_position(4,1/6)[1],ball_position(4,.5)[1])
  self.assertEqual(ball_position(5,.5),ball_position(6,.5))
