#!/usr/bin/env python3
"""
MONTHLY RECAP.

THE RULE THAT SHAPES THIS PAGE: never estimate a turnaround for a row that has
no finish time. Every duration figure carries the count it was measured on, next
to the count that could not be measured. On the SMM Workspace the same feature
was blocked because 308 of 529 finished tasks had no completed_at, and a median
computed over the other 221 would have looked authoritative and been a guess.

Graphic does not have that problem on the way in (measured: 12 finished, 0
unstamped, across the 363 backed-up rows) but it did have five rows carrying a
STALE stamp from being reopened, which the prerequisite pass fixed.

AND: the board currently holds ZERO rows, cleared on 20 August. A page of zeros
that does not say why is worse than no page, so the empty state says what
happened, when, and where the history is.
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

# ── nav ───────────────────────────────────────────────────────────────
sub("nav item",
"""      <div class="nav-section">Extra</div>""",
"""      <div class="nav-item" data-page="recap" onclick="navigateTo('recap')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="17" rx="2"/><path d="M3 10h18M8 2v4M16 2v4"/><path d="M8 15h3"/></svg>
        Recap
      </div>
      <div class="nav-section">Extra</div>""")

# ── section ───────────────────────────────────────────────────────────
sub("section markup",
"""      <!-- ═══ AGENTS ═══ -->""",
"""      <!-- ═══ MONTHLY RECAP ═══ -->
      <section id="section-recap">
        <div class="sec-header" style="gap:12px;flex-wrap:wrap">
          <h2>Monthly Recap</h2>
          <div style="display:flex;gap:8px;align-items:center">
            <select id="rcMonth" onchange="renderRecap()"></select>
            <select id="rcYear" onchange="renderRecap()"></select>
          </div>
        </div>
        <div id="rcSummary"></div>
        <div id="rcBody"></div>
      </section>

      <!-- ═══ AGENTS ═══ -->""")

# ── page title + dispatch ─────────────────────────────────────────────
sub("page title",
"""archived:'Archived',analytics:'Analytics',agents:'Agents'}[page]||page;""",
"""archived:'Archived',analytics:'Analytics',recap:'Monthly Recap',agents:'Agents'}[page]||page;""")

sub("navigateTo dispatch",
"""  // refresh section data
  if(page==='dashboard') renderDashboard();""",
"""  // refresh section data
  if(page==='recap') renderRecap();
  if(page==='dashboard') renderDashboard();""")

sub("renderCurrentPage dispatch",
"""  if(page==='mywork') renderMyWork();
  if(page==='analytics') renderAnalytics();
  if(page==='agents') renderAgents();""",
"""  if(page==='mywork') renderMyWork();
  if(page==='analytics') renderAnalytics();
  if(page==='recap') renderRecap();
  if(page==='agents') renderAgents();""")

# ── styles ────────────────────────────────────────────────────────────
sub("styles",
"""/* ═══ BB APP SHELL + APP FOUNDATIONS, cascade-final ═══════════════════════""",
"""/* ══ MONTHLY RECAP ══════════════════════════════════════════════════ */
.rc-tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(168px,1fr));gap:12px;margin-bottom:18px}
.rc-tile{background:var(--surface);border:1px solid var(--border);border-radius:var(--r-md);padding:14px 16px;border-top:3px solid var(--border-strong)}
.rc-tile.a{border-top-color:var(--accent)} .rc-tile.b{border-top-color:var(--green)}
.rc-tile.c{border-top-color:var(--blue)}   .rc-tile.d{border-top-color:var(--amber)}
.rc-lbl{font-size:0.66rem;font-weight:800;color:var(--text-3);text-transform:uppercase;letter-spacing:0.07em;margin-bottom:6px}
.rc-num{font-size:1.7rem;font-weight:900;line-height:1;color:var(--text)}
.rc-tile.a .rc-num{color:var(--accent)} .rc-tile.b .rc-num{color:var(--green)}
.rc-tile.c .rc-num{color:var(--blue)}    .rc-tile.d .rc-num{color:var(--amber)}
.rc-sub{font-size:0.68rem;color:var(--text-3);margin-top:6px;line-height:1.45}
/* THE GAP IS LABELLED, never hidden. A figure nobody can reproduce is worse
   than a gap that says how big it is. */
.rc-gap{display:inline-block;margin-top:6px;padding:3px 7px;border-radius:99px;
  background:var(--amber-soft);color:var(--amber);font-size:0.6rem;font-weight:800;letter-spacing:0.04em}
.rc-client{background:var(--surface);border:1px solid var(--border);border-radius:var(--r-md);padding:14px 16px;margin-bottom:10px}
.rc-chead{display:flex;align-items:baseline;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-bottom:8px}
.rc-cname{font-size:0.92rem;font-weight:800;color:var(--text)}
.rc-cnums{display:flex;gap:14px;flex-wrap:wrap;font-size:0.72rem;color:var(--text-3)}
.rc-cnums b{color:var(--text);font-weight:800}
.rc-say{font-size:0.8rem;line-height:1.6;color:var(--text-2)}
.rc-empty{background:var(--surface);border:1px solid var(--amber);border-radius:var(--r-md);padding:20px}
.rc-empty h3{font-size:1rem;font-weight:800;color:var(--text);margin-bottom:8px}
.rc-empty p{font-size:0.82rem;line-height:1.65;color:var(--text-2);margin-bottom:8px}
.rc-empty p:last-child{margin-bottom:0}

/* ═══ BB APP SHELL + APP FOUNDATIONS, cascade-final ═══════════════════════""")

# ── behaviour ─────────────────────────────────────────────────────────
sub("recap code",
"""/* ══ SESSION RESTORE — MUST BE THE LAST THING IN THIS SCRIPT ══════════""",
r"""/* ══ MONTHLY RECAP ════════════════════════════════════════════════════
   Definitions, written down so every number on the page can be reproduced:
     opened    created_at falls inside the month
     finished  completed_at falls inside the month
     turnaround  days from created_at to completed_at, and ONLY for rows that
                 have both. Never estimated, never inferred from updated_at.
     still open  not in a finished stage, and created before the month ended
   A duration is always shown with the count it was measured on. */
const RC_FINISHED = ['approved'];
let RC_ROWS = null, RC_KEY = '';

function rcMedian(a){
  if(!a.length) return null;
  const v = a.slice().sort((x,y)=>x-y), m = Math.floor(v.length/2);
  return v.length%2 ? v[m] : (v[m-1]+v[m])/2;
}
function rcDays(from,to){ return (new Date(to)-new Date(from))/86400000; }
function rcNum(n){ return Number.isInteger(n) ? String(n) : n.toFixed(1); }
function rcPlural(n,one,many){ return n===1?one:many; }

async function renderRecap(){
  const mSel=document.getElementById('rcMonth'), ySel=document.getElementById('rcYear');
  if(!mSel||!ySel) return;
  if(!mSel.options.length){
    const now=new Date();
    mSel.innerHTML = MONTHS.slice(1).map((m,i)=>'<option value="'+(i+1)+'">'+m+'</option>').join('');
    const y=now.getFullYear();
    ySel.innerHTML = [y-1,y,y+1].map(v=>'<option value="'+v+'">'+v+'</option>').join('');
    mSel.value = now.getMonth()+1; ySel.value = y;
  }
  const month=parseInt(mSel.value,10), year=parseInt(ySel.value,10);
  const start=new Date(year,month-1,1), end=new Date(year,month,1);
  const body=document.getElementById('rcBody'), sum=document.getElementById('rcSummary');
  body.innerHTML='<div class="rc-say">Loading…</div>'; sum.innerHTML='';

  /* One query. Anything finished in the month was created before it ended, so
     created_at < month end covers opened, finished and still open at once. */
  const key=year+'-'+month;
  if(RC_KEY!==key || !RC_ROWS){
    const r=await sbGet('graphic_projects','?created_at=lt.'+end.toISOString()+
      '&select=id,client_name,current_stage,created_at,completed_at,is_archived,type&order=created_at.asc');
    RC_ROWS = Array.isArray(r)?r:[];
    RC_KEY = key;
  }
  const rows=RC_ROWS;

  const inMonth=(d)=>{ if(!d) return false; const t=new Date(d); return t>=start && t<end; };
  const opened  = rows.filter(p=>inMonth(p.created_at));
  const finished= rows.filter(p=>inMonth(p.completed_at));
  const stillOpen = rows.filter(p=>RC_FINISHED.indexOf(p.current_stage)===-1 && !p.is_archived);

  /* THE HONEST EMPTY STATE. The board was cleared on 20 August, so a recap of
     any earlier month is a page of zeros. Saying why is the whole point. */
  if(!rows.length){
    sum.innerHTML='';
    body.innerHTML='<div class="rc-empty">'
      +'<h3>There is nothing to recap yet</h3>'
      +'<p>The board holds no projects. It was cleared on 20 August 2026 to fix a database size problem, and the team started adding work again from September.</p>'
      +'<p>The history from before that date was exported first and is not lost. It is 363 projects with their stage history, saved to Downloads as a dated backup folder with a restore guide.</p>'
      +'<p>This page will fill itself as soon as work is added. Nothing here is a real zero yet, so please do not read it as one.</p>'
      +'</div>';
    return;
  }

  /* Durations, and ONLY where both ends exist. */
  const measurable = finished.filter(p=>p.created_at && p.completed_at);
  const unmeasurable = finished.length - measurable.length;
  const days = measurable.map(p=>rcDays(p.created_at,p.completed_at));
  const med = rcMedian(days), longest = days.length?Math.max.apply(null,days):null;
  const rate = opened.length ? Math.round(100*finished.length/opened.length) : null;

  sum.innerHTML='<div class="rc-tiles">'
    +'<div class="rc-tile a"><div class="rc-lbl">Jobs opened</div><div class="rc-num">'+opened.length+'</div>'
      +'<div class="rc-sub">created in '+MONTHS[month]+' '+year+'</div></div>'
    +'<div class="rc-tile b"><div class="rc-lbl">Finished</div><div class="rc-num">'+finished.length+'</div>'
      +'<div class="rc-sub">'+(rate===null?'no jobs opened, so no rate':rate+'% of what was opened')+'</div></div>'
    +'<div class="rc-tile c"><div class="rc-lbl">Median turnaround</div><div class="rc-num">'
      +(med===null?'n/a':rcNum(med))+'</div>'
      +'<div class="rc-sub">'+(med===null?'nothing finished with both dates':rcPlural(med,'day','days')
        +', measured on '+measurable.length+' of '+finished.length)+'</div>'
      +(unmeasurable>0?'<div class="rc-gap">'+unmeasurable+' had no finish time</div>':'')+'</div>'
    +'<div class="rc-tile d"><div class="rc-lbl">Still open</div><div class="rc-num">'+stillOpen.length+'</div>'
      +'<div class="rc-sub">across every month, not just this one</div></div>'
    +'</div>';

  /* Per client. A client appears if it opened, finished or still holds work. */
  const names={};
  [].concat(opened,finished,stillOpen).forEach(p=>{ names[p.client_name||'(No client)']=1; });
  const list=Object.keys(names).sort();
  const now=new Date();

  body.innerHTML = list.map(name=>{
    const mine=(arr)=>arr.filter(p=>(p.client_name||'(No client)')===name);
    const o=mine(opened), f=mine(finished), so=mine(stillOpen);
    const meas=f.filter(p=>p.created_at&&p.completed_at);
    const un=f.length-meas.length;
    const d=meas.map(p=>rcDays(p.created_at,p.completed_at));
    const m=rcMedian(d), lg=d.length?Math.max.apply(null,d):null;
    const ages=so.filter(p=>p.created_at).map(p=>rcDays(p.created_at,now));
    const oldest=ages.length?Math.max.apply(null,ages):null;

    /* The plain sentence. It only claims what was measured. */
    let say='';
    if(o.length===0 && f.length===0) say='Nothing opened or finished this month.';
    else say=o.length+' '+rcPlural(o.length,'job','jobs')+' opened and '+f.length+' finished.';
    if(m!==null) say+=' Half were done within '+rcNum(m)+' '+rcPlural(m,'day','days')
                      +', and the slowest took '+rcNum(lg)+'.';
    else if(f.length>0) say+=' None of the finished work has a recorded finish time, so the turnaround cannot be measured.';
    if(un>0 && m!==null) say+=' '+un+' of the finished '+rcPlural(un,'job has','jobs have')+' no finish time and '+rcPlural(un,'is','are')+' left out of that figure.';
    if(so.length>0) say+=' '+so.length+' '+rcPlural(so.length,'job is','jobs are')+' still open'
                        +(oldest!==null?', and the oldest has been waiting '+rcNum(oldest)+' '+rcPlural(oldest,'day','days'):'')+'.';

    return '<div class="rc-client">'
      +'<div class="rc-chead"><span class="rc-cname">'+esc(name)+'</span>'
      +'<span class="rc-cnums"><span>opened <b>'+o.length+'</b></span>'
      +'<span>finished <b>'+f.length+'</b></span>'
      +'<span>median <b>'+(m===null?'n/a':rcNum(m)+'d')+'</b></span>'
      +'<span>longest <b>'+(lg===null?'n/a':rcNum(lg)+'d')+'</b></span>'
      +'<span>open <b>'+so.length+'</b></span></span></div>'
      +'<div class="rc-say">'+esc(say)+'</div>'
      +(un>0?'<div class="rc-gap">'+un+' without a finish time</div>':'')
      +'</div>';
  }).join('');
}

/* ══ SESSION RESTORE — MUST BE THE LAST THING IN THIS SCRIPT ══════════""")

open(SRC,'w').write(s)
print("\n".join("  OK  "+e for e in edits))
print(f"\n  {len(edits)} anchors applied")
