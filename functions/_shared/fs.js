// أدوات مشتركة: قراءة بيانات الأخبار من Firestore (قراءة عامة حسب القواعد) وبناء وسوم المعاينة
export const PROJECT_ID = 'chaibi-1c3aa';
export const API_KEY = 'AIzaSyDZ4hr_MISEoJs67DrPLYxqO0LfsSYPtXY';   // مفتاح الويب العام نفسه المستعمل في الموقع
const BASE = `https://firestore.googleapis.com/v1/projects/${PROJECT_ID}/databases/(default)/documents`;

// يحوّل قيمة Firestore REST المكتوبة {stringValue:..} إلى قيمة JavaScript عادية
export function decode(v){
  if(v == null) return null;
  if('stringValue' in v) return v.stringValue;
  if('integerValue' in v) return Number(v.integerValue);
  if('doubleValue' in v) return v.doubleValue;
  if('booleanValue' in v) return v.booleanValue;
  if('timestampValue' in v) return v.timestampValue;
  if('arrayValue' in v) return (v.arrayValue.values || []).map(decode);
  if('mapValue' in v){ const o = {}; const f = v.mapValue.fields || {}; for(const k of Object.keys(f)) o[k] = decode(f[k]); return o; }
  return null;
}

async function getDoc(path){
  const r = await fetch(`${BASE}/${path}?key=${API_KEY}`, { headers: { accept: 'application/json' }, cf: { cacheTtl: 120, cacheEverything: true } });
  if(!r.ok) return null;
  const j = await r.json();
  const out = {}; for(const k of Object.keys(j.fields || {})) out[k] = decode(j.fields[k]);
  return out;
}

export const todayIso = () => new Date().toISOString().slice(0, 10);

// قائمة الأخبار المنشورة (بعد استبعاد المجدولة لتاريخ لاحق)
export async function getNewsList(){
  const d = await getDoc('siteData/site-news');
  const items = (d && Array.isArray(d.items)) ? d.items : [];
  const t = todayIso();
  return items.filter(n => n && n.id && (!n.iso || n.iso <= t));
}
export async function getNewsItem(id){ return (await getNewsList()).find(n => n.id === id) || null; }
export async function getNewsFull(id){ return getDoc(`newsFull/${encodeURIComponent(id)}`); }

export const esc = s => String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
export const clip = (s, n) => { s = String(s || '').replace(/\s+/g, ' ').trim(); return s.length > n ? s.slice(0, n - 1) + '…' : s; };
export const cleanId = s => String(s || '').replace(/[^\w-]/g, '').slice(0, 60);

// يستبدل أول تطابق وسماً بآخر (يتجاهل إن لم يوجد)
export function swap(html, re, repl){ return re.test(html) ? html.replace(re, repl) : html; }
