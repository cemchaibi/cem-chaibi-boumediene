// خريطة موقع ديناميكية لكل الأخبار المنشورة: /sitemap-news.xml
import { getNewsList, esc, todayIso } from './_shared/fs.js';

export async function onRequestGet({ request }){
  const origin = new URL(request.url).origin;
  let items = [];
  try{ items = await getNewsList(); }catch(e){}
  const today = todayIso();
  const urls = items.map(n => `  <url><loc>${esc(origin + '/n/' + n.id)}</loc><lastmod>${esc(n.iso || today)}</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>`).join('\n');
  const xml = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls}\n</urlset>\n`;
  return new Response(xml, { headers: { 'content-type': 'application/xml; charset=utf-8', 'cache-control': 'public, max-age=600' } });
}
