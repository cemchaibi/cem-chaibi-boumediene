#!/usr/bin/env python3
"""
يولّد من index.html صفحات حقيقية لكل قسم (news.html, timetable.html ...) بعنوان ووصف ووسوم مشاركة خاصة بها،
ويحدّث sitemap.xml. هذا يجعل الأقسام قابلة للفهرسة في Google ولها معاينة مشاركة صحيحة في واتساب وفيسبوك.
التشغيل يدوياً:  python3 scripts/build_pages.py   (وتعمل تلقائياً عبر GitHub Actions عند تعديل index.html)
"""
import html, os, re
from datetime import date

BASE = 'https://cemchaibi.github.io/cem-chaibi-boumediene/'
PAGES = [
  ('news.html', 'news', 'الأخبار والمناسبات | متوسطة شعيبي بومدين', 'آخر أخبار متوسطة شعيبي بومدين والإعلانات الإدارية، مع تقويم المناسبات والاحتفالات القادمة.', 'الأخبار والمناسبات'),
  ('timetable.html', 'timetable', 'جدول الحصص والفروض | متوسطة شعيبي بومدين', 'جدول الحصص الأسبوعي لكل قسم وفوج، ومواعيد الفروض والاختبارات في متوسطة شعيبي بومدين.', 'جدول الحصص والفروض'),
  ('media.html', 'media', 'الوسائط: فيديوهات ومنشورات | متوسطة شعيبي بومدين', 'أحدث فيديوهات ومنشورات متوسطة شعيبي بومدين على يوتيوب وانستغرام وفيسبوك.', 'الوسائط'),
  ('qa.html', 'qa', 'فضاء الأسئلة | متوسطة شعيبي بومدين', 'فضاء يطرح فيه التلاميذ أسئلتهم حول الدروس والتمارين ويتناقشون بمساعدة الأساتذة.', 'فضاء الأسئلة'),
  ('about.html', 'about', 'عن المتوسطة واتصل بنا | متوسطة شعيبي بومدين', 'معلومات متوسطة شعيبي بومدين، سبل التواصل، الوثائق والاستمارات، وصندوق الاقتراحات والشكاوى.', 'عن المتوسطة'),
  ('privacy.html', 'privacy', 'سياسة الخصوصية | متوسطة شعيبي بومدين', 'كيف نحمي بياناتك في موقع متوسطة شعيبي بومدين وما نحفظه من تفضيلات.', 'سياسة الخصوصية'),
]


def sub_once(pattern, repl, text, flags=re.S):
    new, n = re.subn(pattern, lambda m: repl, text, count=1, flags=flags)
    return new if n else text


def build(index_text, fname, key, title, desc, h1):
    s = index_text
    t, d, url = html.escape(title, quote=True), html.escape(desc, quote=True), BASE + fname
    s = sub_once(r'<title>.*?</title>', '<title>%s</title>' % html.escape(title), s)
    s = sub_once(r'<meta name="description" content="[^"]*">', '<meta name="description" content="%s">' % d, s)
    s = sub_once(r'<meta property="og:title" content="[^"]*">', '<meta property="og:title" content="%s">' % t, s)
    s = sub_once(r'<meta property="og:description" content="[^"]*">', '<meta property="og:description" content="%s">' % d, s)
    s = sub_once(r'<meta property="og:url" content="[^"]*">', '<meta property="og:url" content="%s">' % url, s)
    s = sub_once(r'<meta name="twitter:title" content="[^"]*">', '<meta name="twitter:title" content="%s">' % t, s)
    s = sub_once(r'<meta name="twitter:description" content="[^"]*">', '<meta name="twitter:description" content="%s">' % d, s)
    s = sub_once(r'<link rel="canonical" href="[^"]*">', '<link rel="canonical" href="%s">' % url, s)
    s = s.replace('<body>', '<body data-page="%s">' % key, 1)
    # نص ثابت يراه الزاحف ومن عطّل JavaScript
    s = s.replace('<noscript><div style="background:#a8402f',
                  '<noscript><h1>%s</h1><p>%s</p></noscript>\n<noscript><div style="background:#a8402f' % (html.escape(h1), html.escape(desc)), 1)
    return s


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = open(os.path.join(root, 'index.html'), encoding='utf-8').read()
    for fname, key, title, desc, h1 in PAGES:
        with open(os.path.join(root, fname), 'w', encoding='utf-8') as f:
            f.write(build(src, fname, key, title, desc, h1))
    today = date.today().isoformat()
    urls = [('', '1.0', 'weekly')] + [(p[0], '0.8' if p[0] != 'privacy.html' else '0.3', 'weekly' if p[0] != 'privacy.html' else 'yearly') for p in PAGES]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for path, pr, fr in urls:
        sm.append('  <url><loc>%s%s</loc><lastmod>%s</lastmod><changefreq>%s</changefreq><priority>%s</priority></url>' % (BASE, path, today, fr, pr))
    sm.append('</urlset>')
    with open(os.path.join(root, 'sitemap.xml'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(sm) + '\n')
    print('تم توليد %d صفحة و sitemap.xml' % len(PAGES))


if __name__ == '__main__':
    main()
