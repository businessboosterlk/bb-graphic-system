#!/usr/bin/env python3
"""
BB Graphic System — roster + open access.

  1. Designers are Suhana, Farhath, Amjath, Zulfa. Abilashan removed.
  2. EVERY designer sees EVERY client and all work. The per-designer filter
     that commit 8aeb61c added is removed from the shared views.
     "My Work" stays personal — that is the whole point of that page.

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

# ── 1 · the roster ───────────────────────────────────────────────────
sub("USERS",
"""  '3333': { name:'SUHANA', role:'designer', team_member_id:3, label:'Suhana' },
  '5555': { name:'ABILASHAN', role:'designer', team_member_id:null, label:'Abilashan' },""",
"""  '3333': { name:'SUHANA', role:'designer', team_member_id:3, label:'Suhana' },
  '4444': { name:'FARHATH', role:'designer', team_member_id:null, label:'Farhath' },
  '6666': { name:'AMJATH', role:'designer', team_member_id:null, label:'Amjath' },
  '7777': { name:'ZULFA', role:'designer', team_member_id:null, label:'Zulfa' },""")

sub("DESIGNERS",
"""const DESIGNERS = [
  { name:'SUHANA',    label:'Suhana',    team_member_id:3,    freelancer:false },
  { name:'ABILASHAN', label:'Abilashan', team_member_id:null, freelancer:true  },
];""",
"""const DESIGNERS = [
  { name:'SUHANA',  label:'Suhana',  team_member_id:3,    freelancer:false },
  { name:'FARHATH', label:'Farhath', team_member_id:null, freelancer:false },
  { name:'AMJATH',  label:'Amjath',  team_member_id:null, freelancer:false },
  { name:'ZULFA',   label:'Zulfa',   team_member_id:null, freelancer:false },
];""")

# freelancer flag is unused now, but keep the label logic harmless
sub("drop freelance suffix",
"""        (d.team_member_id==null?'':d.team_member_id)+'">'+esc(d.label)+
        (d.freelancer?' (freelance)':'')+'</option>').join('');""",
"""        (d.team_member_id==null?'':d.team_member_id)+'">'+esc(d.label)+
        (d.freelancer?' (freelance)':'')+'</option>').join('');   /* no freelancers on the roster today */""")

# ── 2 · open access ──────────────────────────────────────────────────
sub("scopedProjects opened",
"""function scopedProjects(list){
  const d = designerScope();
  return d ? list.filter(p=>p.assigned_designer===d) : list;
}""",
"""/* OPEN ACCESS (Thulaib, 2026-08-20). Every designer sees every client and all
   work, and can add work for any client. This deliberately reverses the
   per-designer filter from 8aeb61c. Kept as a function, not deleted, so the
   shared views keep one obvious place to re-narrow if that ever changes.
   designerScope() still exists and is still used — but only to DEFAULT a new
   task to the person adding it, never to hide anything from them. */
function scopedProjects(list){
  return list;
}
/* The one place a personal filter is still correct: the My Work page. */
function onlyMine(list){
  const d = designerScope();
  return d ? list.filter(p=>p.assigned_designer===d) : list;
}""")

sub("My Work stays personal",
"""  const myProjects = scopedProjects(projects.filter(p=>!p.is_archived));""",
"""  const myProjects = onlyMine(projects.filter(p=>!p.is_archived));""")

sub("clients quarter unscoped",
"""  let qArr = Array.isArray(qProjects)?qProjects:[];
  const dScope = designerScope();
  if(dScope) qArr = qArr.filter(p=>p.assigned_designer===dScope);""",
"""  let qArr = Array.isArray(qProjects)?qProjects:[];
  /* open access — the client page shows every client's work to everyone */""")

sub("weekly plan unscoped",
"""  let f = wpTasks;
  // Role-based: designers see only their tasks
  const dScope = designerScope();
  if(dScope) f = f.filter(t=>t.assigned_to===dScope);""",
"""  let f = wpTasks;
  /* open access — everyone sees the whole week. Use the Designer filter above
     to narrow it to one person on purpose. */""")

sub("weekly filter bar visible",
"""  const filterBar = document.getElementById('wpFilters');
  if(filterBar && currentUser && currentUser.role==='designer') filterBar.style.display='none';""",
"""  const filterBar = document.getElementById('wpFilters');
  /* designers get the filters too now — they can see everyone, so they need
     a way to narrow it down */
  if(filterBar) filterBar.style.display='';""")

open(SRC,'w').write(s)
print("\n".join("  OK  "+e for e in edits))
print(f"\n  {len(edits)} anchors applied")
print("  Abilashan left:", s.count("ABILASHAN")+s.count("Abilashan"))
