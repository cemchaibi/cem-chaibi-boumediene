#!/usr/bin/env python3
"""
مزامنة تلقائية لآخر فيديوهات ومنشورات المتوسطة إلى الملف media-feed.json
يعمل عبر GitHub Actions كل ساعة، ولا يحتاج خادماً خاصاً.

المصادر (كلها اختيارية، يُفعَّل ما تضبطه فقط):
  YT_CHANNEL_ID      معرّف قناة يوتيوب (يبدأ بـ UC...)  → عبر RSS الرسمي بلا مفتاح
  IG_ACCESS_TOKEN    رمز Instagram Graph API (حساب احترافي)
  FB_PAGE_ID + FB_PAGE_TOKEN   صفحة فيسبوك عبر Graph API
"""
import json, os, re, sys, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

MAX_ITEMS = 60
UA = 'Mozilla/5.0 (compatible; CemMediaSync/1.0)'
NS = {'a': 'http://www.w3.org/2005/Atom', 'yt': 'http://www.youtube.com/xml/schemas/2015', 'm': 'http://search.yahoo.com/mrss/'}


def http_get(url, timeout=25):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode('utf-8', 'replace')


def to_ms(iso):
    iso = (iso or '').replace('Z', '+00:00')
    iso = re.sub(r'([+-]\d{2})(\d{2})$', r'\1:\2', iso)          # +0000 -> +00:00 (فيسبوك)
    try:
        return int(datetime.fromisoformat(iso).timestamp() * 1000)
    except Exception:
        return 0


def first_line(text, limit=90):
    text = (text or '').strip()
    line = next((l.strip() for l in text.splitlines() if l.strip()), '')
    line = re.sub(r'\s+', ' ', line)
    return (line[:limit - 1] + '…') if len(line) > limit else line


def rest_text(text, title, limit=160):
    t = re.sub(r'\s+', ' ', (text or '').strip())
    if t.startswith(title.rstrip('…')):
        t = t[len(title.rstrip('…')):].strip()
    return (t[:limit - 1] + '…') if len(t) > limit else t


def parse_youtube_rss(xml_text):
    out = []
    root = ET.fromstring(xml_text)
    for e in root.findall('a:entry', NS):
        vid = (e.findtext('yt:videoId', default='', namespaces=NS) or '').strip()
        if not re.fullmatch(r'[\w-]{6,20}', vid):
            continue
        title = (e.findtext('a:title', default='', namespaces=NS) or '').strip()
        desc = (e.findtext('m:group/m:description', default='', namespaces=NS) or '').strip()
        out.append({'id': 'yt-' + vid, 'platform': 'youtube', 'url': 'https://www.youtube.com/watch?v=' + vid,
                    'title': title, 'desc': rest_text(desc, '', 160), 'ts': to_ms(e.findtext('a:published', default='', namespaces=NS)),
                    'source': 'auto'})
    return out


def fetch_youtube(channel_id):
    if not re.fullmatch(r'UC[\w-]{20,30}', channel_id or ''):
        print('YT_CHANNEL_ID غير صالح (يجب أن يبدأ بـ UC)'); return []
    return parse_youtube_rss(http_get('https://www.youtube.com/feeds/videos.xml?channel_id=' + channel_id))


def parse_instagram(payload):
    out = []
    for p in payload.get('data', []):
        link = p.get('permalink') or ''
        if not re.search(r'instagram\.com/(p|reel|tv)/', link):
            continue
        cap = p.get('caption') or ''
        title = first_line(cap) or 'منشور جديد على انستغرام'
        out.append({'id': 'ig-' + str(p.get('id')), 'platform': 'instagram', 'url': link, 'title': title,
                    'desc': rest_text(cap, title), 'ts': to_ms(p.get('timestamp')), 'source': 'auto'})
    return out


def fetch_instagram(token):
    url = 'https://graph.instagram.com/me/media?' + urllib.parse.urlencode(
        {'fields': 'id,caption,media_type,permalink,timestamp', 'limit': 12, 'access_token': token})
    return parse_instagram(json.loads(http_get(url)))


def parse_facebook(payload):
    out = []
    for p in payload.get('data', []):
        link = p.get('permalink_url') or ''
        if not link:
            continue
        msg = p.get('message') or ''
        title = first_line(msg) or 'منشور جديد على فيسبوك'
        out.append({'id': 'fb-' + str(p.get('id')), 'platform': 'facebook', 'url': link, 'title': title,
                    'desc': rest_text(msg, title), 'ts': to_ms(p.get('created_time')), 'source': 'auto'})
    return out


def fetch_facebook(page_id, token):
    url = 'https://graph.facebook.com/v19.0/%s/posts?' % urllib.parse.quote(page_id) + urllib.parse.urlencode(
        {'fields': 'message,permalink_url,created_time', 'limit': 12, 'access_token': token})
    return parse_facebook(json.loads(http_get(url)))


def merge(existing, fresh):
    by_id = {i['id']: i for i in existing if i.get('id')}
    for i in fresh:
        old = by_id.get(i['id'])
        if old:                                  # لا نمسح عنواناً أو وصفاً سبق جلبه
            for k in ('title', 'desc'):
                if not i.get(k) and old.get(k):
                    i[k] = old[k]
        by_id[i['id']] = i
    items = sorted(by_id.values(), key=lambda x: x.get('ts', 0), reverse=True)
    return items[:MAX_ITEMS]


def main():
    FEED_FILE = os.environ.get('FEED_FILE', 'media-feed.json')
    try:
        with open(FEED_FILE, encoding='utf-8') as f:
            feed = json.load(f)
    except Exception:
        feed = {'updated': '', 'items': []}
    existing = feed.get('items', [])
    fresh = []
    jobs = []
    if os.environ.get('YT_CHANNEL_ID'):
        jobs.append(('YouTube', lambda: fetch_youtube(os.environ['YT_CHANNEL_ID'].strip())))
    if os.environ.get('IG_ACCESS_TOKEN'):
        jobs.append(('Instagram', lambda: fetch_instagram(os.environ['IG_ACCESS_TOKEN'].strip())))
    if os.environ.get('FB_PAGE_ID') and os.environ.get('FB_PAGE_TOKEN'):
        jobs.append(('Facebook', lambda: fetch_facebook(os.environ['FB_PAGE_ID'].strip(), os.environ['FB_PAGE_TOKEN'].strip())))
    if not jobs:
        print('لا توجد مصادر مفعّلة: اضبط YT_CHANNEL_ID أو رموز انستغرام/فيسبوك في إعدادات المستودع.')
    for name, fn in jobs:
        try:
            got = fn(); fresh += got; print('%s: %d عنصر' % (name, len(got)))
        except Exception as e:                  # فشل مصدر لا يوقف البقية
            print('%s: فشل الجلب (%s)' % (name, e), file=sys.stderr)
    items = merge(existing, fresh) if fresh else existing
    if json.dumps(items, sort_keys=True, ensure_ascii=False) != json.dumps(existing, sort_keys=True, ensure_ascii=False):
        feed = {'updated': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'items': items}
        with open(FEED_FILE, 'w', encoding='utf-8') as f:
            json.dump(feed, f, ensure_ascii=False, indent=1)
        print('تم تحديث %s (%d عنصراً)' % (FEED_FILE, len(items)))
    else:
        print('لا جديد.')


if __name__ == '__main__':
    main()
