"""Reviewed original story bank. No duplicate publishing when exhausted."""
STORIES=[
 ('icecream-count','The Missing Scoop! | Cartoon Story #Shorts',[
 ('fox','Three scoops! One for you, one for me, and one for Duck!','THREE SCOOPS. THREE FRIENDS.'),
 ('fox','Wait. There are only two scoops now!','ONE SCOOP IS MISSING!'),
 ('bunny','Duck? Why is there ice cream on your beak?','DUCK HAS A CLUE...'),
 ('fox','Did you eat your scoop before we even started?','CAUGHT YOU, DUCK!'),
 ('duck','I was checking if it was cold!','QUALITY CONTROL!')]),
 ('icecream-melting','The Slowest Ice Cream Race | Cartoon Story #Shorts',[
 ('fox','Nobody eat! First, we take the perfect ice cream picture!','THE PERFECT PICTURE!'),
 ('fox','Bunny, move left. Duck, smile. No, your other smile!','JUST ONE MORE PHOTO...'),
 ('bunny','Fox, our ice cream is melting!','IT IS MELTING!'),
 ('fox','Quick! Take the picture before it becomes soup!','TOO LATE?'),
 ('duck','Good news. I brought a straw!','DUCK CAME PREPARED!')]),
 ('icecream-manners','Duck Learns to Share | Cartoon Story #Shorts',[
 ('fox','This giant ice cream is for all three of us!','ONE GIANT ICE CREAM!'),
 ('fox','Duck! A tiny bite. Not the whole top scoop!','A TINY BITE!'),
 ('bunny','Let us take turns. Small bites make it fair.','ONE TURN EACH.'),
 ('fox','My turn, Bunny, then Duck. Everyone gets some!','THAT IS BETTER!'),
 ('duck','Can the cone have a turn too? It looks hungry!','THE CONE IS HUNGRY?!')])]
def plan_for_story(item):
 key,title,lines=item
 return {'title':title,'topic':key,'fictional':True,'voice_engine':'kokoro','visual_style':'cartoon',
         'publication_ready':True,'made_for_kids':True,'sources':[],
         'rights':'Original fictional story, original code-drawn animation; Kokoro stock neural voices.',
         'scenes':[{'speaker':sp,'narration':text,'caption':caption,
                    'scoops':(3 if n==0 else 2) if key=='icecream-count' else 3,
                    'clue':key=='icecream-count' and n>=2,
                    'melting':key=='icecream-melting' and n>=2}
                   for n,(sp,text,caption) in enumerate(lines)]}
