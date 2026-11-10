# الانتقال إلى نطاق أفضل ومجاني: Cloudflare Pages

## لماذا هذا الاختيار؟
| | GitHub Pages (الحالي) | **Cloudflare Pages (الجديد)** |
|---|---|---|
| العنوان | `cemchaibi.github.io/cem-chaibi-boumediene` | **`chaibi-boumediene.pages.dev`** (قصير، بلا مجلد فرعي) |
| الروابط | `…/#news` (لا تُفهرس جيداً) | **`/news` و`/timetable` و`/n/رقم-الخبر`** روابط نظيفة |
| معاينة المشاركة (واتساب/فيسبوك) | واحدة لكل الموقع | **لكل خبر: عنوانه + ملخصه + صورته** |
| السرعة والعرض | جيد | شبكة عالمية بلا حدّ للزيارات |
| التكلفة | مجاني | **مجاني** |

> **ملاحظة صريحة:** لا يوجد نطاق «.com» أو «.dz» مجاني حقاً. `.pages.dev` هو أفضل نطاق مجاني قصير وموثوق. وإن اشتريتَ لاحقاً نطاقاً خاصاً (مثلاً `.com` بنحو 10 دولارات سنوياً) فيُربط بالموقع نفسه بنقرات قليلة دون أي تغيير في الملفات.

---

## الخطوة 1: ارفع الملفات الجديدة
افتح GitHub Desktop (كما فعلتَ سابقاً) وانسخ **كل** محتويات الحزمة الجديدة إلى مجلد المستودع واستبدل الموجود، ثم **Commit** ثم **Push**.
تأكد أن هذه موجودة في جذر المستودع: `functions/` و`_headers` و`_routes.json` و`site-origin.js` والأيقونات (`favicon-*.png`، `favicon.ico`).

## الخطوة 2: أنشئ الموقع على Cloudflare (مجاناً، دقائق قليلة)
1. افتح [dash.cloudflare.com](https://dash.cloudflare.com) وأنشئ حساباً مجانياً (بريد إلكتروني وكلمة مرور).
2. من القائمة: **Workers & Pages ← Create ← تبويب Pages ← Connect to Git**.
3. اربط حساب GitHub واختر مستودع `cem-chaibi-boumediene` فقط.
4. الإعدادات:
   - **Project name:** `chaibi-boumediene`  ← يصبح عنوانك `chaibi-boumediene.pages.dev`
   - **Production branch:** `main`
   - **Framework preset:** `None`
   - **Build command:** اتركه **فارغاً**
   - **Build output directory:** اكتب `/` (أو اتركه فارغاً)
5. اضغط **Save and Deploy** وانتظر دقيقة. سيظهر لك الرابط.

> إن كان الاسم محجوزاً اختر اسماً آخر (مثل `cem-chaibi`)، ثم عدّل **السطر الأول** في الملف `site-origin.js` ليطابق عنوانك الحقيقي وارفعه. كل شيء آخر يتحدث تلقائياً (الروابط والوسوم وخريطة الموقع).

من الآن يُنشر الموقع **تلقائياً** عند كل Push إلى GitHub.

## الخطوة 3: السماح لتسجيل الدخول بالعنوان الجديد (مهم جداً)
بدونها يفشل الدخول بـ Google/Facebook على العنوان الجديد.
1. [console.firebase.google.com](https://console.firebase.google.com) ← مشروعك ← **Authentication ← Settings ← Authorized domains ← Add domain**.
2. اكتب `chaibi-boumediene.pages.dev` (دون https) ثم **Add**.
3. فيسبوك: [developers.facebook.com](https://developers.facebook.com) ← تطبيقك ← **Settings ← Basic ← App Domains** أضف النطاق الجديد.
4. إن كنتَ قد قيّدتَ مفتاح API بنطاقات (Google Cloud ← APIs & Services ← Credentials) فأضف `https://chaibi-boumediene.pages.dev/*`.

## الخطوة 4: اختبر
- `https://chaibi-boumediene.pages.dev/` ثم `/news` و`/timetable` و`/qa`.
- من لوحة الإدارة ← الأخبار ← زر **🔗 رابط** بجانب أي خبر ينسخ رابطه المميز `/n/…`.
- الصق رابط خبر في [Facebook Sharing Debugger](https://developers.facebook.com/tools/debug/) لترى بطاقته (العنوان والملخص والصورة). وهو الذي يُحدّث المعاينة المخزّنة إن لم تتغير.
- سجّل الدخول بـ Google للتأكد.

## الخطوة 5: حوِّل زوار العنوان القديم تلقائياً
بعد أن يعمل الموقع الجديد، افتح `site-origin.js` وغيّر:
```
window.SITE_REDIRECT = false;   →   window.SITE_REDIRECT = true;
```
ثم ارفع الملف. عندها يُحوَّل كل من يفتح رابطاً قديماً على github.io إلى مقابله الجديد (حتى روابط الأخبار القديمة `#article-…` تتحول إلى `/n/…`).

## الخطوة 6: ظهور أفضل في Google (باسم المتوسطة وبشعارها)
ما أعددتُه في الموقع:
- بيانات منظّمة (`WebSite` + `School`) باسم «متوسطة شعيبي بومدين» وأسماء بديلة، وهي ما يعتمد عليه Google لاسم الموقع بدل «GitHub Pages documentation».
- أيقونات بمقاسات 48/96/192 و`favicon.ico` وهي ما يشترطه Google لعرض الشعار.
- عنوان ووصف وصورة مشاركة مستقلة لكل قسم، وخريطة موقع `sitemap.xml` + `sitemap-news.xml` (لكل الأخبار تلقائياً).

ما عليك فعله:
1. [Google Search Console](https://search.google.com/search-console) ← **Add property ← URL prefix** ← `https://chaibi-boumediene.pages.dev/`.
2. التحقق: اختر **HTML tag**، وانسخ وسم `<meta name="google-site-verification" ...>` والصقه في `index.html` داخل `<head>` (ابحث عن التعليق المخصص لذلك)، ثم ارفعه واضغط Verify.
3. **Sitemaps** ← أضف `sitemap.xml` ثم `sitemap-news.xml`.
4. **URL Inspection** ← الصق عنوان الصفحة الرئيسية ← **Request indexing**.
5. أبقِ خاصية الموقع القديم في Search Console: مع التحويل وعلامة canonical ينتقل Google تدريجياً.

> **توقّع صادق:** Google هو من يقرر موعد تحديث اسم الموقع وشعاره، وقد يستغرق ذلك من أيام إلى أسابيع بعد أن يزحف على الموقع الجديد. لا توجد طريقة لفرضه فوراً. ولا تُنشئ أكثر من أيقونة أو شعار مختلف حتى لا تتضارب الإشارات.

## الشعار بجودة عالية
شعارك الحالي المتاح للنظام صغير (64 بكسل) فتبدو أيقونات Google والتطبيق ناعمة قليلاً. ارفع **`logo.png` مربعاً بمقاس 512×512 أو أكبر** إلى جذر المستودع، فيعيد Workflow «توليد الأيقونات وصفحات الأقسام» إنشاء كل الأيقونات منه تلقائياً بجودة كاملة.

## مشاكل شائعة
| المشكلة | الحل |
|---|---|
| الدخول بـ Google يفشل بخطأ domain | أضف النطاق في Firebase ← Authorized domains (الخطوة 3) |
| `/n/…` يعطي 404 | تأكد أن مجلد `functions` ورفع `_routes.json` موجودان في جذر المستودع، وانتظر نشر Cloudflare |
| معاينة المشاركة لم تتغير | استعمل Facebook Sharing Debugger لإعادة الجلب (الذاكرة المؤقتة) |
| بعض الصور مكسورة على `/n/…` | حدّث `index.html` و`sw.js` (الوسم `<base>` يُضاف تلقائياً من الدالة) |
| الاسم محجوز | اختر اسماً آخر وعدّل `site-origin.js` |
