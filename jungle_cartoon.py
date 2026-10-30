"""Original jungle cast, continuous movement, speech-driven mouths, shaped Hindi."""
import math, os
from PIL import Image, ImageDraw, ImageFont, features
import renderer
renderer.FPS=30
FONT=os.environ.get('SHORTS_HINDI_FONT','/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf')
def font(n):
 if not features.check('raqm'):raise ValueError('Devanagari captions require RAQM shaping')
 return ImageFont.truetype(FONT,n,layout_engine=ImageFont.Layout.RAQM)
def text_panel(d,text,box,size,color,bg):
 f=font(size);ls=renderer.lines(d,text,f,box[2]-box[0]-44)
 if len(ls)*(size+15)>box[3]-box[1]-20:raise ValueError('Hindi caption would overflow safe area')
 d.rounded_rectangle(box,radius=24,fill=bg)
 for n,line in enumerate(ls):d.text((box[0]+22,box[1]+14+n*(size+15)),line,font=f,fill=color,language='hi')
def friend(d,x,y,kind,t,speaking,scale=1,trunk_raise=0):
 color={'golu':'#91b9d9','tara':'#bd784f','mithu':'#67bd77'}[kind]
 def ellipse(a,b,c,e,fill):d.ellipse((x+a*scale,y+b*scale,x+c*scale,y+e*scale),fill=fill)
 def line(points,fill,width):d.line([(x+a*scale,y+b*scale) for a,b in points],fill=fill,width=max(2,int(width*scale)),joint='curve')
 # Each character has a stable silhouette; slow continuous sway avoids scene resets.
 for side in (-1,1):
  line([(side*25,68),(side*35+4*math.sin(t*3+side),125)],color,24)
  line([(side*38,20),(side*65,45+8*math.sin(t*2+side))],color,17)
 ellipse(-45,-5,45,90,color)
 if kind=='golu':
  ellipse(-88,-74,-25,15,color);ellipse(25,-74,88,15,color)
  ellipse(-78,-62,-40,0,'#d5c0da');ellipse(40,-62,78,0,'#d5c0da')
 elif kind=='tara':
  # Curled tail and round ears distinguish Tara from the earlier bunny.
  d.arc((x+20*scale,y+20*scale,x+115*scale,y+110*scale),210,530,fill=color,width=max(2,int(15*scale)))
  ellipse(-74,-61,-35,-20,color);ellipse(35,-61,74,-20,color)
 ellipse(-57,-82,57,25,color)
 if kind=='tara':ellipse(-43,-65,43,15,'#ffe0ae')
 if kind=='mithu':
  d.polygon([(x-15*scale,y-75*scale),(x-6*scale,y-115*scale),(x+20*scale,y-76*scale)],fill='#32965d')
 for a in (-22,22):
  ellipse(a-12,-54,a+12,-25,'white')
  if math.sin(t*1.8)>.995:line([(a-8,-38),(a+8,-38)],'#253451',3)
  else:ellipse(a-5,-46,a+5,-30,'#253451')
 level=getattr(renderer,'SPEECH_LEVEL',0) if speaking else 0
 if kind=='mithu':
  d.polygon([(x-13*scale,y-15*scale),(x+31*scale,y-6*scale),(x-8*scale,y+(9+level*15)*scale)],fill='#ffb543')
 else:
  if level>.06:ellipse(-12,-3,12,4+level*20,'#5c3144')
  else:d.arc((x-13*scale,y-8*scale,x+13*scale,y+13*scale),0,180,fill='#5c3144',width=3)
 if kind=='golu':line([(15,-18),(49,-1-trunk_raise),(76,-7-trunk_raise),(83,-28-trunk_raise)],color,23)
def frame(s,i,total,p):
 t=i+p;ease=p*p*(3-2*p)
 im=Image.new('RGB',(720,1280),'#d3f2ed');d=ImageDraw.Draw(im)
 for k in range(4):
  x=k*230-80+12*math.sin(t*.3)
  d.ellipse((x,155,x+150,215),fill='#ffffff')
 d.ellipse((-250,610,850,1250),fill='#98d49c');d.rectangle((0,900,720,1280),fill='#f7deb3')
 # Tree stays spatially consistent: the kite and red thread are visible clues.
 bend=(ease if i==3 else 0.)*200
 d.rounded_rectangle((525,410,573,920),radius=20,fill='#986441')
 d.line((548,560,385,510+bend),fill='#986441',width=26)
 for x,y,r in [(420,430,125),(570,360,138),(660,470,110)]:d.ellipse((x-r,y-r,x+r,y+r),fill='#59aa6c')
 setting=s.get('setting','kite')
 if setting=='kite':
  # The same kite is stuck in the tree until Tara frees the thread.
  if i<3:cx,cy=402,515
  elif i==3:cx,cy=402-110*ease,515+180*ease
  else:cx,cy=300+110*ease,600-250*ease
  if i>=1:d.line([(190,895),(260,835),(310,700),(cx,cy+60)],fill='#e74f58',width=4)
  d.polygon([(cx,cy-61),(cx+43,cy),(cx,cy+61),(cx-43,cy)],fill='#f35a61',outline='#aa334b',width=3)
  d.line((cx,cy-61,cx,cy+61),fill='#ffe8ac',width=2)
  d.line((cx-43,cy,cx+43,cy),fill='#ffe8ac',width=2)
  d.line([(cx,cy+61),(cx-10,cy+89),(cx+13,cy+112)],fill='#e74f58',width=3)
 elif setting=='mango':
  # Fallen seed, juice clue, then a planted seed and watering, no instant mature tree.
  d.ellipse((295,922,348,943),fill='#9d653c')
  if i>=3:
   d.ellipse((275,918,370,949),fill='#a77a48')
   for k in range(5):
    yy=820+(k*26+t*70)%105
    d.ellipse((310+k*5,yy,315+k*5,yy+10),fill='#64bad6')

 if setting=='ball':
  if i<3: bx,by=402,510
  elif i==3: bx,by=402-100*ease,510+390*ease
  else: bx,by=302+35*math.sin(p*math.pi*2),900-40*abs(math.sin(p*math.pi*2))
  d.ellipse((bx-30,by-30,bx+30,by+30),fill='#faf5e8',outline='#343951',width=3)
  d.regular_polygon((bx,by,13),5,fill='#343951')
 if setting=='drum':
  d.rectangle((248,872,334,954),fill='#eb9b55',outline='#794c3a',width=3)
  d.ellipse((248,855,334,890),fill='#fff5cb',outline='#794c3a',width=3)
  for xx in range(254,331,22):d.line((xx,888,xx+10,946),fill='#fff5cb',width=3)
 if setting=='rain':
  d.ellipse((220,957,490,985),fill='#8ac6de')
  if i<4:
   for k in range(32):
    xx=(k*83+t*35)%720; yy=390+(k*49+t*150)%600
    d.line((xx,yy,xx-4,yy+17),fill='#73b6d2',width=2)
  d.line((310,610,310,795),fill='#795649',width=6)
  d.pieslice((155,505,465,715),180,360,fill='#e47c92',outline='#a84e71',width=3)
 speaker=s.get('speaker')
 friend(d,150,820+math.sin(t*2)*4,'golu',t,speaker=='golu',1.12,trunk_raise=70*math.sin(p*math.pi) if i==3 else 0)
 friend(d,365,866+math.sin(t*2+.8)*3,'tara',t+.3,speaker=='tara',.9)
 # Bird on a low branch, within frame throughout the mystery.
 d.line((575,725,695,725),fill='#986441',width=14)
 friend(d,626,660+math.sin(t*2+1)*3,'mithu',t+.6,speaker=='mithu',.65)
 if setting=='drum' and i<=2:d.line((649,683,669,650-8*math.sin(p*math.pi*4)),fill='#986441',width=6)
 if setting=='mango' and i>=1:d.ellipse((630,660,642,668),fill='#ffc02f')
 text_panel(d,s['caption'],(35,230,685,370),36,'#343951','#fffdf1')
 text_panel(d,s['narration'],(30,1040,690,1235),29,'#fffdf1','#313e59')
 d.text((35,65),'गोलू • तारा • मिट्ठू',font=font(31),fill='#313e59',language='hi')
 return im
