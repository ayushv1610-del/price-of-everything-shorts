"""Channel-bound OAuth uploads with remote visibility verification."""
import os, json, time, secrets
from pathlib import Path
from store import database, ROOT, event
SCOPES=['https://www.googleapis.com/auth/youtube.upload','https://www.googleapis.com/auth/youtube.readonly']
def config():
    client=os.environ.get('GOOGLE_CLIENT_ID');secret=os.environ.get('GOOGLE_CLIENT_SECRET');base=os.environ.get('SHORTS_PUBLIC_URL','').rstrip('/')
    if not(client and secret and base.startswith('https://')):raise ValueError('Google OAuth client ID, secret and HTTPS public URL must be configured')
    return {'web':{'client_id':client,'client_secret':secret,'auth_uri':'https://accounts.google.com/o/oauth2/auth','token_uri':'https://oauth2.googleapis.com/token','redirect_uris':[base+'/oauth/google/callback']}}
def flow(state=None,verifier=None):
    from google_auth_oauthlib.flow import Flow
    f=Flow.from_client_config(config(),scopes=SCOPES,state=state,code_verifier=verifier,autogenerate_code_verifier=verifier is None)
    f.redirect_uri=config()['web']['redirect_uris'][0]
    return f

def start():
    f=flow();url,state=f.authorization_url(access_type='offline',prompt='consent',include_granted_scopes='true')
    with database() as c:
        c.execute('INSERT OR REPLACE INTO settings VALUES(?,?)',('oauth:'+state,json.dumps(dict(expires=time.time()+600,verifier=f.code_verifier))))
    return url

def callback(state,code):
    with database() as c:
        r=c.execute('SELECT value FROM settings WHERE key=?',('oauth:'+state,)).fetchone()
        if not r:raise ValueError('Unknown or consumed OAuth state')
        c.execute('DELETE FROM settings WHERE key=?',('oauth:'+state,))
    saved=json.loads(r[0])
    if saved['expires']<time.time():raise ValueError('OAuth state expired')
    f=flow(state,saved['verifier']);f.fetch_token(code=code)
    if not f.credentials.refresh_token:raise ValueError('Google did not grant offline access; reconnect with consent')
    ROOT.mkdir(parents=True,exist_ok=True)
    path=ROOT/'google-token.json';tmp=ROOT/'google-token.tmp'
    fd=os.open(tmp,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
    with os.fdopen(fd,'w') as out:out.write(f.credentials.to_json())
    tmp.replace(path)
    return channel()
def client():
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    path=ROOT/'google-token.json'
    if not path.exists():raise ValueError('Google authorization required')
    creds=Credentials.from_authorized_user_file(str(path),SCOPES)
    return build('youtube','v3',credentials=creds,cache_discovery=False)
def channel():
    result=client().channels().list(part='id,snippet',mine=True).execute()
    items=result.get('items',[])
    if len(items)!=1:raise ValueError('Expected exactly one authorized YouTube channel')
    ch={'id':items[0]['id'],'title':items[0]['snippet']['title']}
    from store import set_setting
    set_setting('youtube_channel',ch)
    return ch

def upload_private(job,folder):
    from googleapiclient.http import MediaFileUpload
    expected=os.environ.get('YOUTUBE_CHANNEL_ID')
    if not expected:raise ValueError('YOUTUBE_CHANNEL_ID must be confirmed before uploads')
    if channel()['id']!=expected:raise ValueError('Authorized channel does not match expected channel')
    metadata=json.loads((folder/'metadata.json').read_text())
    api=client()
    request=api.videos().insert(part='snippet,status',notifySubscribers=False,body={'snippet':{'title':metadata['title'],'description':metadata['description'],'tags':metadata['tags'],'categoryId':'27','defaultLanguage':'en'},'status':{'privacyStatus':'private','selfDeclaredMadeForKids':False}},media_body=MediaFileUpload(str(folder/'video.mp4'),mimetype='video/mp4',chunksize=4*1024*1024,resumable=True))
    response=None
    # No automatic retry of ambiguous requests: an interrupted upload requires reconciliation.
    while response is None:_,response=request.next_chunk(num_retries=0)
    if not response.get('id'):raise ValueError('YouTube did not return a video ID')
    return response['id']

def upload_public(folder, made_for_kids):
    """Explicit public upload; caller owns transactional claim and ambiguity handling."""
    from googleapiclient.http import MediaFileUpload
    expected=os.environ.get('YOUTUBE_CHANNEL_ID')
    if not expected or channel()['id']!=expected:
        raise ValueError('Confirmed YouTube channel required')
    metadata=json.loads((folder/'metadata.json').read_text())
    request=client().videos().insert(part='snippet,status',notifySubscribers=False,
        body={'snippet':{'title':metadata['title'],'description':metadata['description'],
                        'tags':metadata['tags'],'categoryId':'24','defaultLanguage':metadata.get('defaultLanguage','en'),'defaultAudioLanguage':metadata.get('defaultLanguage','en')},
              'status':{'privacyStatus':'public','selfDeclaredMadeForKids':made_for_kids}},
        media_body=MediaFileUpload(str(folder/'video.mp4'),mimetype='video/mp4',
                                  chunksize=4*1024*1024,resumable=True))
    result=None
    while result is None:
        _,result=request.next_chunk(num_retries=0)
    if not result.get('id'):raise ValueError('Missing YouTube video ID')
    actual=client().videos().list(part='status',id=result['id']).execute()
    items=actual.get('items',[])
    public=bool(items and items[0]['status'].get('privacyStatus')=='public')
    return {'youtube_id':result['id'],'verified_public':public}
