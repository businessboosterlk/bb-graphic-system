#!/usr/bin/env python3
"""
The three faults that must be fixed BEFORE a recap can report real numbers.

A · THE STALE COMPLETION DATE (the second half of the SMM landmine).
    All three stage handlers stamp completed_at on the way IN to `approved`,
    which is why Graphic does NOT have SMM's 308-of-529 problem: measured
    against the 363 backed-up rows, 12 were finished and 0 were unstamped.
    But nothing clears the stamp on the way OUT. Measured on the same rows:
    17 carried a completion date while only 12 were in a finished stage, so
    FIVE rows claimed a finish time for work that had been reopened. All five
    went approved -> head_review on 2 July and kept the old timestamp.
    A recap would have counted them as finished with a false turnaround.

B · THE LAZY THUMBNAIL STILL DRAGS THE FULL IMAGE.
    The board asks for `select=thumb_url,image_url`, so every card pulls the
    full base64 original anyway and the thumbnail buys nothing. Ask for the
    thumbnail alone, and only fall back to the original for rows uploaded
    before thumb_url existed.

C · ONE IMAGE PATH WRITES NO THUMBNAIL.
    updateImage() sets image_url and leaves thumb_url null, so anything set
    that way has no thumbnail for ever. It takes a URL rather than a file, so
    the link itself is the thumbnail.
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
    edits.append(f"{label} ({n})")

# ── A · clear the stamp on the way out, in all three handlers ──────────
OLD_STAMP = """  if(newStage==='approved') updateData.completed_at = new Date().toISOString();"""
NEW_STAMP = """  /* Stamp on the way IN, and CLEAR on the way OUT. Without the else, a job
     moved back out of Approved keeps its old finish time for ever: five real
     rows did exactly that on 2 July and would have been counted as finished
     with a false turnaround. A stage that is not finished has no finish. */
  updateData.completed_at = (newStage==='approved') ? new Date().toISOString() : null;"""
sub("A · completed_at cleared on reopen (3 handlers)", OLD_STAMP, NEW_STAMP, expect=3)

# ── B · the thumbnail must not carry the original with it ──────────────
sub("B · lazy thumb asks for the thumbnail alone",
"""        /* L-GFX-005: ask for the small thumbnail first. `image_url` is only the
           fallback for rows uploaded before thumb_url existed, and PostgREST
           returns both in one round trip either way. */
        sbGet('graphic_projects','?id=eq.'+pid+'&select=thumb_url,image_url').then(r=>{
          const row = (Array.isArray(r)&&r[0])?r[0]:null;
          const url = row ? (row.thumb_url || row.image_url) : null;
          if(url){ IMG_CACHE[pid]=url; el.src=url; } else { el.style.display='none'; }
        }).catch(()=>{});""",
"""        /* L-GFX-005: ask for the THUMBNAIL ONLY. Asking for both columns in one
           request pulled the full base64 original down for every card anyway,
           which is the exact cost the thumbnail exists to avoid. The original
           is fetched only for rows uploaded before thumb_url existed, and only
           when the small one comes back empty. */
        sbGet('graphic_projects','?id=eq.'+pid+'&select=thumb_url').then(r=>{
          const row = (Array.isArray(r)&&r[0])?r[0]:null;
          if(row && row.thumb_url){ IMG_CACHE[pid]=row.thumb_url; el.src=row.thumb_url; return; }
          return sbGet('graphic_projects','?id=eq.'+pid+'&select=image_url').then(r2=>{
            const old = (Array.isArray(r2)&&r2[0])?r2[0].image_url:null;
            if(old){ IMG_CACHE[pid]=old; el.src=old; } else { el.style.display='none'; }
          });
        }).catch(()=>{});""")

# ── C · the one image path that leaves thumb_url null ──────────────────
sub("C · updateImage writes a thumbnail too",
"""  await sbPatch('graphic_projects','id=eq.'+id, { image_url: url||null, updated_at: new Date().toISOString() });""",
"""  /* This one takes a URL rather than a file, so the link IS the thumbnail.
     Leaving thumb_url null here meant anything set this way had no thumbnail
     for ever and fell back to fetching the full column on every board load. */
  await sbPatch('graphic_projects','id=eq.'+id,
    { image_url: url||null, thumb_url: url||null, updated_at: new Date().toISOString() });""")

open(SRC,'w').write(s)
print("\n".join("  OK  "+e for e in edits))
print(f"\n  {len(edits)} anchors applied")
