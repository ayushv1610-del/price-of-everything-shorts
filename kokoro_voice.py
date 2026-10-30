"""Local neural character voices; no billable API calls or silent fallback."""
import os
from pathlib import Path
_ENGINE=None
VOICES={'fox':'am_adam','bunny':'af_sarah','duck':'am_puck'}
HINDI_VOICES={'golu':'hm_omega','tara':'hf_alpha','mithu':'hm_psi'}
def synthesize(text,speaker,output,language='en'):
    global _ENGINE
    import soundfile as sf
    from kokoro_onnx import Kokoro
    voices=HINDI_VOICES if language=='hi' else VOICES
    if language not in ('en','hi'):raise ValueError('Unsupported dialogue language')
    if speaker not in voices:raise ValueError('Character voice does not match dialogue language')
    if language=='hi' and not any('\u0900'<=c<='\u097f' for c in text):raise ValueError('Hindi dialogue requires Devanagari text')
    root=Path(os.environ.get('SHORTS_VOICE_MODEL_DIR','/data/voice-models'))
    if _ENGINE is None:_ENGINE=Kokoro(str(root/'kokoro-v1.0.onnx'),str(root/'voices-v1.0.bin'))
    samples,rate=_ENGINE.create(text,voice=voices[speaker],speed=1.0,lang='hi' if language=='hi' else 'en-us')
    sf.write(str(output),samples,rate,subtype='PCM_16')
    from dialogue import inspect_voice
    return inspect_voice(output)
