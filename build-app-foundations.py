#!/usr/bin/env python3
"""
BB Graphic System — the nine phone knobs + BBF.

PRIOR ART, and one correction to the brief that matters:
  The brief named ~/bb-video-system as the best build. For FIT that is right:
  same posture, same tables, same single-file shape. But its BBF module
  PREDATES the 11 August freeze fix, the one bb-app-foundations calls "the worst
  bug this skill has produced". Measured 2026-08-21:

      scheduleSync present:  video 0 | master-skeleton 0 | restaurant 0
                             gym-skeleton 3 | gym-member 3 | bb-smm-workspace 3

  Porting video's module verbatim would have shipped a known browser freeze onto
  the phones of the people who use this daily. So:
    - the SHAPE, the safe-area targets and the app wiring come from video
    - the MODULE INTERNALS come from bb-smm-workspace, the most recent port
      (2026-08-21) and one of only three files carrying the fix.

  Taken from SMM: scheduleSync coalescing, the inSync reentrancy guard, the
  syncRuns counter the harness asserts on, the KEEP list, and overlaySelector()
  so the check asks the module rather than carrying its own selector.

GRAPHIC'S TWO OVERLAY TRAPS, both real in this file:
  1. `.sidebar` (line 189) is permanently `display:flex` and hidden by
     translateX(-100%). It has a non-zero rect at all times, so a visibility
     test judges it ALWAYS OPEN. It is deliberately NOT in OVS.
  2. `#sidebarOverlay` (line 555) is a SIBLING of `#sidebar` (line 558), so the
     shield would inert the drawer while its own backdrop is up and the drawer
     would go dead to the touch. That is what KEEP is for.
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

CSS = r"""
/* ═══ BB APP SHELL + APP FOUNDATIONS, cascade-final ═══════════════════════
   ONE block at the very end of the last sheet on purpose. The documented trap
   is a @media rule resetting a box further down and killing the inset on the
   ONE screen that has a notch. Last in the sheet wins everywhere.
   Rollback is deleting this block. */

/* 1 · TOUCH. No double-tap zoom, no pull to refresh, no blue flash, no
      long-press copy on controls. Text and values stay selectable, because
      somebody copying a client name or a brief is fine and blocking it is rude. */
html{touch-action:manipulation}
html,body{overscroll-behavior-y:none}
*{-webkit-tap-highlight-color:transparent}
button,label,.nav-item,.btn,.k-advance,.wp-item-box,.wp-item-next,.gd-next,.gd-back,.gd-skip,
.stage-dot,.badge,[role="button"]{
 -webkit-touch-callout:none;-webkit-user-select:none;user-select:none}

/* 2 · THE FIELD ZOOM. iOS zooms the whole viewport when a focused input has
      text under 16px, and does not zoom back. 16 is the platform threshold,
      not a preference. Coarse pointers only, so the desktop keeps its scale. */
@media (pointer:coarse){
 input,select,textarea,.login-input-big{font-size:16px!important}
}

/* 3 · A sheet must not chain its scroll into the page behind it. */
.modal,.modal-overlay,.gd-wrap,.gd-body,.wp-grid-wrap,.kanban-cards,.content{
 overscroll-behavior:contain}

/* 4 · SAFE AREA. Read from the device, never detected. Every element that
      touches the top or bottom edge uses the variables. */
.topbar{height:auto;min-height:calc(var(--topbar-h) + var(--sat));padding-top:var(--sat)}
.sidebar{padding-top:var(--sat);padding-bottom:var(--sab)}
.login{padding-top:calc(24px + var(--sat));padding-bottom:calc(24px + var(--sab))}
.gd-wrap{padding:calc(22px + var(--sat)) 22px calc(22px + var(--sab))}
.toast-wrap{bottom:calc(24px + var(--sab))}
.modal-overlay{padding:calc(20px + var(--sat)) 20px calc(20px + var(--sab))}
#bbGfxSentinelBanner{top:var(--sat)!important}

/* 5 · vh is measured against the TALLEST the viewport ever gets, so a modal at
      90vh pushes its own buttons off screen the moment the address bar appears.
      dvh tracks the real height. */
.modal{max-height:min(90dvh,calc(100dvh - var(--sat) - var(--sab) - 32px))}

/* 6 · THE FREEZE. overflow:hidden alone does not hold on iOS: the page keeps
      its rubber band and silently forgets where it was. BBF pins the body at a
      negative top and puts it back on close, and the restore is the entire
      reason to do it this way. */
body.sheet-open{position:fixed;left:0;right:0;width:100%}

/* 7 · TAP TARGETS ON THE WEEKLY GRID. The tick box is drawn 17px so the grid
      stays dense, which is right under a mouse and a miss waiting to happen
      under a finger. 44px is the platform minimum. A near miss on the tick
      opens the cell editor instead, so getting this wrong silently drops
      somebody into a text box when they meant to tick a job done. */
@media (pointer:coarse){
 .wp-item{padding:12px 0}
 .wp-item-box,.wp-item-next{position:relative}
 .wp-item-box::after,.wp-item-next::after{
   content:'';position:absolute;left:50%;top:50%;
   width:44px;height:44px;transform:translate(-50%,-50%);inset:auto}
}
"""

sub("CSS block, cascade-final",
"""</style>
</body>""",
CSS + """</style>
</body>""")

BBF = r"""
/* ═══ BB APP FOUNDATIONS (BBF) ═════════════════════════════════════════════
   Makes this behave like an app rather than a page on a phone: the page behind
   a sheet is frozen AND out of reach, Back closes the sheet instead of leaving
   the app, and the keyboard's action key says what the button says.

   Module internals taken from bb-smm-workspace, NOT from bb-video-system.
   Video's copy predates the 11 August freeze fix: its observers call sync()
   directly on every mutation batch, and sync() reads layout for every overlay,
   so a render storm hung the browser for 30 seconds. Verified 2026-08-21 that
   video, bb-master-skeleton and restaurant-skeleton all still lack the fix. */
var BBF=(function(){
 /* Backdrops and full-screen dialogs only.
    NOT `.sidebar`: it is permanently display:flex and hidden by
    translateX(-100%), so it has a non-zero rect at all times and a visibility
    test would call it open forever. */
 var OVS='.modal-overlay, .sidebar-overlay, .gd-wrap';
 /* Must stay reachable while a backdrop is up. #sidebarOverlay is a SIBLING of
    #sidebar, so without this the shield inerts the drawer the backdrop belongs
    to and the drawer goes dead under the thumb. */
 var KEEP='#sidebar';
 var lockedY=0, locked=false, lastFocus=null, histDepth=0, closing=false;
 try{if('scrollRestoration' in history)history.scrollRestoration='manual';}catch(e){}

 /* AN OVERLAY IS OPEN WHEN IT IS VISIBLE, not when it carries a class. This app
    uses .open on modals, .show on the sidebar backdrop and the hidden attribute
    on the walkthrough. Visibility is true of all three. */
 function isOpen(el){
  var cs=getComputedStyle(el);
  if(cs.display==='none'||cs.visibility==='hidden')return false;
  var r=el.getBoundingClientRect();
  if(!(r.width>0&&r.height>0))return false;
  /* A FADING OVERLAY IS OPEN THE MOMENT IT STARTS. Opacity reads 0 for one
     frame and the observer fires BEFORE that frame, so it was judged closed and
     the body was never pinned. A running transition means it is opening. */
  if(parseFloat(cs.opacity||'1')<0.05){
   var moving=false;
   try{moving=el.getAnimations().some(function(a){
    return a.playState==='running'||a.playState==='pending';});}catch(e){}
   if(!moving)return false;
  }
  return true;
 }
 function anyOpen(){var n=document.querySelectorAll(OVS),i;
  for(i=0;i<n.length;i++)if(isOpen(n[i]))return n[i];return null;}

 function lock(){if(locked)return;
  lockedY=window.scrollY||window.pageYOffset||0;
  document.body.style.top=(-lockedY)+'px';
  document.body.classList.add('sheet-open');locked=true;}
 function unlock(){if(!locked)return;
  document.body.classList.remove('sheet-open');document.body.style.top='';
  window.scrollTo(0,lockedY);locked=false;}

 /* Covered is not the same as out of reach: a thumb still hits a button through
    the gap beside a sheet, and a keyboard or screen reader walks straight into
    content the person cannot see. Generic, so it survives any later screen. */
 var shielded=[];
 function shield(ov){release();if(!ov)return;
  [].slice.call(document.body.children).forEach(function(el){
   if(el===ov||el.contains(ov))return;
   if(/^(SCRIPT|STYLE|TEMPLATE|LINK)$/.test(el.tagName))return;
   if(el.matches&&el.matches(KEEP))return;
   if(el.querySelector&&el.querySelector(KEEP))return;
   if(el.hasAttribute('inert'))return;
   el.setAttribute('inert','');el.setAttribute('aria-hidden','true');shielded.push(el);});}
 function release(){shielded.forEach(function(el){
  el.removeAttribute('inert');el.removeAttribute('aria-hidden');});shielded=[];}

 function takeFocus(ov){lastFocus=document.activeElement;
  var f=ov.querySelector('button,[href],input,[tabindex]:not([tabindex="-1"])');
  if(f){try{f.focus({preventScroll:true});}catch(e){}}}
 function giveBackFocus(){if(lastFocus&&lastFocus.focus){
  try{lastFocus.focus({preventScroll:true});}catch(e){}}lastFocus=null;}

 /* BACK CLOSES THE SHEET, it does not leave the app. On Android this is the
    loudest tell that a product is really a web page. */
 function closeTop(){var ov=anyOpen();if(!ov)return false;
  var oc=ov.getAttribute&&ov.getAttribute('onclick');
  if(oc&&/close/i.test(oc)){ov.click();return true;}
  var btn=ov.querySelector('[onclick*="close"],[onclick*="Close"],[data-close]');
  if(btn){btn.click();return true;}
  if(ov.id==='gdWrap'&&typeof gdEnd==='function'){try{gdEnd();return true;}catch(e){}}
  ov.classList.remove('open');ov.classList.remove('show');return true;}
 window.addEventListener('popstate',function(){
  if(closing)return;                 /* this pop is the one our own close asked for */
  if(histDepth>0){histDepth--;closeTop();}});
 window.addEventListener('keydown',function(e){
  if(e.key==='Escape'&&anyOpen()){e.preventDefault();history.back();}});

 /* COALESCE. A render can ask for a sync hundreds of times; the work runs once.
    Doing layout work per mutation is what froze the OS on 11 August. */
 var syncQueued=false,inSync=false,syncRuns=0;
 function scheduleSync(){if(syncQueued)return;syncQueued=true;
  setTimeout(function(){syncQueued=false;sync();},0);}
 function sync(){if(inSync)return;inSync=true;syncRuns++;
  try{syncBody();}finally{inSync=false;}}
 function syncBody(){
  var ov=anyOpen();
  if(ov&&!locked){lock();shield(ov);takeFocus(ov);
   histDepth++;try{history.pushState({bbSheet:1},'');}catch(e){}}
  else if(!ov&&locked){release();giveBackFocus();
   /* Unlock synchronously, always. Deferring it behind a timer left the body
      pinned for whatever ran next, and that could then not scroll at all. */
   unlock();
   if(histDepth>0){histDepth--;closing=true;
    try{history.back();}catch(e){}
    setTimeout(function(){closing=false;},0);}}}

 /* ONE observer, never N edited open functions. The body observer's job is
    spotting NEW overlays, so it only schedules when it actually saw one. */
 function start(){
  var mo=new MutationObserver(scheduleSync);
  var watch=function(el){mo.observe(el,{attributes:true,attributeFilter:['class','style','hidden']});};
  document.querySelectorAll(OVS).forEach(watch);
  new MutationObserver(function(muts){
   var sawOverlay=false;
   muts.forEach(function(m){[].slice.call(m.addedNodes).forEach(function(n){
    if(n.nodeType===1&&n.matches&&n.matches(OVS)){watch(n);sawOverlay=true;}});});
   if(sawOverlay)scheduleSync();
  }).observe(document.body,{childList:true,subtree:true});
  sync();
 }

 /* THE KEYBOARD SAYS WHAT THE BUTTON SAYS. Applied at focus, which is the only
    moment it is read, because most fields here do not exist until their page or
    modal renders. */
 function hint(el){
  if(!el||!/^(INPUT|TEXTAREA)$/.test(el.tagName))return;
  if(el.getAttribute('enterkeyhint'))return;
  var form=el.closest('.modal,.filter-bar,.login-card,form')||document.body;
  var peers=form.querySelectorAll('input:not([type=checkbox]):not([type=radio]),textarea');
  el.setAttribute('enterkeyhint',peers.length&&peers[peers.length-1]===el?'go':'next');
  if(el.type==='email'||el.inputMode==='email'||el.inputMode==='numeric'||el.inputMode==='decimal'){
   el.setAttribute('autocapitalize','off');el.setAttribute('autocorrect','off');
   el.setAttribute('spellcheck','false');}}
 function hintKeyboards(){
  document.addEventListener('focusin',function(e){hint(e.target);});
  document.querySelectorAll('input,textarea').forEach(hint);}

 /* The check asks the module for its selector. A hand written selector inside a
    check is a selector that can be pointed at nothing and pass on silence. */
 return {start:start,hintKeyboards:hintKeyboards,anyOpen:anyOpen,sync:sync,
         overlaySelector:function(){return OVS;},
         keepSelector:function(){return KEEP;},
         runs:function(){return syncRuns;},
         isLocked:function(){return locked;}};
})();
BBF.start();BBF.hintKeyboards();

/* The tool copies a service worker and never registers it, so the app installs
   and the worker never runs. Register it here. It is network-first and never
   caches the database: a stale board is worse than no board. */
if('serviceWorker' in navigator){
  window.addEventListener('load',function(){
    navigator.serviceWorker.register('./sw.js').catch(function(){});
  });
}

"""

sub("BBF module",
"""/* ══ SESSION RESTORE — MUST BE THE LAST THING IN THIS SCRIPT ══════════""",
BBF + """/* ══ SESSION RESTORE — MUST BE THE LAST THING IN THIS SCRIPT ══════════""")

# BBF now owns the freeze, and it restores scroll position, which the manual
# overflow toggle never did. Hand it over rather than having two owners.
sub("walkthrough hands the freeze to BBF",
"""  GD_I = 0; w.hidden = false; document.body.style.overflow='hidden';""",
"""  GD_I = 0; w.hidden = false;   /* BBF owns the freeze now, and it restores scroll */""")
sub("walkthrough close",
"""  w.hidden = true; document.body.style.overflow='';""",
"""  w.hidden = true;""")

open(SRC,'w').write(s)
print("\n".join("  OK  "+e for e in edits))
print(f"\n  {len(edits)} anchors applied")
