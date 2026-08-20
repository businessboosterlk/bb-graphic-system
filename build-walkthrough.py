#!/usr/bin/env python3
"""
BB Graphic System — the welcome walkthrough.

PRIOR ART (bb-build-on-the-best, answered in writing):
  Has BB built this before?  Yes.
  Which build is the best?   The gym member app walkthrough in
                             ~/bb-systems/master-skeleton/gym-member-skeleton.html
                             (gdCards / gdOpen / renderGuideRow), built 2026-08-12.
                             NOT the BSWL app: its student app has one static
                             "Getting started" row with no state (line 1375) and
                             bswl-system.html has onboardingDoc(), which prints a
                             starter guide for a CUSTOMER. Neither is a walkthrough.
  What does it do that mine does not?
                             (a) a permanent reopen entry, which the standard calls
                                 half the feature, because the people who skip on
                                 day one are the ones asking in week two;
                             (b) it opens from the sign-in door, never a boot timer,
                                 after an earlier version greeted somebody by name
                                 over the login screen;
                             (c) every number in the copy is READ from the app, after
                                 it once said "four screens" of a five screen app.
  What am I deliberately NOT taking?
                             BBF.sync() overlay pinning (this app has its own modal
                             layer), and the derived first-week checklist. The
                             standard says a walkthrough and a checklist are two
                             different things and both should exist. The checklist
                             is offered separately rather than faked here.

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

# ── 1 · styles ───────────────────────────────────────────────────────
sub("CSS",
"""  --sidebar-w:232px;--topbar-h:60px;
}""",
"""  --sidebar-w:232px;--topbar-h:60px;
}

/* ══ WELCOME WALKTHROUGH ══════════════════════════════════════════════
   Full screen on purpose. A new designer should read one idea at a time,
   not a tooltip pinned to a control they have not found yet. */
.gd-wrap{position:fixed;inset:0;z-index:400;background:var(--bg);
  display:flex;flex-direction:column;padding:22px 22px calc(22px + env(safe-area-inset-bottom));
  max-width:560px;margin:0 auto}
.gd-wrap[hidden]{display:none}
.gd-top{display:flex;align-items:center;gap:14px;margin-bottom:26px;padding-top:env(safe-area-inset-top)}
.gd-dots{display:flex;gap:6px;flex:1}
.gd-dot{height:4px;flex:1;border-radius:99px;background:var(--border-strong);transition:background var(--t)}
.gd-dot.on{background:var(--accent)}
.gd-skip{background:none;border:none;color:var(--text-3);font-size:14px;font-weight:600;
  cursor:pointer;padding:10px 6px;min-height:44px}
.gd-skip:hover{color:var(--text)}
.gd-body{flex:1;display:flex;flex-direction:column;justify-content:center;overflow-y:auto;-webkit-overflow-scrolling:touch}
.gd-ic{width:56px;height:56px;border-radius:var(--r-md);background:var(--accent-soft);
  display:grid;place-items:center;color:var(--accent);margin-bottom:20px;flex:none}
.gd-ic svg{width:28px;height:28px}
.gd-h{font-size:26px;line-height:1.15;font-weight:800;letter-spacing:-0.02em;margin-bottom:16px;color:var(--text)}
.gd-p{font-size:15.5px;line-height:1.6;color:var(--text-2);margin-bottom:12px}
.gd-p b{color:var(--text);font-weight:650}
.gd-foot{display:flex;gap:12px;align-items:center;padding-top:20px;flex:none}
.gd-back{background:none;border:1px solid var(--border-strong);color:var(--text-2);
  border-radius:var(--r-sm);padding:13px 20px;font-size:14px;font-weight:600;cursor:pointer;min-height:46px}
.gd-back:hover{color:var(--text);border-color:var(--text-3)}
.gd-next{flex:1;background:linear-gradient(135deg,var(--accent) 0%,var(--accent-2) 100%);
  color:#fff;border:none;border-radius:var(--r-sm);padding:13px 20px;font-size:14.5px;
  font-weight:800;letter-spacing:0.02em;cursor:pointer;min-height:46px;box-shadow:0 6px 18px var(--accent-glow)}
/* THE REOPEN ENTRY. This is the half that makes skipping safe. */
.gd-reopen{width:100%;background:none;border:1px solid var(--border);color:var(--text-3);
  border-radius:var(--r-sm);padding:9px 10px;font-size:11.5px;font-weight:600;cursor:pointer;text-align:left}
.gd-reopen:hover{color:var(--text);border-color:var(--border-strong)}""")

# ── 2 · markup ───────────────────────────────────────────────────────
sub("HTML",
"""      <div class="sidebar-actions">
        <button onclick="toggleTheme()">Theme</button>
        <button onclick="logout()">Logout</button>
      </div>""",
"""      <div id="gfxGuideRow"></div>
      <div class="sidebar-actions">
        <button onclick="toggleTheme()">Theme</button>
        <button onclick="logout()">Logout</button>
      </div>""")

sub("overlay markup",
"""<!-- Bulk Add Modal (Pipeline) -->""",
"""<!-- ══ WELCOME WALKTHROUGH: opens on first sign-in, reopenable forever ══
     Everybody skips a tour. The ones who skip it are exactly the ones asking
     in week two, so it lives permanently in the sidebar and is never a
     one-time thing a person can lose. -->
<div class="gd-wrap" id="gdWrap" hidden role="dialog" aria-modal="true" aria-labelledby="gdH">
  <div class="gd-top">
    <div class="gd-dots" id="gdDots"></div>
    <button class="gd-skip" id="gdSkip" onclick="gdEnd()">Skip</button>
  </div>
  <div class="gd-body">
    <div class="gd-ic" id="gdIc"></div>
    <h2 class="gd-h" id="gdH"></h2>
    <div id="gdP"></div>
  </div>
  <div class="gd-foot">
    <button class="gd-back" id="gdBack" onclick="gdGo(-1)">Back</button>
    <button class="gd-next" id="gdNext" onclick="gdGo(1)"></button>
  </div>
</div>

<!-- Bulk Add Modal (Pipeline) -->""")

# ── 3 · behaviour ────────────────────────────────────────────────────
sub("JS",
"""// ─── TOAST ───""",
"""/* ══ WELCOME WALKTHROUGH ═══════════════════════════════════════════════
   Cards answer what a new designer actually turns up wanting to know, never
   "here is our Analytics tab". Any number in the copy is READ from the app,
   never typed, so the guide can never contradict the thing it is describing. */
const GD_ICONS = {
  wave:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 11V6a2 2 0 0 0-4 0v5"/><path d="M14 10V4a2 2 0 0 0-4 0v6"/><path d="M10 10.5V6a2 2 0 0 0-4 0v8"/><path d="M18 8a2 2 0 1 1 4 0v6a8 8 0 0 1-8 8h-2a8 8 0 0 1-8-8"/></svg>',
  board:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="18" rx="1.5"/><rect x="14" y="3" width="7" height="11" rx="1.5"/></svg>',
  plus:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 8v8M8 12h8"/></svg>',
  eye:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1.5 12S5 5.5 12 5.5 22.5 12 22.5 12 19 18.5 12 18.5 1.5 12 1.5 12z"/><circle cx="12" cy="12" r="3"/></svg>',
  week:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M3 10h18M9 4v6M15 4v6"/></svg>',
  ask:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>'
};
function gdCards(){
  const first = (currentUser && currentUser.label ? String(currentUser.label).split(' ')[0] : 'there');
  /* COUNTED, NOT REMEMBERED. A guide that miscounts the thing it describes is
     the fastest way to lose a new person's trust. */
  const pages  = document.querySelectorAll('.nav-item[onclick]').length || 8;
  const stages = STAGES.length;
  const nClients = (clients && clients.length) ? clients.length : 0;
  return [
   {ic:'wave', h:'Welcome, '+first,
    p:['This is where every design job for every client lives, from the first brief to the client approving it.',
       'It is '+pages+' pages and takes about a minute to learn. Skip this if you like. It stays in the sidebar under your name for whenever you want it again.']},
   {ic:'board', h:'The board is your day',
    p:['<b>Pipeline</b> is the main screen. Every post is a card. The '+stages+' columns are the stages a post moves through, from Brief all the way to Approved.',
       'To move a post, drag the card into the next column. You can also press the <b>Move to</b> button at the bottom of it. On your phone use the button.',
       '<b>Move the card as you go, not at the end of the day.</b> The board is how everyone else knows what is happening without asking you.']},
   {ic:'plus', h:'Three ways to add work',
    p:['<b>Quick add</b> on the dashboard is fastest. Type a title, pick the client, done.',
       '<b>Add Post</b> gives you the full form: deadline, priority, size, brief notes and a Drive link.',
       '<b>Bulk Add</b> is for a whole month at once. Use it when a plan lands rather than typing twenty posts one at a time.']},
   {ic:'eye', h:'You can see everything'+(nClients?' ('+nClients+' clients)':''),
    p:['You see every client and every post on the board, not just your own. You can add work for any client and assign it to anyone on the team.',
       '<b>My Work</b> is the one page that stays yours. That is your list for the day.',
       'Use the filters at the top of Pipeline to narrow the board down to one client, one designer or one month.']},
   {ic:'week', h:'The week and the day',
    p:['<b>Weekly Plan</b> is what is meant to happen Monday to Friday. You see the whole team\\'s week, so use the Designer filter if you only want yours.',
       '<b>Daily Pillars</b> is your own short checklist for the day. Tick them off as you go.']},
   {ic:'ask', h:'Two last things',
    p:['<b>Upload the design to the post.</b> Open a post and add the image there. That is what the heads look at when they review, so a post with no image cannot be checked.',
       'If something looks wrong or a page will not load, <b>say so straight away</b> rather than working around it. If the app cannot load something it will now tell you on screen, so send a screenshot of that message.']}
  ];
}
let GD_I = 0;
function gdOpen(){
  const w = document.getElementById('gdWrap'); if(!w) return;
  GD_I = 0; w.hidden = false; document.body.style.overflow='hidden';
  gdRender();
}
function gdEnd(){
  const w = document.getElementById('gdWrap'); if(!w) return;
  w.hidden = true; document.body.style.overflow='';
  try{ localStorage.setItem('bbgfx_guide_seen','1'); }catch(e){}
  renderGuideRow();
}
function gdGo(d){
  const n = gdCards().length;
  if(GD_I + d >= n){ gdEnd(); return; }
  GD_I = Math.max(0, GD_I + d);
  gdRender();
}
function gdRender(){
  const cards = gdCards(), c = cards[GD_I], last = GD_I === cards.length-1;
  document.getElementById('gdIc').innerHTML = GD_ICONS[c.ic]||'';
  document.getElementById('gdH').textContent = c.h;
  document.getElementById('gdP').innerHTML = c.p.map(t=>'<p class="gd-p">'+t+'</p>').join('');
  document.getElementById('gdDots').innerHTML = cards.map((_,i)=>'<span class="gd-dot'+(i<=GD_I?' on':'')+'"></span>').join('');
  document.getElementById('gdBack').style.visibility = GD_I ? '' : 'hidden';
  document.getElementById('gdNext').textContent = last ? 'Start' : 'Next';
  document.getElementById('gdSkip').style.visibility = last ? 'hidden' : '';
  const b = document.querySelector('.gd-body'); if(b) b.scrollTop = 0;
}
function gdSeen(){ try{ return localStorage.getItem('bbgfx_guide_seen')==='1'; }catch(e){ return true; } }
/* THE REOPEN ROW. Half the feature: a tour you can only see once is lost by
   exactly the people who needed it. */
function renderGuideRow(){
  const el = document.getElementById('gfxGuideRow'); if(!el) return;
  el.innerHTML = '<button class="gd-reopen" onclick="gdOpen()">How this works &middot; '+gdCards().length+' cards</button>';
}

// ─── TOAST ───""")

# ── 4 · open it from the SIGN-IN DOOR, never a boot timer ────────────
sub("trigger",
"""  loadAll();
  loadAgentAlerts();""",
"""  loadAll();
  loadAgentAlerts();
  renderGuideRow();
  /* From the sign-in door, never a boot timer: an earlier BB build opened the
     guide over the login screen and greeted somebody before they had proved
     who they were. currentUser is set by the time we get here. */
  if(!gdSeen()) setTimeout(gdOpen, 500);""")

open(SRC,'w').write(s)
print("\n".join("  OK  "+e for e in edits))
print(f"\n  {len(edits)} anchors applied")
