#!/usr/bin/env python3
"""
Graphic Weekly Plan -> the Video System shape.

PRIOR ART (bb-build-on-the-best):
  Best build = the Video System Weekly Plan (bb-video-system, 1e2369b + e4caecf).
  Taken:    designer x day GRID, per-item tick boxes, PENDING/DONE cell pills,
            today column highlight, day totals + week total, the carry-over
            panel ("Last week is not finished") with Move / Done / Drop, and the
            hands-vs-waiting summary split.
  REFUSED:  the "[x] " text-prefix encoding of done-ness. Video needs it because
            a cell is one free-text blob. graphic_weekly_plan has ONE ROW PER
            TASK with a real `status` column, so a tick writes real state.
            Copying the hack here would be strictly worse than the original.
  Registry: MODULE-REGISTRY.md had no Weekly Plan row at all. Adding one is part
            of this job.
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

# ══ CSS ══════════════════════════════════════════════════════════════
sub("CSS",
"""/* ══ WELCOME WALKTHROUGH ══════════════════════════════════════════════
   Full screen on purpose. A new designer should read one idea at a time,
   not a tooltip pinned to a control they have not found yet. */""",
"""/* ══ WEEKLY PLAN GRID ═════════════════════════════════════════════════
   Designer rows x Mon-Fri. The table scrolls INSIDE its own wrapper so the
   page itself never scrolls sideways on a phone. */
.wp-grid-wrap{overflow-x:auto;-webkit-overflow-scrolling:touch;border:1px solid var(--border);
  border-radius:var(--r);background:var(--surface)}
.wp-grid-table{width:100%;min-width:760px;border-collapse:collapse}
.wp-grid-table th{background:var(--surface-2);padding:10px 12px;text-align:left;
  font-size:0.68rem;font-weight:800;letter-spacing:0.08em;text-transform:uppercase;color:var(--text-3);
  border-bottom:1px solid var(--border);white-space:nowrap}
.wp-grid-table td{padding:0;border-bottom:1px solid var(--border);border-left:1px solid var(--border);vertical-align:top}
.wp-grid-table tr:last-child td{border-bottom:none}
.wp-who{padding:12px;font-weight:800;font-size:0.8rem;color:var(--text);white-space:nowrap;
  background:var(--surface-2);border-left:none;min-width:104px}
.wp-day-date{display:block;font-size:0.64rem;font-weight:600;color:var(--text-3);margin-top:2px;letter-spacing:0}
.wp-today-col{color:var(--accent)}
th.wp-today-col{background:var(--accent-soft)}
.wp-cell{padding:9px 10px;min-width:132px;border-left:3px solid transparent}
.wp-cell.has.pending{border-left-color:var(--amber);background:var(--amber-soft)}
.wp-cell.has.done{border-left-color:var(--green);background:var(--green-soft)}
.wp-cell-empty{padding:14px 10px;color:var(--text-3);font-size:0.8rem;text-align:center}
/* ITEMS. One line = one task. The tick writes the real status column. */
.wp-item{display:flex;align-items:flex-start;gap:7px;padding:4px 0;font-size:0.76rem;
  font-weight:600;color:var(--text);line-height:1.35}
.wp-item+.wp-item{border-top:1px dashed var(--border)}
.wp-item-box{position:relative;flex:none;width:17px;height:17px;margin-top:1px;
  border:1.5px solid var(--border-strong);border-radius:5px;background:var(--surface-3);
  cursor:pointer;display:grid;place-items:center;color:transparent;transition:all var(--t-fast)}
.wp-item-box:hover{border-color:var(--accent)}
.wp-item.done .wp-item-box{background:var(--green);border-color:var(--green);color:#fff}
.wp-item.done .wp-item-txt{text-decoration:line-through;color:var(--text-3);font-weight:500}
.wp-item-txt{flex:1;min-width:0;overflow-wrap:break-word;cursor:pointer}
.wp-item-sub{display:block;font-size:0.66rem;font-weight:500;color:var(--text-3);margin-top:1px}
.wp-item-next{position:relative;flex:none;opacity:0;border:none;background:none;color:var(--text-3);
  cursor:pointer;padding:0 2px;line-height:1;border-radius:5px;transition:opacity var(--t-fast)}
.wp-item:hover .wp-item-next{opacity:1}
.wp-item-next:hover{color:var(--accent);background:var(--surface-3)}
/* A 17px box is right for a dense grid but wrong for a thumb, so the tap area
   is grown invisibly rather than making the box bigger. */
.wp-item-box::after,.wp-item-next::after{content:'';position:absolute;inset:-13px;z-index:1}
.wp-pill{display:inline-flex;align-items:center;gap:4px;margin-top:7px;padding:3px 7px;
  border-radius:99px;font-size:0.6rem;font-weight:800;letter-spacing:0.05em;text-transform:uppercase}
.wp-pill.pending{background:var(--amber-soft);color:var(--amber)}
.wp-pill.done{background:var(--green-soft);color:var(--green)}
.wp-total-row td{background:var(--surface-2);font-weight:800;font-size:0.8rem;color:var(--text);padding:10px 12px}
.wp-week-total{text-align:right;margin-top:10px;font-size:0.8rem;font-weight:800;color:var(--text-2)}
.wp-week-total b{color:var(--accent);font-size:1.05rem}
/* ══ SUMMARY BOXES ══ */
.wp-sum{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:16px}
@media(max-width:900px){.wp-sum{grid-template-columns:repeat(2,1fr)}}
@media(max-width:520px){.wp-sum{grid-template-columns:1fr}}
.wp-sum-col{background:var(--surface);border:1px solid var(--border);border-radius:var(--r-md);padding:13px 14px;border-top:3px solid var(--border-strong)}
.wp-sum-col.a{border-top-color:var(--amber)} .wp-sum-col.b{border-top-color:var(--green)}
.wp-sum-col.c{border-top-color:var(--accent)} .wp-sum-col.d{border-top-color:var(--blue)}
.wp-sum-head{display:flex;align-items:center;justify-content:space-between;gap:8px}
.wp-sum-title{font-size:0.78rem;font-weight:800;color:var(--text)}
.wp-sum-total{font-size:1.5rem;font-weight:900;color:var(--text)}
.wp-sum-col.a .wp-sum-total{color:var(--amber)} .wp-sum-col.b .wp-sum-total{color:var(--green)}
.wp-sum-col.c .wp-sum-total{color:var(--accent)} .wp-sum-col.d .wp-sum-total{color:var(--blue)}
.wp-sum-sub{font-size:0.68rem;color:var(--text-3);margin:2px 0 9px;line-height:1.4}
.wp-sum-row{display:flex;justify-content:space-between;gap:10px;padding:4px 0;font-size:0.74rem;
  color:var(--text-2);border-top:1px dashed var(--border)}
.wp-sum-row b{color:var(--text);font-weight:700}
.wp-sum-empty{font-size:0.72rem;color:var(--text-3);font-style:italic;padding:6px 0}
/* ══ CARRY-OVER ══ */
.wp-carry{background:var(--amber-soft);border:1px solid var(--amber);border-radius:var(--r-md);padding:14px 16px;margin-bottom:16px}
.wp-carry-head{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}
.wp-carry-title{font-size:0.86rem;font-weight:800;color:var(--text)}
.wp-carry-count{font-size:1.35rem;font-weight:900;color:var(--amber)}
.wp-carry-sub{font-size:0.7rem;color:var(--text-3);margin:3px 0 10px;line-height:1.45}
.wp-carry-row{display:flex;align-items:flex-start;gap:10px;padding:8px 0;border-top:1px dashed var(--border);flex-wrap:wrap}
.wp-carry-who{min-width:78px;font-weight:800;font-size:0.74rem;color:var(--text)}
.wp-carry-day{min-width:36px;font-size:0.64rem;color:var(--text-3);text-transform:uppercase;font-weight:700;padding-top:2px}
.wp-carry-txt{flex:1;min-width:130px;font-size:0.74rem;color:var(--text-2);line-height:1.45}
.wp-carry-acts{display:flex;gap:6px;flex-wrap:wrap}
.wp-carry-btn{border:1px solid var(--border-strong);background:var(--surface-2);color:var(--text-2);
  border-radius:var(--r-sm);padding:7px 10px;font-size:0.66rem;font-weight:700;cursor:pointer;min-height:34px}
.wp-carry-btn:hover{background:var(--surface-3);color:var(--text)}
.wp-carry-btn.move{border-color:var(--accent);color:var(--accent)}
.wp-carry-btn.done{border-color:var(--green);color:var(--green)}
.wp-carry-btn.drop{border-color:var(--red);color:var(--red)}
.wp-carry-all{margin-top:10px;display:flex;gap:8px;flex-wrap:wrap}

/* ══ WELCOME WALKTHROUGH ══════════════════════════════════════════════
   Full screen on purpose. A new designer should read one idea at a time,
   not a tooltip pinned to a control they have not found yet. */""")

# ══ L-GFX-015 · THE WHOLE APP WAS 158px WIDE ON A PHONE ══════════════
#    `.main` (line 133) carries BOTH `margin-left:var(--sidebar-w)` AND
#    `max-width:calc(100vw - var(--sidebar-w))`. The 900px breakpoint reset the
#    margin but NOT the max-width, so on a 390px screen every page was capped at
#    390-232 = 158px, with the content section rendering at 126px. The sidebar is
#    `position:fixed`, so it was never in flow and the cap bought nothing.
#    Measured on the LIVE build before any of this work, so it is pre-existing.
sub("mobile width cap",
"""  .main{margin-left:0}""",
"""  .main{margin-left:0;max-width:100vw}   /* L-GFX-015: without the max-width
     reset every page was capped at 100vw minus the sidebar, so the app rendered
     158px wide on a 390px phone. The sidebar is position:fixed and never in
     flow, so the cap was wrong at every width below 901px. */""")

# ══ #wpBoard used to BE the five-column day grid. It now holds one scrolling
#    table, so its old grid rules squashed the whole page to 126px wide. ══
sub("wp-board becomes a plain block",
""".wp-board{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:24px}""",
""".wp-board{display:block;margin-bottom:16px}""")

sub("drop the old wp-board breakpoint",
"""@media(max-width:900px){.wp-board{grid-template-columns:1fr}}""",
"""/* (the old .wp-board day-column breakpoint is gone: the grid table now
   scrolls inside .wp-grid-wrap instead of reflowing) */""")

# ══ MARKUP: summary + carry-over containers ══════════════════════════
sub("markup",
"""        <div class="wp-board" id="wpBoard"></div>
        <div id="wpPendingSection"></div>""",
"""        <div class="wp-sum" id="wpSummary"></div>
        <div id="wpCarry"></div>
        <div class="wp-board" id="wpBoard"></div>
        <div class="wp-week-total" id="wpWeekTotal"></div>
        <div id="wpPendingSection"></div>""")

# ══ carry-over fetch inside wpLoadWeek ═══════════════════════════════
sub("carry fetch",
"""  const fri = new Date(wpWeekStart); fri.setDate(fri.getDate()+4);""",
"""  /* Last week's unfinished work, but ONLY while looking at the CURRENT week.
     Browsing back through history should not nag about the week before it. */
  _wpCarry = []; _wpCarryKey = null;
  const thisMon = wpGetMonday(new Date());
  if(ws === thisMon.toISOString().slice(0,10)){
    const prev = new Date(wpWeekStart); prev.setDate(prev.getDate()-7);
    const pk = prev.toISOString().slice(0,10);
    const pr = await sbGet('graphic_weekly_plan','?week_start=eq.'+pk+'&order=day_of_week.asc');
    if(Array.isArray(pr)){
      _wpCarryKey = pk;
      _wpCarry = pr.filter(t=>t.status!=='done');
    }
  }
  const fri = new Date(wpWeekStart); fri.setDate(fri.getDate()+4);""")

# ══ THE GRID ═════════════════════════════════════════════════════════
sub("wpRender",
"""  board.innerHTML = WP_DAYS.map((name,i)=>{
    const dayNum = i+1;
    const dayDate = new Date(wpWeekStart); dayDate.setDate(dayDate.getDate()+i);
    const isToday = dayDate.getTime()===today.getTime();
    const tasks = nonPending.filter(t=>t.day_of_week===dayNum);
    const totalDesigns = tasks.reduce((s,t)=>s+(t.design_count||0),0);
    return `
      <div class="wp-day">
        <div class="wp-day-header ${isToday?'today':''}">
          <h4>${name}</h4>
          <span class="wp-date">${wpFmtDate(dayDate)}${totalDesigns?' &middot; '+totalDesigns+' designs':''}</span>
        </div>
        <div class="wp-day-body">
          ${tasks.map(t=>wpRenderTask(t)).join('')}
          ${tasks.length===0?'<div style="padding:16px;text-align:center;color:var(--text-3);font-size:0.78rem">No tasks</div>':''}
        </div>
      </div>
    `;
  }).join('');""",
"""  /* THE GRID: designer rows x Mon-Fri, the Video System shape. Rows are the
     people who actually have work this week, so an empty roster never renders
     a wall of dashes. */
  const rows = DESIGNERS.map(d=>d.label);
  filtered.forEach(t=>{ if(t.assigned_to && rows.indexOf(t.assigned_to)===-1) rows.push(t.assigned_to); });
  const withWork = rows.filter(r=>filtered.some(t=>t.assigned_to===r));
  const unassigned = filtered.filter(t=>!t.assigned_to);
  const showRows = withWork.length ? withWork : rows;

  const dayTotals=[0,0,0,0,0];
  filtered.forEach(t=>{ const i=(t.day_of_week||1)-1; if(i>=0&&i<5) dayTotals[i]+=(t.design_count||0); });
  const weekTotal = dayTotals.reduce((a,b)=>a+b,0);

  const cell = (who,dayNum)=>{
    const ts = filtered.filter(t=>t.day_of_week===dayNum && (who===null ? !t.assigned_to : t.assigned_to===who));
    if(!ts.length) return '<td class="wp-cell"><div class="wp-cell-empty">&mdash;</div></td>';
    const allDone = ts.every(t=>t.status==='done');
    return '<td class="wp-cell has '+(allDone?'done':'pending')+'">'
      + ts.map(t=>wpRenderItem(t)).join('')
      + '<span class="wp-pill '+(allDone?'done':'pending')+'">'+(allDone?'&#10003; Done':'&#9679; Pending')+'</span>'
      + '</td>';
  };

  board.innerHTML = '<div class="wp-grid-wrap"><table class="wp-grid-table">'
    + '<thead><tr><th class="wp-who" style="background:var(--surface-2)">Designer</th>'
    + WP_DAYS.map((name,i)=>{
        const dd=new Date(wpWeekStart); dd.setDate(dd.getDate()+i);
        const isT = dd.getTime()===today.getTime();
        return '<th class="'+(isT?'wp-today-col':'')+'">'+name
             + '<span class="wp-day-date">'+wpFmtDate(dd)+'</span></th>';
      }).join('')
    + '</tr></thead><tbody>'
    + showRows.map(who=>'<tr><td class="wp-who">'+esc(who)+'</td>'
        + [1,2,3,4,5].map(d=>cell(who,d)).join('') + '</tr>').join('')
    + (unassigned.length ? '<tr><td class="wp-who" style="color:var(--text-3)">Unassigned</td>'
        + [1,2,3,4,5].map(d=>cell(null,d)).join('') + '</tr>' : '')
    + '<tr class="wp-total-row"><td class="wp-who">Total designs</td>'
        + dayTotals.map(n=>'<td class="wp-total-row">'+(n||'&mdash;')+'</td>').join('')
    + '</tr></tbody></table></div>';

  const wt = document.getElementById('wpWeekTotal');
  if(wt) wt.innerHTML = 'Designs planned this week: <b>'+weekTotal+'</b>';

  wpRenderSummary();
  wpRenderCarry();""")

# ══ item renderer, tick, move, summary, carry ════════════════════════
sub("helpers",
"""function wpRenderTask(t){""",
"""/* ONE TASK = ONE LINE. The tick writes the real `status` column, so the pill,
   the carry-over panel and every other reader agree with what a person sees.
   No "[x] " text prefix: the Video System needs that because its cell is one
   free-text blob. This table has a status column, so we use it. */
function wpRenderItem(t){
  const done = t.status==='done';
  const label = (t.client_name||'No client') + (t.design_count>1?' '+t.design_count:'');
  const sub = (WP_TYPES[t.task_type]||t.task_type||'') + (t.notes?' &middot; '+esc(t.notes):'');
  return '<div class="wp-item'+(done?' done':'')+'">'
    + '<span class="wp-item-box" title="'+(done?'Mark not done':'Mark done')+'" onclick="event.stopPropagation();wpToggleTask('+t.id+')">'
    +   '<svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>'
    + '</span>'
    + '<span class="wp-item-txt" onclick="wpOpenEdit('+t.id+')">'+esc(label)
    +   (sub?'<span class="wp-item-sub">'+sub+'</span>':'')
    + '</span>'
    + '<button class="wp-item-next" title="Move to next week" onclick="event.stopPropagation();wpMoveNextWeek('+t.id+')">'
    +   '<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>'
    + '</button></div>';
}

async function wpToggleTask(id){
  const t = (wpTasks||[]).find(x=>x.id===id); if(!t) return;
  const next = t.status==='done' ? 'planned' : 'done';
  t.status = next;                                   /* paint immediately */
  wpRender();
  const ok = await sbPatch('graphic_weekly_plan','id=eq.'+id,{status:next, updated_at:new Date().toISOString()});
  if(!ok){ t.status = next==='done'?'planned':'done'; wpRender(); toast('Could not save that tick','error'); }
}

async function wpMoveNextWeek(id){
  const t = (wpTasks||[]).find(x=>x.id===id); if(!t) return;
  const d = new Date(t.week_start+'T00:00:00'); d.setDate(d.getDate()+7);
  const nk = d.toISOString().slice(0,10);
  const ok = await sbPatch('graphic_weekly_plan','id=eq.'+id,{week_start:nk, updated_at:new Date().toISOString()});
  if(ok){ toast('Moved to the week of '+wpFmtDate(d)); wpLoadWeek(); }
  else toast('Could not move that task','error');
}

/* WHO IS ACTUALLY HOLDING THE BALL. A board that says "362 open" tells nobody
   how much is really with a designer. These four boxes split it. Stage lists
   are the graphic equivalent of the Video System's BB_HANDS / WAITING. */
const WP_NOT_STARTED = ['brief'];
const WP_OUR_HANDS   = ['in_progress','first_draft','revisions'];
const WP_WAITING     = ['head_review','sent_to_client','client_changes'];
function wpByClient(list){
  const o={};
  list.forEach(p=>{ const k=p.client_name||'(No client)'; o[k]=(o[k]||0)+1; });
  return Object.entries(o).sort((a,b)=>b[1]-a[1]);
}
function wpRenderSummary(){
  const el = document.getElementById('wpSummary'); if(!el) return;
  const live = (projects||[]).filter(p=>!p.is_archived);
  const box=(cls,title,sub,rows,empty)=>{
    const tot=rows.reduce((s,r)=>s+r[1],0);
    return '<div class="wp-sum-col '+cls+'">'
      + '<div class="wp-sum-head"><span class="wp-sum-title">'+title+'</span><span class="wp-sum-total">'+tot+'</span></div>'
      + '<div class="wp-sum-sub">'+sub+'</div>'
      + (rows.length ? rows.map(r=>'<div class="wp-sum-row"><span>'+esc(r[0])+'</span><b>'+r[1]+'</b></div>').join('')
                     : '<div class="wp-sum-empty">'+empty+'</div>')
      + '</div>';
  };
  const weekDesigns = (wpGetFiltered()||[]).reduce((s,t)=>s+(t.design_count||0),0);
  el.innerHTML =
      box('a','Not started','Briefed. Nobody has begun designing.', wpByClient(live.filter(p=>WP_NOT_STARTED.includes(p.current_stage))),'Nothing sitting in Brief')
    + box('c','In our hands','Being designed or revised by our team right now.', wpByClient(live.filter(p=>WP_OUR_HANDS.includes(p.current_stage))),'Nothing being worked on')
    + box('d','Waiting on others','With a reviewer or the client. Nobody is designing these.', wpByClient(live.filter(p=>WP_WAITING.includes(p.current_stage))),'Nothing waiting')
    + box('b','Planned this week','Designs on the plan above, per client.', wpByClient((wpGetFiltered()||[]).flatMap(t=>Array(Math.max(1,t.design_count||1)).fill({client_name:t.client_name}))),'Nothing planned yet');
}

let _wpCarry=[], _wpCarryKey=null;
function wpRenderCarry(){
  const el = document.getElementById('wpCarry'); if(!el) return;
  if(!_wpCarry.length){ el.innerHTML=''; return; }
  el.innerHTML = '<div class="wp-carry">'
    + '<div class="wp-carry-head"><span class="wp-carry-title">Last week is not finished</span>'
    +   '<span class="wp-carry-count">'+_wpCarry.length+'</span></div>'
    + '<div class="wp-carry-sub">These were planned last week and never marked done. Move them into this week, mark them done, or drop them. Only Done counts as finished.</div>'
    + _wpCarry.map(c=>'<div class="wp-carry-row">'
        + '<div class="wp-carry-who">'+esc(c.assigned_to||'Unassigned')+'</div>'
        + '<div class="wp-carry-day">'+(WP_DAYS[(c.day_of_week||1)-1]||'').slice(0,3)+'</div>'
        + '<div class="wp-carry-txt">'+esc(c.client_name||'No client')+' &middot; '+esc(WP_TYPES[c.task_type]||c.task_type||'')+(c.design_count>1?' &times;'+c.design_count:'')+'</div>'
        + '<div class="wp-carry-acts">'
        +   '<button class="wp-carry-btn move" onclick="wpCarryAct('+c.id+',\\'move\\')">Move to this week</button>'
        +   '<button class="wp-carry-btn done" onclick="wpCarryAct('+c.id+',\\'done\\')">Done</button>'
        +   '<button class="wp-carry-btn drop" onclick="wpCarryAct('+c.id+',\\'drop\\')">Drop</button>'
        + '</div></div>').join('')
    + '<div class="wp-carry-all">'
    +   '<button class="wp-carry-btn move" onclick="wpCarryAll(\\'move\\')">Move all '+_wpCarry.length+' into this week</button>'
    +   '<button class="wp-carry-btn done" onclick="wpCarryAll(\\'done\\')">Mark all done</button>'
    + '</div></div>';
}
async function wpCarryAct(id,action){
  const ws = wpWeekStart.toISOString().slice(0,10);
  let ok=false;
  if(action==='move')      ok = await sbPatch('graphic_weekly_plan','id=eq.'+id,{week_start:ws, updated_at:new Date().toISOString()});
  else if(action==='done') ok = await sbPatch('graphic_weekly_plan','id=eq.'+id,{status:'done', updated_at:new Date().toISOString()});
  else if(action==='drop') ok = await sbDel('graphic_weekly_plan','id=eq.'+id);
  if(!ok){ toast('Could not do that','error'); return; }
  wpLoadWeek();
}
async function wpCarryAll(action){
  const ids=_wpCarry.map(c=>c.id);
  for(const id of ids){ await wpCarryActQuiet(id,action); }
  toast(ids.length+' item'+(ids.length!==1?'s':'')+' '+(action==='move'?'moved into this week':'marked done'));
  wpLoadWeek();
}
async function wpCarryActQuiet(id,action){
  const ws = wpWeekStart.toISOString().slice(0,10);
  if(action==='move') return sbPatch('graphic_weekly_plan','id=eq.'+id,{week_start:ws, updated_at:new Date().toISOString()});
  return sbPatch('graphic_weekly_plan','id=eq.'+id,{status:'done', updated_at:new Date().toISOString()});
}

function wpRenderTask(t){""")

open(SRC,'w').write(s)
print("\n".join("  OK  "+e for e in edits))
print(f"\n  {len(edits)} anchors applied")
