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


# New locale starts on hold: signal-level QA cannot certify Hindi pronunciation.
HINDI_STORIES=[
 ('hi-red-kite-v1','लाल पतंग का रहस्य! | Golu & Tara #Shorts',[
 ('golu','अरे! मेरी लाल पतंग कहाँ गई? अभी तो यहीं थी!','लाल पतंग गायब!'),
 ('tara','रुको गोलू! पेड़ तक लाल धागा जा रहा है।','यह धागा किसका है?'),
 ('golu','ऊपर देखो! पतंग तो डाल में फँसी है। अब क्या करें?','पतंग मिल गई!'),
 ('tara','अपनी सूँड़ से डाल को धीरे से नीचे करो। मैं धागा छुड़ाती हूँ।','धीरे से, गोलू!'),
 ('mithu','वाह! पतंग बच गई। मुझे तो लगा, पेड़ उड़ने वाला है!','पेड़ नहीं, पतंग उड़ेगी!')]),
 ('hi-mango-seed-v1','गायब आम का राज़! | Golu & Tara #Shorts',[
 ('golu','तारा! मेरा आम गायब है। यहाँ तो बस एक गुठली पड़ी है!','आम कहाँ गया?'),
 ('tara','मिट्ठू की चोंच देखो! उस पर पीला रस लगा है।','पीला रस एक सुराग!'),
 ('mithu','माफ़ करना! भूख लगी थी। अगला आम हम बाँटकर खाएँगे।','मिट्ठू ने सच बताया।'),
 ('tara','चलो, गुठली बो देते हैं। पानी देंगे, तो एक दिन पेड़ बनेगा।','एक गुठली, नई शुरुआत!'),
 ('golu','तब आम बाँटेंगे! पर पेड़ को बड़ा होने का समय तो दो!','दोस्ती का मीठा फल!')])]
STORIES=HINDI_STORIES+STORIES
_english_plan_for_story=plan_for_story
def plan_for_story(item):
 if not item[0].startswith('hi-'):return _english_plan_for_story(item)
 key,title,dialogue=item
 return {'title':title,'topic':key,'fictional':True,'voice_engine':'kokoro',
         'visual_style':'cartoon','cast':'jungle-friends','language':'hi',
         'publication_ready':False,'language_review_required':True,'made_for_kids':True,
         'sources':[],'rights':'Original story, original cartoon cast and animation; Kokoro Hindi stock voices.',
         'scenes':[{'speaker':speaker,'narration':text,'caption':caption,
                    'setting':'kite' if key=='hi-red-kite-v1' else 'mango'}
                   for speaker,text,caption in dialogue]}
