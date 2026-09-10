# BB GRAPHIC SYSTEM — LANDMINES

Registered faults for `~/bb-graphic-system/index.html` (live at
businessboosterlk.github.io/bb-graphic-system/).
Prefix `L-GFX-`. Never delete an entry. Mark it FIXED with the commit sha.

Created 2026-07-30 during the first full audit of this system.

---

## L-GFX-001 · base64 images live in a Postgres text column · OPEN
`graphic_projects.image_url` holds a full base64 data URI, not a link.
Measured 2026-07-30: 363 rows, 361 images, **86 MB of image bytes on active
(non-archived) projects**, table total 91 MB. Largest single image 5,345 kB.

Any query that does not name its columns drags every image across the wire.
**Rule: never `select=*` on `graphic_projects` or `graphic_project_comments`.
Name the columns. `PROJ_LIST_COLS` (line 1154) is the canonical list and it
deliberately excludes `image_url`.**

Partly fixed in 1d64713 (board query, lazy thumbs, `return=minimal` on PATCH,
canvas downscale on upload). See L-GFX-002 and L-GFX-003 for what survived.

The permanent fix is moving images to a Supabase Storage bucket. That is an
infra change and is gated on Thulaib.

## L-GFX-002 · the archive page still runs the original unfixed query · OPEN
`loadArchived()` line 2055:
`sbGet('graphic_projects','?is_archived=eq.true&order=updated_at.desc')` —
no column list, so it pulls `image_url` for every archived project. The render
directly below (lines 2067-2076) uses six fields and never touches the image.

This is the exact bug 1d64713 fixed on the board, left live on this page.
Cheap today only because there is **1** archived row (223 kB). It grows by the
full size of every image the team ever archives.

## L-GFX-003 · project comments fetch their images eagerly · OPEN (latent)
`openProjectDetail()` line 1623 fetches `graphic_project_comments` with no
column list. That table has an `image_url` text column (written at line 1769,
rendered inline at line 1645 capped to 200px on screen).

Costs nothing today because the table has **0 rows**. It becomes L-GFX-002
again the first time a designer attaches an image to a comment.

## L-GFX-004 · compression works, but not to the figure in memory · OPEN
`compressImageDataUrl()` (line 1409) downscales to 1400px JPEG q0.82. The
memory note records "9.3 MB → 86 KB verified" — that was **one sample**, not
the typical result.

Measured distribution 2026-07-30 across 361 images:

| band | images | bytes |
|---|---|---|
| over 2 MB | 2 | 10,039 kB |
| 1-2 MB | 6 | 8,747 kB |
| 200-500 KB | 177 | 40 MB |
| under 200 KB | 176 | 29 MB |

The 8 images over 1 MB are the pre-compression ones named in the old note.
The other 353 average roughly 200 KB, not 86 KB. Quote the band table, never
the 86 KB figure.

## L-GFX-005 · thumbnails fetch the full-size original · FIXED + LIVE 2026-08-20 (`941a87a`)
There is no thumbnail column. `observeLazyThumbs()` (lines 1177-1194) fetches
the **whole** base64 image per card to fill an `img.lazy-thumb`, with
`rootMargin:250px`, and caches every one in `IMG_CACHE` for the session.

The board query itself is genuinely fixed (362 rows of list columns measured at
10 kB of text). The remaining slowness the designers feel is here: scrolling a
full board walks up to 86 MB, one request per card. Designers are scoped to
their own work (8aeb61c) so they see a subset; heads see all 362.

Cannot be fixed without either a new thumbnail column or the Storage bucket.
Both need Thulaib's sign-off.

## L-GFX-006 · a shared Supabase Auth password is hardcoded in public source · OPEN
Line 937: `const GAPP = { email:'nirvana@bb-leads.app', password:'pin2222secure' };`
served on a public GitHub Pages URL. The app silently signs in as this one
shared account for every user; the name+PIN screen is local only.

Second-order fault: `gBearer()` (line 948) falls back to the anon key when
`gLogin()` fails. If that account's password ever changes, the app degrades
silently to anon reads and every authenticated-only table starts returning 401.

This is the role-floor (Mold 6) item. **Not to be touched without Thulaib's
per-system go.** Related: L-CC-001 in the Command Centre register.

## L-GFX-012 · the live system FAILS BB's own quality gate · DEFERRED 2026-08-14 (GUARD-ALLOW)
`guard.py` was updated on this machine (mtime 2026-08-12 11:00) and now hard-fails
rule **L-015, a live credential written into a page that ships**:

```
FAIL L-015 a password literal in the source: password:'pin2222secure'
FAIL L-015 a password sign-in from the page in the source: grant_type=password
```

**This fails on the pristine live file too** (sha `d9747f1`), not just on any
change. Verified by running guard against both. It is L-GFX-006 promoted from a
note to a gate failure.

Practical effect: by BB's own rules this system cannot ship until the credential
is removed or an explicit `GUARD-ALLOW L-015` exemption is written in (guard
honours that marker within 2500 characters of the hit — see guard.py line 171).

**🔴 THE GROUNDS OF THAT SIGN-OFF ARE FALSE. MEASURED 2026-09-07.** The
exemption was taken on the stated basis that the published password "grants
exactly what this app's own tables already allow". It does not. Measured
against live policies and row counts:

| table | rows | policy | anon can read | that password can read |
|---|---|---|---|---|
| clients | 27 | `public access` + `authenticated_all` | yes | yes |
| graphic_projects | 63 | `anon_read` + `public_all` | yes | yes |
| **invoices** | **184** | `authenticated_all` ONLY | **no** | **all 184** |
| **costs** | **163** | `authenticated_all` ONLY | **no** | **all 163** |

The finance tables carry an authenticated-only policy. That published password
grants the `authenticated` role. So it grants strictly MORE than anon: every
invoice and every cost in the business, to anyone who opens the page and reads
the source, from anywhere, with no need to touch this app at all. It is also a
named person's account.

The SMM Workspace removed this same session for this same reason and its own
comment says so. **The sign-off predates that discovery, so it needs re-taking
rather than assuming.** Raised with Thulaib 2026-09-07. Found by the
cross-system scan chat, confirmed here independently against the database.

**Thulaib chose the exemption on 2026-08-14 (Option A) so the team was not
blocked.** A `GUARD-ALLOW L-015` block now sits above `GAPP` and guard passes.
It is a DEFERRAL WITH AN OWNER, not a fix. The real fix is the role-floor work. Adding freelancer logins
(Abilashan) raises the stakes, since more people now hold a login that rides on
one shared password published in a public repo.

## L-GFX-008 · one failed query empties EVERY list · FIXED + LIVE 2026-08-14 (`9d7f6c4`) · SECOND OCCURRENCE
Reported from the field 2026-08-10: Suhana cannot pick a client when adding a
Weekly Plan or Pipeline task. Second time this symptom has hit. First time was
2026-06-22 (see "why it came back" below).

**Root cause, reproduced and measured 2026-08-10 against live code (sha d9747f1):**

`loadAll()` line 1160 runs four queries under a single `Promise.all`. That is
all-or-nothing: if ANY ONE of them rejects, the whole thing throws to the catch
on line 1172 and **none** of the four state arrays get assigned. `clients` stays
at whatever it was, which on first load is `[]`.

Measured, by rejecting only the big `graphic_projects` list query (a dropped
connection) and leaving `clients` perfectly reachable:

| measurement | result |
|---|---|
| `loadAll()` normal duration | 591 ms |
| clients loaded normally | 24 |
| **clients after ONE unrelated query failed** | **0** |
| toasts shown to the user | **0** |
| console errors | 1 (invisible to her) |
| Add Task dropdown | **`["Select Client"]`** — matches the screenshot exactly |

The query most likely to fail is the heaviest one: 362 project rows, bloated by
the 346 duplicates in L-GFX-010. **So the performance landmine is what triggers
the dropdown bug.** They are one fault, not two. State stays wrong until a later
180-second refresh happens to succeed.

**DISPROVEN — do not re-chase these.** An earlier version of this entry blamed
silent-auth/JWT failure. That was written from reading the code, not from
measurement, and it is WRONG. Measured:
- Forcing an invalid JWT does NOT break the read. `sbGet` line 975 retries after
  a fresh `gLogin()` and recovers.
- Even with `gLogin()` failing outright, `clients` still returns all 24 rows,
  because `clients` carries a `public access` policy `FOR ALL TO public`
  alongside `authenticated_all`. Anon reads work.
- `wpPopulateClients()` (line 2353) rebuilds the list on EVERY modal open, so it
  does self-heal — as soon as `clients` is non-empty. It is not a one-shot.

Likely already caused bad data: projects 438 and 439, created by DINUKA on
29 July with `client_name` NULL and "Waverley" typed into the title instead.

**Why it came back.** 2026-06-22 commit `06109a9` fixed the same symptom after
the `clients` table was locked to authenticated, by adding silent auth. That fix
addressed the trigger of the day and never touched the failure MODE: a read that
fails still renders as an empty dropdown with nothing shown to the user. The
lesson was never written to `~/bb-web-learnings.md` — grep for "silent auth",
"RLS lockdown" or "clients stays readable" returns **zero** hits, and the whole
Graphic System appears only twice in 1,898 lines. The fix lived in a git commit
message; the learning was never captured. See L-GFX-011.

**Fix applied 2026-08-10 (built and verified, awaiting deploy):**
1. `Promise.allSettled` in `loadAll()`; each array assigned only on its own
   success, last-known-good kept otherwise.
2. A failed read now toasts: "Could not refresh <what>. Showing last known data."
3. Same treatment for the second instance of the pattern in `openProjectDetail()`
   (line ~1622), where a failed comments read stopped the modal opening at all
   with no message.

Regression test, run against the fix, same reproduction as above:

| | before | after |
|---|---|---|
| clients after the projects query is dropped | 0 | **24** |
| Add Task dropdown | `["Select Client"]` | **25 options, WAVERLEY present** |
| told the user | nothing | **"Could not refresh projects. Showing last known data."** |

**Still open, deliberately not changed:** `sbGet` still returns a PostgREST error
object on failure rather than signalling it, so `Array.isArray(x)?x:[]` guards
elsewhere (`loadArchived` 2055, `renderAnalytics` 2093, `loadClients`, the weekly
plan read 2271) can still turn a failed read into a convincing empty state.
Changing `sbGet`'s contract would alter behaviour across every caller at once, so
it needs its own change with its own verification. **This is the same bug class,
still live on those pages.**

## L-GFX-011 · the learning loop had no write step · OPEN
The 2026-06-22 client-dropdown incident was fixed in code and never recorded in
`~/bb-web-learnings.md`. Same for the whole Graphic System: 2 mentions in 1,898
lines, despite this being the system where the base64 landmine was found.

A fix that lives only in a commit message is not a learning. The next session
starts from the learnings file and the memory index, neither of which knew this
had happened before, so the same class of bug was free to return through a
different door.

**Rule going forward: no fix is finished until the lesson is written where the
next session will actually read it** — `~/bb-web-learnings.md` for web/system
work, this file for a system-specific trap, and the memory index if it changes
how BB operates. Verify by grepping for the lesson afterwards, not by intending
to write it.

Related failure of the same kind: an earlier version of L-GFX-008 above stated
fabricated measurements ("captured live", "measured") for tests that were never
run. Corrected 2026-08-10. **A register entry must say what was SEEN. If it was
reasoned from reading code, it must say so.**

## L-GFX-009 · the designer list was hardcoded in EIGHT places · FIXED + LIVE 2026-08-14 (`9d7f6c4`)
Adding or removing a designer meant hand-editing 8 separate spots: three filter
dropdowns (565, 646, 838), the assign dropdown (735, keyed on team_member_id),
`USERS` (955), the private map in `designerScope()` (1140), the Daily Pillars
array (2010), and two bulk-add row templates (2449, 2535).

That is why RUKSHAN survived his own replacement: commit 947d366 swapped him for
Dinuka in the app but left `team_members.active = true` and 27 weekly-plan rows
behind. Ghosts are the signature of this pattern.

Replaced with one `DESIGNERS` array plus `fillDesignerSelects()`, which renders
every `<select data-designers="placeholder">` at boot and after each bulk row.
**Add or remove a designer HERE ONLY.**

Side fix that came free: the edit form set `projDesigner.value` from
`assigned_designer_id`, which is NULL on 346 live rows, so a project with a
designer rendered as "Unassigned". The select is now keyed on the NAME (the
value every filter and scope check already used), with the id in `data-id`.

## L-GFX-010 · 346 duplicate projects from one bulk add · FIXED + LIVE 2026-08-20 (`941a87a`)
`SQUARE 1 AI` holds 346 active projects created on 2026-07-02 by SUHANA from
**17 distinct titles** — roughly 20 copies of each. They are 346 of the 362
projects on the entire board and a large share of the 86 MB in L-GFX-001.

Not touched: live data, Thulaib's call. A bulk-add dedup guard was added for
the weekly plan in a5f0c68 but `graphic_projects` bulk add has no equivalent.

## L-GFX-007 · no self-test harness · FIXED + LIVE 2026-08-21 (`a8f851d`)
This system has no equivalent of Section 12 in
`~/bb-systems/master-skeleton/bb-master-skeleton.html`. Confirmed by grep:
zero hits for `runSelfTest`.

Note the skeleton's harness cannot be copy-pasted. It is welded to the
skeleton's own model (`DB._d`, `CFG`, `signIn`, `invBalance`, `spread`). This
app's state is live Supabase, so a harness here must stub `sbPost`/`sbPatch`/
`sbDel` to record-and-refuse, snapshot the in-memory arrays, and restore —
otherwise the harness writes to live client data.

## L-GFX-013 · THE REAL CAUSE of the empty client dropdown · FIXED + LIVE 2026-08-20 (`a940b20`)
A temporal dead zone error on the session-restore path.

The restore block sat at line ~1247 and called `showApp()` -> `loadAll()`.
`loadAll`'s first statement reads `PROJ_LIST_COLS`, a **`const` declared ~80
lines BELOW it** (line 1329). A `const` is unreachable until its own line
executes, so every session restore threw:

```
ReferenceError: Cannot access 'PROJ_LIST_COLS' before initialization
    at loadAll  <- showApp  <- the boot IIFE
```

`loadAll` never ran at all. `clients` stayed `[]`. Add Task had nothing to pick.

**Why it read as random, and why it survived two investigations:**

| path | what happens | result |
|---|---|---|
| Sign in fresh | `attemptLogin()` calls `showApp()` long after the script finished evaluating | **works** |
| **Reload with a saved session** | boot block runs mid-script, const not initialised yet | **empty board** |

Live since `1d64713` (2 July), when `PROJ_LIST_COLS` was introduced. Captured
from the live browser console on 2026-08-20, not reasoned from source.

**Honest correction to L-GFX-008.** The `Promise.allSettled` work in `9d7f6c4`
fixed a real and separate failure mode, but it was NOT what Suhana hit and it did
not fix this. The throw happened inside the old `try/catch` and became one
`console.error` nobody reads. **Making failures visible is what surfaced this**,
which is the entire argument for not swallowing errors.

**Fix:** the session-restore block moved to the very END of the script, below
every declaration it touches, with a comment telling the next person not to move
it back. It is now wrapped in `try/catch` so a failed restore clears the bad
session and lands the person on the login door instead of a half-opened app.

**Verified on the LIVE site**, real reload with a saved session, nothing stubbed:
restored as Suhana, 24 clients, 362 projects, Add Task 24 clients, Add Post 24
clients, zero console errors.

**THE RULE THIS LEAVES:** in a single-file app, anything that RUNS at parse time
must sit below everything it reads. Function declarations hoist; `const` and
`let` do not. Grep for top-level IIFEs and check what they call.

## L-GFX-014 · walkthrough · LIVE 2026-08-20 (`47a5902`)
Six cards on first sign-in, greeting by name, skippable, and reopenable forever
from the sidebar. Prior art was the gym member app, NOT BSWL, whose student app
has one static "Getting started" row with no state.

Numbers in the copy are READ from the app (`9 pages` off the nav, `8 columns`
off `STAGES`, client count off the loaded list) because the gym build once said
"four screens" of a five screen app.

**Still owed, per the onboarding standard:** a walkthrough TEACHES, a checklist
CHANGES BEHAVIOUR, and they are two different things. The derived first-week
checklist is NOT built here and was deliberately not faked.

## L-GFX-015 · the whole app was 158px wide on a phone · FIXED 2026-08-20
`.main` (line 133) carries BOTH `margin-left:var(--sidebar-w)` and
`max-width:calc(100vw - var(--sidebar-w))`. The 900px breakpoint reset the
margin but **not the max-width**, so on a 390px screen every page was capped at
390-232 = 158px and the active section rendered at **126px**.

The sidebar is `position:fixed` (line 107) and never in flow, so that cap bought
nothing at any width.

Measured on the LIVE build BEFORE this work, so it is pre-existing, not a
regression: `content_width 158, section_width 126, sidebar_x -232`.

Fix: `.main{margin-left:0;max-width:100vw}` inside the 900px breakpoint.
After: every one of the 8 pages measures **358px** at a 390px viewport, page
`scrollWidth` still 390, no sideways scroll.

**This is why the phone experience felt cramped everywhere, not just on one
page.** Any future `max-width` tied to `--sidebar-w` must be reset at the same
breakpoint that hides the sidebar.

## L-GFX-016 · week keys are stored as SUNDAY, not Monday · OPEN · DO NOT "FIX" CASUALLY
`wpWeekStart` is a local Monday, but every read and write uses
`wpWeekStart.toISOString().slice(0,10)`. `toISOString()` converts to UTC, and
Sri Lanka is UTC+5:30, so **Monday 17 Aug local becomes 2026-08-16, a Sunday.**
Verified: `wpWeekStart_local "Mon Aug 17 2026"`, key used `2026-08-16`, and every
existing row in `graphic_weekly_plan` carries the Sunday key.

Nothing is broken today because loading, saving and the new carry-over all use
the same shifted key, so the app is internally consistent. It matters because:
1. Anyone running the app in a different timezone computes a different key.
2. Any agent or SQL that writes a proper Monday key creates rows the app cannot
   see.

**Changing the key format orphans every existing row.** It needs a data
migration, exactly like the Video System did in `1081365` ("migrate week keys to
Monday and remove the compatibility path") after `5da80a6` ("fix 16 UTC date
bugs"). Do it deliberately or not at all.

## L-GFX-017 · two "+ Add Task" buttons on the Weekly Plan · FIXED 2026-09-07
One in the topbar page-action slot (set in `navigateTo`, ~line 1120) and one in
the section header. Confirmed on the live build before this work, so it is
pre-existing. Harmless, both call `wpOpenAdd()`, but it looks unfinished.

**FIXED 2026-09-07.** The section-header copy is gone and the topbar slot keeps
it, which is what every other page does. `.topbar-actions` has no rule hiding it
on a narrow screen, so the phone keeps the button. The check counts the buttons
**on the Weekly Plan itself**: the first version of it ran on the dashboard,
found zero and passed for the wrong reason, which is the "a check that passes
because it could not find its target" trap in this register's own words.

## L-GFX-018 · guard.py does not check CSS · CLOSED 2026-08-21 (check now in the harness)
While building the weekly grid an edit left a CSS comment unterminated
(`/* WELCOME WALKTHROUGH` with no `*/`), which silently swallowed the entire
`.gd-wrap` rule set. **`guard.py` passed**, because it only parses JavaScript.

Caught by counting `/*` against `*/` inside every `<style>` block: 38 vs 37.
That check is now part of the build routine for this system. Same family as
[[checks-must-watch-the-right-surface]]: ask what the checker actually READ.

## BOARD CLEARED 2026-08-20 for the September restart

Thulaib's call. `graphic_projects` 363 -> 0, `graphic_stage_history` 439 -> 0,
`graphic_project_comments` 0 -> 0. **`graphic_weekly_plan` (137 rows) was NOT
touched** and still holds the live week.

Backed up first and verified against the live tables, not assumed:
`~/Downloads/bb-graphic-backup-20260820-2231/` — 363 rows, 361 images, 86.7 MB,
plus a RESTORE-README.md with the exact restore command.

**A caught failure worth keeping.** The first backup of `graphic_projects`
returned a 100-byte file that `json.load` happily parsed. It was
`{"code":"57014","message":"canceling statement due to statement timeout"}` —
a 4-key error object, so a naive `len()` reported "4 rows". A single request for
87 MB exceeds the statement timeout. Fixed by paginating in batches of 10.
**Counting the rows caught it. An exit code would not have.**

### What this RESOLVES

- **L-GFX-001** (86 MB of base64 in a text column) — the data is gone.
  `graphic_projects` is **1512 kB**, down from 91 MB. Autovacuum reclaimed it on
  its own at 05:01 UTC, so no VACUUM FULL was needed.
- **L-GFX-004** (the 86 KB compression claim) — moot, no images left. The band
  table stands as the record of what compression really produced.
- **L-GFX-005** (thumbnails fetch full-size originals) — no thumbnails to fetch.
  **The underlying fault is NOT fixed.** There is still no thumbnail column, so
  this returns as soon as the team uploads designs again. Keep it OPEN.
- **L-GFX-010** (346 duplicate SQUARE 1 AI rows) — gone. **The bulk-add path
  still has no dedup guard**, so it can happen again. Keep it OPEN.

### Measured after

| | before | after |
|---|---|---|
| `loadAll()` median | 591 ms (362 projects) | **285 ms** |
| `graphic_projects` on disk | 91 MB | **1512 kB** |
| board | 362 cards | 0, empty states on every page |
| clients | 24 | **24, untouched** |
| console errors | 0 | 0 |

**Still true and still owed:** L-GFX-005 and L-GFX-010 are dormant, not fixed.
The first bulk add of September can recreate both. A thumbnail column or the
Storage bucket, and a dedup guard on `graphic_projects` bulk add, are the real
fixes.

---

## ROSTER as deployed 2026-08-14 (`9d7f6c4`)
Graphic designers in the system are **Suhana** (staff, `team_member_id` 3) and
**Abilashan** (freelancer, PIN 5555, `team_member_id` null).

**Open discrepancy, raised with Thulaib and not resolved:** the Client Allocation
Master PDF he supplied the same day lists **Farhath** with 10 clients / 112 posts
as one of two staff designers, and does not mention Abilashan. Thulaib then said
twice that the two designers are Suhana and Abilashan. The app follows his spoken
instruction; the PDF has not been reissued. If Farhath is real, he is one line in
`DESIGNERS` plus a `USERS` entry.

**PINs 5555 (Abilashan) was chosen by me as a placeholder and never confirmed.**

## PENDING DB WRITES — approved by nobody yet, deliberately NOT run
None of these were executed. The app change went live without them, which is safe
because scoping runs on the NAME, not `team_member_id`.
- `team_members`: no row for ABILASHAN. Add one (role 'Graphic Designer').
- `team_members` id 16 DINUKA still `active = true`.
- `team_members` id 4 RUKSHAN still `active = true`, replaced 28 July, and still
  holds 27 `graphic_weekly_plan` rows.
- `graphic_projects` 438 and 439 still `assigned_designer = 'Dinuka'` with
  `client_name` NULL. Both are Waverley by title.

---

## 2026-08-20 · both regrowth traps disarmed (`941a87a`)

**L-GFX-010, dedup on projects bulk add.** Key is title + client + target month
+ year, lowercased and trimmed. It deliberately excludes designer and priority:
the same post for the same client in the same month is the same post, whoever it
was handed to. It checks BOTH what is already on the board AND what has already
been added inside the same batch. The in-batch half is the one that mattered:
346 rows from 17 titles is a Save pressed repeatedly, not 346 typos, and the
weekly plan guard in `a5f0c68` does NOT have that half.

Measured live: 3 rows submitted with one repeated -> 2 inserted, toast read
"2 posts added, 1 duplicate skipped". Locally with a richer batch: 6 submitted
(1 already on the board, 2 in-batch pairs) -> 3 inserted, 3 skipped.

**L-GFX-005, real thumbnails.** New nullable column `graphic_projects.thumb_url`
(rollback: `alter table graphic_projects drop column thumb_url`). A 360px q0.62
copy is written at the same moment as the 1400px image, on every path that
stores one: single add, edit, detail upload, bulk add. The lazy loader requests
`thumb_url,image_url` and prefers the thumb, so any row predating the column
still renders.

Measured on a deliberately incompressible 2000x2000 image: 1124 KB -> 49 KB,
23x smaller. On a flat-colour 1200x1200: 12 KB -> 2 KB.

### STILL NOT FIXED, and it is the real cure
Images are **still base64 in Postgres**. The Storage bucket needs dashboard or
service_role access, which is not reachable from this session, so it remains
Thulaib's to do. Until then the table still grows with every upload, roughly 20x
slower than before but in the same direction. L-GFX-001 stays OPEN.

---

## 2026-08-21 · the harness exists, and it was proven (`a8f851d`)

37 checks. `?selftest` in the URL, or `runSelfTest()` in the console. 37/37 green
on live.

**Safety, because this app's state is a LIVE shared database** and not the local
object the master-skeleton harness owns: every write function is swapped for a
recorder and restored in a `finally`; the arrays, the signed-in user and the
current page are snapshotted and put back. Verified state identical before and
after, zero writes leaving the browser.

**Ten of the checks are REGRESSION checks** for bugs that reached the team:
L-GFX-002, L-GFX-005, L-GFX-008 (x2), L-GFX-010 (x4 incl. behaviour),
L-GFX-013 (x2), plus L-GFX-015 on layout. Each cost a field report. **Do not
delete one for looking redundant.**

### It was PROVEN, not assumed
Three regressions were reintroduced into a scratch copy: `Promise.all` back in
`loadAll`, the dedup guard deleted, and the archive `select` stripped.
**`guard.py` passed that broken file** — which is the whole argument for having a
harness at all. The harness caught all three, and only those three.

### THREE FLAWS IN THE HARNESS ITSELF, all found by breaking the app on purpose
1. **One throwing check aborted the run.** 15 of 35 checks never executed, and
   the report said only "Harness completed without throwing: false". Same
   all-or-nothing shape as L-GFX-008. Sections now isolate failures.
2. **The L-GFX-008 check passed for the wrong reason.** It seeded `clients` with
   a row before the test, so "clients is not empty" stayed true even when
   `loadAll` threw and assigned nothing. It now starts from empty, the way a
   real first load does, and asserts the healthy query was APPLIED.
3. **The source-grep checks matched the harness's own text.** The harness sits in
   the page it greps, so `src.indexOf('...select=...')` found the check itself.
   L-GFX-002 went green on a build where it was genuinely broken. Fixed with
   explicit sentinels, and function-level checks now read
   `Function.prototype.toString()`, which cannot collide.

**All three would have shipped a harness reporting ALL GREEN on a broken app.**
A checker nobody has tried to break is not evidence. Break it, watch it fail,
then trust the green.

### How to keep it useful
Every future bug in this system should arrive with a regression check in Section
12 before the fix is called done. That is the difference between a register that
records history and one that prevents it.

---

## 2026-08-21 · the app shell and the phone foundations

Shell 0 of 7 to **7 of 7**. Phone knobs 0 of 9 to **9 of 9**. Harness 40 to
**58**, green at 1280 AND at 390px with `pointer:coarse` true.

## L-GFX-019 · the brief named the wrong build to copy the module from · FIXED
The prior-art gate answered "the best build is bb-video-system", and for FIT
that is right: same posture, same tables, same single-file shape.

**But video's BBF predates the 11 August freeze fix**, the one
`bb-app-foundations` calls "the worst bug this skill has produced": observers
calling `sync()` on every mutation batch while `sync()` reads layout for every
overlay. Measured 2026-08-21:

```
scheduleSync present:  bb-video-system 0 | bb-master-skeleton 0 | restaurant 0
                       gym-skeleton 3 | gym-member-skeleton 3 | bb-smm-workspace 3
```

Porting video verbatim would have shipped a known browser freeze onto the phones
of the people who use this daily. Resolution: the SHAPE, safe-area targets and
app wiring from video; the MODULE INTERNALS from `bb-smm-workspace`, the most
recent port and one of only three files carrying the fix.

**THE RULE: "which build is best" is not one answer. It is best-for-fit and
best-for-correctness, and they can be different files.** Check the specific
defect history of the specific block you are copying, not the reputation of the
file it lives in.

## L-GFX-020 · the sticky topbar scrolled away on a phone · FIXED
`.main` carried `overflow:hidden`, which makes it a **scroll container**, so the
sticky topbar bound to a box that never scrolls while the window did. Measured
at 390px: topbar top went **0 to -284.5** on a 700px scroll. It scrolled clean
off the screen.

This is the exact fault `bb-app-shell` says "shipped broken twice" elsewhere, and
the documented fix applies unchanged: `overflow-x:clip` clips without creating a
scroll container. Now `.main{overflow:visible;overflow-x:clip}`, measured 0 to 0
at both widths.

**The harness could not see this.** It is now check "Layout: the topbar survives
a scroll".

## L-GFX-021 · apply_app_shell.py ships three faults while reporting all green · FIXED
All seven checks flipped to yes while the app was still wrong in three ways a
person would see on their home screen. `bb-app-shell` documents all three; they
were all present here.

1. **The manifest was Total Uplift's, verbatim.** `name: "Total Uplift"`,
   `short_name: "Uplift"`, the gym's description and `#0B1117` colours. The icon
   on a designer's phone would have been labelled **Uplift**. It also declared
   **13 icons while 4 existed**, so nine were dead references including an
   `icon.svg` that exists nowhere.
2. **The icons were the neutral defaults.** Regenerated from `bb-logo.png` with
   `sips` (no Pillow on this Mac), padded on Graphic's own `#0c0d10`, 11 sizes
   plus two maskable.
3. **sw.js was the gym's** (`tu-member-v1`) **and was never registered**, so the
   app installed and the worker never ran. Rewritten as `bb-graphic-v1` and
   registered. It keeps the SMM rule: **never cache the database.** A stale board
   is worse than no board, because somebody ticks a post that already moved on.

Also: the page's `theme-color` meta was the gym's `#0E141B` against Graphic's
`#0c0d10`.

**Two new checks now catch all of it**: "Shell: the manifest names THIS app" and
"Shell: every icon the manifest declares actually exists". Neither existed in any
BB harness before today.

## L-GFX-022 · the two overlay traps, both live in this file · HANDLED
1. **`.sidebar` is permanently `display:flex`** and hidden by
   `translateX(-100%)`, so it has a non-zero rect at all times and a visibility
   test calls it **open forever**. It is deliberately excluded from `OVS`.
2. **`#sidebarOverlay` is a SIBLING of `#sidebar`**, so a generic shield inerts
   the drawer its own backdrop belongs to and the drawer goes dead under the
   thumb. That is what `KEEP='#sidebar'` prevents, and there is now a check
   named "App: the drawer stays usable while its own backdrop is up".

## A check of mine that was wrong at desktop · FIXED
`REGRESSION L-GFX-015` compared the active section against the whole viewport.
Above 900px the sidebar legitimately takes 232px, so it failed on every desktop
run reporting "1000px of 1280px" as though it were the 126-of-390 bug. It now
measures against the space actually available. **A regression check that cries
wolf gets deleted by the next person, which is how the real bug comes back.**

## bb-elevate · what the brief did not ask for and should have

**1. NOBODY IS TOLD HOW TO INSTALL IT, and that is the whole point of the pass.**
The brief's own "what done looks like" opens with "a designer adds the Graphic
System to their home screen". Nothing in the app tells them how. `bb-app-shell`
rule 7 is explicit: tell the person at the TOP of the first screen, with the
share glyph DRAWN, because "tap the share button" means nothing until they can
see which button. Dismissible, and absent once installed.

The shell is now correct and unusable-as-intended: it installs beautifully for
anybody who already knows the gesture. **This is the highest-value thing left and
it is one dismissible banner on the login screen.** Held because the brief scoped
this pass to the foundation layer, and an install prompt is user-facing copy.

**2. No landscape breakpoint.** `bb-video-system` carries
`@media(orientation:landscape) and (max-height:500px)` to shrink the topbar,
because a phone on its side gives up most of its height to chrome. Graphic has
none. A designer checking the board on a rotated phone loses a 60px topbar plus
the inset out of 390px of height.

**3. The service worker caches nothing useful yet.** It is registered and it
correctly refuses to cache the database, but `SHELL` lists four files. The app is
ONE 3,900-line HTML file, which is already in the list as `./`. So offline works,
but the icons and manifest are the only extras. That is correct and worth saying
out loud rather than implying an offline mode nobody tested. **Offline was not
tested in this pass.**

**4. `env()` is still unproven on glass.** The harness asserts the VARIABLE is
wired by pushing `--sat:59px` and watching the chrome move. That proves the
plumbing. It does not prove a real notch, because `env()` cannot be read or faked
from JavaScript. **Only a real handset proves that, and nobody has held one.**

**5. The `?selftest` URL is a foot-gun on a live system.** It runs 59 checks
against whatever is loaded. Every write is stubbed and state is restored, so it
is safe, but it also navigates pages and toggles overlays under the user. It is
fine for Thulaib and wrong for a designer who pastes a link. Not changed, but
worth knowing before that URL is shared.

## L-GFX-023 · six faults in the bulk add paths, found on a deep trace · FIXED 2026-08-31
Asked "is bulk add working perfectly", so the whole path was read line by line
rather than trusting the last green test. Six faults, two of them introduced by
the duplicate fix itself.

1. **`_bulkInserted` never forgot anything.** A post deleted by mistake and
   re-added correctly in the same session was silently skipped as a duplicate.
   Introduced by the 456-duplicate fix. Now `forgetBulkKeyFor(id)` runs on every
   delete and archive, single or bulk.
2. **The key was remembered AFTER the second write.** If the stage-history post
   failed, the project existed but was forgotten, and the next press duplicated
   it. Also introduced by the fix. The key is now remembered the moment the
   project insert returns an id.
3. **A network throw mid-batch was silent.** `sbPost` does not catch; the
   rejection escaped both `finally` blocks. Rows already saved, no toast, modal
   left open, board never refreshed. Per-row try/catch now counts `failed`, the
   toast says "2 posts added, 1 FAILED to save", the modal stays open so the
   failed rows can be retried, and the board still refreshes.
4. **A non-array response was silently uncounted.** RLS or constraint errors
   come back as an object; the row vanished from the count with no mention.
   Now counted as failed and said.
5. **Two em dashes in user-facing toasts**, one on each bulk path. House rule.
6. **`wpBulkSaveAll` had none of the three blocks.** Identical shape to the one
   that produced 456 duplicates: dedup against stale `wpTasks`, live button,
   silence. Now has the re-entrancy flag, the disabled counting button and a
   surviving inserted set. Proven by firing it twice.

Also: `bulkDeleteSelected` did not delete `graphic_project_comments`, so every
bulk delete left orphaned comment rows. The single delete did. Now consistent.

## Archive versus delete · the permission split · LIVE 2026-08-31
Thulaib: a designer should archive, not delete; only SMM and heads delete for
good. `canDeleteForever()` = role in `head`, `graphic_head`, `smm`.

Enforced IN the functions (`deleteProject`, `bulkDeleteSelected`), not only by
hiding buttons, so a stale tab cannot get round it. Archive stays open to
everyone and is reversible from the Archived page via `restoreProject`.
New `bulkArchiveSelected()` is the safe bulk clear for designers.

Verified all four roles side by side with writes stubbed: designer blocked with
a clear message and zero writes, head/graphic_head/smm delete with three writes
each (history, comments, project).

## L-GFX-024 · a runtime clone carried a duplicate id · FIXED 2026-08-31
A Settings sheet module (`BBPUSH`, not written in this stream of work, absent
from the 20-Aug baseline, present in HEAD) injects a "Settings" nav item by
deep-cloning the LAST nav item. That item is Agents, which carries
`<span id="agentBadge">`. The clone kept the id, so the page had two, the
Settings item showed the agent count, and the harness's duplicate-id check went
red.

It was invisible to earlier green runs because the injection fires late and the
harness usually ran first. **A check that depends on timing is a check that
sometimes lies.** The clone now sheds every descendant id.

**Rule: anything that clones DOM must strip descendant ids, not just its own.**

## L-GFX-025 · another session shares this working tree and reverted a fix · OPEN (process)
While verifying 5102ab1 on live, HEAD had moved to e8dc067, a commit from a
different Claude session ("fix: alerts...") working in the SAME directory. Its
rewrite of the BBPUSH inject() block deleted the L-GFX-024 clone-id fix, and the
duplicate agentBadge came straight back on live. It did not touch any other
function of mine (checked: 0 hits on the bulk or permission code).

This is also why bb-web-learnings.md, guard.py and build scripts kept changing
mid-session. Two sessions, one tree, no coordination.

**Rules:** (1) before claiming a deploy is live, compare the live markers to
LOCAL, not to memory of what was pushed: HEAD may not be yours. (2) any fix that
lives inside a block another module owns needs a comment naming the fix, so a
rewrite of that block does not silently drop it. (3) grep the live file for the
CODE, not for a comment phrase: my first check searched the wrong tense and
reported 0 for a fix that was present at the time.
Re-applied with the comment in the commit after e8dc067.

## L-GFX-026 · Daily Pillars never saved, for eleven weeks · FIXED 2026-09-04
Farhath: "the tick gets ticked and then it disappears." Every designer had the
same fault since the 14 June rebuild and nobody reported it.

Root cause: the app wrote `{who, date, item, done}` to `pillars`. That table is
the Command Centre's, shape `id, who, done_ids, top3, updated_at`, UNIQUE(who).
It has no `item` and no `date`. PostgREST rejected every write. The code ignored
the write's result, so the rejection was silent, and the 400ms re-render read
back nothing, so the tick vanished.

Fix: pillars now live in `daily_pillar_state` (`user_name, pillar_date, state
jsonb`, UNIQUE on the pair), the table the Video and SMM systems already use,
via a PostgREST upsert on the pair. The done list is mirrored into the CC
`pillars` table exactly as Video does, so the CC Team page shows the right
count. A failed write now toasts instead of vanishing.

Proven with a REAL round trip, not a stub: tick written, read back true, unticked,
read back false, probe rows deleted. And the exact reported symptom driven
through the real checkbox: still ticked after the 400ms re-render, counter
"1 of 7 done".

**Why it was not caught, honestly.** Every test stubbed writes, by design, so
the harness never once asked the database whether the columns it would write to
exist. It proved the panel rendered seven boxes and that a click called the
right function. It never proved a tick came back. **Schema drift between the
app and a table is invisible to a harness that stubs writes.** New section in
the harness: a read-only probe (`?select=<cols>&limit=0`) for every column the
app writes, in seven tables. Proven to bite: asking for the old shape returns
"column pillars.date does not exist".

## L-GFX-024, second clobber · the fix now lives in owned code · FIXED 2026-09-04
The clone-id fix was removed AGAIN by 4a958a4 (09:43, another session rewriting
the BBPUSH inject() block from its own copy), sixteen minutes after c8e1f87
re-applied it. Re-applying inside their block is futile. The fix now lives in a
standalone MutationObserver in this system's own region, repairs the clone the
moment it appears, and a harness check WAITS for the injection instead of racing
it, so a future drop turns the gate red. 67/67 twice with the injection landed.

---

## L-GFX-028 · undo, and the four copies of one rule

**Added** 2026-09-04 with the undo feature, cast from the Video System mold
(L-VID-025). Same rules: reversal goes through the normal writer, in memory for
this session only, a bulk move is one undo, each post returns to its own
previous stage, reached from a bar, a Pipeline button and Ctrl+Z.

**What this system had that the Video System did not: FOUR writers.** A stage
change was written in four places, each with its own copy of the completed_at
rule, and two of them carried the same comment about the five rows that kept a
false finish time on 2 July:

| Where | |
|---|---|
| `onDrop` | drag and drop |
| `moveStage` | the Previous and Next buttons |
| `quickMove` | the card menu |
| `bulkMoveSelected` | bulk move |

Undo would have been a fifth. All four now call **`gfxSetStage`**, the one
writer, which also records the undo. Four copies of a rule is four chances for
it to drift, and the drift is silent: a job reopened from Approved through the
one path nobody fixed keeps a false finish time.

**I only found the fourth because a check failed.** The patch was written for
three, `quickMove` was invisible until an anchor matched twice. **When a
replacement anchor matches more times than you expect, that is the finding, not
the obstacle.**

**And then my check itself was wrong.** The first version counted
`sbPatch('graphic_projects' ... current_stage` and matched across newlines, so
it counted `gfxSetStage`'s OWN write and failed on correct code. It now counts
the thing that was actually duplicated, the completed_at stamp, and asserts
exactly one copy exists inside the one writer. **A check that cannot tell the
fix from the fault is worse than no check: it trains you to ignore it.**

**Six checks**, 73 passing. Proven live: post 1038 "Puwakaramba" moved
in_progress to first_draft and back, and the history reads
`first_draft (Moved from In Progress) -> in_progress (Undo, back from First Draft)`.

## L-GFX-027 · designer visibility has changed three times, so it lives in ONE function · 2026-09-05
8aeb61c (Aug) scoped each designer to their own work by label. 43d100a
(20 Aug, Thulaib) opened every designer to everything. 5 Sep (Thulaib):
"Farhath sees all work and the other members see only work assigned to them,
like the Video System." Each flip was one body: `scopedProjects(list)`.

**The rule now:** a plain designer sees only rows whose `assigned_designer_id`
is their `team_member_id` (the Video System's id match), falling back to the
label only for rows written before the id was stored. Unassigned work is not
theirs yet, exactly as in Video. `graphic_head`, `smm`, `head` and `brief` see
everything. Designers can still ADD work for any client; the rule governs what
they SEE. Ten call sites: dashboard counts, board, clients page, archive,
recap (which reads the table directly, so it scopes its own result), and the
harness.

**Why one function matters:** the recap was added after 43d100a and fetched
its own rows, so under the old scoping it would have leaked everyone's month
to a designer. Any NEW surface that reads `graphic_projects` must pass its
list through `scopedProjects`. The harness proves the rule in both directions
with four fixtures (theirs by id, theirs by label, someone else's, unassigned)
for a designer, the graphic head and an SMM.

## L-GFX-029 · the Graphic alert ladder, and the stage that alerts nobody · 2026-09-07
Eight stages now carry alert rules, set by Thulaib. Recipients are computed by
MEANING: the doer from `assigned_designer_id`, the head from `is_head` plus a
graphic role, the client's OWN SMM from `clients.assigned_smm` (never both
SMMs), the CEO by role. No rule names a person. The SQL, the matrix and the
proof live at `~/bb-systems/push/rules/graphic-2026-09-07.sql`.

**`in_progress` alerts nobody, on purpose.** Its only recipient is the doer,
and the doer is the only person who moves a card there, so it would ring the
phone of whoever just tapped it. Stored inactive with the reason, not deleted.
See L-PUSH-009 for the one column that makes it safe.

**Two things changed for Thulaib personally:** he no longer gets `head_review`
(his own matrix puts the head alone on that stage) and he now gets
`sent_to_client`, which nothing alerted on before.

**Never add a stage to `STAGES` without deciding its alert row.** A new stage
with no rule is silent, and silence looks identical to working.

## L-GFX-030 · the alert ladder was half silent because an id column was empty · FIXED 2026-09-07
Measured the morning after the ladder shipped: `assigned_designer_id` was NULL
on **60 of 63 active graphics**, while `assigned_designer` (the name, as text)
was set on every single one.

Visibility survived that, because `scopedProjects` falls back to the name. The
ALERTS did not: `bb_notify_on_stage` finds the doer through the id alone, so
the doer half of revisions, client changes and approved would have reached the
designer on 3 cards out of 63. The head, the SMM and the CEO were unaffected,
which is exactly why it would have looked like it was working.

Backfilled from the name, only ever filling a NULL, every row matching an
active member (59 Farhath, 1 Zulfa, 0 unmatched). The app already wrote both on
new work, so this was a one-off.

**The lesson: two columns for one fact will drift, and the surface that reads
the less-used one fails quietly.** When a feature depends on a column, count
how many rows actually carry it BEFORE calling the feature done. `select
count(*) ... where <that column> is null` is one line and it was the difference
between shipped and working.

## L-GFX-031 · the page that would not scroll, and why guessing stopped · FIXED 2026-09-07
Farhath reported that the app would not scroll up or down. Six surfaces at
phone width were driven on 5 September (dashboard, pipeline, weekly plan, the
Settings sheet, the walkthrough, a detail modal) and every one scrolled, with
the body never left pinned. No reproduction, so no root cause.

The symptom has exactly ONE shape, whatever causes it: `body` is left with
`position:fixed` (the `sheet-open` pin) while no overlay is open. So rather
than keep hunting the trigger, BBF now carries a **watchdog** that checks every
two seconds and on every `pageshow` and tab return. If the page is pinned and
nothing is open, it frees it and counts it.

**It judges the PAGE, not our own bookkeeping.** The first version tested only
BBF's internal `locked` flag, so it could not heal a pin left behind by
anything else, which is the most likely shape of a fault nobody can reproduce.
The check caught that: it faked the DOM state, the watchdog ignored it, and the
check went red. It now asks both questions.

It frees an orphan pin **without scrolling**, because the original position is
unknown and guessing would throw the person somewhere they never were.

Proven by reproducing the symptom: with the body pinned a scroll to 400px
stayed at 0, and after the watchdog the page was static and scrolled to 400
again. `BBF.healed()` counts every heal, so if this keeps happening the number
grows and we finally get evidence instead of a description.

## L-GFX-032 · the Settings sheet was invisible to the freeze layer · FIXED 2026-09-07
Farhath reported twice that the app would not scroll. The first hunt found
nothing because it drove the surfaces the app has always had. The Settings
sheet is a LATER module, injected at runtime by its own block, and nothing ever
registered it with `BBF`.

**Measured on the live build with Settings open:** `BBF.anyOpen()` returned
null, the body was never pinned, and the page behind scrolled underneath the
sheet. Android Back did not close it, because BBF pushes the history entry and
BBF did not know the sheet existed. The backdrop is `position:fixed; inset:0;
z-index:100000` with `pointer-events:auto`, so while it is up it takes every
touch on the screen, and if it is ever left showing **nothing heals it**: the
body is not pinned, so even the new watchdog sees nothing wrong. A full-screen
element that takes every touch and that no layer owns is precisely what "the
app will not scroll" feels like.

**Fix:** `#bbset-back` joins `OVS` and `#bbset-sheet` joins `KEEP`. The keep
matters: the backdrop is a SIBLING of the panel, so recognising the backdrop
without keeping the panel would inert the panel its own backdrop belongs to,
which is the trap already recorded for `#sidebar` and `#sidebarOverlay`.
`closeTop` clicks the backdrop, because its close handler lives on the `onclick`
PROPERTY where the two existing lookups cannot find it.

**The general fix, which is the point.** `BBF.unowned()` returns every
full-screen fixed element that takes pointer events and is matched by neither
`OVS` nor `KEEP`, and a check fails on it **with the Settings sheet open**,
because every fault it caused was invisible while it was shut. The next module
injected this way is found by a check instead of by somebody's thumb.

**Estate-wide, and NOT fixed here.** Measured the same day: the SMM Workspace
(`OVS='.modal-bg, #smm-checkin-overlay, #agent-drawer-overlay, #bb-detail-overlay, .sidebar-backdrop'`)
and the Video System (`OVS='.modal-backdrop, .m-sheet'`) both carry the
Settings sheet and neither knows about it, so both have this fault today. The
Command Centre and the Dev System carry the sheet and have no overlay selector
at all. Those are other chats' systems and the fix is theirs to apply; it is
written out in `~/bb-systems/push/SHARED-CHANGES.md`.

## L-GFX-033 · the self-test could not finish, so nothing was being verified · FIXED 2026-09-07
Reported by the cross-system scan chat: `runSelfTest()` was still running after
45 seconds and never resolved. Reproduced here, capped at 25 seconds and still
going, while a single database read from the same page took 378ms, so the
network was fine and the harness itself was the problem.

**Two causes, both mine, both from the same afternoon.** `navigateTo` blocks
for about a second per page, and the unowned-overlay check added that day
walked six pages, two of which fetch. And the schema probe makes seven REAL
reads with no time limit, so one stalled request would hang the entire run with
no way to tell a hang from slow work.

**Fixed three ways.** The run carries a 20 second budget; a section reached
after the budget is recorded as a FAILURE naming the overrun, never silently
dropped, because a short run must never read as a green run. Every read the
harness makes has a 4 second limit. The page walk is three pages by default and
`runSelfTest({deep:true})` walks all six. Measured after: 9 to 11 seconds,
84 of 84, and the run now reports its own elapsed time as a check.

**The lesson worth keeping: a harness that cannot finish is a harness nobody
runs, which means the system was shipping unverified while showing every sign
of being tested.** Any check suite that touches the network or re-renders pages
needs a deadline the day it is written, not the day someone notices.

## L-GFX-034 · three stages were unreachable by drag on a laptop · FIXED 2026-09-07
Reported as "moving left and right on the pipeline, it gets stuck".

**Measured at 1440x900:** the board is 2084px wide inside a 1160px window, so
924px sits off the right edge and THREE stages are not on screen at all: Sent
to Client, Client Changes and Approved. HTML5 drag does not auto-scroll a
container, and nothing in this file did it either. So you pick a card up, push
it against the right edge, and nothing moves. The three stages it made
unreachable are the ones where work LEAVES the team.

**Why every sweep missed it.** Below 900px `.kanban` becomes
`flex-direction:column`, the columns stack and there is nothing to scroll
sideways. Every phone test therefore passed, correctly, on a layout where the
fault cannot exist. **A fault that only exists at one width is invisible to a
suite that only runs at another.** The phone-first habit that caught the
16px-field and safe-area faults is the same habit that hid this one.

**Fix:** a dragover listener on the document scrolls the board when the pointer
is within 90px of either edge. It nudges on the EVENT as well as on a timer,
because a hidden or background tab throttles `setInterval` to about once a
second, which moved 24px in 700ms and made a correct implementation look
broken while it was being tested. It stops on dragend and drop, never on
dragleave, which fires constantly as the pointer crosses cards.

**Proven:** 40 dragover events at the right edge scrolled the full 924px and
brought Sent to Client, Client Changes and Approved into view; the left edge
returned it to 0; it stopped on dragend. The check asserts ARMING plus movement
rather than a distance in a fixed time, so timer throttling cannot make it
flaky, and it says so out loud when the board fits the window and there is
nothing to prove.

**Login sweep the same day, all eight PINs at 1440x900:** every one renders the
board with zero console errors and the full navigation. Cards visible follow
the visibility rule (heads and SMMs 62, Suhana 1, Zulfa 1, Amjath 0, because
nothing is assigned to him).

## L-GFX-035 · the Weekly Plan showed only Suhana, and it was not a permission fault · FIXED 2026-09-07
Reported: everyone opening the Weekly Plan saw only Suhana's work.

**Measured in `graphic_weekly_plan` before changing anything.** Of the 143 rows
ever written, Suhana holds 131 across 15 weeks, Farhath 6 in a single week, 6
are unassigned, and **Amjath and Zulfa have never had a single row.** This week
holds 12 rows, all Suhana's. Nobody was being filtered out. Suhana's work was
the only work in the table.

**What turned that into a fault.** The grid built its rows from the people who
had work: `withWork.length ? withWork : rows`, with the comment "so an empty
roster never renders a wall of dashes". So the three people a head most needs
to hand work to were the three who did not appear on the page. **A planning
surface that hides the people with nothing on cannot be used to hand work out,
which is the only thing it is for.** The empty row IS the invitation.

**Fixed to Thulaib's rule, 2026-09-07.** Thulaib, Shiara, Farhath, Nirvana and
Tiana see every designer, with or without work. A plain designer sees their own
row, matching the pipeline rule of 5 September. Proven for all eight logins:
the five planners each render Suhana, Farhath, Amjath and Zulfa; Suhana, Amjath
and Zulfa each render only themselves.

**Two faults in the CHECKS found while proving this, both worth more than the
fix.** The new check counted the day-totals row as a designer row, so it failed
on a correct app and sent me looking for a bug in code that was right. And at a
0x0 viewport, which a pane reports before it lays out, `BBF.unowned()` treated
every fixed element as covering 80 percent of the screen and named the whole
page as unowned, while the overlay checks failed because nothing has a rectangle
at 0x0. Five red checks, none of them real. The register already carries this
lesson from 2026-08-10 (`if a whole suite reds together, read the viewport
before the code`) and it still cost twenty minutes. **Every rect-based check now
sits behind one explicit viewport test that FAILS OUT LOUD and skips, rather
than inventing failures.**

## L-GFX-036 · a hung self-test left the app unable to save anything · FIXED 2026-09-09
While `runSelfTest()` runs it replaces `sbPost`, `sbPatch`, `sbDel` and
`loadAll` with stubs that discard everything. That is correct and it is the
whole reason the harness is safe to run against live data. It restored them in
a `finally`, which covers a throw.

**It did not cover a run that never ends.** If one await never settles,
`finally` never runs, and the app is left with every save silently doing
nothing while the screen looks completely normal. Nobody could report that as
anything more useful than "there is a bug".

**Observed, not theorised, 2026-09-09.** An interrupted run left `loadAll`
stubbed: it returned in 0ms and the board showed 0 projects against a database
holding 63, with no error anywhere. `?selftest` in the URL starts a run
automatically, so this is reachable by anyone holding that link.

**Fix:** the restore is idempotent and armed on a TIMER before the first check
runs, as well as in the `finally` which cancels it. `window.__bbHarnessStubbed`
marks the window while a run is in flight, so the state is visible instead of
invisible. A check asserts both.

**A second fault while fixing it, worth more than the fix.** The failsafe read
`HARNESS_BUDGET_MS` above the line that declares it: `Cannot access
'HARNESS_BUDGET_MS' before initialization`. That is the temporal dead zone this
register already carries as L-GFX-013, and **guard.py cannot see it, because
the file parses perfectly.** A `const` is hoisted as a name, never as a value.
Declare anything the stubs or the failsafe read at the very top of the function.

## L-GFX-037 · navigateTo blanked the app on a name that does not exist · FIXED 2026-09-09
`document.getElementById('section-'+page).classList.add('active')` ran AFTER
every section had been deactivated, so an unknown page threw and left the app
with no active section: a blank screen and no error a person could see. Found
when a check of mine called `navigateTo('archive')` and the page is `archived`.

Nothing routes off the URL today, so no user can reach it yet. It is fixed
anyway because the day somebody adds hash routing or mistypes a call, a blank
screen is the worst possible way to find out. It now falls back to the
dashboard and says so in the console.

**The check that came out of it is the valuable part:** it walks the nav
itself, so every item is proven to lead to a section that exists, and it
deliberately navigates to a name that does not exist and asserts the app still
shows exactly one section. **My own harness had been walking 'archive' for two
days, a page that does not exist, and silently proving nothing there.**

## L-GFX-041 · the page body swallowed the finger, reported three times · FIXED 2026-09-10
Farhath said three times that he could not scroll up or down on his phone. Two
earlier passes could not reproduce it and shipped defensive fixes that were not
the cause: a freeze watchdog (L-GFX-031) and the Settings sheet joining the
overlay layer (L-GFX-032). Both were real faults. Neither was this one.

**The cause, in two lines of CSS that were never meant to meet.**
`.content` is the whole page body: `flex:1; padding:24px; overflow-y:auto`. The
`overflow-y:auto` makes it a scroll container. And `.content` had been added to
the sheet list carrying `overscroll-behavior:contain`, whose entire job is to
stop a scroll inside a sheet reaching the page behind it.

Together they mean a finger landing anywhere on the page content drags a box
that has nothing to scroll, and the containment stops that touch reaching the
window. Nothing moves. A finger on the topbar, which is outside `.content`,
works fine, which is why it reads as intermittent to the person using it.

**Why three rounds of green checks missed it, which is the real lesson.**
Every scroll check in this harness used `window.scrollTo()`. That sets the
scroll position directly and never goes near touch scroll chaining, so it
reports a perfectly healthy page on a build where no thumb can move anything.
**A check that exercises a different mechanism from the user is not a weaker
check, it is a different check, and it will pass forever on a broken app.**

**Fix:** `.content` comes out of the sheet list (it is not a sheet, it is the
page) and gets `overflow:visible`, so the window is the only scroller. Desktop
is untouched: `.main` is `min-height`, never a fixed height, so nothing needed
the inner scroller there either.

**The block, and it is proven.** Two checks read the STATE that makes the trap
possible rather than trying to simulate a thumb: no full-screen element may be
both a scroll container and overscroll-contained, and the page body may not be
a scroll container at all. Rebuilt the pre-fix file and watched both go red
naming `content [overflow-y auto, overscroll contain]`, then watched both go
green on the fix. 94 checks.

**TWO MORE OF THE SAME, found the moment the first fix went live and the new
sweep ran on a different page.**

`.wp-grid-wrap` on the Weekly Plan asks only for `overflow-x:auto`, to let the
seven-day grid scroll sideways. **CSS will not let one axis scroll while the
other stays visible: set `overflow-x` and `overflow-y` computes to `auto` along
with it.** So the wrapper silently became a vertical scroll container too, and
the containment then stopped a finger inside the grid scrolling the page. On
the page the graphic head uses most. Fixed by containing the axis that actually
scrolls, `overscroll-behavior-x:contain` with `-y:auto`, which keeps the
sideways swipe from triggering the browser back gesture and lets a vertical
touch chain to the page.

`.kanban-cards` came out too. It is a real vertical scroller in a desktop
column and on a phone `max-height:none` means it never scrolls at all.
Chaining at the end of a column is what a person expects in both cases.
Containment is for a sheet sitting OVER the page, which a column is not.

**And the check that found the first one nearly missed these two**, because it
swept whichever page the harness happened to be on. It now walks four pages.
**A trap that lives on one screen is invisible to a check that only visits
another**, which this register has now learned three separate times.

**Estate: checked, and Graphic was the only one.** The other four apps keep
sheets in that list (`.modal`, `.modal-bg`, `.detail-panel`, drawers), not a
page-level container. Verified 2026-09-10 by reading each app's contain list.
