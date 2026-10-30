"""Read a bounded story-only feed from the owner's exact repo; never execute remote code."""
import hashlib,json,logging,time,urllib.request
from pathlib import Path
from store import ROOT
URL='https://raw.githubusercontent.com/ayushv1610-del/price-of-everything-shorts/content/story_feed.json'
LOG=logging.getLogger('shorts.feed')
_last_fetch=0.

def validate(items):
    if not isinstance(items,list) or len(items)>90:raise ValueError('Expected at most 90 stories')
    result=[];seen=set();scripts=set()
    for item in items:
        key=item.get('id','')
        if not isinstance(key,str) or not key.startswith('hi-') or len(key)>100 or key in seen:raise ValueError('Unique Hindi story ID required')
        title=item.get('title','')
        if not isinstance(title,str) or not 4<=len(title)<=100:raise ValueError('Invalid title')
        scenes=item.get('scenes',[])
        if not 4<=len(scenes)<=7:raise ValueError('Story must have 4–7 scenes')
        for s in scenes:
            if s.get('speaker') not in ('golu','tara','mithu'):raise ValueError('Unknown character')
            if s.get('setting') not in ('kite','mango','ball','rain','drum'):raise ValueError('Unsupported setting')
            for field,limit in [('narration',150),('caption',60)]:
                text=s.get(field,'')
                if not isinstance(text,str) or not 3<=len(text)<=limit or not any('\u0900'<=c<='\u097f' for c in text):raise ValueError('Readable Hindi text required')
        digest=hashlib.sha256(' '.join(s['narration'] for s in scenes).encode()).hexdigest()
        if digest in scripts:raise ValueError('Duplicate script')
        scripts.add(digest);seen.add(key)
        result.append({'title':title,'topic':key,'fictional':True,'voice_engine':'kokoro',
            'visual_style':'cartoon','cast':'jungle-friends','language':'hi',
            'publication_ready':True,'language_review_required':True,'automated_language_review':True,
            'made_for_kids':True,'sources':[],'script_sha256':digest,
            'rights':'Original fictional story and code-drawn animation. Kokoro Hindi character voices.',
            'scenes':[{k:s[k] for k in ('speaker','narration','caption','setting')} for s in scenes]})
    return result

def plans(refresh=False):
    global _last_fetch
    cache=ROOT/'story-feed.json'
    if refresh and time.monotonic()-_last_fetch>=600:
        _last_fetch=time.monotonic()
        try:
            with urllib.request.urlopen(URL,timeout=10) as r:data=r.read(250001)
            if len(data)>250000:raise ValueError('Feed too large')
            validate(json.loads(data))
            ROOT.mkdir(parents=True,exist_ok=True)
            tmp=cache.with_suffix('.tmp');tmp.write_bytes(data);tmp.replace(cache)
        except Exception:LOG.exception('Story feed refresh failed; using last validated feed')
    for path in (cache,Path(__file__).with_name('story_feed.json')):
        if path.is_file():
            try:return validate(json.loads(path.read_text()))
            except Exception:LOG.exception('Invalid story feed %s',path.name)
    return []
