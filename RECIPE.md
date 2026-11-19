# RECIPE: BB Graphic System
Kind: system
Live: https://businessboosterlk.github.io/bb-graphic-system/
Live commit: a84f09b
Last verified: 2026-11-18, GRAPHIC PIPELINE 2 (Farhath's three changes) and GRAPHIC COUNTERS 1 (dashboard from today), merged, not yet pushed

Checked by `python3 ~/bb-systems/qa/recipe-check.py <this folder>`. A fresh chat rebuilds from this file
alone. Anything that lives only in a chat is lost: write it here or it did not happen.

## 1. What it is
The graphic team's single-file PWA: PIN login, weekly plan, pipeline, Team Score stars and the head's
morning brief, all reading Supabase project yyviiwnqgphyklcoijyd over REST. On 9 Nov 2026 Thulaib
approved his graphics head's six changes ("Build it now"): every weekly task carries an auto-set
deadline, a non-revision task for n designs creates n empty pipeline slots under the client in the new
Approved Posts view, the tick stamps done_at (sent on the WhatsApp group) and moves those slots to Head
Review, designers upload the approved posts into the slots, Post Revision tasks make no slots, and the
Add Task client select has a New Client option. The data stages stay brief, head_review, approved; only
the screen simplified.

## 2. Where the source lives
- This folder is the true copy and its own git repo: github.com businessboosterlk/bb-graphic-system,
  branch main. index.html is the whole app; sw.js the service worker (network first, CACHE name must be
  bumped on every ship or phones keep the old build).
- Database: Supabase yyviiwnqgphyklcoijyd, tables graphic_projects (slots; plan_task_id ties a slot to
  its weekly task), graphic_weekly_plan (deadline date, done_at timestamptz), graphic_stage_history,
  graphic_project_comments, clients, team_members. Decision 98's approval trigger lives in the database.
- The Command Centre (~/bb-command-centre) READS graphic_weekly_plan for the team week board; it shows a
  raw "revision" label until its TW_TYPES learns the word (cosmetic, another repo).

## 3. Rebuild from nothing
```bash
git clone git@github.com:businessbooster.lk/bb-graphic-system.git 2>/dev/null \
  || git clone git@github.com:businessboosterlk/bb-graphic-system.git
cd bb-graphic-system
python3 -m http.server 8761 &
open "http://localhost:8761/index.html?selftest"
```
Schema, if the database is ever rebuilt: the columns the app touches are listed in index.html's
selftest probes (search "probes = ["); deadline, done_at and plan_task_id were added 9 Nov 2026 with
an index on graphic_projects(plan_task_id).

## 4. Gates
```bash
open "http://localhost:8761/index.html?selftest"
```
Sign in, read the selftest panel: every check PASS (245 of 245 expected on 18 Nov; at a phone width the one toast line fails on old and new code alike, see L-GFX-080; run it ONCE per page load, two overlapping runs fail timing checks), including "Harness: ZERO writes reached the
database". Run it with the browser pane visible: a hidden 0x0 pane skips every width check.

The dashboard cut-off has its own standing check, writes faked, safe to run any time (second url is origin/main, where it must FAIL):
```bash
node dash-count-from.check.mjs http://localhost:8761/index.html <main-url>
```

## 5. Deliver or deploy
```bash
cd ~/bb-graphic-system
git add -A && git commit -m "GRAPHIC <JOB> N: <what changed>" && git push origin main
```
Push to main IS the deploy (GitHub Pages). Bump `const CACHE = 'bb-graphic-vN'` in sw.js first, every
time, or the team's phones keep serving the old build.

## 6. Finishing touches
- Slots are archived, never deleted, and only empty To-do ones move | why: Supabase hygiene, work in flight is never destroyed | held by: index.html#image_url=is.null
- A revision task makes no slots | why: head's spec, a revision reworks a post that already has a slot | held by: index.html#revision
- The tick means sent on the WhatsApp group: done_at stamps it and the badge says On time or Late | why: head's spec point 3 | held by: index.html#done_at
- The duplicate-task question still ASKS, never refuses, with slot writes in the save path | why: L-GFX-074, Farhath's second carousel | held by: index.html#CARRIER
- Bulk-added tasks make slots and get the day's deadline too | why: the head lays whole weeks in bulk, the rule must not silently skip them | held by: index.html#slotsWanted
- Upload all fills only EMPTY slots, in slot number order, files sorted 1, 2, 10; extra files are left out after a confirm; one shared path slotPutFile for single and bulk | why: Farhath 14 Nov, twelve story posts were twelve uploads | held by: index.html#slotUploadAll
- Approved Posts lists clients and tasks NEWEST FIRST (by created_at); slots inside a task stay 1, 2, 3 | why: Farhath 16 Nov, new slots were buried by A to Z; Upload all fills by slot number | held by: index.html#slotStamp
- Grid and Board tabs are hidden, Approved Posts is the only pipeline view; the grid and board code stays so the selftest and a bring-back still work, and a saved grid or board choice is ignored | why: Farhath 16 Nov | held by: index.html#bbgfx_seen_slots
- New Client saves the typed name as-is with client_id null | why: Thulaib 9 Nov, scheduling before the client row exists | held by: index.html#__new__
- A carousel slot takes many pictures (image_urls jsonb, 20 at most, name order, uploads append, one write after every picture stored); image_url and thumb_url mirror slide 1; a post slot stays one picture; until the column exists the carousel slot behaves as one picture | why: Farhath 18 Nov, one carousel is one slot with many images | held by: index.html#GFX_HAS_SLIDES
- Uploading into an EMPTY carousel sheet redraws that sheet through slideAddPick, never slotUploadSlides | why: phone click-path 18 Nov, the sheet kept saying No slides yet after the pictures saved | held by: index.html#slideAddPick
- The Pipeline filters (client, stage, type) survive every change and a reload of the lists; a client that has gone falls back to All Clients | why: Farhath 18 Nov, loadAll reset them | held by: index.html#populateClientDropdowns
- Add Task has a Target Month that follows the Deadline month until touched; slots are made for that month and Edit moves the still-empty ones | why: Farhath 18 Nov | held by: index.html#wpTargetMonth
- Pipeline Quick add selects show their full words on a phone: 42px high, Client on its own line | why: 18 Nov click-path, the Type, Client and Month words were cut | held by: index.html#qaClient
- The dashboard (five stat cards, Pipeline Overview, Recent Activity, Overdue) counts only work created on or after DASH_COUNT_FROM, Colombo midnight, so it starts from 0; the Pipeline, Approved Posts and Team Score still hold older work | why: Thulaib 18 Nov, a clean start without deleting history | held by: index.html#DASH_COUNT_FROM

## 6b. Database change that waits on a yes (18 Nov 2026)
`migrations/2026-11-18-image-urls.sql` adds `graphic_projects.image_urls jsonb` (additive, rollback in the file). Until it is applied the app runs
as before: a carousel slot takes one picture (feature detection in `gfxLoadProjectList`). After it is applied, carousel slots take up to 20 pictures.

## 7. Cast a copy
This is BB's own internal system, never cast for a client. If a client ever needs one, start from
bb-systems/MODULE-REGISTRY.md prior art, new Supabase project, new PINs; never point a copy at
yyviiwnqgphyklcoijyd.

## 8. Not on disk
The Supabase service role key and the team's PINs (server side since 7 Oct 2026). The DB trigger behind
decision 98 lives in Supabase migrations, not this folder. Nothing else: the app is one file.
