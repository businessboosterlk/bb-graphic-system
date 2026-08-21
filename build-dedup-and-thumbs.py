#!/usr/bin/env python3
"""
Close the two traps the board clear left armed.

L-GFX-010 · bulk add had NO dedup guard. 17 titles became 346 rows in one day.
  The weekly plan got a guard in a5f0c68; the projects bulk add never did.
  Ported that pattern and made it stricter: it also dedups WITHIN the batch,
  which the weekly plan version does not, because clicking Save twice is exactly
  how you get twenty copies of the same seventeen titles.

L-GFX-005 · board thumbnails fetched the FULL-SIZE original per card, ~240 KB
  each. Now a real thumbnail is written at upload time into the new `thumb_url`
  column (360px, q0.62, roughly 15-25 KB) and the lazy loader fetches that
  instead. The full image is still only fetched when a post is actually opened.

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

# ── 1 · a thumbnail maker beside the existing compressor ─────────────
sub("thumb maker",
"""function readImageFile(file, hostId) {""",
"""/* L-GFX-005. A board thumbnail never needs to be 1400px. This makes a small
   one at upload time so the board fetches ~20 KB a card instead of ~240 KB.
   Same canvas path as compressImageDataUrl, just a smaller box and lower
   quality, because it is rendered about 200px wide. */
function makeThumbDataUrl(dataUrl, maxDim = 360, quality = 0.62){
  return compressImageDataUrl(dataUrl, maxDim, quality);
}

function readImageFile(file, hostId) {""")

# ── 2 · write the thumb on every path that writes an image ───────────
sub("PROJ_LIST_COLS carries thumb presence",
"""const PROJ_LIST_COLS = 'id,title,client_id,client_name,""",
"""/* thumb_url is deliberately NOT in this list. It is small, but 360 of them
   still add up, so the board fetches each one lazily as a card scrolls in. */
const PROJ_LIST_COLS = 'id,title,client_id,client_name,""")

# lazy loader now pulls the thumbnail, falling back to the full image for any
# row uploaded before thumb_url existed
sub("lazy thumbs use thumb_url",
"""        sbGet('graphic_projects','?id=eq.'+pid+'&select=image_url').then(r=>{
          const url = (Array.isArray(r)&&r[0])?r[0].image_url:null;
          if(url){ IMG_CACHE[pid]=url; el.src=url; } else { el.style.display='none'; }
        }).catch(()=>{});""",
"""        /* L-GFX-005: ask for the small thumbnail first. `image_url` is only the
           fallback for rows uploaded before thumb_url existed, and PostgREST
           returns both in one round trip either way. */
        sbGet('graphic_projects','?id=eq.'+pid+'&select=thumb_url,image_url').then(r=>{
          const row = (Array.isArray(r)&&r[0])?r[0]:null;
          const url = row ? (row.thumb_url || row.image_url) : null;
          if(url){ IMG_CACHE[pid]=url; el.src=url; } else { el.style.display='none'; }
        }).catch(()=>{});""")

# ── 3 · DEDUP GUARD on the projects bulk add ─────────────────────────
sub("bulk add dedup",
"""async function bulkSaveAll(){
  const rows = document.querySelectorAll('#bulkRows tr');
  let count=0;
  window.__gdSaving = true;
  try {
    for(const row of rows){
      const title = row.querySelector('.bk-title').value.trim();
      if(!title) continue;
      const clientSel = row.querySelector('.bk-client');
      const clientId = clientSel.value ? parseInt(clientSel.value) : null;
      const clientName = clientSel.value ? clientSel.options[clientSel.selectedIndex].dataset.name : null;
      const data = {""",
"""/* L-GFX-010. The key a duplicate is judged on. Deliberately does NOT include
   designer or priority: the same post for the same client in the same month is
   the same post, whoever it was handed to. */
function bulkKey(title, clientName, month, year){
  return [String(title||'').trim().toLowerCase(),
          String(clientName||'').trim().toLowerCase(),
          month, year].join('|');
}

async function bulkSaveAll(){
  const rows = document.querySelectorAll('#bulkRows tr');
  let count=0, skipped=0;
  const month = new Date().getMonth()+1, year = new Date().getFullYear();
  /* Seed from what is already on the board, then keep adding to it as we go.
     The second half is what the weekly plan guard is missing: 346 rows came
     from 17 titles, which is a Save pressed more than once, not 346 typos. */
  const seen = new Set((projects||[])
    .filter(p=>!p.is_archived)
    .map(p=>bulkKey(p.title, p.client_name, p.target_month, p.target_year)));
  window.__gdSaving = true;
  try {
    for(const row of rows){
      const title = row.querySelector('.bk-title').value.trim();
      if(!title) continue;
      const clientSel = row.querySelector('.bk-client');
      const clientId = clientSel.value ? parseInt(clientSel.value) : null;
      const clientName = clientSel.value ? clientSel.options[clientSel.selectedIndex].dataset.name : null;
      const k = bulkKey(title, clientName, month, year);
      if(seen.has(k)){ skipped++; continue; }
      seen.add(k);
      const data = {""")

sub("bulk add writes a thumb",
"""        image_url: row._img || null,
        current_stage: 'brief',
        target_month: new Date().getMonth()+1,
        target_year: new Date().getFullYear(),
        created_by: currentUser.name,
      };""",
"""        image_url: row._img || null,
        thumb_url: row._thumb || null,
        current_stage: 'brief',
        target_month: month,
        target_year: year,
        created_by: currentUser.name,
      };""")

sub("bulk add reports skips",
"""  if(count===0){ toast('No posts to add — fill at least one title','error'); return; }
  toast(count+' post'+(count>1?'s':'')+' added');
  closeModal('modalBulkPipeline');""",
"""  if(count===0 && skipped===0){ toast('No posts to add — fill at least one title','error'); return; }
  if(count===0){ toast('Nothing added — all '+skipped+' were already on the board','error'); closeModal('modalBulkPipeline'); return; }
  let msg = count+' post'+(count!==1?'s':'')+' added';
  if(skipped) msg += ', '+skipped+' duplicate'+(skipped!==1?'s':'')+' skipped';
  toast(msg);
  closeModal('modalBulkPipeline');""")

# cache the thumb the board will want, not the full image
sub("bulk caches the thumb",
"""        if(row._img){ IMG_IDS.add(res[0].id); IMG_CACHE[res[0].id] = row._img; }""",
"""        if(row._img){ IMG_IDS.add(res[0].id); IMG_CACHE[res[0].id] = row._thumb || row._img; }""")

# ── 4 · every path that stores an image now stores a thumbnail too ───
sub("PENDING_THUMB store",
"""const PENDING_IMG = {};""",
"""const PENDING_IMG = {};
/* L-GFX-005: the small board copy, made at the same moment as the big one so
   the two can never drift apart. */
const PENDING_THUMB = {};""")

sub("readImageFile makes a thumb",
"""    const compressed = await compressImageDataUrl(ev.target.result);
    PENDING_IMG[hostId] = compressed;
    const pv = document.getElementById(hostId + '-preview');""",
"""    const compressed = await compressImageDataUrl(ev.target.result);
    PENDING_IMG[hostId] = compressed;
    PENDING_THUMB[hostId] = await makeThumbDataUrl(ev.target.result);
    const pv = document.getElementById(hostId + '-preview');""")

sub("clearPendingImg clears the thumb",
"""function clearPendingImg(hostId) {
  delete PENDING_IMG[hostId];""",
"""function clearPendingImg(hostId) {
  delete PENDING_IMG[hostId];
  delete PENDING_THUMB[hostId];""")

sub("saveDetailImage writes a thumb",
"""async function saveDetailImage(projId) {
  const img = PENDING_IMG['detailImg'];
  if (!img) return;
  await sbPatch('graphic_projects', 'id=eq.' + projId, { image_url: img, updated_at: new Date().toISOString() });
  IMG_IDS.add(projId); IMG_CACHE[projId] = img;""",
"""async function saveDetailImage(projId) {
  const img = PENDING_IMG['detailImg'];
  if (!img) return;
  const th = PENDING_THUMB['detailImg'] || null;
  await sbPatch('graphic_projects', 'id=eq.' + projId, { image_url: img, thumb_url: th, updated_at: new Date().toISOString() });
  IMG_IDS.add(projId); IMG_CACHE[projId] = th || img;""")

sub("saveProject writes a thumb",
"""  const newImg = PENDING_IMG['addProj'] || document.getElementById('projImageUrl').value.trim();""",
"""  const newImg = PENDING_IMG['addProj'] || document.getElementById('projImageUrl').value.trim();
  const newThumb = PENDING_THUMB['addProj'] || null;""")

sub("saveProject edit branch",
"""    if(newImg) data.image_url = newImg;   // omit when empty → preserves existing image
    await sbPatch('graphic_projects','id=eq.'+editingProjectId, data);
    if(newImg){ IMG_IDS.add(editingProjectId); IMG_CACHE[editingProjectId] = newImg; }""",
"""    if(newImg){ data.image_url = newImg; data.thumb_url = newThumb; }   // omit when empty → preserves existing image
    await sbPatch('graphic_projects','id=eq.'+editingProjectId, data);
    if(newImg){ IMG_IDS.add(editingProjectId); IMG_CACHE[editingProjectId] = newThumb || newImg; }""")

sub("saveProject add branch",
"""    data.image_url = newImg || null;
    data.current_stage = 'brief';""",
"""    data.image_url = newImg || null;
    data.thumb_url = newThumb;
    data.current_stage = 'brief';""")

sub("bulk row makes a thumb",
"""    const compressed = await compressImageDataUrl(ev.target.result);
    tr._img = compressed;
    const thumb = tr.querySelector('.bk-img-thumb');""",
"""    const compressed = await compressImageDataUrl(ev.target.result);
    tr._img = compressed;
    tr._thumb = await makeThumbDataUrl(ev.target.result);
    const thumb = tr.querySelector('.bk-img-thumb');""")

open(SRC,'w').write(s)
print("  OK  thumbnail written on every image path")
print(f"  {len(edits)} anchors applied in total")
