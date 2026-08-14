#!/usr/bin/env python3
"""
BB Graphic System — one verified change:
  A. Dinuka out. Farhath + Abilashan (freelancer) in. ONE designer list.
  B. L-GFX-008: one dead query must not blank every list. + tell the user.
  C. clients query names its columns (stops mrr/contact reaching the browser).

Every replacement asserts its anchor matched exactly once.
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

# ═══ A · THE DESIGNER LIST ═══════════════════════════════════════════
sub("A1 filterDesigner",
"""          <select id="filterDesigner" onchange="applyFilters()">
            <option value="">All Designers</option>
            <option value="Dinuka">Dinuka</option>
            <option value="Suhana">Suhana</option>
          </select>""",
"""          <select id="filterDesigner" onchange="applyFilters()" data-designers="All Designers"></select>""")

sub("A2 wpFilterDesigner",
"""          <select id="wpFilterDesigner" onchange="wpRender()">
            <option value="">All Designers</option>
            <option value="Dinuka">Dinuka</option>
            <option value="Suhana">Suhana</option>
          </select>""",
"""          <select id="wpFilterDesigner" onchange="wpRender()" data-designers="All Designers"></select>""")

sub("A3 projDesigner",
"""          <select id="projDesigner">
            <option value="">Unassigned</option>
            <option value="16" data-name="Dinuka">Dinuka</option>
            <option value="3" data-name="Suhana">Suhana</option>
          </select>""",
"""          <select id="projDesigner" data-designers="Unassigned"></select>""")

sub("A4 wpAssigned",
"""          <select id="wpAssigned">
            <option value="">Unassigned</option>
            <option value="Dinuka">Dinuka</option>
            <option value="Suhana">Suhana</option>
          </select>""",
"""          <select id="wpAssigned" data-designers="Unassigned"></select>""")

sub("A5 bk-designer",
"""<td><select class="bk-designer"><option value="">—</option><option value="Dinuka">Dinuka</option><option value="Suhana">Suhana</option></select></td>""",
"""<td><select class="bk-designer" data-designers="—"></select></td>""")

sub("A6 wbk-designer",
"""<td><select class="wbk-designer"><option value="">—</option><option value="Dinuka">Dinuka</option><option value="Suhana">Suhana</option></select></td>""",
"""<td><select class="wbk-designer" data-designers="—"></select></td>""")

sub("A7 USERS",
"""  '2323': { name:'DINUKA', role:'designer', team_member_id:16, label:'Dinuka' },
  '3333': { name:'SUHANA', role:'designer', team_member_id:3, label:'Suhana' },""",
"""  '3333': { name:'SUHANA', role:'designer', team_member_id:3, label:'Suhana' },
  '5555': { name:'ABILASHAN', role:'designer', team_member_id:null, label:'Abilashan' },""")

# Guard rule L-015 — accepted risk, Thulaib's explicit call 2026-08-14 (Option A).
sub("A7b GUARD-ALLOW L-015",
"""// ── Silent app auth: obtain a real JWT so login-only tables stay readable here ──""",
"""/* GUARD-ALLOW L-015 — ACCEPTED RISK, signed off by Thulaib 2026-08-14.
   This is a shared APP credential, not a per-user secret: it is how every BB
   single-file system reads login-only tables, and it grants exactly what this
   app's own tables already allow. It is published in a public repo, so treat it
   as public. It is NOT a substitute for real auth.
   This marker is a DEFERRAL WITH AN OWNER, not a fix. The real fix is the
   role-floor project (per-user Supabase Auth). See L-GFX-006 and L-GFX-012 in
   LANDMINES.md. Revisit before any further non-staff login is added. */
// ── Silent app auth: obtain a real JWT so login-only tables stay readable here ──""")

sub("A8 DESIGNERS const",
"""const STAGES = ['brief','in_progress','first_draft','revisions','head_review','sent_to_client','client_changes','approved'];""",
"""/* ─── THE ONE DESIGNER LIST ───────────────────────────────────────────
   Every designer dropdown in this app renders from this array at boot.
   To add or remove a designer, EDIT HERE ONLY. Hand-editing the <option>
   lists is what left Rukshan haunting the system after 28 July. L-GFX-009.
   `freelancer:true` marks someone who takes overflow work but is NOT one of
   the staff designers in the Client Allocation Master.
   team_member_id may stay null until the team_members row exists; the app
   stores and filters on the NAME, which is what every scope check uses. */
const DESIGNERS = [
  { name:'SUHANA',    label:'Suhana',    team_member_id:3,    freelancer:false },
  { name:'ABILASHAN', label:'Abilashan', team_member_id:null, freelancer:true  },
];

/* Fill every <select data-designers="placeholder"> from DESIGNERS. Keeps the
   current selection if it is still valid. Safe to call repeatedly. */
function fillDesignerSelects(root){
  (root||document).querySelectorAll('select[data-designers]').forEach(sel=>{
    const keep = sel.value;
    sel.innerHTML = '<option value="">'+esc(sel.dataset.designers)+'</option>'+
      DESIGNERS.map(d=>'<option value="'+esc(d.label)+'" data-id="'+
        (d.team_member_id==null?'':d.team_member_id)+'">'+esc(d.label)+
        (d.freelancer?' (freelance)':'')+'</option>').join('');
    if(keep) sel.value = keep;
  });
}

const STAGES = ['brief','in_progress','first_draft','revisions','head_review','sent_to_client','client_changes','approved'];""")

sub("A9 designerScope",
"""  if(!currentUser || currentUser.role!=='designer') return null;
  const map = {DINUKA:'Dinuka',SUHANA:'Suhana'};
  return map[currentUser.name]||null;""",
"""  if(!currentUser || currentUser.role!=='designer') return null;
  const d = DESIGNERS.find(x=>x.name===currentUser.name);
  return d ? d.label : null;""")

sub("A10 pillars designers",
"""  const designers = ['DINUKA','SUHANA'];""",
"""  const designers = DESIGNERS.map(d=>d.name);""")

sub("A11 saveProject designer read",
"""  const designerId = designerSel.value ? parseInt(designerSel.value) : designerScopeId();
  const designerName = designerSel.value ? designerSel.options[designerSel.selectedIndex].dataset.name : designerScope();""",
"""  const designerOpt = designerSel.value ? designerSel.options[designerSel.selectedIndex] : null;
  const designerName = designerSel.value || designerScope();
  const designerId = designerOpt
    ? (designerOpt.dataset.id ? parseInt(designerOpt.dataset.id) : null)
    : designerScopeId();""")

sub("A12 openAddProject prefill",
"""  document.getElementById('projDesigner').value = designerScopeId()||'';""",
"""  document.getElementById('projDesigner').value = designerScope()||'';""")

sub("A13 openEditProject prefill",
"""  document.getElementById('projDesigner').value = p.assigned_designer_id||'';""",
"""  document.getElementById('projDesigner').value = p.assigned_designer||'';""")

sub("A14 bulk pipeline row fill",
"""  document.getElementById('bulkRows').appendChild(tr);""",
"""  fillDesignerSelects(tr);
  document.getElementById('bulkRows').appendChild(tr);""")

sub("A15 bulk weekly row fill",
"""  document.getElementById('wpBulkRows').appendChild(tr);""",
"""  fillDesignerSelects(tr);
  document.getElementById('wpBulkRows').appendChild(tr);""")

sub("A16 session boot fill",
"""(function(){
  const saved = sessionStorage.getItem('bbgfx_user');
  if(saved){ currentUser = JSON.parse(saved); showApp(); }
})();""",
"""(function(){
  fillDesignerSelects();
  const saved = sessionStorage.getItem('bbgfx_user');
  if(saved){ currentUser = JSON.parse(saved); showApp(); }
})();""")

# ═══ B + C · loadAll must survive one dead query, and name its columns ═══
sub("B1 loadAll",
"""async function loadAll(){
  try{
    const [p, c, h, imgs] = await Promise.all([
      sbGet('graphic_projects','?order=created_at.desc&is_archived=eq.false&select='+PROJ_LIST_COLS),
      sbGet('clients','?order=name.asc'),
      sbGet('graphic_stage_history','?order=entered_at.desc&limit=50'),
      sbGet('graphic_projects','?is_archived=eq.false&image_url=not.is.null&select=id')
    ]);
    projects = Array.isArray(p)?p:[];
    clients = Array.isArray(c)?c:[];
    stageHistory = Array.isArray(h)?h:[];
    IMG_IDS = new Set(Array.isArray(imgs)?imgs.map(x=>x.id):[]);
    populateClientDropdowns();
    renderCurrentPage();
  } catch(e){ console.error('loadAll error',e); }
}""",
"""/* L-GFX-008 — this used to be one Promise.all. That is all-or-nothing: a single
   dropped query threw to the catch and left EVERY list unassigned, so `clients`
   went to 0 and the Add Task dropdown showed only "Select Client" with nothing
   said to the user. It hit the team twice (2026-06-22, 2026-08-10).
   Now: each list is assigned only on its OWN success, everything else keeps its
   last known good value, and a failed read is announced instead of swallowed. */
async function loadAll(){
  const res = await Promise.allSettled([
    sbGet('graphic_projects','?order=created_at.desc&is_archived=eq.false&select='+PROJ_LIST_COLS),
    sbGet('clients','?order=name.asc&select='+CLIENT_LIST_COLS),
    sbGet('graphic_stage_history','?order=entered_at.desc&limit=50'),
    sbGet('graphic_projects','?is_archived=eq.false&image_url=not.is.null&select=id')
  ]);
  const failed = [];
  // a PostgREST error comes back as an OBJECT, not an array — treat that as failure too
  const take = (r, label, current) => {
    if(r.status==='fulfilled' && Array.isArray(r.value)) return r.value;
    failed.push(label);
    console.error('loadAll ['+label+']', r.reason || r.value);
    return current;
  };
  projects     = take(res[0], 'projects', projects);
  clients      = take(res[1], 'clients',  clients);
  stageHistory = take(res[2], 'history',  stageHistory);
  if(res[3].status==='fulfilled' && Array.isArray(res[3].value))
    IMG_IDS = new Set(res[3].value.map(x=>x.id));
  else { failed.push('images'); console.error('loadAll [images]', res[3].reason || res[3].value); }

  if(failed.length) toast('Could not refresh '+failed.join(', ')+'. Showing last known data.','error');

  populateClientDropdowns();
  renderCurrentPage();
}""")

sub("C1 CLIENT_LIST_COLS",
"""const PROJ_LIST_COLS = 'id,title,client_id,client_name,""",
"""/* Only the columns the UI actually renders. Keeps `mrr` and `contact` out of
   the browser entirely, which matters now that freelancers have logins. */
const CLIENT_LIST_COLS = 'id,name,package,industry,health,monthly_posts';
const PROJ_LIST_COLS = 'id,title,client_id,client_name,""")

sub("B2 project detail",
"""  // load comments and history
  const [comments, history] = await Promise.all([
    sbGet('graphic_project_comments','?graphic_project_id=eq.'+id+'&order=created_at.desc'),
    sbGet('graphic_stage_history','?graphic_project_id=eq.'+id+'&order=entered_at.desc')
  ]);""",
"""  // load comments and history — same L-GFX-008 rule as loadAll: one dead read
  // must not stop the modal opening. Before this, a failed comments fetch made
  // clicking a card do nothing at all, with no message.
  const _d = await Promise.allSettled([
    sbGet('graphic_project_comments','?graphic_project_id=eq.'+id+'&order=created_at.desc'),
    sbGet('graphic_stage_history','?graphic_project_id=eq.'+id+'&order=entered_at.desc')
  ]);
  const _took = [];
  const comments = (_d[0].status==='fulfilled' && Array.isArray(_d[0].value)) ? _d[0].value : (_took.push('comments'), []);
  const history  = (_d[1].status==='fulfilled' && Array.isArray(_d[1].value)) ? _d[1].value : (_took.push('history'), []);
  if(_took.length) toast('Could not load '+_took.join(' and ')+' for this post.','error');""")

open(SRC,'w').write(s)
print("\n".join("  OK  "+e for e in edits))
print(f"\n  {len(edits)} anchors applied")
print("  'Dinuka' left in file:", s.count("Dinuka")+s.count("DINUKA"))
print("  Promise.all( left  :", s.count("Promise.all("))
