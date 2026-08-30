#!/usr/bin/env python3
"""
Harness sections E, F and G: the app shell and the phone foundations.

Names carried from bb-video-system so the two systems stay greppable.

THE RULE THAT MAKES THESE WORTH HAVING: a check that passes because it could not
find its target is worse than no check, because it also spends your confidence.
Every check here that selects something fails loudly when the selection is empty.

Three checks are NOT in the brief and are added because they catch bugs found in
this very pass: apply_app_shell.py turns all seven green while leaving a manifest
that says "Total Uplift", declaring 13 icons when 4 exist, and a service worker
it never registers.
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

# video's checks read BBF.ovs; keep that name so they port across unchanged
sub("expose ovs under video's name",
""" return {start:start,hintKeyboards:hintKeyboards,anyOpen:anyOpen,sync:sync,
         overlaySelector:function(){return OVS;},""",
""" return {start:start,hintKeyboards:hintKeyboards,anyOpen:anyOpen,sync:sync,
         ovs:OVS,                       /* the name bb-video-system's checks use */
         overlaySelector:function(){return OVS;},""")

CHECKS = r"""
    });

    await section('App shell and phone foundations', async () => {
    const cs = el => getComputedStyle(el);

    /* ── E · BB APP SHELL ─────────────────────────────────────────────── */
    ok('Shell: viewport-fit=cover is set, so env() is not always 0',
       /viewport-fit\s*=\s*cover/.test((document.querySelector('meta[name=viewport]')||{content:''}).content),
       'without it env() reports 0 on every device and the whole thing silently does nothing');
    ok('Shell: the page paints the status bar strip', !!document.querySelector('.statusfill'));
    ok('Shell: it is installable', !!document.querySelector('link[rel=manifest]'));
    const bar = document.querySelector('.topbar');
    if(!bar){
      ok('Shell: chrome moves down for a notch', false, 'NO .topbar FOUND, this check proved nothing');
      ok('Shell: and leaves no gap without one', false, 'not proven');
    } else {
      /* env() cannot be read or faked from JS, which is exactly WHY the inset is
         stored in an overridable variable. Push it and assert the chrome moved.
         This proves the wiring. Only a real handset proves a real notch. */
      const root = document.documentElement;
      root.style.setProperty('--sat','59px');
      const moved = parseFloat(cs(bar).paddingTop);
      root.style.setProperty('--sat','0px');
      const back = parseFloat(cs(bar).paddingTop);
      root.style.removeProperty('--sat');
      ok('Shell: chrome moves down for a notch', moved>=59, 'padding-top became '+moved+'px');
      ok('Shell: and leaves no gap without one', back===0, 'padding-top became '+back+'px');
    }

    /* Not in the brief. Added because apply_app_shell.py turned all seven green
       while the manifest still said "Total Uplift" and declared 13 icons against
       4 on disk. A home screen icon labelled with another product is the most
       visible possible failure and no existing check looked at it. */
    try{
      const mf = await (await fetch('./manifest.json',{cache:'no-store'})).json();
      ok('Shell: the manifest names THIS app',
         /graphic/i.test(mf.name||'') && !/uplift|gym/i.test((mf.name||'')+(mf.short_name||'')),
         'name is "'+mf.name+'", short_name "'+mf.short_name+'"');
      const declared = (mf.icons||[]).map(i=>i.src);
      const missing = [];
      for(const src of declared){
        try{ const r = await fetch(src,{method:'HEAD',cache:'no-store'}); if(!r.ok) missing.push(src); }
        catch(e){ missing.push(src); }
      }
      ok('Shell: every icon the manifest declares actually exists',
         declared.length>0 && missing.length===0,
         declared.length+' declared, '+missing.length+' missing'+(missing.length?': '+missing.slice(0,3).join(', '):''));
    }catch(e){
      ok('Shell: the manifest names THIS app', false, 'manifest.json unreadable: '+(e&&e.message));
      ok('Shell: every icon the manifest declares actually exists', false, 'not proven');
    }

    /* ── F · BB APP FOUNDATIONS ───────────────────────────────────────── */
    ok('App: double tap does not zoom', cs(document.documentElement).touchAction==='manipulation',
       cs(document.documentElement).touchAction);
    ok('App: the page does not pull to refresh', cs(document.body).overscrollBehaviorY==='none',
       cs(document.body).overscrollBehaviorY);
    const nav = document.querySelector('.nav-item');
    ok('App: no blue flash on tap',
       !!nav && /rgba\(0, 0, 0, 0\)|transparent/.test(cs(nav).webkitTapHighlightColor),
       nav ? cs(nav).webkitTapHighlightColor : 'NO .nav-item FOUND, this check proved nothing');
    ok('App: chrome does not select on drag', !!nav && cs(nav).userSelect==='none',
       nav ? cs(nav).userSelect : 'NO .nav-item FOUND, this check proved nothing');

    /* The field-zoom rule is coarse-pointer only, so on a laptop it can NEVER
       fail. A desktop green here proves nothing about the phone, and the detail
       says so rather than quietly banking a pass. */
    if(matchMedia('(pointer:coarse)').matches){
      const small=[];
      document.querySelectorAll('input,select,textarea').forEach(el=>{
        if(el.type==='hidden')return;
        if(parseFloat(cs(el).fontSize)<16) small.push((el.id||el.className||el.tagName)+' '+cs(el).fontSize);
      });
      ok('App: no field under 16px, so focusing one cannot zoom the screen', small.length===0,
         small.slice(0,3).join(', ') || 'all 16px or more, measured at coarse pointer');
    } else {
      ok('App: no field under 16px, so focusing one cannot zoom the screen', true,
         'FINE POINTER: the rule is coarse only, so this cannot fail here. RUN AT 390px TO PROVE IT');
    }
    ok('App: the foundation layer is present', typeof BBF==='object' && !!BBF.start);
    ok('App: scroll restoration is manual', history.scrollRestoration==='manual',
       history.scrollRestoration);

    /* Not in the brief. The 11 August freeze was an observer doing layout work
       per mutation. The invariant is that a render is not an overlay change. */
    if(typeof BBF.runs==='function'){
      const r0 = BBF.runs();
      ['dashboard','pipeline','clients','weeklyplan'].forEach(p=>{ try{ navigateTo(p); }catch(e){} });
      const spent = BBF.runs() - r0;
      ok('App: rendering pages does not storm the observer', spent<=3,
         'four navigations caused '+spent+' sync runs; more than 3 means the coalescing is gone');
    }

    /* ── G · THE FREEZE, proven by doing it ───────────────────────────── */
    let frozen=false, shielded=false, used='';
    const all = [].slice.call(document.querySelectorAll(BBF.ovs));
    if(!all.length){
      ok('App: the page behind an open sheet is frozen', false,
         'COULD NOT FIND ANY OVERLAY ('+BBF.ovs+'), so this check proved nothing');
      ok('App: the page behind an open sheet is out of reach', false, 'not proven');
    } else {
      /* Try every declared overlay until one opens, and name which one proved
         it. This app opens modals with .open, the sidebar backdrop with .show
         and the walkthrough by dropping the hidden attribute, so the restore
         has to put back exactly what it found in all three shapes. */
      for(let i=0;i<all.length && !frozen;i++){
        const ov = all[i];
        const had = {open:ov.classList.contains('open'),
                     show:ov.classList.contains('show'),
                     hidden:ov.hasAttribute('hidden')};
        ov.classList.add('open'); ov.classList.add('show'); ov.removeAttribute('hidden');
        BBF.sync();                    /* the observer runs a tick later; drive it */
        if(cs(document.body).position==='fixed'){
          frozen = true;
          shielded = !!document.querySelector('[inert]');
          used = (String(ov.className).split(' ')[0] || ov.id || ov.tagName);
        }
        if(!had.open) ov.classList.remove('open');
        if(!had.show) ov.classList.remove('show');
        if(had.hidden) ov.setAttribute('hidden','');
        BBF.sync();
      }
      ok('App: the page behind an open sheet is frozen', frozen,
         frozen ? ('pinned, proven on .'+used) : ('none of '+all.length+' overlays froze it'));
      ok('App: the page behind an open sheet is out of reach', shielded,
         shielded ? 'inert applied to the rest of the body' : 'still tappable and tabbable');
    }

    /* The drawer must survive its own backdrop. #sidebarOverlay is a SIBLING of
       #sidebar, so a generic shield inerts the drawer the backdrop belongs to
       and it goes dead under the thumb. That is what the keep list prevents. */
    const sb = document.getElementById('sidebar'), sbo = document.getElementById('sidebarOverlay');
    if(!sb || !sbo){
      ok('App: the drawer stays usable while its own backdrop is up', false,
         'NO #sidebar or #sidebarOverlay FOUND, this check proved nothing');
    } else {
      const hadShow = sbo.classList.contains('show');
      sbo.classList.add('show'); BBF.sync();
      const dead = sb.hasAttribute('inert');
      if(!hadShow) sbo.classList.remove('show');
      BBF.sync();
      ok('App: the drawer stays usable while its own backdrop is up', !dead,
         dead ? 'the sidebar was inerted by its own backdrop, so the drawer is dead to the touch'
              : 'kept reachable by the keep list');
    }
"""

sub("harness sections E F G",
"""    });

  }catch(e){
    ok('Harness completed without throwing', false, e && e.message);""",
CHECKS + """
    });

  }catch(e){
    ok('Harness completed without throwing', false, e && e.message);""")

open(SRC,'w').write(s)
print("\n".join("  OK  "+e for e in edits))
print(f"\n  {len(edits)} anchors applied")
