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

## L-GFX-005 · thumbnails fetch the full-size original · OPEN
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

## L-GFX-010 · 346 duplicate projects from one bulk add · OPEN
`SQUARE 1 AI` holds 346 active projects created on 2026-07-02 by SUHANA from
**17 distinct titles** — roughly 20 copies of each. They are 346 of the 362
projects on the entire board and a large share of the 86 MB in L-GFX-001.

Not touched: live data, Thulaib's call. A bulk-add dedup guard was added for
the weekly plan in a5f0c68 but `graphic_projects` bulk add has no equivalent.

## L-GFX-007 · no self-test harness · OPEN
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

## L-GFX-017 · two "+ Add Task" buttons on the Weekly Plan · OPEN (cosmetic)
One in the topbar page-action slot (set in `navigateTo`, ~line 1120) and one in
the section header. Confirmed on the live build before this work, so it is
pre-existing. Harmless, both call `wpOpenAdd()`, but it looks unfinished.

## L-GFX-018 · guard.py does not check CSS · OPEN
While building the weekly grid an edit left a CSS comment unterminated
(`/* WELCOME WALKTHROUGH` with no `*/`), which silently swallowed the entire
`.gd-wrap` rule set. **`guard.py` passed**, because it only parses JavaScript.

Caught by counting `/*` against `*/` inside every `<style>` block: 38 vs 37.
That check is now part of the build routine for this system. Same family as
[[checks-must-watch-the-right-surface]]: ask what the checker actually READ.

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
