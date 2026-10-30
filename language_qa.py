"""Independent Hindi ASR on encoded media; fail closed, no billable APIs."""
import os, re, unicodedata
from difflib import SequenceMatcher
_MODEL = None

def normalize(text):
    text = unicodedata.normalize('NFC', text)
    return ''.join(c for c in text if '\u0900' <= c <= '\u097f' or c.isdecimal())

def compare(expected, actual):
    left, right = normalize(expected), normalize(actual)
    return SequenceMatcher(None, left, right, autojunk=False).ratio() if left and right else 0.

def model():
    global _MODEL
    if _MODEL is None:
        from faster_whisper import WhisperModel
        _MODEL = WhisperModel(os.environ.get('SHORTS_ASR_MODEL_DIR', '/opt/asr-model'),
                              device='cpu', compute_type='int8', cpu_threads=2, num_workers=1,
                              local_files_only=True)
    return _MODEL

def verify_samples(samples, scenes, durations, recognizer=None):
    """Check each spoken interval independently; prompts never reveal expected words."""
    recognizer = recognizer or model()
    reports=[];offset=0.
    for scene, duration in zip(scenes,durations,strict=True):
        audio=samples[round(offset*16000):round((offset+duration)*16000)]
        segments,_=recognizer.transcribe(audio,language='hi',beam_size=5,
            condition_on_previous_text=False, vad_filter=False, temperature=0)
        heard=' '.join(s.text for s in segments).strip()
        score=compare(scene['narration'],heard)
        reports.append({'expected':scene['narration'],'heard':heard,'similarity':round(score,3),'passed':score>=.65})
        offset+=duration
    passed=bool(reports) and all(r['passed'] for r in reports) and sum(r['similarity'] for r in reports)/len(reports)>=.78
    return {'method':'independent-whisper-small-hi-int8','passed':passed,'lines':reports,
            'note':'Checks intelligibility against script; does not certify a human accent or subjective voice appeal.'}
