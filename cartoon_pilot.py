import math
from PIL import Image,ImageDraw,ImageFont
import renderer
renderer.FPS=30
PLAN={'title':'The Last Ice Cream — Cartoon Pilot','topic':'cartoon-icecream','voice_engine':'kokoro','sources':[],'fact_checked':False,'rights':'Original code-drawn cartoon characters and backgrounds; offline synthetic voices. Fictional story.','scenes':[
 {'narration':'One coin. One ice cream. This should be easy!', 'caption':'ONE COIN. ONE ICE CREAM.'},
 {'narration':'Wait! That giant cone costs three coins? I only have one!', 'caption':'GIANT CONE: 3 COINS'},
 {'narration':'My tiny cone costs one coin. But your giant cone has three scoops!', 'caption':'TINY CONE: 1 COIN'},
 {'narration':'Three scoops? Then we can share! One coin each!', 'caption':'THREE FRIENDS. ONE COIN EACH.'},
 {'narration':'Great plan! But who gets the cone? Oh no! The duck!', 'caption':'WHO GETS THE CONE?!'}]}
def f(n):return ImageFont.truetype(renderer.FONT,n)
def character(d,x,y,kind,mouth,t,scale=1):
 def box(a,b,c,e):return (x+a*scale,y+b*scale,x+c*scale,y+e*scale)
 color={'fox':'#ed823c','bunny':'#c1a9e7','duck':'#ffd83c'}[kind]
 # Moving legs and arms, body follows its own bouncing trajectory.
 for side in [-1,1]:
  foot=math.sin(t*math.pi*4+side)*12
  d.line((x+side*22*scale,y+115*scale,x+(side*34+foot)*scale,y+155*scale),fill='#263449',width=max(3,int(12*scale)))
  d.line((x+side*42*scale,y+55*scale,x+side*75*scale,y+(30+18*math.sin(t*8+side))*scale),fill=color,width=max(3,int(17*scale)))
 d.ellipse(box(-47,20,47,125),fill=color)
 if kind=='bunny':
  for a in [-36,12]:d.ellipse(box(a,-125,a+25,-35),fill=color)
 elif kind=='fox':
  d.polygon([(x-55*scale,y-35*scale),(x-60*scale,y-95*scale),(x-5*scale,y-56*scale)],fill=color)
  d.polygon([(x+55*scale,y-35*scale),(x+60*scale,y-95*scale),(x+5*scale,y-56*scale)],fill=color)
 d.ellipse(box(-62,-65,62,52),fill=color)
 d.ellipse(box(-45,-15,45,45),fill='#fff5df')
 blink=math.sin(t*19)>.98
 for a in [-27,22]:
  d.ellipse(box(a-10,-36,a+10,-8),fill='white')
  if blink:d.line((x+(a-7)*scale,y-21*scale,x+(a+7)*scale,y-21*scale),fill='#263449',width=3)
  else:d.ellipse(box(a-4,-29,a+5,-12),fill='#263449')
 d.ellipse(box(-7,-6,7,5),fill='#263449')
 if mouth and getattr(renderer,'SPEECH_LEVEL',0)>.06:d.ellipse(box(-14,12,14,18+getattr(renderer,'SPEECH_LEVEL',0)*22),fill='#692e43')
 else:d.arc(box(-16,5,16,29),0,180,fill='#692e43',width=3)
def frame(s,i,total,p):
 ease=p*p*(3-2*p)
 im=Image.new('RGB',(720,1280),'#a4e3f5');d=ImageDraw.Draw(im)
 # Parallax clouds and park background.
 for k in range(4):
  x=(k*240+p*25)%900-100
  d.ellipse((x,110+k%2*100,x+170,170+k%2*100),fill='white')
 d.ellipse((-300,580,950,1400),fill='#9bd486');d.rectangle((0,880,720,1280),fill='#f3d8a8')
 d.rounded_rectangle((315,405,690,780),radius=20,fill='#fff3d5')
 d.rectangle((300,405,705,480),fill='#f77480')
 for k in range(5):d.rectangle((300+k*80,405,340+k*80,480),fill='#fff4d9')
 d.text((345,510),'ICE CREAM',font=f(31),fill='#754765')
 d.text((395,565),'1 / 3',font=f(45),fill='#754765')
 # Cone and scoops animate upward as each scene reveals the deal.
 cx=520 if i<3 else 375
 cy=740-int(20*math.sin(p*math.pi))
 if i==4:cx=375+int(ease*300);cy=760+int(ease*190)
 d.polygon([(cx-40,cy),(cx+40,cy),(cx,cy+110)],fill='#bd7a39')
 colors=['#ffc3cf','#ac825f','#b8eac7']
 for k in range(s.get('scoops',3 if i>=1 else 1)):
  squash=.5 if s.get('melting') else 1.
  d.ellipse((cx-45,cy-int((45+k*44)*squash),cx+45,cy+int((35-k*44)*squash)),fill=colors[k],outline='#754765',width=3)
 if s.get('melting'):d.ellipse((cx-65,cy+95,cx+65,cy+120),fill='#ffc3cf')
 t=i+p
 character(d,165,790+math.sin(t*12)*9,'fox',s.get('speaker')=='fox',t)
 character(d,430,840+math.sin(t*12+2)*7,'bunny',s.get('speaker')=='bunny',t+.4,.8)
 if i>=2:character(d,615 if i==3 else 600-int(ease*140),900,'duck',s.get('speaker')=='duck',t+.8,.55)
 if i==1:
  for k in range(3):d.ellipse((70+k*28,640,93+k*28,663),fill='#ffd24e',outline='#bf842a',width=2)
 if s.get('clue'):d.ellipse((603,893,618,908),fill='#ffc3cf')
 # Dialogue bubble and safe-area subtitles.
 d.rounded_rectangle((35,240,685,365),radius=28,fill='white')
 ls=renderer.lines(d,s['caption'],f(30),590)
 for k,line in enumerate(ls):d.text((65,265+k*40),line,font=f(30),fill='#48344f')
 d.rounded_rectangle((30,1065,690,1190),radius=20,fill='#392b50')
 narration=renderer.lines(d,s['narration'],f(25),610)
 for k,line in enumerate(narration):d.text((55,1080+k*33),line,font=f(25),fill='white')
 d.text((35,55),'THE PRICE OF EVERYTHING',font=f(24),fill='#392b50')
 return im
for scene,speaker in zip(PLAN['scenes'],['fox','fox','bunny','fox','duck']):scene['speaker']=speaker
if __name__=='__main__':
 renderer.frame=frame
 print(renderer.render(PLAN,'/workspace/scratch/3c7e16e82dab/cartoon-neural-pilot'),flush=True)
