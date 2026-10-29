import json, time, uuid, threading, shutil, traceback, logging
from datetime import datetime, timezone
from store import database, event, setting, ROOT
from catalog import CATALOG, plan_for
from renderer import render
LOG=logging.getLogger('shorts.worker')
STOP=threading.Event()

def enqueue(plan,key):
    # Reject missing research rather than inventing a verified claim.
    if not plan.get('fact_checked') or not plan.get('sources'):raise ValueError('Verified source evidence required')
    if not 3<=len(plan['scenes'])<=12:raise ValueError('Expected 3–12 scenes')
    now=time.time();jid=uuid.uuid4().hex
    with database() as c:
        old=c.execute('SELECT id FROM jobs WHERE key=?',(key,)).fetchone()
        if old:return old[0],False
        c.execute('INSERT INTO jobs(id,key,plan,status,created,updated) VALUES(?,?,?,?,?,?)',(jid,key,json.dumps(plan),'queued',now,now))
        event(c,jid,'queued')
    return jid,True

def enqueue_next():
    with database() as c: used={r[0] for r in c.execute('SELECT key FROM jobs')}
    item=next((i for i in CATALOG if 'topic:'+i['slug'] not in used),None)
    return enqueue(plan_for(item),'topic:'+item['slug']) if item else (None,False)

def recover():
    with database() as c:
        # Ambiguous uploads are never retried automatically; they may have reached YouTube.
        for row in c.execute("SELECT id,status,attempts FROM jobs WHERE status IN ('rendering','uploading')").fetchall():
            state=('failed' if row['attempts']>=3 else 'queued') if row['status']=='rendering' else 'upload_unknown'
            c.execute('UPDATE jobs SET status=?,updated=? WHERE id=?',(state,time.time(),row['id']))
            event(c,row['id'],'recovered',state)

def tick():
    if setting('daily_enabled',True):
        today=datetime.now(timezone.utc).date().isoformat()
        with database() as c:
            row=c.execute("SELECT value FROM settings WHERE key='last_daily'").fetchone()
        if not row or json.loads(row[0])!=today:
            enqueue_next()
            from store import set_setting
            set_setting('last_daily',today)
    with database() as c:
        c.execute('BEGIN IMMEDIATE')
        row=c.execute("SELECT * FROM jobs WHERE status='queued' AND attempts<3 ORDER BY created LIMIT 1").fetchone()
        if not row:return False
        c.execute("UPDATE jobs SET status='rendering', attempts=attempts+1,updated=? WHERE id=?",(time.time(),row['id']))
        event(c,row['id'],'render_started')
    folder=ROOT/row['id']
    try:
        ROOT.mkdir(parents=True,exist_ok=True)
        if shutil.disk_usage(ROOT).free<150*1024**2:raise RuntimeError('Insufficient storage: need 150MB free')
        qa=render(json.loads(row['plan']),folder)
        with database() as c:
            c.execute("UPDATE jobs SET status='ready',qa=?,error=NULL,updated=? WHERE id=?",(json.dumps(qa),time.time(),row['id']))
            event(c,row['id'],'render_complete',json.dumps(qa))
    except Exception as e:
        LOG.exception('Render failed for %s',row['id'])
        state='failed' if row['attempts']+1>=3 else 'queued'
        with database() as c:
            c.execute('UPDATE jobs SET status=?,error=?,updated=? WHERE id=?',(state,str(e)[:1500],time.time(),row['id']))
            event(c,row['id'],'render_failed',type(e).__name__)
    return True

def worker():
    recover()
    while not STOP.is_set():
        try:worked=tick()
        except Exception:LOG.exception('Worker tick failed');worked=False
        STOP.wait(2 if worked else 15)
