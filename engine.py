import json, time, uuid, threading, shutil, traceback, logging, os
from zoneinfo import ZoneInfo
from datetime import datetime, timezone
from store import database, event, setting, ROOT
from catalog import CATALOG, plan_for
from renderer import render

def feed_enabled():
    return os.environ.get('SHORTS_CONTENT_MODE')=='cartoon' and os.environ.get('SHORTS_FEED_ENABLED')=='1'

def publishable(plan, qa):
    return (plan.get('visual_style')=='cartoon' and plan.get('publication_ready')
            and qa.get('dialogue_validated')
            and (not plan.get('language_review_required') or
                 (plan.get('automated_language_review') and qa.get('language_validated'))))
LOG=logging.getLogger('shorts.worker')
STOP=threading.Event()

def enqueue(plan,key,scheduled_date=None):
    # Reject missing research rather than inventing a verified claim.
    if not plan.get('fictional') and (not plan.get('fact_checked') or not plan.get('sources')):raise ValueError('Verified source evidence required')
    if not 3<=len(plan['scenes'])<=12:raise ValueError('Expected 3–12 scenes')
    now=time.time();jid=uuid.uuid4().hex
    with database() as c:
        c.execute('BEGIN IMMEDIATE')
        if scheduled_date:
            old=c.execute('SELECT job FROM daily_slots WHERE date=?',(scheduled_date,)).fetchone()
            if old:return old[0],False
            plan=dict(plan,scheduled_date=scheduled_date)
        old=c.execute('SELECT id FROM jobs WHERE key=?',(key,)).fetchone()
        if old:return old[0],False
        c.execute('INSERT INTO jobs(id,key,plan,status,created,updated) VALUES(?,?,?,?,?,?)',(jid,key,json.dumps(plan),'queued',now,now))
        if scheduled_date:
            c.execute('INSERT INTO daily_slots(date,job) VALUES(?,?)',(scheduled_date,jid))
        event(c,jid,'queued')
    return jid,True

def enqueue_next(scheduled_date=None):
    with database() as c: used={r[0] for r in c.execute('SELECT key FROM jobs')}
    if feed_enabled():
        from story_feed import plans
        for plan in plans(refresh=True):
            if 'story:'+plan['topic'] not in used:
                with database() as c:
                    duplicate=any(json.loads(r[0]).get('script_sha256')==plan['script_sha256'] for r in c.execute('SELECT plan FROM jobs'))
                if not duplicate:return enqueue(plan,'story:'+plan['topic'],scheduled_date)
        return None,False
    if os.environ.get('SHORTS_CONTENT_MODE')=='cartoon':
        from cartoon_stories import STORIES,plan_for_story
        item=next((i for i in STORIES if 'story:'+i[0] not in used),None)
        return enqueue(plan_for_story(item),'story:'+item[0]) if item else (None,False)
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
        local=datetime.now(ZoneInfo('Asia/Kolkata'))
        today=local.date().isoformat()
        key='last_scheduled_v2' if feed_enabled() else 'last_daily'
        if os.environ.get('SHORTS_CONTENT_MODE')=='cartoon' and local.hour<9:
            today=None
        if today and setting(key)!=today:
            jid,created=enqueue_next(scheduled_date=today) if feed_enabled() else enqueue_next()
            from store import set_setting
            # A day is consumed only after a durable queue insert, never on exhaustion.
            if jid:
                set_setting(key,today)
                with database() as c:event(c,jid,'daily_scheduled',today)
            elif setting('supply_alert_date')!=today:
                set_setting('supply_alert_date',today)
                with database() as c:event(c,None,'story_supply_empty',today)
    with database() as c:
        c.execute('BEGIN IMMEDIATE')
        row=c.execute("SELECT * FROM jobs WHERE status='queued' AND attempts<3 ORDER BY created LIMIT 1").fetchone()
        if row:
            c.execute("UPDATE jobs SET status='rendering', attempts=attempts+1,updated=? WHERE id=?",(time.time(),row['id']))
            event(c,row['id'],'render_started')
    if row is None:return publish_next()
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

def publish_next():
    if os.environ.get('SHORTS_AUTO_PUBLISH')!='1' or os.environ.get('SHORTS_PUBLIC_PUBLISHING_ENABLED')!='1':return False
    import youtube
    from renderer import sha
    with database() as c:
        c.execute('BEGIN IMMEDIATE')
        rows=c.execute("SELECT * FROM jobs WHERE status='ready' AND youtube_id IS NULL ORDER BY created").fetchall()
        row=next((r for r in rows if publishable(json.loads(r['plan']),json.loads(r['qa'] or '{}'))),None)
        if row is None:return False
        plan=json.loads(row['plan']);qa=json.loads(row['qa'])
        if sha(ROOT/row['id']/'video.mp4')!=qa['sha256']:raise ValueError('Output changed after QA')
        c.execute("UPDATE jobs SET status='uploading',approved_hash=?,updated=? WHERE id=?",(qa['sha256'],time.time(),row['id']))
        event(c,row['id'],'auto_public_upload_started')
    try:
        result=youtube.upload_public(ROOT/row['id'],plan['made_for_kids'],
            on_uploaded=lambda vid:remember_upload(row['id'],vid))
        state='published' if result['verified_public'] else 'uploaded_not_public'
        with database() as c:
            c.execute('UPDATE jobs SET status=?,youtube_id=?,updated=? WHERE id=?',(state,result['youtube_id'],time.time(),row['id']))
            event(c,row['id'],state,result['youtube_id'])
    except Exception:
        LOG.exception('Automatic upload requires reconciliation')
        with database() as c:
            c.execute("UPDATE jobs SET status='upload_unknown',error='Remote upload requires reconciliation',updated=? WHERE id=?",(time.time(),row['id']))
            event(c,row['id'],'auto_upload_unknown')
    return True

def remember_upload(jid,vid):
    # Persist the remote ID before any follow-up request can fail.
    with database() as c:
        c.execute('UPDATE jobs SET youtube_id=?,updated=? WHERE id=?',(vid,time.time(),jid))
        event(c,jid,'remote_id_recorded',vid)

_last_reconcile=0.
def reconcile_known_uploads():
    global _last_reconcile
    if time.monotonic()-_last_reconcile<300:return
    _last_reconcile=time.monotonic()
    with database() as c:
        rows=c.execute("SELECT id,youtube_id FROM jobs WHERE status IN ('upload_unknown','uploaded_not_public') AND youtube_id IS NOT NULL").fetchall()
    if not rows:return
    import youtube
    api=youtube.client()
    for row in rows:
        result=api.videos().list(part='status',id=row['youtube_id']).execute()
        if any(v['status'].get('privacyStatus')=='public' for v in result.get('items',[])):
            with database() as c:
                c.execute("UPDATE jobs SET status='published',error=NULL,updated=? WHERE id=?",(time.time(),row['id']))
                event(c,row['id'],'published_reconciled',row['youtube_id'])

def prune_old_assets():
    # Retain DB IDs/scripts forever for deduplication; bounded media avoids volume exhaustion.
    cutoff=time.time()-14*86400
    with database() as c:
        rows=c.execute("SELECT id FROM jobs WHERE status='published' AND updated<?",(cutoff,)).fetchall()
    for row in rows:
        folder=ROOT/row['id']
        if folder.is_dir():shutil.rmtree(folder)


def worker():
    recover()
    while not STOP.is_set():
        try:
            reconcile_known_uploads()
            prune_old_assets()
            worked=tick()
        except Exception:LOG.exception('Worker tick failed');worked=False
        STOP.wait(2 if worked else 15)


def catalog_status():
    if feed_enabled():
        from story_feed import plans
        entries=[('story:'+p['topic'],p) for p in plans()]
    elif os.environ.get('SHORTS_CONTENT_MODE')=='cartoon':
        from cartoon_stories import STORIES,plan_for_story
        entries=[('story:'+item[0],plan_for_story(item)) for item in STORIES]
    else:entries=[('topic:'+item['slug'],plan_for(item)) for item in CATALOG]
    with database() as c:used={row[0] for row in c.execute('SELECT key FROM jobs')}
    pending=[plan for key,plan in entries if key not in used]
    return {'total':len(entries),'remaining':len(pending),
            'remaining_publishable':sum(bool(p.get('publication_ready')) and (not p.get('language_review_required',False) or p.get('automated_language_review')) for p in pending),
            'next_topic':pending[0]['topic'] if pending else None}
