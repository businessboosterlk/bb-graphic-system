// Targeted proof for GFX-1..GFX-10 (6 Oct 2026). Writes are stubbed, reads go live.
// Usage: node prove-graphic-fixes.mjs <path-to-index.html>
import { createRequire } from 'module'; import http from 'http'; import fs from 'fs';
const require = createRequire('/Users/thulaibhassen/bb-systems/batch/node_modules/'); const { chromium } = require('playwright');
const FILE = process.argv[2] || '/Users/thulaibhassen/bb-graphic-system/index.html';
const html = fs.readFileSync(FILE);
const server = http.createServer((req,res)=>{ res.writeHead(200,{'content-type':'text/html'}); res.end(html); }).listen(8841);
const b = await chromium.launch();
const c = await b.newContext({ viewport:{width:1440,height:900}, timezoneId:'Asia/Colombo', serviceWorkers:'block' });
await c.addInitScript(()=>{ sessionStorage.setItem('bbgfx_user',JSON.stringify({name:'THULAIB',role:'head',team_member_id:23,label:'Thulaib (CEO)'})); localStorage.setItem('bbgfx_guide_seen','1'); });
const p = await c.newPage();
const writes = []; const errs = [];
let failWrites = false, failRecap = false, archFixture = false;
p.on('pageerror', e=>errs.push(e.message.slice(0,160)));
await p.route(/supabase\.co\/(rest|functions)\//, r=>{
  const req = r.request(), m = req.method(), u = req.url();
  if(['GET','HEAD','OPTIONS'].includes(m)){
    if(failRecap && /graphic_projects\?created_at=lt\./.test(u)) return r.fulfill({status:500,contentType:'application/json',body:'{"message":"forced"}'});
    if(archFixture && /graphic_projects\?is_archived=eq\.true/.test(u)) return r.fulfill({status:200,contentType:'application/json',body:JSON.stringify([
      {id:-901,title:'SUHANA ARCHIVED',client_name:'X',assigned_designer:'Suhana',assigned_designer_id:3,current_stage:'approved',is_archived:true,updated_at:'2026-10-01T00:00:00Z'},
      {id:-902,title:'FARHATH ARCHIVED',client_name:'X',assigned_designer:'Farhath',assigned_designer_id:17,current_stage:'approved',is_archived:true,updated_at:'2026-10-01T00:00:00Z'}])});
    return r.continue();
  }
  writes.push({m, u:decodeURIComponent(u.replace(/^.*\/rest\/v1\//,'')), body:req.postData()});
  if(failWrites) return r.fulfill({status:500,contentType:'application/json',body:'{"message":"forced failure"}'});
  return r.fulfill({status:201,contentType:'application/json',body:'[{"id":-999}]'});
});
const results = []; const ok=(n,pass,d)=>results.push({n,pass:!!pass,d});
await p.goto('http://localhost:8841/',{waitUntil:'load'}); await p.waitForTimeout(9000);
const toasts = ()=>p.evaluate(()=>[...document.querySelectorAll('#toastWrap .toast')].map(t=>t.className+'|'+t.textContent));
const clearToasts = ()=>p.evaluate(()=>{document.getElementById('toastWrap').innerHTML='';});
const n0 = ()=>writes.length;

// GFX-10 todayStr at 00:30 Colombo on 7 Oct (19:00 UTC on 6 Oct)
const td = await p.evaluate(()=>{ const R=Date; class FD extends R{constructor(...a){ if(a.length) super(...a); else super('2026-10-06T19:00:00Z'); } static now(){return new R('2026-10-06T19:00:00Z').getTime();}} window.Date=FD; let v; try{ v=todayStr(); } finally { window.Date=R; } return v; });
ok('GFX-10 todayStr is the local date after midnight', td==='2026-10-07', td);

// GFX-5 wpMoveNextWeek keeps the Sunday key
let w0=n0();
await p.evaluate(()=>{ window._wpSave=wpTasks; wpTasks=[{id:-501,week_start:'2026-10-04',status:'planned'}]; return wpMoveNextWeek(-501); });
await p.waitForTimeout(800);
const wpw = writes.slice(w0).find(x=>x.m==='PATCH' && /graphic_weekly_plan/.test(x.u));
ok('GFX-5 move to next week writes the next Sunday key', wpw && JSON.parse(wpw.body).week_start==='2026-10-11', wpw && wpw.body);

// GFX-4 same stage writes nothing, a real move still writes
w0=n0();
const gs = await p.evaluate(async()=>{ window._pSave=projects; projects=[{id:-401,title:'T',current_stage:'approved'}]; const a=await gfxSetStage(-401,'approved','Moved in bulk'); return a; });
const sameW = writes.length-w0;
w0=n0();
await p.evaluate(async()=>{ BBU.suspended=true; await gfxSetStage(-401,'brief','test'); BBU.suspended=false; });
const moveW = writes.slice(w0).map(x=>x.m+' '+x.u.split('?')[0]);
ok('GFX-4 same stage returns true with 0 writes', gs===true && sameW===0, 'returned '+gs+', writes '+sameW);
ok('GFX-4 a real move still writes the post and its history', moveW.includes('PATCH graphic_projects') && moveW.includes('POST graphic_stage_history'), moveW.join(', '));

// GFX-2 / GFX-3 / GFX-1 edit path
const cid = await p.evaluate(()=>clients[0] && clients[0].id);
await p.evaluate((cid)=>{ projects=[{id:-55,title:'Edit me',client_id:cid,client_name:'C',current_stage:'brief',target_month:1,target_year:2027,type:'post',priority:'normal'}]; IMG_IDS.add(-55); IMG_CACHE[-55]='data:image/jpeg;base64,STOREDIMAGE'; return openEditProject(-55); }, cid);
await p.waitForTimeout(400);
const pre = await p.evaluate(()=>document.getElementById('projImageUrl').value);
w0=n0(); await clearToasts();
await p.evaluate(()=>{ document.getElementById('projTitle').value='Edit me, new title'; return saveProject(); });
await p.waitForTimeout(500);
const e1 = writes.slice(w0).find(x=>x.m==='PATCH' && /graphic_projects/.test(x.u));
const b1 = e1 ? JSON.parse(e1.body) : {};
ok('GFX-2 edit prefilled the stored image', pre==='data:image/jpeg;base64,STOREDIMAGE', pre.slice(0,40));
ok('GFX-2 title-only edit sends no image_url and no thumb_url', e1 && !('image_url' in b1) && !('thumb_url' in b1), Object.keys(b1).join(','));
ok('GFX-3 edit leaves target_year out', e1 && !('target_year' in b1), Object.keys(b1).join(','));
// typed a different URL
await p.evaluate(()=>{ projects=[{id:-55,title:'Edit me',client_id:clients[0].id,client_name:'C',current_stage:'brief',target_month:1,target_year:2027,type:'post',priority:'normal'}]; return openEditProject(-55); });
await p.waitForTimeout(400);
w0=n0();
await p.evaluate(()=>{ document.getElementById('projImageUrl').value='https://example.com/new.jpg'; return saveProject(); });
await p.waitForTimeout(500);
const e2 = writes.slice(w0).find(x=>x.m==='PATCH' && /graphic_projects/.test(x.u));
ok('GFX-2 a typed new URL is sent', e2 && JSON.parse(e2.body).image_url==='https://example.com/new.jpg', e2 && e2.body.slice(0,120));
// failing edit keeps the modal open
await p.evaluate(()=>{ projects=[{id:-55,title:'Edit me',client_id:clients[0].id,client_name:'C',current_stage:'brief',target_month:1,target_year:2027,type:'post',priority:'normal'}]; return openEditProject(-55); });
await p.waitForTimeout(400); await clearToasts(); failWrites=true;
await p.evaluate(()=>saveProject()); await p.waitForTimeout(500); failWrites=false;
let st = await p.evaluate(()=>document.getElementById('modalAddProject').classList.contains('open'));
let tt = await toasts();
ok('GFX-1 failed edit keeps the modal open with an error toast', st && tt.some(x=>/error\|Could not save the changes/.test(x)) && !tt.some(x=>/Post updated/.test(x)), JSON.stringify(tt));
await p.evaluate(()=>closeModal('modalAddProject'));

// GFX-1 create path: fail then succeed, GFX-3 year rule
await p.evaluate(()=>{ openAddProject(); document.getElementById('projTitle').value='New one'; document.getElementById('projClient').value=clients[0].id; document.getElementById('projTargetMonth').value='3'; });
await clearToasts(); failWrites=true;
await p.evaluate(()=>saveProject()); await p.waitForTimeout(500); failWrites=false;
st = await p.evaluate(()=>document.getElementById('modalAddProject').classList.contains('open'));
tt = await toasts();
ok('GFX-1 failed create keeps the modal open with an error toast', st && tt.some(x=>/error\|Could not save the post/.test(x)) && !tt.some(x=>/Post created/.test(x)), JSON.stringify(tt));
w0=n0(); await clearToasts();
await p.evaluate(()=>saveProject()); await p.waitForTimeout(1500);
const c1 = writes.slice(w0).find(x=>x.m==='POST' && /^graphic_projects/.test(x.u));
st = await p.evaluate(()=>document.getElementById('modalAddProject').classList.contains('open'));
tt = await toasts();
const yr = c1 ? JSON.parse(c1.body).target_year : null;
const expectYr = await p.evaluate(()=>{ const n=new Date(); return n.getFullYear()+(((n.getMonth()+1)-3)>6?1:0); });
ok('GFX-1 successful create closes the modal and says created', !st && tt.some(x=>/Post created/.test(x)), JSON.stringify(tt));
ok('GFX-3 create for a month over six behind is next year', yr===expectYr, 'target_year '+yr+', expected '+expectYr);
const ty = await p.evaluate(()=>{ const R=Date; class FD extends R{constructor(...a){ if(a.length) super(...a); else super('2026-12-15T06:00:00Z'); }} window.Date=FD; let v; try{ v=(typeof gfxTargetYear==="function")?[gfxTargetYear(1),gfxTargetYear(6),gfxTargetYear(12)]:["no gfxTargetYear"]; } finally { window.Date=R; } return v; });
ok('GFX-3 in December: Jan next year, Jun this year, Dec this year', ty.join()==='2027,2026,2026', ty.join());

// GFX-1 deleteProject: one DELETE on the post, failure says so
await p.evaluate(()=>{ window.confirm=()=>true; projects=[{id:-66,title:'Del',current_stage:'brief'}]; });
w0=n0(); await clearToasts(); failWrites=true;
await p.evaluate(()=>deleteProject(-66)); await p.waitForTimeout(500); failWrites=false;
tt = await toasts();
ok('GFX-1 failed delete says not deleted', tt.some(x=>/error\|Could not delete/.test(x)) && !tt.some(x=>/Project deleted/.test(x)), JSON.stringify(tt));
w0=n0(); await clearToasts();
await p.evaluate(()=>deleteProject(-66)); await p.waitForTimeout(1500);
const dels = writes.slice(w0).filter(x=>x.m==='DELETE').map(x=>x.u);
tt = await toasts();
ok('GFX-1 delete sends one DELETE, on graphic_projects only, then says deleted', dels.length===1 && /^graphic_projects\?id=eq\.-66$/.test(dels[0]) && tt.some(x=>/Project deleted/.test(x)), dels.join(' ; ')+' '+JSON.stringify(tt));

// GFX-9 drop zone bound once
const reads = await p.evaluate(async()=>{ openAddProject(); closeModal('modalAddProject'); openAddProject(); closeModal('modalAddProject'); openAddProject();
  let n=0; const real=window.readImageFile; window.readImageFile=function(){ n++; };
  const zone=document.querySelector('[data-drop-host="addProj"]'); const dt=new DataTransfer(); dt.items.add(new File([new Uint8Array([137,80,78,71])],'a.png',{type:'image/png'}));
  zone.dispatchEvent(new DragEvent('drop',{dataTransfer:dt,bubbles:true,cancelable:true}));
  window.readImageFile=real; closeModal('modalAddProject'); return n; });
ok('GFX-9 one drop after three opens reads the file once', reads===1, 'readImageFile ran '+reads+' times');

// GFX-6 recap failed read is not cached
await p.evaluate(()=>{ projects=window._pSave; RC_ROWS=null; RC_KEY=''; });
failRecap=true; await p.evaluate(()=>navigateTo('recap')); await p.waitForTimeout(2500);
let rc = await p.evaluate(()=>({t:document.getElementById('rcBody').innerText, cached:RC_ROWS}));
failRecap=false;
ok('GFX-6 failed recap read says could not load and is not cached', /Could not load/.test(rc.t) && !/nothing to recap/i.test(rc.t) && rc.cached===null, rc.t.slice(0,80)+' cached='+JSON.stringify(rc.cached));
await p.evaluate(()=>renderRecap()); await p.waitForTimeout(2500);
rc = await p.evaluate(()=>({t:document.getElementById('rcBody').innerText, n:(RC_ROWS||[]).length}));
ok('GFX-6 recap reads again once the connection is back', rc.n>0 && !/Could not load/.test(rc.t), rc.n+' rows');
await p.evaluate(()=>navigateTo('analytics')); await p.waitForTimeout(2500);
const an = await p.evaluate(()=>document.getElementById('section-analytics').innerText);
ok('GFX-6 Analytics says all time', /Analytics, all time/i.test(an) && /Clients, all time/i.test(an) && !/Active Clients/i.test(an), an.slice(0,120).replace(/\n/g,' | '));
await p.evaluate(()=>{ RC_ROWS=[{id:-1,sentinel:true}]; return loadAll(); }); await p.waitForTimeout(2500);
const rcAfter = await p.evaluate(()=>RC_ROWS===null);
ok('GFX-6 loadAll drops the recap cache', rcAfter, '');

// GFX-7 archive scoped for a designer
archFixture=true;
const arch = await p.evaluate(async()=>{ const save=currentUser; currentUser={name:'SUHANA',role:'designer',label:'Suhana',team_member_id:3}; await loadArchived(); const t=document.getElementById('archivedTable').innerText; currentUser=save; await loadArchived(); const t2=document.getElementById('archivedTable').innerText; return [t,t2]; });
archFixture=false;
ok('GFX-7 a designer sees only their own archived post', /SUHANA ARCHIVED/.test(arch[0]) && !/FARHATH ARCHIVED/.test(arch[0]), arch[0].replace(/\n/g,' | ').slice(0,140));
ok('GFX-7 a head still sees every archived post', /SUHANA ARCHIVED/.test(arch[1]) && /FARHATH ARCHIVED/.test(arch[1]), '');

// GFX-8 ids and the login log
const ids = await p.evaluate(()=>({t:USERS['1031'].team_member_id, s:USERS['1006'].team_member_id}));
ok('GFX-8 heads carry 23 and 24', ids.t===23 && ids.s===24, JSON.stringify(ids));
w0=n0();
await p.evaluate(()=>{ logout && 0; document.getElementById('loginName').value='Tiana'; document.getElementById('loginPin').value='8888'; return attemptLogin(); });
await p.waitForTimeout(1500);
const ll = writes.slice(w0).find(x=>x.m==='POST' && /team_login_logs/.test(x.u));
ok('GFX-8 login log carries Tiana id 22', ll && JSON.parse(ll.body).team_member_id===22, ll && ll.body);

await b.close(); server.close();
let f=0; for(const r of results){ if(!r.pass) f++; console.log((r.pass?'PASS ':'FAIL ')+r.n+(r.d?'  ['+String(r.d).slice(0,160)+']':'')); }
console.log(`\n${results.length} checks, ${f} failed, page errors ${errs.length}`); errs.forEach(e=>console.log('  err '+e));
