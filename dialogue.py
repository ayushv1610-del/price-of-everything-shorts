"""Dialogue timing and audio validation. Never substitute a robotic or silent track."""
import math, wave, struct
from pathlib import Path
class DialogueError(ValueError):pass
CHARACTERS={'fox':{'delivery':'curious, energetic','voice_key':'fox'},
            'bunny':{'delivery':'warm, playful','voice_key':'bunny'},
            'duck':{'delivery':'cheeky, quick','voice_key':'duck'}}
def inspect_voice(path):
    try:
        with wave.open(str(path),'rb') as w:
            if w.getsampwidth()!=2:raise DialogueError('Voice must be 16-bit PCM')
            rate=w.getframerate();channels=w.getnchannels();raw=w.readframes(w.getnframes())
    except (wave.Error,EOFError,FileNotFoundError) as e:raise DialogueError('Missing or invalid voice audio') from e
    if channels not in (1,2) or rate<16000:raise DialogueError('Voice needs mono/stereo audio at 16kHz or higher')
    values=struct.unpack('<'+'h'*(len(raw)//2),raw)
    if not values:raise DialogueError('Empty voice audio')
    duration=len(values)/channels/rate
    rms=math.sqrt(sum(v*v for v in values)/len(values))/32768
    clipping=sum(abs(v)>=32760 for v in values)/len(values)
    if rms<.003:raise DialogueError('Voice audio is silent or too quiet')
    if clipping>.01:raise DialogueError('Voice audio is clipped')
    if not .3<=duration<=20:raise DialogueError('Dialogue line must last 0.3–20 seconds')
    return {'duration':duration,'rms':round(rms,5),'clipping_fraction':round(clipping,5)}
def prepare_dialogue(scenes,voice_assets):
    timeline=[];cursor=0
    for index,scene in enumerate(scenes):
        speaker=scene.get('speaker')
        if speaker not in CHARACTERS:raise DialogueError('Unknown dialogue character')
        text=scene.get('narration','').strip()
        if not text:raise DialogueError('Dialogue text required')
        asset=voice_assets.get(str(index))
        if not asset:raise DialogueError(f'Natural voice asset missing for line {index+1}; no fallback permitted')
        if asset.get('provider')=='flite' or not asset.get('text')==text:
            raise DialogueError('Rejected voice provider or script/audio mismatch')
        info=inspect_voice(asset['path']);end=cursor+info['duration']
        timeline.append({'speaker':speaker,'text':text,'start':round(cursor,3),'speech_end':round(end,3),
                         'end':round(end+.22,3),'path':str(Path(asset['path']).resolve()),'qa':info})
        cursor=end+.22
    if not 12<=cursor<=60:raise DialogueError('Complete dialogue must last 12–60 seconds')
    return timeline
