# dtool-lookup-gui — Issue & PR Triage

_Generated 2026-06-12 by an authenticated `gh` pull of `livMatS/dtool-lookup-gui`._
_Prioritization lens: **bugs over features**, focus on shipping milestones **0.8.0 / 0.9.0**._

## Snapshot at triage time

- 33 open issues, 16 open PRs.
- Open milestones: **0.8.0** (5 issues), **0.9.0** (3 issues) — neither has a due date.
- Labeling is sparse: 2 `bug`, 11 `enhancement`, 25 issues with no milestone. Milestone/label
  alone does not surface urgency — several real bugs are unlabeled.
- **Branch protection on `master`:** `required_reviews: 1`, **no required status checks**,
  admins not enforced. → PRs are gated only by review, not by CI.

## Actions taken in this session

- **Merged 13 Dependabot PRs** (squash + delete branch): #840, #841, #842, #843, #844,
  #848, #849, #850, #852, #853, #854, #855, #856. Includes the security-relevant bumps
  (cryptography 46.0.5, urllib3 2.6.3 linux/macos, aiohttp 3.13.3 all platforms).
- **#851** (urllib3/win) had a real merge conflict (its requirements file was already changed
  by #849). Triggered `@dependabot rebase`; needs a final approve + merge once rebased.

## B — Root cause of the CI failures on #855 / #856 / #857

The identical `test (3.9–3.12)` FAILURE on these PRs is **a pre-existing CI helper bug, not
caused by the PRs**:

- The workflow runs `pytest -n $(python maintenance/collect_number_of_tests.py)`.
- On `master`, that script does `print("Error while running pytest:", e.stderr)` — to **stdout**
  — when `pytest --collect-only` errors. The error string is captured by `$(...)`, so pytest
  receives `-n Error` → `invalid parse_numprocesses value: 'Error'` → exit 4.
- **Already fixed** on branch `2026-06-12-claude` (commit `cd55d20`, "BUG: fix
  collect_number_of_tests.py propagating errors to stdout") which routes the message to stderr
  and falls back to `auto`. **That fix is not yet on `master`.**

**Action:** land `cd55d20` on `master`, then rebase #857. (Note: the fallback masks *why*
`--collect-only` errors in CI in the first place — worth confirming collection actually
succeeds, not just that parallelism falls back to `auto`.)

The `build` job failure on #857 is separate: it ran 6h5m (GitHub's max) and was killed —
a hung/timeout job, no error emitted.

## Priority tiers

### P0 — merge-ready backlog (done / nearly done)
Dependabot bumps — see "Actions taken". Remaining: **#851** after rebase.

### P1 — real bug fixes
1. **PR #857** — bundle gdk-pixbuf loaders, fixes GTK image crash on Linux. Highest-value
   open bug PR. Blocked only by review; CI red is the B helper bug + a hung build job.
   Land `cd55d20` on master, rebase, re-run.
2. **#370** — failure querying dependency graph (diagnosed as server-side worker timeout).
   Decide: close as not-a-GUI-bug, or add client-side timeout handling. Related: **#182**
   (large dep graphs often fail to load).
3. **#45** — base URI listing needs configurable timeout (`bug`, milestone 0.8.0). Shares the
   "timeout + graceful error" theme with #370 / #182 — fix once.
4. **#169** — failed dataset copy freezes the status bar. **#526** — README tree doesn't
   reload after edit (`bug`). Both concrete, reproducible.
5. **#199 / #211** — missing/unclear error messages (invalid dataset name; bad auth URL).
   Cheap robustness wins.

### P2 — milestone scope decisions
- **0.8.0** mixes a bug (#45) with epics: **#60** "Tests, tests, tests", **#212** "Wish list
  of functions", plus #247 (README) and #384 (.deb bundle). Recommend demoting #60/#212 out
  of 0.8.0 so the milestone can ship; keep #384 (tangible deliverable).
- **0.9.0**: #243, #276 (server-side admin / change notification) are substantial features —
  fine to keep, but scope accordingly.

### P3 — defer / groom
- macOS polish: #159, #171.
- GTK-4 migration: #59 (large).
- Older enhancement wishlist: #7, #16, #35, #36, #55, #79, #86.
- **#32** already `invalid,wontfix` → close.

## Suggested next steps
1. Approve + merge #851 once Dependabot finishes rebasing.
2. Land `cd55d20` on `master`; rebase #857 and re-run CI; merge the crash fix.
3. Triage the timeout cluster (#45 / #182 / #370) as one piece of work.
4. Groom milestones: demote #60/#212 from 0.8.0, close #32.
5. Add `bug` labels to the unlabeled bugs (#169, #182, #199, #211, #370).

---

## Issue #60 "Tests, tests, tests" — testing inventory (2026-06-12)

**Status: NOT greenfield.** Already ~89 test functions across 2,533 LOC in `test/`,
following the project's GIO-action doctrine (`CONTRIBUTING.md`): per action, a
`*_direct_call` test (calls `app.do_x(...)` against mocked `dtool_lookup_api`) and a
`*_action_trigger` test (`activate_action('x')`, assert internals dispatched).

### Action coverage: 37 / 42 `do_*` covered
Coverage measured by both `do_x` direct references **and** `activate_action('x-dash')`
dash-names (the latter corrected an initial false-negative on the pagination cluster,
which *is* tested in `test/test_main_window_missing_actions.py`).

**5 genuinely untested — all framework-level, not `Gio.SimpleAction`s:**

| Symbol | Location | Nature |
|---|---|---|
| `do_activate` | `main.py:128` | GApplication lifecycle vfunc override |
| `do_command_line` | `main.py:163` | GApplication lifecycle vfunc override |
| `do_startup` | `main.py:223` | GApplication lifecycle vfunc override |
| `do_dtool_config_changed` | `main.py:361` | config signal handler |
| `do_loglevel_changed` | `main.py` | log-level signal handler |

These need integration-style tests, not the simple direct-call pattern. Beyond these,
the broader win is filling the **second** test of the two-test pair where only one exists,
plus raising line/branch coverage of non-action modules (measure via `--cov`).

### Local test environment (mirror of `.github/workflows/test.yml`)
The repo `venv/` has the editable install + PyGObject but is missing test deps.
To run the suite locally:

- **apt:** `libgirepository1.0-dev libgirepository-2.0-dev libcairo2-dev pkg-config
  python3-dev gir1.2-gtk-3.0 gir1.2-gtksource-4 libgtksourceview-4-0 xvfb
  libglib2.0-bin tini`
- **pip (into venv):** `flake8 pytest pytest-cov pytest-asyncio` then `pip install .[test]`
- **patch:** `python maintenance/patch_dtool_cli_compat.py` (dtool-cli 0.7.1 / py3.12 shim)
- **schemas:** `glib-compile-schemas .` in `dtool_lookup_gui/` (required or import fails)
- **run:** `xvfb-run --auto-servernum pytest -n auto`
- Note: `master`'s `collect_number_of_tests.py` is broken (see B); the fix is on branch
  `2026-06-12-claude` (commit `cd55d20`).
