// رابط مميّز لكل خبر: /n/<id>
// يعيد صفحة الموقع نفسها مع وسوم معاينة خاصة بالخبر (عنوان + ملخص + صورة) ليظهر مميزاً في واتساب وفيسبوك وتيليغرام وGoogle.
import { getNewsItem, esc, clip, cleanId, swap } from '../_shared/fs.js';

export async function onRequestGet({ request, params, env }){
  const url = new URL(request.url);
  const origin = url.origin;
  const id = cleanId(params.id);

  const asset = await env.ASSETS.fetch(new URL('/', request.url));
  let html = await asset.text();

  let item = null;
  try{ item = id ? await getNewsItem(id) : null; }catch(e){ item = null; }

  // الصفحات النسبية (الصور والسكربتات) تعمل من الجذر حتى داخل /n/
  html = html.replace('<head>', '<head>\n<base href="/">');
  html = html.replace('<body>', `<body data-page="article" data-article="${esc(id)}">`);

  if(item){
    const title = `${item.title} | متوسطة شعيبي بومدين`;
    const desc = clip(item.excerpt || item.title, 200);
    const pageUrl = `${origin}/n/${id}`;
    const img = `${origin}/n/${id}/image`;
    html = swap(html, /<title>[\s\S]*?<\/title>/, `<title>${esc(title)}</title>`);
    html = swap(html, /<meta name="description" content="[^"]*">/, `<meta name="description" content="${esc(desc)}">`);
    html = swap(html, /<meta property="og:title" content="[^"]*">/, `<meta property="og:title" content="${esc(item.title)}">`);
    html = swap(html, /<meta property="og:description" content="[^"]*">/, `<meta property="og:description" content="${esc(desc)}">`);
    html = swap(html, /<meta property="og:url" content="[^"]*">/, `<meta property="og:url" content="${esc(pageUrl)}">`);
    html = swap(html, /<meta property="og:image" content="[^"]*">/, `<meta property="og:image" content="${esc(img)}">`);
    html = swap(html, /<meta property="og:type" content="[^"]*">/, `<meta property="og:type" content="article">`);
    html = swap(html, /<meta name="twitter:title" content="[^"]*">/, `<meta name="twitter:title" content="${esc(item.title)}">`);
    html = swap(html, /<meta name="twitter:description" content="[^"]*">/, `<meta name="twitter:description" content="${esc(desc)}">`);
    html = swap(html, /<meta name="twitter:image" content="[^"]*">/, `<meta name="twitter:image" content="${esc(img)}">`);
    html = swap(html, /<link rel="canonical" href="[^"]*">/, `<link rel="canonical" href="${esc(pageUrl)}">`);
    const ld = {
      '@context': 'https://schema.org', '@type': 'NewsArticle', headline: clip(item.title, 110), description: desc,
      image: [img], mainEntityOfPage: pageUrl, inLanguage: 'ar',
      author: { '@type': 'Organization', name: 'متوسطة شعيبي بومدين' },
      publisher: { '@type': 'Organization', name: 'متوسطة شعيبي بومدين', logo: { '@type': 'ImageObject', url: `${origin}/favicon-512.png` } }
    };
    if(item.iso) ld.datePublished = item.iso;
    html = html.replace('</head>', `<script type="application/ld+json">${JSON.stringify(ld).replace(/</g, '\\u003c')}</script>\n</head>`);
  }

  return new Response(html, {
    status: item || !id ? 200 : 404,
    headers: { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'public, max-age=120, s-maxage=600' }
  });
}
