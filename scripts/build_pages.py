#!/usr/bin/env python3
"""
يولّد من index.html صفحات حقيقية لكل قسم (news.html, timetable.html ...) بعنوان ووصف وصورة معاينة خاصة بها،
ويحدّث sitemap.xml و robots.txt، ويوحّد عنوان الموقع في كل الوسوم اعتماداً على الملف site-origin.js.
يعمل تلقائياً عبر GitHub Actions عند تعديل index.html أو site-origin.js.
التشغيل يدوياً:  python3 scripts/build_pages.py
"""
import html, os, re
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (الملف، المفتاح، العنوان، الوصف، العنوان الظاهر لمن عطّل JavaScript)
PAGES = [
  ('news.html', 'news', 'الأخبار والمناسبات | متوسطة شعيبي بومدين', 'آخر أخبار متوسطة شعيبي بومدين والإعلانات الإدارية، مع تقويم المناسبات والاحتفالات القادمة.', 'الأخبار والمناسبات'),
  ('timetable.html', 'timetable', 'جدول الحصص والفروض | متوسطة شعيبي بومدين', 'جدول الحصص الأسبوعي لكل قسم وفوج، ومواعيد الفروض والاختبارات في متوسطة شعيبي بومدين.', 'جدول الحصص والفروض'),
  ('media.html', 'media', 'الوسائط: فيديوهات ومنشورات | متوسطة شعيبي بومدين', 'أحدث فيديوهات ومنشورات متوسطة شعيبي بومدين على يوتيوب وانستغرام وفيسبوك.', 'الوسائط'),
  ('qa.html', 'qa', 'فضاء الأسئلة | متوسطة شعيبي بومدين', 'فضاء يطرح فيه التلاميذ أسئلتهم حول الدروس والتمارين ويتناقشون بمساعدة الأساتذة.', 'فضاء الأسئلة'),
  ('parents.html', 'parents', 'فضاء الأولياء | متوسطة شعيبي بومدين', 'فضاء تواصل خاص بأولياء التلاميذ تحت إشراف إدارة متوسطة شعيبي بومدين.', 'فضاء الأولياء'),
  ('about.html', 'about', 'عن المتوسطة واتصل بنا | متوسطة شعيبي بومدين', 'معلومات متوسطة شعيبي بومدين، سبل التواصل، الوثائق والاستمارات، وصندوق الاقتراحات والشكاوى.', 'عن المتوسطة'),
  ('privacy.html', 'privacy', 'سياسة الخصوصية | متوسطة شعيبي بومدين', 'كيف نحمي بياناتك في موقع متوسطة شعيبي بومدين وما نحفظه من تفضيلات.', 'سياسة الخصوصية'),
]


def read_origin():
    src = open(os.path.join(ROOT, 'site-origin.js'), encoding='utf-8').read()
    m = re.search(r"window\.SITE_ORIGIN\s*=\s*'([^']+)'", src)
    if not m:
        raise SystemExit('تعذر قراءة SITE_ORIGIN من site-origin.js')
    return m.group(1).rstrip('/') + '/'


def sub_once(pattern, repl, text, flags=re.S):
    new, n = re.subn(pattern, lambda m: repl, text, count=1, flags=flags)
    return new if n else text


def og_for(base, key):
    p = 'og-%s.png' % key
    return base + (p if os.path.exists(os.path.join(ROOT, p)) else 'og-image.png')


def build(index_text, base, fname, key, title, desc, h1):
    s = index_text
    t, d = html.escape(title, quote=True), html.escape(desc, quote=True)
    url, img = base + key, og_for(base, key)
    s = sub_once(r'<title>.*?</title>', '<title>%s</title>' % html.escape(title), s)
    s = sub_once(r'<meta name="description" content="[^"]*">', '<meta name="description" content="%s">' % d, s)
    s = sub_once(r'<meta property="og:title" content="[^"]*">', '<meta property="og:title" content="%s">' % t, s)
    s = sub_once(r'<meta property="og:description" content="[^"]*">', '<meta property="og:description" content="%s">' % d, s)
    s = sub_once(r'<meta property="og:url" content="[^"]*">', '<meta property="og:url" content="%s">' % url, s)
    s = sub_once(r'<meta property="og:image" content="[^"]*">', '<meta property="og:image" content="%s">' % img, s)
    s = sub_once(r'<meta name="twitter:image" content="[^"]*">', '<meta name="twitter:image" content="%s">' % img, s)
    s = sub_once(r'<meta name="twitter:title" content="[^"]*">', '<meta name="twitter:title" content="%s">' % t, s)
    s = sub_once(r'<meta name="twitter:description" content="[^"]*">', '<meta name="twitter:description" content="%s">' % d, s)
    s = sub_once(r'<link rel="canonical" href="[^"]*">', '<link rel="canonical" href="%s">' % url, s)
    s = s.replace('<body>', '<body data-page="%s">' % key, 1)
    s = s.replace('<noscript><div style="background:#a8402f',
                  '<noscript><h1>%s</h1><p>%s</p></noscript>\n<noscript><div style="background:#a8402f' % (html.escape(h1), html.escape(desc)), 1)
    return s


def main():
    base = read_origin()
    idx_path = os.path.join(ROOT, 'index.html')
    src = open(idx_path, encoding='utf-8').read()

    # توحيد عنوان الموقع في index.html نفسه (canonical / og / JSON-LD ...)
    m = re.search(r'<link rel="canonical" href="([^"]+)">', src)
    if m and m.group(1) != base:
        old = m.group(1)
        src = src.replace(old, base).replace(old.rstrip('/'), base.rstrip('/'))
        with open(idx_path, 'w', encoding='utf-8') as f:
            f.write(src)
        print('تم توحيد عنوان الموقع إلى', base)

    for fname, key, title, desc, h1 in PAGES:
        with open(os.path.join(ROOT, fname), 'w', encoding='utf-8') as f:
            f.write(build(src, base, fname, key, title, desc, h1))

    today = date.today().isoformat()
    rows = [('', '1.0', 'weekly')] + [(p[1], '0.3' if p[1] == 'privacy' else '0.8', 'yearly' if p[1] == 'privacy' else 'weekly') for p in PAGES]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for path, pr, fr in rows:
        sm.append('  <url><loc>%s%s</loc><lastmod>%s</lastmod><changefreq>%s</changefreq><priority>%s</priority></url>' % (base, path, today, fr, pr))
    sm.append('</urlset>')
    with open(os.path.join(ROOT, 'sitemap.xml'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(sm) + '\n')

    with open(os.path.join(ROOT, 'robots.txt'), 'w', encoding='utf-8') as f:
        f.write('User-agent: *\nAllow: /\nDisallow: /admin.html\nDisallow: /admin\n\nSitemap: %ssitemap.xml\nSitemap: %ssitemap-news.xml\n' % (base, base))
    print('تم توليد %d صفحة + sitemap.xml + robots.txt  (العنوان: %s)' % (len(PAGES), base))


if __name__ == '__main__':
    main()
