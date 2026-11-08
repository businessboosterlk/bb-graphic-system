/* Pass marks for the From Thulaib card in the Graphic System (THULAIB CC HANDOFF, 8 Nov 2026).
   Adapted from bb-command-centre handoff/parts/handoff.check.mjs (the H5 half). Opens the real index.html signed in as
   FARHATH (team member 17) on a 390 px phone and a 1440 px desk with every Supabase call answered by test data, so
   nothing reaches the database. Checks the card's rows, the Done, Stuck and Carry on calls with their exact bodies,
   no card when there are no tasks, no card when signed out, the rest of the dashboard still drawn, and runSelfTest
   failing no more checks than origin/main does (pass a second url for main to compare).
   node handoff-from-card.check.mjs [base-url] [main-url] */
import { chromium } from '/Users/thulaibhassen/bb-systems/batch/node_modules/playwright/index.mjs';
const BASE = process.argv[2] || 'http://127.0.0.1:8841/index.html';
const MAIN = process.argv[3] || '';
const rows = []; let bad = 0, total = 0;
const pass = (name, ok, note = '') => { total++; if (!ok) bad++; rows.push(`${ok ? 'PASS' : 'FAIL'}  ${name}${note ? '  (' + note + ')' : ''}`); };

const CLIENTS = [{ id: 41, name: 'SASTHO' }, { id: 42, name: 'SUN ZAPPER' }, { id: 43, name: 'WAVERLEY' }];
/* tasks sent TO Farhath: one fresh, one late, one stuck with Thulaib's reply, one done today */
const CARD = [
  { id: 901, title: 'Redo the Waverley carousel cover', due: '2026-11-20', client_id: 43, notes: 'Use the new logo', sent_by: 'THULAIB', seen_at: null, stuck_note: null, stuck_at: null, stuck_reply: null, stuck_reply_at: null, done: false, done_note: null, completed_at: null, created_at: '2026-11-08T03:00:00Z' },
  { id: 902, title: 'Sastho shoot poster', due: '2026-11-02', client_id: 41, notes: null, sent_by: 'THULAIB', seen_at: '2026-11-07T03:00:00Z', stuck_note: null, stuck_at: null, stuck_reply: null, stuck_reply_at: null, done: false, done_note: null, completed_at: null, created_at: '2026-11-07T03:00:00Z' },
  { id: 903, title: 'Sun Zapper menu card', due: null, client_id: 42, notes: null, sent_by: 'THULAIB', seen_at: '2026-11-07T03:00:00Z', stuck_note: '07 Nov 10:15 Waiting on the prices', stuck_at: '2026-11-07T04:45:00Z', stuck_reply: 'Use last month for now', stuck_reply_at: '2026-11-07T05:00:00Z', done: false, done_note: null, completed_at: null, created_at: '2026-11-06T03:00:00Z' },
  { id: 904, title: 'Resize the leave poster', due: null, client_id: null, notes: null, sent_by: 'THULAIB', seen_at: '2026-11-08T03:00:00Z', stuck_note: null, stuck_at: null, stuck_reply: null, stuck_reply_at: null, done: true, done_note: 'Sent to Shiara', completed_at: '2026-11-08T05:00:00Z', created_at: '2026-11-05T03:00:00Z' }
];

async function page(b, opts, url, { cardRows = CARD, signedIn = true } = {}) {
  const ctx = await b.newContext({ ...opts, colorScheme: 'dark', serviceWorkers: 'block' });
  await ctx.addInitScript((si) => {
    if (si) { sessionStorage.setItem('bbgfx_user', JSON.stringify({ name: 'FARHATH' })); sessionStorage.setItem('bbgfx_pass', 'test-pass'); }
    try { localStorage.setItem('bbgfx_guide_seen', '1'); } catch (e) {}
  }, signedIn);
  const calls = [], writes = [];
  await ctx.route(/supabase\.co\//, async (route) => {
    const req = route.request(), u = new URL(req.url());
    const json = (body, status = 200) => route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(body) });
    if (req.method() !== 'GET' && req.method() !== 'HEAD') writes.push(req.method() + ' ' + u.pathname);
    if (u.pathname === '/rest/v1/rpc/app_session_check') return json('FARHATH');
    if (u.pathname.startsWith('/rest/v1/rpc/bb_handoff_')) {
      const name = u.pathname.split('/').pop(); calls.push({ name, body: JSON.parse(req.postData() || '{}') }); return json({ ok: true });
    }
    if (u.pathname === '/rest/v1/clients') return json(CLIENTS);
    if (u.pathname === '/rest/v1/tasks' && u.search.includes('sent_to_id=eq.17')) { calls.push({ name: 'GET tasks', body: u.search }); return json(cardRows); }
    if (u.pathname.startsWith('/functions/')) return json({});
    return json([]);
  });
  const p = await ctx.newPage();
  const errs = [], cerrs = [];
  p.on('pageerror', e => errs.push(String(e.message || e)));
  p.on('console', m => { if (m.type() === 'error') cerrs.push(m.text()); });
  await p.goto(url, { waitUntil: 'domcontentloaded' });
  if (signedIn) await p.waitForSelector('#appShell.active', { timeout: 15000 }).catch(() => {});
  await p.waitForTimeout(1500);
  return { ctx, p, calls, writes, errs, cerrs };
}

async function selftestFails(b, url) {
  const { ctx, p } = await page(b, { viewport: { width: 1440, height: 900 } }, url);
  const r = await p.evaluate(async () => { const x = await window.runSelfTest(); return x.results.filter(r => !r.pass).map(r => r.name); }).catch(e => ['runSelfTest threw: ' + e.message]);
  const all = await p.evaluate(() => 1).catch(() => 0);
  await ctx.close(); return r;
}

/* BUILD 5 speed (bb-speed rule 4): no picture pasted into the page over the 20 KB budget. The BB logo sat in the page
   twice as a 37 KB base64 PNG (100 KB of the page); it now loads from bb-logo.png beside the page. */
{
  const { readFileSync } = await import('node:fs');
  const html = readFileSync(new URL('./index.html', import.meta.url), 'utf8');
  const big = (html.match(/data:image\/[a-z+]+;base64,[A-Za-z0-9+\/=]+/g) || []).map(x => Math.round(x.length * 0.75 / 1024)).filter(k => k > 20);
  pass('no image pasted into the page over 20 KB', big.length === 0, big.map(k => k + ' KB').join(', '));
  pass('both BB logos load bb-logo.png with a set size', (html.match(/<img class="(bb-logo-img|sidebar-bb-logo-img)" src="bb-logo\.png" width="834" height="338"/g) || []).length === 2);
}
const b = await chromium.launch();
for (const [size, opts] of [['phone', { viewport: { width: 390, height: 844 }, deviceScaleFactor: 3, isMobile: true, hasTouch: true }], ['desk', { viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 }]]) {
  const L = size;
  const { ctx, p, calls, writes, errs, cerrs } = await page(b, opts, BASE);
  await p.waitForSelector('#ho-card-mount .ho-card', { timeout: 10000 }).catch(() => {});
  const card = p.locator('#ho-card-mount .ho-card');
  pass(`${L} signed in as Farhath, the dashboard is the first screen`, await p.locator('#section-dashboard.active').count() === 1);
  const pos = await p.evaluate(() => { const m = document.getElementById('ho-card-mount'), c = m && m.querySelector('.ho-card'); const r = c && c.getBoundingClientRect();
    return { first: m && m.parentNode.id === 'section-dashboard' && m.parentNode.firstElementChild === m, shown: !!(c && getComputedStyle(c).display !== 'none' && r.height > 40), top: r ? Math.round(r.top) : -1, inView: r ? r.top < innerHeight : false }; });
  pass(`${L} card sits first on the dashboard and shows on the first screen`, pos.first && pos.shown && pos.inView, JSON.stringify(pos));
  const q = calls.find(c => c.name === 'GET tasks');
  pass(`${L} card reads only Farhath's tasks (sent_to_id 17, not cancelled)`, q && /sent_to_id=eq\.17&cancelled_at=is\.null/.test(q.body), q && q.body.slice(0, 80));
  pass(`${L} card shows From Thulaib`, (await card.locator('.ho-card-title').textContent().catch(() => '')) === 'From Thulaib');
  pass(`${L} card says 3 to do`, (await card.locator('.ho-card-sub').textContent().catch(() => '')) === '3 to do');
  pass(`${L} card rows in order, done last`, (await card.locator('.ho-t-title').allTextContents()).join('|') === 'Redo the Waverley carousel cover|Sastho shoot poster|Sun Zapper menu card|Resize the leave poster');
  pass(`${L} client names come from this system's clients list`, (await card.locator('.ho-task[data-id="901"] .ho-t-meta').textContent().catch(() => '')) === 'WAVERLEY · by Fri 20 Nov', await card.locator('.ho-task[data-id="901"] .ho-t-meta').textContent().catch(() => ''));
  pass(`${L} late row says was due`, (await card.locator('.ho-task[data-id="902"] .ho-late').textContent().catch(() => '')) === 'was due Mon 2 Nov');
  pass(`${L} done row shows the what I did line`, (await card.locator('.ho-task[data-id="904"] .ho-t-meta').textContent().catch(() => '')) === 'Done · Sent to Shiara');
  const seen = calls.filter(c => c.name === 'bb_handoff_seen' && c.body.p_carry_on === false);
  pass(`${L} an unseen row is marked seen once, as FARHATH`, seen.length === 1 && seen[0].body.p_id === 901 && seen[0].body.p_who === 'FARHATH', JSON.stringify(seen.map(c => c.body)));
  /* Done with the optional line */
  let k = calls.length;
  await card.locator('.ho-task[data-id="901"] button:has-text("Done")').click(); await p.waitForTimeout(150);
  const inp = card.locator('.ho-task[data-id="901"] .ho-t-form .ho-in');
  const fs = await inp.evaluate(x => parseFloat(getComputedStyle(x).fontSize)).catch(() => 0);
  pass(`${L} Done opens a What I did line at 16px`, fs >= 16 && (await inp.getAttribute('placeholder')) === 'What I did (optional)', fs + 'px');
  await inp.fill('New cover uploaded');
  await card.locator('.ho-task[data-id="901"] button:has-text("Mark done")').click(); await p.waitForTimeout(500);
  let c = calls.slice(k).find(x => x.name === 'bb_handoff_done');
  pass(`${L} Mark done calls bb_handoff_done { p_id 901, p_who FARHATH, p_note }`, c && c.body.p_id === 901 && c.body.p_who === 'FARHATH' && c.body.p_note === 'New cover uploaded', JSON.stringify(c && c.body));
  pass(`${L} the toast says Thulaib can see it`, await p.locator('#toastWrap .toast', { hasText: 'Done. Thulaib can see it' }).count() >= 1);
  /* Done with nothing typed sends null */
  k = calls.length;
  await card.locator('.ho-task[data-id="902"] button:has-text("Done")').click(); await card.locator('.ho-task[data-id="902"] button:has-text("Mark done")').click(); await p.waitForTimeout(500);
  c = calls.slice(k).find(x => x.name === 'bb_handoff_done');
  pass(`${L} Mark done with no line sends p_note null`, c && c.body.p_id === 902 && c.body.p_note === null, JSON.stringify(c && c.body));
  /* Stuck needs a reason */
  k = calls.length;
  await card.locator('.ho-task[data-id="902"] button:has-text("Stuck")').click(); await card.locator('.ho-task[data-id="902"] .ho-t-form button:has-text("Send")').click(); await p.waitForTimeout(200);
  pass(`${L} Stuck with nothing typed asks why and calls nothing`, calls.slice(k).filter(x => x.name.startsWith('bb_')).length === 0 && (await card.locator('.ho-task[data-id="902"] .ho-err').textContent().catch(() => '')) === 'Say what is in the way first.');
  await card.locator('.ho-task[data-id="902"] .ho-t-form .ho-in').fill('No photos from the shoot yet');
  await card.locator('.ho-task[data-id="902"] .ho-t-form button:has-text("Send")').click(); await p.waitForTimeout(500);
  c = calls.slice(k).find(x => x.name === 'bb_handoff_stuck');
  pass(`${L} Stuck calls bb_handoff_stuck { p_id 902, p_who FARHATH, p_note }`, c && c.body.p_id === 902 && c.body.p_who === 'FARHATH' && c.body.p_note === 'No photos from the shoot yet', JSON.stringify(c && c.body));
  /* Carry on after a reply */
  pass(`${L} the stuck row shows the reply`, (await card.locator('.ho-task[data-id="903"] .ho-t-reply').textContent().catch(() => '')) === 'Thulaib: Use last month for now');
  pass(`${L} Carry on shows only after a reply`, await card.locator('button:has-text("Carry on")').count() === 1 && await card.locator('.ho-task[data-id="903"] button:has-text("Carry on")').count() === 1);
  k = calls.length;
  await card.locator('.ho-task[data-id="903"] button:has-text("Carry on")').click(); await p.waitForTimeout(500);
  c = calls.slice(k).find(x => x.name === 'bb_handoff_seen');
  pass(`${L} Carry on calls bb_handoff_seen { p_id 903, p_who FARHATH, p_carry_on true }`, c && c.body.p_id === 903 && c.body.p_who === 'FARHATH' && c.body.p_carry_on === true, JSON.stringify(c && c.body));
  const btns = await p.evaluate(() => [...document.querySelectorAll('#ho-card-mount button')].filter(x => x.offsetParent).map(x => ({ t: x.textContent, h: x.getBoundingClientRect().height, bg: getComputedStyle(x).backgroundColor, cut: x.scrollWidth > x.clientWidth + 1 })));
  pass(`${L} every card button is 44px tall, none cut`, btns.length >= 6 && btns.every(x => x.h >= 43.5 && !x.cut), btns.filter(x => x.h < 43.5 || x.cut).map(x => x.t).join(','));
  const prim = btns.filter(x => x.t === 'Done' || x.t === 'Carry on');
  pass(`${L} primary buttons wear the accent (the page has no btn-primary of its own)`, prim.some(x => x.bg !== 'rgba(0, 0, 0, 0)' && x.bg !== 'rgb(239, 239, 239)'), prim.map(x => x.t + ' ' + x.bg).join(', '));
  /* nothing else on the first screen broke */
  pass(`${L} the dashboard still draws its stats and pipeline`, await p.locator('#dashStats .stat-card').count() >= 4 && await p.locator('#dashPipeline > *').count() >= 1);
  await p.evaluate(() => navigateTo('pipeline')); await p.waitForTimeout(300); await p.evaluate(() => navigateTo('dashboard')); await p.waitForTimeout(300);
  pass(`${L} away to the pipeline and back, the card is still there and only one page is active`, await p.locator('#section-dashboard #ho-card-mount .ho-card').count() === 1 && await p.locator('.content section.active').count() === 1);
  const over = await p.evaluate(() => document.documentElement.scrollWidth - innerWidth);
  pass(`${L} page never scrolls sideways`, over <= 0, over + 'px');
  if (size === 'phone') await p.screenshot({ path: '/private/tmp/claude-501/-Users-thulaibhassen-bb-command-centre--claude-worktrees-vigilant-cannon-efb76a/51ff8c77-f434-488b-840b-24afbe57c7b8/scratchpad/gfx-phone-card.png' });
  else await p.screenshot({ path: '/private/tmp/claude-501/-Users-thulaibhassen-bb-command-centre--claude-worktrees-vigilant-cannon-efb76a/51ff8c77-f434-488b-840b-24afbe57c7b8/scratchpad/gfx-desk-card.png' });
  /* sign out takes the card away */
  await p.evaluate(() => logout()); await p.waitForTimeout(300);
  pass(`${L} sign out removes the card`, await p.locator('#ho-card-mount').count() === 0);
  const other = writes.filter(w => !/\/rest\/v1\/rpc\/(bb_handoff_(seen|done|stuck)|app_session_check|app_session_end)$/.test(w) && !/team_login_logs|functions\//.test(w));
  pass(`${L} the card writes only through bb_handoff_*`, other.length === 0, other.join(', '));
  pass(`${L} no page errors and no console errors`, errs.length === 0 && cerrs.length === 0, [...errs, ...cerrs].slice(0, 3).join(' | '));
  await ctx.close();
}
/* no tasks: no card at all */
for (const [size, opts] of [['phone', { viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true }], ['desk', { viewport: { width: 1440, height: 900 } }]]) {
  const { ctx, p, errs } = await page(b, opts, BASE, { cardRows: [] });
  const r = await p.evaluate(() => { const m = document.getElementById('ho-card-mount'); return { m: !!m, hidden: m && m.hidden, h: m ? m.getBoundingClientRect().height : 0, cards: document.querySelectorAll('.ho-card').length }; });
  pass(`${size} no tasks: no card, nothing takes space`, r.m && r.hidden && r.h === 0 && r.cards === 0, JSON.stringify(r));
  pass(`${size} no tasks: no page errors`, errs.length === 0, errs.join(' | '));
  await ctx.close();
}
/* signed out: the login screen has no card */
{
  const { ctx, p } = await page(b, { viewport: { width: 1440, height: 900 } }, BASE, { signedIn: false });
  pass('signed out: no card on the login screen', await p.locator('#ho-card-mount').count() === 0);
  await ctx.close();
}
/* runSelfTest: the card's own checks pass and nothing else got worse than origin/main */
{
  const mine = await selftestFails(b, BASE);
  pass('runSelfTest: the From card checks are in and pass', !mine.some(n => /^From card/.test(n)), mine.filter(n => /From card/.test(n)).join(', '));
  if (MAIN) {
    const base = await selftestFails(b, MAIN);
    const worse = mine.filter(n => !base.includes(n));
    pass('runSelfTest: no check fails that passes on origin/main', worse.length === 0, `main ${base.length} fail, this ${mine.length} fail${worse.length ? ': ' + worse.join(', ') : ''}`);
  }
  const { ctx, p } = await page(b, { viewport: { width: 1440, height: 900 } }, BASE);
  const sc = await p.evaluate(() => BBHO.selfcheck());
  pass('BBHO.selfcheck names its checks From card and all pass when signed in', sc.length === 4 && sc.every(x => x.pass && /^From card: /.test(x.name)), sc.map(x => (x.pass ? 'ok ' : 'NO ') + x.name).join('; '));
  await ctx.close();
}
/* BUILD 5 click path: on the weekly plan a filled cell lost its padding, so the next cell's tick box (grown 13px for a
   thumb) sat over this row's Move to next week arrow and the click ticked the neighbour's job. Two filled cells side by
   side, drawn by the page's own wpRenderItem and CSS: the arrow's centre must hit its own button, the tick its own box. */
for (const [size, opts] of [['phone', { viewport: { width: 402, height: 874 }, isMobile: true, hasTouch: true }], ['desk', { viewport: { width: 1440, height: 900 } }]]) {
  const { ctx, p } = await page(b, opts, BASE);
  const r = await p.evaluate(() => {
    const t = (id) => ({ id, status: 'planned', client_name: 'CLIENT ' + id, design_count: 1, task_type: 'post', notes: null, week_start: '2026-11-08' });
    const box = document.createElement('div'); box.style.cssText = 'position:fixed;left:0;top:200px;width:900px;z-index:99999;background:#111';
    box.innerHTML = '<table class="wp-grid-table" style="min-width:0;width:400px"><tbody><tr><td class="wp-cell has planned">' + wpRenderItem(t(1)) + '</td><td class="wp-cell has planned">' + wpRenderItem(t(2)) + '</td></tr></tbody></table>';
    document.body.appendChild(box);
    const hit = (sel, n) => { const e = box.querySelectorAll(sel)[n], q = e.getBoundingClientRect(); const h = document.elementFromPoint(q.left + q.width / 2, q.top + q.height / 2); return (h && h.closest(sel)) === e; };
    const out = { next1: hit('.wp-item-next', 0), next2: hit('.wp-item-next', 1), tick1: hit('.wp-item-box', 0), tick2: hit('.wp-item-box', 1) };
    box.remove(); return out;
  });
  pass(`${size} weekly plan: Move to next week and the tick each hit their own row, not the next cell's`, r.next1 && r.next2 && r.tick1 && r.tick2, JSON.stringify(r));
  await ctx.close();
}
await b.close();
console.log(rows.join('\n'));
console.log(`\nRESULT: ${total - bad} of ${total} PASS${bad ? ', ' + bad + ' FAIL' : ''}`);
process.exit(bad ? 1 : 0);
