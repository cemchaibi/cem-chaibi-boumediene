// صورة معاينة الخبر: /n/<id>/image
// الصور مخزنة داخل Firestore كنص base64؛ هذه الدالة تحوّلها إلى ملف صورة حقيقي يفهمه واتساب وفيسبوك.
import { getNewsFull, getNewsItem, cleanId } from '../../_shared/fs.js';

function dataUriToBytes(uri){
  const m = /^data:(image\/(?:jpeg|png|webp|gif));base64,([A-Za-z0-9+/=]+)$/.exec(uri || '');
  if(!m) return null;
  const bin = atob(m[2]);
  const bytes = new Uint8Array(bin.length);
  for(let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return { type: m[1], bytes };
}

export async function onRequestGet({ request, params }){
  const origin = new URL(request.url).origin;
  const id = cleanId(params.id);
  const fallback = () => Response.redirect(origin + '/og-image.png', 302);
  if(!id) return fallback();
  try{
    const item = await getNewsItem(id);
    if(!item) return fallback();
    const full = await getNewsFull(id);
    // الأفضلية: صورة المشاركة JPEG (1200×630)، ثم الصورة الأصلية، ثم المصغّرة
    const pic = dataUriToBytes(full && full.og) || dataUriToBytes(full && full.image) || dataUriToBytes(item.thumb);
    if(!pic) return fallback();
    return new Response(pic.bytes, { headers: { 'content-type': pic.type, 'cache-control': 'public, max-age=86400, s-maxage=86400' } });
  }catch(e){ return fallback(); }
}
