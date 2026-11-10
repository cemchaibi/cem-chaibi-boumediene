#!/usr/bin/env python3
"""
يولّد كل أيقونات الموقع (favicon.ico وأحجام PNG وأيقونة التطبيق) من شعار المتوسطة.
المصدر: logo.png إن وُجد (الأفضل: صورة مربعة 512x512 فما فوق)، وإلا favicon.png.
Google يشترط أن يكون حجم الأيقونة من مضاعفات 48 بكسل (48 / 96 / 144 / 192...)، ولذلك نولّد 48 و96 و192 و512.
"""
import os, sys
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRAND = (14, 59, 76, 255)      # #0e3b4c


def load_source():
    for name in ('logo.png', 'favicon.png'):
        p = os.path.join(ROOT, name)
        if os.path.exists(p):
            return name, Image.open(p).convert('RGBA')
    sys.exit('لا يوجد logo.png ولا favicon.png')


def square(img, size, pad=0.0, bg=None):
    """يضع الشعار داخل مربع size×size بحواف pad (نسبة) وبخلفية اختيارية، مع الحفاظ على النسبة."""
    canvas = Image.new('RGBA', (size, size), bg or (0, 0, 0, 0))
    inner = int(size * (1 - 2 * pad))
    w, h = img.size
    k = min(inner / w, inner / h)
    r = img.resize((max(1, int(w * k)), max(1, int(h * k))), Image.LANCZOS)
    canvas.alpha_composite(r, ((size - r.width) // 2, (size - r.height) // 2))
    return canvas


def main():
    name, src = load_source()
    out = lambda f: os.path.join(ROOT, f)
    for s in (48, 96, 192, 512):
        square(src, s, pad=0.04).save(out('favicon-%d.png' % s), optimize=True)
    # أيقونة آيفون: خلفية صلبة (iOS يحوّل الشفافية إلى أسود)
    square(src, 180, pad=0.10, bg=(255, 255, 255, 255)).convert('RGB').save(out('apple-touch-icon.png'), optimize=True)
    # أيقونة التطبيق القابلة للقص (maskable): خلفية بلون المتوسطة وهامش آمن 20%
    square(src, 512, pad=0.20, bg=BRAND).save(out('icon-maskable-512.png'), optimize=True)
    # favicon.ico متعدد الأحجام (Google يطلب /favicon.ico تلقائياً)
    square(src, 256, pad=0.04).save(out('favicon.ico'), sizes=[(16, 16), (32, 32), (48, 48)])
    print('تم توليد الأيقونات من', name)


if __name__ == '__main__':
    main()
