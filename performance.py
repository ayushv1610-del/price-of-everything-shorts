"""Bounded, read-only public statistics. No estimates of retention or revenue."""
import json, os, time
from store import database, setting, set_setting, event

def summary():
    return setting('public_performance', {'status':'not_checked','checked_at':None})

def refresh():
    now=time.time()
    if now-setting('performance_attempt_at',0)<3600:return
    set_setting('performance_attempt_at',now)
    with database() as c:
        ids=[r[0] for r in c.execute("SELECT DISTINCT youtube_id FROM jobs WHERE status='published' AND youtube_id IS NOT NULL ORDER BY updated DESC LIMIT 50")]
    if not ids:return
    try:
        import youtube
        expected=os.environ.get('YOUTUBE_CHANNEL_ID')
        if not expected:raise ValueError('Channel identity unavailable')
        result=youtube.client().videos().list(part='snippet,status,statistics',id=','.join(ids)).execute(num_retries=0)
        rows=[]
        for item in result.get('items',[]):
            if item.get('id') not in ids:continue
            if item.get('status',{}).get('privacyStatus')!='public':continue
            if item.get('snippet',{}).get('channelId')!=expected:continue
            stats=item.get('statistics',{})
            # Unavailable is distinct from a real zero, including disabled comments.
            def count(key):
                v=stats.get(key)
                return int(v) if isinstance(v,(str,int)) and str(v).isdigit() else None
            rows.append({'youtube_id':item['id'],'views':count('viewCount'),
                         'likes':count('likeCount'),'comments':count('commentCount')})
        rows.sort(key=lambda r: r['views'] if r['views'] is not None else -1,reverse=True)
        data={'status':'ok' if len(rows)==len(ids) else 'partial',
              'checked_at':now,'requested_videos':len(ids),'verified_public_videos':len(rows),
              'scope':'latest_50_recorded_published_videos',
              'views_reported':sum(r['views'] for r in rows if r['views'] is not None),
              'videos_with_view_counts':sum(r['views'] is not None for r in rows),
              'retention_available':False,'videos':rows}
        set_setting('public_performance',data)
        with database() as c:event(c,None,'performance_snapshot',json.dumps(data))
    except Exception as exc:
        previous=summary()
        previous.update(status='unavailable',last_attempt_at=now,error_type=type(exc).__name__)
        set_setting('public_performance',previous)
