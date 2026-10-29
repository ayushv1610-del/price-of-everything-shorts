"""Original fictional hotel comparison pilot. Prices are illustrative."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import renderer
PLAN={'title':'Same hotel. Three prices. What changed?', 'topic':'hotel-comparison-pilot','sources':[], 'fact_checked':False,'rights':'Original fictional hotel interface and motion graphics; synthetic offline narration.','scenes':[
 {'narration':'Same room. Same night. Three prices. What changed?', 'caption':'SAME ROOM. THREE PRICES.'},
 {'narration':'This fictional offer is eighty nine dollars. But you cannot cancel.', 'caption':'$89 • NO CANCELLATION'},
 {'narration':'This one is one hundred nine dollars. You can cancel before the deadline.', 'caption':'$109 • FLEXIBLE CANCELLATION'},
 {'narration':'And this one hundred nineteen dollar offer includes breakfast.', 'caption':'$119 • BREAKFAST INCLUDED'},
 {'narration':'The room looks identical. The deal is not. Compare the total and the terms.', 'caption':'COMPARE THE DEAL. NOT JUST THE ROOM.'}]}
def font(size):return ImageFont.truetype(renderer.FONT,size)
def frame(scene,index,total,p):
 im=Image.new('RGB',(720,1280),'#f4f0e8');d=ImageDraw.Draw(im)
 d.rectangle((0,0,720,170),fill='#101c2b');d.text((40,55),'THE PRICE OF EVERYTHING',font=font(29),fill='#f0c477')
 d.text((40,210),'ONE ROOM / ONE NIGHT',font=font(31),fill='#101c2b')
 # Original room illustration, not a real hotel photo.
 d.rounded_rectangle((40,285,680,570),radius=24,fill='#d3c4ad')
 d.rectangle((80,315,240,460),fill='#91b4c5');d.line((160,315,160,460),fill='white',width=6)
 d.rounded_rectangle((280,380,620,530),radius=20,fill='#fdfaf4');d.rectangle((280,470,620,530),fill='#243d53')
 cards=[('$89','NON-REFUNDABLE'),('$109','CANCEL BY DEADLINE'),('$119','BREAKFAST INCLUDED')]
 for i,(price,label) in enumerate(cards):
  y=615+i*125;selected=index==i+1 or index==0
  d.rounded_rectangle((40,y,680,y+105),radius=16,fill='#101c2b' if selected else '#e0dbd2')
  color='white' if selected else '#637080'
  d.text((65,y+20),price,font=font(45),fill='#f0c477' if selected else color)
  d.text((240,y+39),label,font=font(20),fill=color)
 f=font(33);lines=renderer.lines(d,scene['caption'],f,640)
 for i,line in enumerate(lines):d.text((40,1035+i*45),line,font=f,fill='#101c2b')
 d.text((40,1195),'FICTIONAL OFFERS • ILLUSTRATIVE PRICES',font=font(18),fill='#596777')
 d.rectangle((0,1268,int(720*(index+p)/total),1280),fill='#cf7746')
 return im
if __name__=='__main__':
 renderer.frame=frame
 print(renderer.render(PLAN,'/workspace/scratch/3c7e16e82dab/hotel-pilot'),flush=True)
