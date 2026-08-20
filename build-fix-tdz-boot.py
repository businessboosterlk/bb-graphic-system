#!/usr/bin/env python3
"""
L-GFX-013 — THE REAL CAUSE of the empty client dropdown.

The session-restore block ran at its position in the script (line ~1247) and
called showApp() -> loadAll(). loadAll's first statement reads PROJ_LIST_COLS,
a `const` declared ~80 lines LATER. A const is in its temporal dead zone until
its own line executes, so this threw

    ReferenceError: Cannot access 'PROJ_LIST_COLS' before initialization

every single time somebody arrived with a saved session. loadAll never ran, so
`clients` stayed [] and the Add Task dropdown had nothing in it.

Fresh sign-in worked, because attemptLogin() calls showApp() long after the
whole script has finished evaluating. RELOADING with a session did not. That is
the difference nobody could pin down: it looked random, and it was not.

Live since 1d64713 (2 July) introduced PROJ_LIST_COLS. Captured on the live site
2026-08-20 from the browser console, not reasoned from source.

Before the L-GFX-008 fix this was invisible: the throw happened inside loadAll's
try/catch and became one console.error nobody reads. The allSettled work did not
cause it and did not fix it. It made it VISIBLE, which is how it was found.

THE FIX: move the session-restore block to the very end of the script, so every
declaration it depends on is initialised before it runs. Nothing else moves.
"""
import sys
SRC = sys.argv[1]
s = open(SRC).read()

OLD = """// check session on load
(function(){
  fillDesignerSelects();
  const saved = sessionStorage.getItem('bbgfx_user');
  if(saved){ currentUser = JSON.parse(saved); showApp(); }
})();

"""
assert s.count(OLD) == 1, f"boot block anchor matched {s.count(OLD)} times"
s = s.replace(OLD, "// (session restore now runs at the END of this script — see L-GFX-013)\n\n")

TAIL_ANCHOR = """  closeModal('modalWpBulk');
  wpLoadWeek();
}
</script>"""
assert s.count(TAIL_ANCHOR) == 1, f"tail anchor matched {s.count(TAIL_ANCHOR)} times"

NEW_TAIL = """  closeModal('modalWpBulk');
  wpLoadWeek();
}

/* ══ SESSION RESTORE — MUST BE THE LAST THING IN THIS SCRIPT ══════════
   L-GFX-013. This used to sit around line 1247, roughly 80 lines ABOVE the
   `const PROJ_LIST_COLS` that loadAll() reads on its first line. A const is in
   its temporal dead zone until its own line runs, so restoring a session threw
   "Cannot access 'PROJ_LIST_COLS' before initialization", loadAll never ran,
   and the client dropdown was empty. Signing in fresh worked; RELOADING did
   not, which is why it read as random.

   If you add anything here, it must stay below every declaration it touches.
   Do not move this block back up. */
(function(){
  fillDesignerSelects();
  let saved = null;
  try{ saved = sessionStorage.getItem('bbgfx_user'); }catch(e){}
  if(saved){
    try{ currentUser = JSON.parse(saved); showApp(); }
    catch(e){
      /* A restore that fails must not leave a half-open app. Send them to the
         login door instead, and say why. */
      console.error('session restore failed', e);
      try{ sessionStorage.removeItem('bbgfx_user'); }catch(_){}
      currentUser = null;
      toast('Could not restore your session. Please sign in again.','error');
    }
  }
})();
</script>"""
s = s.replace(TAIL_ANCHOR, NEW_TAIL)

open(SRC,'w').write(s)
print("  OK  session-restore block moved to end of script")
print("  OK  wrapped in try/catch so a bad restore lands on the login door")
