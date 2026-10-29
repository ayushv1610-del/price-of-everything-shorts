"""Isolated Shorts production service with authenticated publishing controls."""
import os, secrets, json, time, threading, sqlite3, shutil
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Header, HTTPException, Depends, Request, Response
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from pydantic import BaseModel, Field
import store
from store import database, ROOT, event, setting, set_setting
import engine
from renderer import sha
TOKEN=os.environ.get('SHORTS_ADMIN_TOKEN','')
@asynccontextmanager
async def lifespan(app):
    engine.STOP.clear()
    thread=None
    app.state.worker=None
    if os.environ.get('SHORTS_WORKER_ENABLED','1')=='1':
        thread=threading.Thread(target=engine.worker,daemon=True);app.state.worker=thread;thread.start()
    yield
    engine.STOP.set()
    if thread:thread.join(timeout=5)
app=FastAPI(title='The Price of Everything Studio',docs_url=None,redoc_url=None,openapi_url=None,lifespan=lifespan)

def require_admin(request:Request,authorization:str|None=Header(default=None)):
    candidate=authorization or ('Bearer '+request.cookies.get('shorts_admin',''))
    authorized=bool(TOKEN and secrets.compare_digest(candidate,'Bearer '+TOKEN))
    operator=os.environ.get('SHORTS_TEST_OPERATOR_TOKEN','')
    if (operator and request.url.path.startswith(('/api/test-import','/api/jobs/','/api/produce'))
        and time.time()<float(os.environ.get('SHORTS_TEST_OPERATOR_EXPIRES','0'))
        and secrets.compare_digest(candidate,'Bearer '+operator)):
        authorized=True
    if not authorized:raise HTTPException(401,'Unauthorized')
    if request.method not in ('GET','HEAD') and request.headers.get('origin'):
        if request.headers['origin']!=str(request.base_url).rstrip('/') and request.headers['origin']!=os.environ.get('SHORTS_PUBLIC_URL','').rstrip('/'):
            raise HTTPException(403,'Invalid origin')

@app.middleware('http')
async def security(request,call_next):
    response=await call_next(request)
    response.headers['Cache-Control']='no-store'
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Referrer-Policy']='no-referrer'
    response.headers['X-Frame-Options']='DENY'
    response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; media-src 'self'; img-src 'self'; frame-ancestors 'none'"
    return response

@app.get('/health')
def health():
    return {'status':'ok','service':'shorts-engine','version':'2.0','youtube_connected':(ROOT/'google-token.json').exists(),'publishing_enabled':os.environ.get('SHORTS_PUBLIC_PUBLISHING_ENABLED')=='1'}
@app.get('/ready')
def ready():
    try:
        with database() as c:c.execute('SELECT 1').fetchone()
        ROOT.mkdir(parents=True,exist_ok=True)
        free=shutil.disk_usage(ROOT).free
        if free<50*1024**2:raise RuntimeError('Low disk')
        if not shutil.which('ffmpeg'):raise RuntimeError('ffmpeg unavailable')
        if os.environ.get('SHORTS_WORKER_ENABLED','1')=='1':
            thread=getattr(app.state,'worker',None)
            if thread is None or not thread.is_alive():raise RuntimeError('Worker not running')
        return {'status':'ready','worker':os.environ.get('SHORTS_WORKER_ENABLED','1')=='1','ffmpeg':bool(shutil.which('ffmpeg'))}
    except Exception:raise HTTPException(503,'Storage unavailable or full')
@app.get('/',response_class=HTMLResponse)
def home():return Path('dashboard.html').read_text()
class Login(BaseModel):token:str=Field(min_length=1,max_length=256)
@app.post('/api/login')
def login(body:Login,response:Response):
    if not TOKEN or not secrets.compare_digest(body.token,TOKEN):raise HTTPException(401,'Unauthorized')
    response.set_cookie('shorts_admin',TOKEN,httponly=True,secure=os.environ.get('SHORTS_COOKIE_SECURE','1')=='1',samesite='lax',max_age=86400)
    return {'ok':True}
@app.post('/api/logout')
def logout(response:Response):response.delete_cookie('shorts_admin');return {'ok':True}
class Draft(BaseModel):
    title:str=Field(min_length=4,max_length=100)
    script:str=Field(min_length=30,max_length=5000)
@app.post('/api/drafts',status_code=201,dependencies=[Depends(require_admin)])
def create_draft(draft:Draft):
    with database() as c:
        cur=c.execute('INSERT INTO drafts(title,script,created_at) VALUES(?,?,?)',(draft.title,draft.script,str(time.time())))
        return {'id':cur.lastrowid,'status':'draft'}
@app.get('/api/drafts',dependencies=[Depends(require_admin)])
def drafts():
    with database() as c:return [dict(r) for r in c.execute('SELECT id,title,status FROM drafts ORDER BY id DESC LIMIT 100')]
@app.get('/api/status',dependencies=[Depends(require_admin)])
def status():
    with database() as c:counts={r[0]:r[1] for r in c.execute('SELECT status,count(*) FROM jobs GROUP BY status')}
    return {'jobs':counts,'daily_enabled':setting('daily_enabled',True),'youtube_connected':(ROOT/'google-token.json').exists(),'google_configured':bool(os.environ.get('GOOGLE_CLIENT_ID') and os.environ.get('GOOGLE_CLIENT_SECRET')),'channel':setting('youtube_channel'),'publishing_enabled':os.environ.get('SHORTS_PUBLIC_PUBLISHING_ENABLED')=='1','free_mb':round(shutil.disk_usage(ROOT).free/1024**2),'catalog_size':len(engine.CATALOG),'content_mode':os.environ.get('SHORTS_CONTENT_MODE','explainers'),'auto_publish':os.environ.get('SHORTS_AUTO_PUBLISH')=='1','schedule_timezone':'Asia/Kolkata','schedule_hour':9}
@app.get('/api/jobs',dependencies=[Depends(require_admin)])
def jobs():
    with database() as c:
        result=[]
        for r in c.execute('SELECT * FROM jobs ORDER BY created DESC LIMIT 100'):
            d=dict(r);d['plan']=json.loads(d['plan']);d['qa']=json.loads(d['qa']) if d['qa'] else None;result.append(d)
        return result
@app.post('/api/produce',dependencies=[Depends(require_admin)])
def produce():
    jid,new=engine.enqueue_next()
    if not jid:raise HTTPException(409,'Curated research catalog exhausted. No duplicate or unverified content generated.')
    return {'id':jid,'created':new}
class Schedule(BaseModel):enabled:bool
@app.post('/api/schedule',dependencies=[Depends(require_admin)])
def schedule(body:Schedule):set_setting('daily_enabled',body.enabled);return {'enabled':body.enabled,'interval':'one new curated topic per UTC day'}

def get_job(jid):
    with database() as c:r=c.execute('SELECT * FROM jobs WHERE id=?',(jid,)).fetchone()
    if not r:raise HTTPException(404,'Job not found')
    return dict(r)
@app.get('/api/jobs/{jid}/assets/{name}',dependencies=[Depends(require_admin)])
def asset(jid:str,name:str):
    get_job(jid)
    allowed={'video.mp4','thumbnail.jpg','captions.srt','metadata.json','plan.json','qa.json'}
    if name not in allowed:raise HTTPException(404,'Unknown asset')
    path=ROOT/jid/name
    if not path.is_file():raise HTTPException(404,'Asset not ready')
    return FileResponse(path)
@app.post('/api/jobs/{jid}/retry',dependencies=[Depends(require_admin)])
def retry(jid:str):
    get_job(jid)
    with database() as c:
        cur=c.execute("UPDATE jobs SET status='queued',attempts=0,error=NULL,updated=? WHERE id=? AND status='failed'",(time.time(),jid))
        if cur.rowcount!=1:raise HTTPException(409,'Only failed rendering jobs can be retried')
        event(c,jid,'manual_retry')
    return {'status':'queued'}
class Approval(BaseModel):sha256:str=Field(pattern='^[a-f0-9]{64}$')
@app.post('/api/jobs/{jid}/approve-private',dependencies=[Depends(require_admin)])
def approve(jid:str,body:Approval):
    row=get_job(jid)
    if row['status']!='ready' or sha(ROOT/jid/'video.mp4')!=body.sha256:raise HTTPException(409,'Ready asset hash does not match')
    with database() as c:
        c.execute('UPDATE jobs SET approved_hash=?,updated=? WHERE id=?',(body.sha256,time.time(),jid));event(c,jid,'approved_private',body.sha256)
    return {'approved':'private_upload_only'}
@app.post('/api/jobs/{jid}/upload-private',dependencies=[Depends(require_admin)])
def upload(jid:str):
    import youtube
    row=get_job(jid)
    if row['youtube_id']:return {'youtube_id':row['youtube_id'],'privacy':'private'}
    if row['status']!='ready' or not row['approved_hash']:raise HTTPException(409,'Private upload approval required')
    if not (ROOT/'google-token.json').exists():raise HTTPException(409,'Google authorization required')
    if sha(ROOT/jid/'video.mp4')!=row['approved_hash']:raise HTTPException(409,'Asset changed after approval')
    with database() as c:
        cur=c.execute("UPDATE jobs SET status='uploading' WHERE id=? AND status='ready'",(jid,))
        if cur.rowcount!=1:raise HTTPException(409,'Upload already claimed')
        event(c,jid,'private_upload_started')
    try:
        vid=youtube.upload_private(jid,ROOT/jid)
        with database() as c:
            c.execute("UPDATE jobs SET status='uploaded_private',youtube_id=?,updated=? WHERE id=?",(vid,time.time(),jid));event(c,jid,'uploaded_private',vid)
        return {'youtube_id':vid,'privacy':'private'}
    except Exception:
        with database() as c:
            c.execute("UPDATE jobs SET status='upload_unknown',error='Upload interrupted or rejected: reconcile in YouTube Studio before retry',updated=? WHERE id=?",(time.time(),jid));event(c,jid,'upload_requires_reconciliation')
        raise HTTPException(502,'Upload outcome requires reconciliation; automatic retry blocked')
@app.get('/api/events',dependencies=[Depends(require_admin)])
def events():
    with database() as c:return [dict(r) for r in c.execute('SELECT * FROM events ORDER BY id DESC LIMIT 100')]
@app.post('/api/google/connect',dependencies=[Depends(require_admin)])
def connect():
    import youtube
    try:return {'url':youtube.start()}
    except ValueError as e:raise HTTPException(409,str(e))
@app.get('/oauth/google/callback')
def callback(state:str='',code:str='',error:str=''):
    import youtube
    if error:raise HTTPException(400,'Google authorization declined')
    try:youtube.callback(state,code)
    except Exception:raise HTTPException(400,'Authorization failed or expired; restart connection')
    return RedirectResponse('/',status_code=303)

class PublicUpload(BaseModel):
    sha256:str=Field(pattern='^[a-f0-9]{64}$')
    made_for_kids:bool

@app.post('/api/jobs/{jid}/publish',dependencies=[Depends(require_admin)])
def publish(jid:str,body:PublicUpload):
    import youtube
    if os.environ.get('SHORTS_PUBLIC_PUBLISHING_ENABLED')!='1':
        raise HTTPException(409,'Public publishing switch is disabled')
    row=get_job(jid)
    if row['youtube_id']:
        return {'youtube_id':row['youtube_id'],'status':row['status']}
    plan=json.loads(row['plan'])
    # Render QA alone does not establish editorial quality. Existing demos are excluded.
    if not plan.get('publication_ready') or plan.get('topic') in {
        'inflation','compounding','basket','hotel-comparison-pilot','cartoon-icecream'}:
        raise HTTPException(409,'Prototype excluded from public publishing')
    if row['status']!='ready' or not row['qa']:
        raise HTTPException(409,'Completed media validation required')
    if sha(ROOT/jid/'video.mp4')!=body.sha256:
        raise HTTPException(409,'Asset hash mismatch')
    if not (ROOT/'google-token.json').exists():
        raise HTTPException(409,'Google authorization required')
    with database() as c:
        cur=c.execute("UPDATE jobs SET status='uploading',approved_hash=?,updated=? WHERE id=? AND status='ready'",
                      (body.sha256,time.time(),jid))
        if cur.rowcount!=1:raise HTTPException(409,'Upload already claimed')
        event(c,jid,'public_upload_authorized',json.dumps({'sha256':body.sha256,'made_for_kids':body.made_for_kids}))
    try:
        result=youtube.upload_public(ROOT/jid,body.made_for_kids)
        state='published' if result['verified_public'] else 'uploaded_not_public'
        with database() as c:
            c.execute('UPDATE jobs SET status=?,youtube_id=?,updated=? WHERE id=?',
                      (state,result['youtube_id'],time.time(),jid))
            event(c,jid,state,result['youtube_id'])
        return dict(result,status=state)
    except Exception:
        with database() as c:
            c.execute("UPDATE jobs SET status='upload_unknown',error='Reconcile remote upload before retry',updated=? WHERE id=?",(time.time(),jid))
            event(c,jid,'public_upload_unknown')
        raise HTTPException(502,'Upload outcome unknown; duplicate retry blocked')


class TestImport(BaseModel):
    title:str=Field(min_length=4,max_length=100)
    description:str=Field(max_length=4500)
    video_b64:str=Field(max_length=14000000)
    sha256:str=Field(pattern='^[a-f0-9]{64}$')
    made_for_kids:bool

@app.post('/api/test-import',dependencies=[Depends(require_admin)])
def test_import(body:TestImport):
    import base64, hashlib
    from renderer import probe,run
    try:data=base64.b64decode(body.video_b64,validate=True)
    except Exception:raise HTTPException(422,'Invalid base64')
    if len(data)>10*1024**2 or hashlib.sha256(data).hexdigest()!=body.sha256:
        raise HTTPException(422,'Media size or hash invalid')
    jid=body.sha256[:32];key='import:'+body.sha256
    with database() as c:
        old=c.execute('SELECT id,status FROM jobs WHERE key=?',(key,)).fetchone()
        if old:return dict(old)
    folder=ROOT/jid;folder.mkdir(parents=True,exist_ok=True)
    path=folder/'video.mp4';path.write_bytes(data)
    try:
        info=probe(path);duration=float(info['format']['duration'])
        vs=next(x for x in info['streams'] if x['codec_type']=='video')
        if vs['height']<=vs['width'] or not 12<=duration<=60:raise ValueError('Invalid vertical Short')
        run(['ffmpeg','-v','error','-i',str(path),'-f','null','-'])
    except Exception:raise HTTPException(422,'Media decode validation failed')
    qa={'sha256':body.sha256,'duration':duration,'width':vs['width'],'height':vs['height'],'full_decode':True}
    plan={'title':body.title,'topic':'cartoon-silent-test-v2','publication_ready':True,
          'made_for_kids':body.made_for_kids,'scenes':[],'sources':[],
          'rights':'Original code-drawn animation and original synthesized chimes. Fictional story. No synthetic voice.'}
    (folder/'metadata.json').write_text(json.dumps({'title':body.title,'description':body.description,'tags':['cartoon','Shorts','animation']}))
    (folder/'qa.json').write_text(json.dumps(qa))
    with database() as c:
        c.execute('INSERT INTO jobs(id,key,plan,status,created,updated,qa) VALUES(?,?,?,?,?,?,?)',
                  (jid,key,json.dumps(plan),'ready',time.time(),time.time(),json.dumps(qa)))
        event(c,jid,'imported_authorized_test',body.sha256)
    return {'id':jid,'status':'ready','qa':qa}


@app.get('/api/jobs/{jid}/status',dependencies=[Depends(require_admin)])
def job_status(jid:str):
    row=get_job(jid)
    return {'id':jid,'status':row['status'],'attempts':row['attempts'],'error':row['error'],
            'youtube_id':row['youtube_id'],'qa':json.loads(row['qa']) if row['qa'] else None}
