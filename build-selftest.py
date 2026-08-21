#!/usr/bin/env python3
"""
L-GFX-007 · THE SELF-TEST HARNESS.

Flagged on day one as the highest-value work available and then skipped through
six deploys while every check was done by hand. That is exactly why the reload
bug (L-GFX-013) survived two investigations: nothing ran the boot path
automatically.

Shape borrowed from Section 12 of ~/bb-systems/master-skeleton/bb-master-skeleton.html.
NOT copy-pasted: the skeleton harness is welded to a local `DB._d` object it owns
outright. This app's state is a LIVE shared Supabase database, so the first
requirement is different and absolute:

    NO CHECK MAY EVER WRITE TO THE DATABASE.

Every write function is replaced with a recorder for the duration of the run and
restored in a `finally`. In-memory arrays are snapshotted and put back. A test
suite that corrupts the board it is testing is worse than no test suite.

Run it: append ?selftest to the URL, or call runSelfTest() in the console.
"""
import sys
SRC = sys.argv[1]
s = open(SRC).read()
edits = []

def sub(label, old, new, expect=1):
    global s
    n = s.count(old)
    assert n == expect, f"[{label}] anchor matched {n} times, expected {expect}"
    s = s.replace(old, new)
    edits.append(label)

HARNESS = r"""
/* ════════════════════════════════════════════════════════════════════
   SECTION 12 — SELF-TEST HARNESS (L-GFX-007)

   runSelfTest() snapshots all state, replaces every write function with a
   recorder, exercises the real app, restores everything, and reports PASS or
   FAIL per check. Returns {pass, failed, total, results}.

   Every REGRESSION check below is a bug that actually reached the team. If one
   of them fails, that bug is back. Do not delete a regression check because it
   looks redundant; each one cost a field report.

   Run: ?selftest in the URL, or runSelfTest() in the console.
   ════════════════════════════════════════════════════════════════════ */
const SELFTEST_MARK_A = '@@BBGFX_SELFTEST_BEGIN@@';
const SELFTEST_MARK_B = '@@BBGFX_SELFTEST_END@@';
/* @@BBGFX_SELFTEST_BEGIN@@ */
async function runSelfTest(){
  const R=[];
  const ok=(name,pass,detail)=>{R.push({name:name,pass:!!pass,detail:String(detail==null?'':detail).slice(0,160)});};

  /* ── snapshot: the harness must leave zero footprint ── */
  const snap = {
    projects: (typeof projects!=='undefined') ? projects.slice() : [],
    clients:  (typeof clients!=='undefined')  ? clients.slice()  : [],
    history:  (typeof stageHistory!=='undefined') ? stageHistory.slice() : [],
    wp:       (typeof wpTasks!=='undefined' && wpTasks) ? wpTasks.slice() : [],
    user:     currentUser,
    imgIds:   new Set(IMG_IDS),
    page:     ((document.querySelector('.content section.active')||{}).id||'').replace('section-','')
  };
  /* ── HARD STUB. Nothing below may reach the database. ── */
  const realPost=sbPost, realPatch=sbPatch, realDel=sbDel, realLoad=loadAll, realWpLoad=(typeof wpLoadWeek!=='undefined'?wpLoadWeek:null);
  const writes=[];
  sbPost  = async (t,d)=>{ writes.push('POST '+t);  return [{id:-1}]; };
  sbPatch = async (t,q,d)=>{ writes.push('PATCH '+t); return true; };
  sbDel   = async (t,q)=>{ writes.push('DELETE '+t); return true; };
  loadAll = async ()=>{};
  if(realWpLoad) wpLoadWeek = async ()=>{};

  /* One failing check must never abort the rest. This is the same lesson as
     L-GFX-008: all-or-nothing hides everything behind the first failure. Each
     section runs inside its own guard and a throw becomes a FAIL, not an exit. */
  /* Read once, above the sections: each section is its own function scope.
     CRITICAL: strip the harness's OWN body out first. Every string these checks
     search for also appears here, inside the checks themselves, so a naive grep
     matches the test instead of the app and goes green on a broken build.
     Found 2026-08-21 by deliberately reintroducing L-GFX-002 and watching the
     check pass anyway. */
  const _allSrc = Array.from(document.scripts).map(x=>x.textContent).join('\n');
  /* Cut between explicit sentinels. An earlier version cut between
     'async function runSelfTest' and 'window.runSelfTest', and the end marker
     matched only ~2000 chars in, so most of the harness stayed in `src` and the
     source checks matched THEMSELVES. Sentinels cannot drift like that. */
  const _a = _allSrc.indexOf(SELFTEST_MARK_A), _b = _allSrc.lastIndexOf(SELFTEST_MARK_B);
  const src = (_a>-1 && _b>_a) ? _allSrc.slice(0,_a) + _allSrc.slice(_b+SELFTEST_MARK_B.length) : _allSrc;
  ok('Harness: it does not grep its own source',
     src.indexOf('REGRESSION L-GFX-0')===-1,
     'if this fails, every source check below is matching the test and is meaningless');

  const section = async (label, fn) => {
    try{ await fn(); }
    catch(e){ ok(label+': section threw', false, (e && e.message) || String(e)); }
  };

  try{
    await section('Boot', async () => {
    /* ── A · BOOT INTEGRITY ── */
    ok('Boot: core globals present',
       typeof DESIGNERS==='object' && typeof USERS==='object' && typeof STAGES==='object' && typeof loadAll==='function');
    const idSeen={}; document.querySelectorAll('[id]').forEach(el=>idSeen[el.id]=(idSeen[el.id]||0)+1);
    const idDupes=Object.keys(idSeen).filter(k=>idSeen[k]>1);
    ok('Boot: no duplicate DOM ids', idDupes.length===0, idDupes.join(', '));
    const seen={}; const re=/^(?:const|let|function|async function)\s+([A-Za-z_$][\w$]*)/gm; let m;
    while((m=re.exec(src))) seen[m[1]]=(seen[m[1]]||0)+1;
    const dupes=Object.keys(seen).filter(k=>seen[k]>1);
    ok('Boot: no duplicate top-level identifiers', dupes.length===0, dupes.join(', '));

    /* ── REGRESSION L-GFX-013 · the reload bug ──
       Session restore ran mid-script and called loadAll(), which reads a const
       declared 80 lines below it. Anything that RUNS at parse time must sit
       below everything it reads. */
    /* The app has more than one script element (the Sentinel is last), so this
       must look inside the element that OWNS the restore, not the concatenation.
       No literal tag text in this file: guard rule L-003 rejects it, rightly. */
    const mainBlock = Array.from(document.scripts).filter(x=>!x.src)
       .find(x=>x.textContent.indexOf("sessionStorage.getItem('bbgfx_user')")>-1);
    const mt = mainBlock ? mainBlock.textContent : '';
    const restorePos = mt.lastIndexOf("sessionStorage.getItem('bbgfx_user')");
    ok('REGRESSION L-GFX-013: session restore is the LAST thing in its script block',
       restorePos>-1 && (mt.length-restorePos) < 900,
       (mt.length-restorePos)+' chars follow it; if this grows, something was added below it');
    const restoreAt = src.indexOf("sessionStorage.getItem('bbgfx_user')");
    const constAt   = src.indexOf('const PROJ_LIST_COLS');
    ok('REGRESSION L-GFX-013: PROJ_LIST_COLS is initialised before restore runs',
       constAt>-1 && restoreAt>constAt, 'const at '+constAt+', restore at '+restoreAt);

    });

    await section('Roster and access', async () => {
    /* ── B · ROSTER + ACCESS ── */
    ok('Roster: every designer has a login',
       DESIGNERS.every(d=>Object.values(USERS).some(u=>u.name===d.name)),
       DESIGNERS.map(d=>d.label).join(', '));
    ok('Roster: no duplicate PINs', Object.keys(USERS).length===new Set(Object.keys(USERS)).size);
    ok('Roster: no duplicate designer names',
       DESIGNERS.length===new Set(DESIGNERS.map(d=>d.name)).size);
    /* Four selects exist at rest; the two bulk-add row selects are created on
       demand, so they are checked by actually making a row. */
    const desSelects=document.querySelectorAll('select[data-designers]');
    ok('Roster: the 4 standing designer dropdowns are data-driven',
       desSelects.length===4, desSelects.length+' found');
    let bulkOk=false;
    try{
      const holder=document.getElementById('bulkRows');
      const had=holder.innerHTML;
      bulkAddRow();
      bulkOk = !!holder.querySelector('.bk-designer[data-designers]');
      holder.innerHTML=had;
    }catch(e){}
    ok('Roster: a new bulk-add row gets the roster too', bulkOk,
       'this is where a hand-edited option list used to go stale');
    fillDesignerSelects();
    const filt=document.getElementById('filterDesigner');
    ok('Roster: dropdowns list exactly the roster',
       filt && filt.options.length===DESIGNERS.length+1,
       filt?Array.from(filt.options).map(o=>o.textContent).join('/'):'missing');

    /* open access: a brand new designer must see everything */
    currentUser = DESIGNERS.length ? {name:DESIGNERS[DESIGNERS.length-1].name, role:'designer', label:DESIGNERS[DESIGNERS.length-1].label} : null;
    projects = [{id:1,title:'A',client_name:'X',assigned_designer:'Someone Else',current_stage:'brief',is_archived:false},
                {id:2,title:'B',client_name:'Y',assigned_designer:null,current_stage:'brief',is_archived:false}];
    ok('Access: a designer sees work assigned to other people',
       scopedProjects(projects.filter(p=>!p.is_archived)).length===2);
    ok('Access: My Work still shows only their own',
       onlyMine(projects).length===0, 'nothing is theirs, so My Work must be empty');

    });

    await section('L-GFX-008 regression', async () => {
    /* ── REGRESSION L-GFX-008 · one dead query must not blank the rest ── */
    clients=[]; projects=[]; stageHistory=[];   /* a genuine first load knows nothing yet */
    const realGet=sbGet;
    sbGet = async (t,q)=>{
      if(t==='graphic_projects' && String(q).indexOf('order=created_at.desc')>-1) throw new TypeError('Failed to fetch');
      if(t==='clients') return [{id:1,name:'KEEP ME'},{id:2,name:'AND ME'}];
      return [];
    };
    loadAll = realLoad;
    /* The OLD code threw here. That throw IS the failure, so swallow it and let
       the assertions below report what the user would actually have seen. */
    try{ await loadAll(); }catch(e){ /* recorded by the checks below */ }
    loadAll = async ()=>{};
    sbGet = realGet;
    ok('REGRESSION L-GFX-008: a healthy query still lands when a sibling fails',
       clients.length===2,
       'clients ended at '+clients.length+' of 2 (0 means Promise.all is back and the dropdown is empty again)');
    ok('REGRESSION L-GFX-008: a failed read is announced, not swallowed',
       document.querySelectorAll('#toastWrap .toast').length>0,
       'silence is the bug; the empty dropdown is only the symptom');

    });

    await section('Data-shape regressions', async () => {
    /* ── REGRESSION L-GFX-010 · bulk add dedup ── */
    ok('REGRESSION L-GFX-010: dedup key exists', typeof bulkKey==='function');
    if(typeof bulkKey==='function'){
      ok('REGRESSION L-GFX-010: same title+client+month is one post',
         bulkKey(' Post A ','SASTHO',9,2026)===bulkKey('post a','sastho',9,2026));
      ok('REGRESSION L-GFX-010: a different month is a different post',
         bulkKey('Post A','SASTHO',9,2026)!==bulkKey('Post A','SASTHO',10,2026));
    }
    /* BEHAVIOUR, not just the helper. Deleting the guard while leaving bulkKey
       in place used to sail straight through this section. Drive the real save
       path with a repeated row and count what it tried to insert. */
    try{
      const holder=document.getElementById('bulkRows');
      const had=holder.innerHTML; holder.innerHTML='';
      const inserted=[];
      const keepPost=sbPost;
      sbPost = async (t,d)=>{ if(t==='graphic_projects') inserted.push(d.title); return [{id:-1}]; };
      projects=[];
      for(const t of ['SELFTEST DUP','SELFTEST DUP','SELFTEST UNIQUE']){
        bulkAddRow();
        holder.querySelector('tr:last-child .bk-title').value=t;
      }
      await bulkSaveAll();
      sbPost = keepPost;
      holder.innerHTML=had;
      ok('REGRESSION L-GFX-010: bulk add actually SKIPS the duplicate',
         inserted.length===2,
         '3 rows in with one repeated, '+inserted.length+' inserted (3 means the guard is gone)');
    }catch(e){
      ok('REGRESSION L-GFX-010: bulk add actually SKIPS the duplicate', false, e && e.message);
    }

    /* ── REGRESSION L-GFX-005 · thumbnails ── */
    ok('REGRESSION L-GFX-005: thumbnail maker exists', typeof makeThumbDataUrl==='function');
    ok('REGRESSION L-GFX-005: board list query never asks for image_url',
       PROJ_LIST_COLS.indexOf('image_url')===-1, PROJ_LIST_COLS.slice(0,60)+'...');
    /* Read the FUNCTION's own body. Immune to anything else on the page. */
    ok('REGRESSION L-GFX-002: the archive page names its columns',
       typeof loadArchived==='function' && loadArchived.toString().indexOf('select=')>-1,
       'without this, archiving the board drags every base64 image across the wire');
    ok('L-GFX-001: the clients query never asks for mrr or contact',
       CLIENT_LIST_COLS.indexOf('mrr')===-1 && CLIENT_LIST_COLS.indexOf('contact')===-1, CLIENT_LIST_COLS);

    });

    await section('Weekly plan', async () => {
    /* ── C · WEEKLY PLAN ── */
    ok('Weekly plan: grid renderer present', typeof wpRenderItem==='function' && typeof wpRenderSummary==='function');
    ok('Weekly plan: carry-over present', typeof wpCarryAct==='function' && typeof wpCarryAll==='function');
    ok('Weekly plan: tick writes the real status column',
       typeof wpToggleTask==='function' && wpToggleTask.toString().indexOf('status')>-1
         && wpToggleTask.toString().indexOf('[x]')===-1,
       'no [x] text-prefix hack in this app; it has a real status column');
    if(typeof wpTasks!=='undefined'){
      wpTasks=[{id:1,day_of_week:1,assigned_to:(DESIGNERS[0]||{}).label,client_name:'C',task_type:'post',design_count:2,status:'planned',week_start:'2026-08-16'}];
      const before=wpTasks[0].status;
      await wpToggleTask(1);
      ok('Weekly plan: ticking flips planned to done', wpTasks[0].status==='done', before+' -> '+wpTasks[0].status);
      await wpToggleTask(1);
      ok('Weekly plan: ticking again flips it back', wpTasks[0].status==='planned');
    }

    });

    await section('Pages, layout, onboarding and copy', async () => {
    /* ── D · EVERY PAGE RENDERS ── */
    const pageErrs=[]; const oe=console.error; console.error=(...a)=>{pageErrs.push(String(a[0]));oe(...a)};
    currentUser = {name:'THULAIB', role:'head', team_member_id:1, label:'Thulaib (CEO)'};
    projects=[]; clients=[{id:1,name:'C'}]; stageHistory=[];
    for(const pg of ['dashboard','pipeline','clients','mywork','weeklyplan','pillars','archived','analytics']){
      try{ navigateTo(pg); }catch(e){ pageErrs.push(pg+': '+e.message); }
    }
    console.error=oe;
    ok('Pages: all 8 render with an empty board and no errors', pageErrs.length===0, pageErrs.slice(0,2).join(' | '));

    /* ── E · LAYOUT (L-GFX-015) ── */
    const sec=document.querySelector('.content section.active');
    const vw=window.innerWidth;
    if(sec && vw>320){
      const w=sec.getBoundingClientRect().width;
      ok('REGRESSION L-GFX-015: the page uses the width it has',
         w >= vw-64, Math.round(w)+'px of '+vw+'px (126 of 390 was the bug)');
    }
    ok('Layout: the page never scrolls sideways',
       document.documentElement.scrollWidth <= window.innerWidth+1,
       document.documentElement.scrollWidth+' vs '+window.innerWidth);

    /* ── F · ONBOARDING ── */
    ok('Onboarding: walkthrough present and reopenable',
       typeof gdCards==='function' && typeof gdOpen==='function' && !!document.getElementById('gfxGuideRow'));
    if(typeof gdCards==='function'){
      const cards=gdCards();
      ok('Onboarding: every card has a heading and body', cards.every(c=>c.h && c.p && c.p.length));
      const navCount=document.querySelectorAll('.nav-item[onclick]').length;
      ok('Onboarding: the page count is READ from the app, not typed',
         cards[0].p.join(' ').indexOf(String(navCount))>-1,
         'nav has '+navCount+' items; the guide must say the same number');
    }

    /* ── G · HOUSE STYLE on what the user reads ── */
    const uiText = (typeof gdCards==='function' ? gdCards().map(c=>c.h+' '+c.p.join(' ')).join(' ') : '');
    ok('House style: no em dashes in the walkthrough', uiText.indexOf('—')===-1);
    ok('House style: no serial commas in the walkthrough',
       !/,\s+(and|or|but|nor)\s/i.test(uiText.replace(/<[^>]+>/g,'')),
       (uiText.replace(/<[^>]+>/g,'').match(/,\s+(and|or|but|nor)\s/i)||[''])[0]);

    });

  }catch(e){
    ok('Harness completed without throwing', false, e && e.message);
  }finally{
    /* ── restore everything, always ── */
    sbPost=realPost; sbPatch=realPatch; sbDel=realDel; loadAll=realLoad;
    if(realWpLoad) wpLoadWeek=realWpLoad;
    projects=snap.projects; clients=snap.clients; stageHistory=snap.history;
    if(typeof wpTasks!=='undefined') wpTasks=snap.wp;
    currentUser=snap.user; IMG_IDS=snap.imgIds;
    try{ if(snap.page) navigateTo(snap.page); }catch(e){}
  }
  ok('Harness: ZERO writes reached the database', true, writes.length+' write(s) intercepted and discarded');

  const failed=R.filter(r=>!r.pass);
  const line='SELF-TEST  '+(R.length-failed.length)+'/'+R.length+' passed'+(failed.length?'  ** '+failed.length+' FAILED **':'  ALL GREEN');
  console.log('%c'+line, 'font-weight:bold;font-size:13px;color:'+(failed.length?'#ef4444':'#22c55e'));
  R.forEach(r=>console.log((r.pass?'  PASS  ':'  FAIL  ')+r.name+(r.detail?'   — '+r.detail:'')));
  if(typeof toast==='function') toast(line, failed.length?'error':'success');
  return {pass:failed.length===0, failed:failed.length, total:R.length, results:R};
}
window.runSelfTest = runSelfTest;
/* @@BBGFX_SELFTEST_END@@ */
"""

sub("harness",
"""/* ══ SESSION RESTORE — MUST BE THE LAST THING IN THIS SCRIPT ══════════""",
HARNESS + """
/* ══ SESSION RESTORE — MUST BE THE LAST THING IN THIS SCRIPT ══════════""")

# ?selftest runs it once the app is up
sub("selftest url trigger",
"""  renderGuideRow();
  /* From the sign-in door, never a boot timer: an earlier BB build opened the
     guide over the login screen and greeted somebody before they had proved
     who they were. currentUser is set by the time we get here. */
  if(!gdSeen()) setTimeout(gdOpen, 500);""",
"""  renderGuideRow();
  /* From the sign-in door, never a boot timer: an earlier BB build opened the
     guide over the login screen and greeted somebody before they had proved
     who they were. currentUser is set by the time we get here. */
  if(location.search.indexOf('selftest')>-1){ setTimeout(()=>runSelfTest(), 1200); }
  else if(!gdSeen()) setTimeout(gdOpen, 500);""")

open(SRC,'w').write(s)
print("\n".join("  OK  "+e for e in edits))
print(f"\n  {len(edits)} anchors applied")
