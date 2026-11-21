// POST /api/push  — يرسل إشعارات الهاتف (FCM) لأولياء التلاميذ المرتبطين
// يستدعيه برنامج الحضور بعد رفع إشعارات الغياب. يتطلب Authorization: Bearer <Firebase ID token> لحساب مصرّح (بوابة/مدير).
// المتغيرات (Cloudflare Pages ← Settings ← Variables and Secrets):
//   FCM_SERVICE_ACCOUNT  (Secret)  محتوى ملف JSON لحساب الخدمة (Service Account) كاملاً
const PROJECT = 'chaibi-1c3aa';
const API_KEY = 'AIzaSyDZ4hr_MISEoJs67DrPLYxqO0LfsSYPtXY';
const OWNER = 'cemchaibi@gmail.com';
const MAX_KEYS = 10, MAX_SENDS = 32;
const FS = `https://firestore.googleapis.com/v1/projects/${PROJECT}/databases/(default)/documents`;

const cors = { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': 'Content-Type, Authorization', 'Access-Control-Allow-Methods': 'POST, OPTIONS', 'Access-Control-Max-Age': '86400' };
const json = (o, status = 200) => new Response(JSON.stringify(o), { status, headers: { 'Content-Type': 'application/json', ...cors } });
export const onRequestOptions = () => new Response(null, { status: 204, headers: cors });

const b64u = (buf) => btoa(String.fromCharCode(...new Uint8Array(buf))).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
const b64uStr = (s) => b64u(new TextEncoder().encode(s));

async function serviceToken(sa) {
  const now = Math.floor(Date.now() / 1000);
  const head = b64uStr(JSON.stringify({ alg: 'RS256', typ: 'JWT' }));
  const claim = b64uStr(JSON.stringify({ iss: sa.client_email, scope: 'https://www.googleapis.com/auth/datastore https://www.googleapis.com/auth/firebase.messaging', aud: 'https://oauth2.googleapis.com/token', iat: now, exp: now + 3300 }));
  const pem = sa.private_key.replace(/-----[^-]+-----/g, '').replace(/\s+/g, '');
  const der = Uint8Array.from(atob(pem), (c) => c.charCodeAt(0));
  const key = await crypto.subtle.importKey('pkcs8', der, { name: 'RSASSA-PKCS1-v1_5', hash: 'SHA-256' }, false, ['sign']);
  const sig = await crypto.subtle.sign('RSASSA-PKCS1-v1_5', key, new TextEncoder().encode(head + '.' + claim));
  const r = await fetch('https://oauth2.googleapis.com/token', { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: 'grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer&assertion=' + head + '.' + claim + '.' + b64u(sig) });
  const j = await r.json();
  if (!j.access_token) throw new Error('service token failed');
  return j.access_token;
}

const val = (f) => f == null ? null : 'stringValue' in f ? f.stringValue : 'integerValue' in f ? +f.integerValue : 'booleanValue' in f ? f.booleanValue : 'timestampValue' in f ? f.timestampValue : 'arrayValue' in f ? (f.arrayValue.values || []).map(val) : null;
const docId = (s) => String(s).replace(/[\/\s]+/g, '_');

async function fsGet(tok, path) {
  const r = await fetch(`${FS}/${path}`, { headers: { Authorization: 'Bearer ' + tok } });
  if (r.status === 404) return null;
  if (!r.ok) throw new Error('fs ' + r.status);
  return r.json();
}
async function fsQuery(tok, col, field, op, value) {
  const body = { structuredQuery: { from: [{ collectionId: col }], where: { fieldFilter: { field: { fieldPath: field }, op, value } }, limit: 200 } };
  const r = await fetch(`${FS}:runQuery`, { method: 'POST', headers: { Authorization: 'Bearer ' + tok, 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  if (!r.ok) throw new Error('query ' + r.status);
  return (await r.json()).filter((x) => x.document).map((x) => x.document);
}

export async function onRequestPost({ request, env }) {
  try {
    if (!env.FCM_SERVICE_ACCOUNT) return json({ error: 'FCM_SERVICE_ACCOUNT not set' }, 503);
    const auth = request.headers.get('Authorization') || '';
    const idToken = auth.startsWith('Bearer ') ? auth.slice(7) : '';
    if (!idToken) return json({ error: 'unauthorized' }, 401);

    // 1) التحقق من هوية المستدعي
    const lk = await fetch('https://identitytoolkit.googleapis.com/v1/accounts:lookup?key=' + API_KEY, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ idToken }) });
    if (!lk.ok) return json({ error: 'invalid token' }, 401);
    const user = ((await lk.json()).users || [])[0];
    const email = ((user && user.email) || '').toLowerCase();
    if (!email) return json({ error: 'unauthorized' }, 401);

    const sa = JSON.parse(env.FCM_SERVICE_ACCOUNT);
    const tok = await serviceToken(sa);
    let allowed = email === OWNER && user.emailVerified;
    if (!allowed) {
      for (const d of ['admins', 'gate']) {
        const doc = await fsGet(tok, 'config/' + d);
        const list = doc && doc.fields && doc.fields.emails ? val(doc.fields.emails) : [];
        if ((list || []).map((x) => String(x).toLowerCase()).includes(email)) { allowed = true; break; }
      }
    }
    if (!allowed) return json({ error: 'forbidden' }, 403);

    // 2) المستندات المطلوب إرسالها
    const body = await request.json().catch(() => ({}));
    const keys = (Array.isArray(body.keys) ? body.keys : []).slice(0, MAX_KEYS).map(String);
    const done = [], skipped = [];
    let sends = 0, sent = 0;
    const origin = new URL(request.url).origin;

    for (const key of keys) {
      const nd = await fsGet(tok, 'parentNotices/' + encodeURIComponent(docId(key)));
      if (!nd || !nd.fields) { done.push(key); continue; }
      const f = nd.fields;
      if (f.pushedAt) { done.push(key); continue; }
      const studentId = val(f.studentId);
      const links = await fsQuery(tok, 'parentLinks', 'studentId', 'EQUAL', { stringValue: String(studentId) });
      const uids = [...new Set(links.map((d) => val(d.fields.uid)).filter(Boolean))];
      const tokens = [];
      for (const uid of uids) {
        const ts = await fsQuery(tok, 'pushTokens', 'uid', 'EQUAL', { stringValue: uid });
        ts.forEach((d) => tokens.push({ token: val(d.fields.token), name: d.name }));
      }
      if (sends + tokens.length > MAX_SENDS && sends > 0) { skipped.push(key); continue; }
      const kind = val(f.kind) || 'absence';
      const title = kind === 'announcement' ? (val(f.title) || 'إعلان من المتوسطة') : kind === 'alert' ? 'تنبيه: غياب متكرر — ' + val(f.name) : 'إشعار غياب — ' + val(f.name);
      for (const t of tokens) {
        sends++;
        const r = await fetch(`https://fcm.googleapis.com/v1/projects/${PROJECT}/messages:send`, {
          method: 'POST', headers: { Authorization: 'Bearer ' + tok, 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: { token: t.token, notification: { title, body: val(f.message) || '' }, data: { studentId: String(studentId), kind, url: origin + '/#my-children' }, webpush: { fcm_options: { link: origin + '/#my-children' }, notification: { icon: origin + '/favicon-192.png', dir: 'rtl', lang: 'ar' } } } }),
        });
        if (r.ok) sent++;
        else if (r.status === 404 || r.status === 400) { await fetch(`https://firestore.googleapis.com/v1/${t.name}`, { method: 'DELETE', headers: { Authorization: 'Bearer ' + tok } }); }
      }
      // علامة «تم الإرسال» حتى لا يتكرر (حتى لو لم يكن للولي جهاز مسجَّل: يراه داخل الموقع)
      await fetch(`${FS}/parentNotices/${encodeURIComponent(docId(key))}?updateMask.fieldPaths=pushedAt`, { method: 'PATCH', headers: { Authorization: 'Bearer ' + tok, 'Content-Type': 'application/json' }, body: JSON.stringify({ fields: { pushedAt: { timestampValue: new Date().toISOString() } } }) });
      done.push(key);
    }
    return json({ ok: true, done, skipped, sent });
  } catch (e) {
    return json({ error: String(e && e.message || e) }, 500);
  }
}
