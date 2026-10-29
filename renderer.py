"""Offline original motion typography, synthetic voice, timed captions and measured QA."""
import subprocess, json, math, hashlib, textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
W,H,FPS=720,1280,24
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
def run(args):
    p=subprocess.run(args, capture_output=True, timeout=240)
    if p.returncode: raise RuntimeError(p.stderr.decode(errors='replace')[-1500:])
    return p.stdout

def probe(path):
    return json.loads(run(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(path)]))
def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def lines(draw,text,font,width):
    out=[]; line=''
    for word in text.split():
        candidate=(line+' '+word).strip()
        if draw.textbbox((0,0),candidate,font=font)[2]>width and line:
            out.append(line);line=word
        else:line=candidate
    return out+[line]
def frame(scene,index,total,progress):
    im=Image.new('RGB',(W,H),'#091221');d=ImageDraw.Draw(im)
    gold='#edc77c'; white='#f3f0e9'
    d.text((48,78),'THE PRICE OF',font=ImageFont.truetype(FONT,27),fill=gold)
    d.text((48,115),'EVERYTHING',font=ImageFont.truetype(FONT,43),fill=white)
    d.text((48,215),f'{index+1:02d} / {total:02d}',font=ImageFont.truetype(FONT,22),fill='#8193af')
    # Different geometries and smooth movement per scene, all created from scratch.
    for k in range(6):
        height=60+((k*53+index*31)%190)
        x=65+k*100
        y=650-int(height*(0.6+0.4*progress))
        d.rounded_rectangle((x,y,x+58,650),radius=10,fill=gold if k==index%6 else '#253d58')
    caption=scene['caption'];size=58
    while True:
        f=ImageFont.truetype(FONT,size); ls=lines(d,caption,f,620)
        if len(ls)<=4 or size<=30:break
        size-=2
    y=760
    for line in ls:
        d.text((48,y),line,font=f,fill=white);y+=size+14
    d.text((48,1100),'MONEY. VALUE. THE HIDDEN DIFFERENCE.',font=ImageFont.truetype(FONT,19),fill='#8193af')
    d.rounded_rectangle((48,1170,672,1178),radius=3,fill='#253d58')
    d.rounded_rectangle((48,1170,49+int(622*(index+progress)/total),1178),radius=3,fill=gold)
    return im

def render(plan,folder):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    durations=[]; parts=[]; cursor=0.; subs=[]
    for i,s in enumerate(plan['scenes']):
        text=folder/f'speech-{i}.txt';text.write_text(s['narration'])
        wav=folder/f'voice-{i}.wav'
        # Text file avoids passing narration as filter syntax or shell input.
        run(['ffmpeg','-v','error','-y','-f','lavfi','-i',f'flite=textfile={text}:voice=slt','-ar','48000',str(wav)])
        length=float(probe(wav)['format']['duration'])+.3
        count=math.ceil(max(3.,length)*FPS);duration=count/FPS
        durations.append(duration)
        video=folder/f'scene-{i}.mp4'
        cmd=['ffmpeg','-v','error','-y','-threads','1','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','pipe:0','-i',str(wav),'-af','apad','-t',str(duration),'-c:v','libx264','-threads','1','-preset','ultrafast','-crf','25','-pix_fmt','yuv420p','-c:a','aac','-b:a','128k',str(video)]
        with open(folder/'ffmpeg.log','wb') as err:
            p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=err)
            try:
                for j in range(count):p.stdin.write(frame(s,i,len(plan['scenes']),j/max(1,count-1)).tobytes())
                p.stdin.close()
                if p.wait(timeout=120):raise RuntimeError('Scene encoding failed')
            finally:
                if p.poll() is None:p.kill();p.wait()
        parts.append(video)
        def stamp(t):
            ms=round(t*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
        subs.append(f"{i+1}\n{stamp(cursor)} --> {stamp(cursor+duration)}\n{s['narration']}\n")
        cursor+=duration
    if not 12<=cursor<=60: raise ValueError(f'Narration duration outside 12–60 seconds: {cursor:.2f}')
    concat=folder/'concat.txt';concat.write_text(''.join(f"file '{p.name}'\n" for p in parts))
    temp=folder/'rendering.mp4';video=folder/'video.mp4'
    run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',str(concat),'-c','copy','-movflags','+faststart',str(temp)])
    info=probe(temp);vs=next(s for s in info['streams'] if s['codec_type']=='video');audio=next(s for s in info['streams'] if s['codec_type']=='audio')
    if (vs['width'],vs['height'])!=(W,H) or audio['codec_name']!='aac':raise ValueError('Invalid output streams')
    # Decode every frame to catch corruption before making the asset available.
    run(['ffmpeg','-v','error','-i',str(temp),'-f','null','-'])
    temp.replace(video)
    frame(plan['scenes'][0],0,len(plan['scenes']),.7).save(folder/'thumbnail.jpg')
    (folder/'captions.srt').write_text('\n'.join(subs))
    description='\n'.join([plan['title'],'','Sources:']+[s['url'] for s in plan['sources']]+['','Original animation and synthetic narration. Educational explainer. #Shorts'])
    metadata=dict(title=plan['title'],description=description,tags=['Shorts','economics','The Price of Everything'],privacyStatus='private')
    (folder/'metadata.json').write_text(json.dumps(metadata,indent=2))
    (folder/'plan.json').write_text(json.dumps(plan,indent=2))
    qa=dict(width=W,height=H,fps=FPS,duration=round(float(info['format']['duration']),3),audio=True,codec=vs['codec_name'],sha256=sha(video),bytes=video.stat().st_size,full_decode=True,voice='flite-slt-offline')
    (folder/'qa.json').write_text(json.dumps(qa,indent=2))
    for p in parts:p.unlink()
    for pattern in ('voice-*.wav','speech-*.txt'):
        for p in folder.glob(pattern):p.unlink()
    concat.unlink()
    return qa
