"""Local neural character voices; no billable API calls or silent fallback."""
import os
from pathlib import Path
_ENGINE=None
VOICES={'fox':'am_adam','bunny':'af_sarah','duck':'am_puck'}
def synthesize(text,speaker,output):
    global _ENGINE
    import soundfile as sf
    from kokoro_onnx import Kokoro
    if speaker not in VOICES:raise ValueError('Unknown character voice')
    root=Path(os.environ.get('SHORTS_VOICE_MODEL_DIR','/data/voice-models'))
    if _ENGINE is None:_ENGINE=Kokoro(str(root/'kokoro-v1.0.onnx'),str(root/'voices-v1.0.bin'))
    samples,rate=_ENGINE.create(text,voice=VOICES[speaker],speed=1.02,lang='en-us')
    sf.write(str(output),samples,rate,subtype='PCM_16')
    from dialogue import inspect_voice
    return inspect_voice(output)
