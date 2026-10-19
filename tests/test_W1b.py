"""W1b (RULING W1b, 19 Oct): automatic dry runs.

A push to dry/<item> starts the nightly workflow as a dry run whose result
goes to data-dryrun-<item>; the key is not passed; the run waits in the
nightly-dryrun group, never nightly-data. Before it does anything the --due
gate skips it, green, in a quiet window (21:30 UTC until the night's nightly
has committed, at the latest 03:17 UTC; within 1 hour of a deadline) or at
the cap of 6 dry runs a UTC day, counted with the Actions API. Manual
dispatch keeps its inputs and data-dryrun.
"""

import io
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import fpl_dryrun as D      # noqa: E402
import fpl_nightly as N     # noqa: E402
import fpl_prepush as PP    # noqa: E402
import fpl_publish as PUB   # noqa: E402
import test_fpl as TF       # noqa: E402

UTC = timezone.utc
PUSH = {"GITHUB_EVENT_NAME": "push", "GITHUB_REF": "refs/heads/dry/S16", "GITHUB_REF_NAME": "dry/S16",
        "GITHUB_REPOSITORY": "o/r", "GITHUB_RUN_ID": "900", "GH_TOKEN": "t-not-a-real-token",
        "GITHUB_WORKFLOW_REF": "o/r/.github/workflows/nightly.yml@refs/heads/dry/S16"}


def at(text):
    return datetime.fromisoformat(text).replace(tzinfo=UTC)


def _read(*parts):
    with open(os.path.join(HERE, *parts), encoding="utf-8") as fh:
        return fh.read()


def _code(y):
    return "\n".join(l for l in y.splitlines() if not l.strip().startswith("#"))


class Trigger(unittest.TestCase):
    """Points 1, 2, 4 and 6 in the workflow text (no YAML parser in the
    standard library)."""

    def setUp(self):
        self.y = _code(_read(".github", "workflows", "nightly.yml"))
        self.on = self.y[self.y.index("\non:\n"):self.y.index("\npermissions:")]

    def test_the_push_trigger_is_dry_only(self):
        self.assertIn('\n  push:\n    branches:\n      - "dry/**"\n', self.on)
        self.assertEqual(self.on.count("push:"), 1)
        for other in ("branches-ignore", "tags", "paths", "pull_request", "\n  release", "merge_group"):
            self.assertNotIn(other, self.on)
        items = [l.strip() for l in self.on.splitlines() if l.strip().startswith("- ")]
        self.assertEqual(items, ['- "dry/**"', '- cron: "40 21 * * *"', '- cron: "17 3 * * *"'])

    def test_schedule_and_manual_dispatch_stay_as_they_were(self):
        self.assertIn('- cron: "40 21 * * *"', self.on)
        self.assertIn('- cron: "17 3 * * *"', self.on)
        for name, default in (("dry_run", "true"), ("odds_live", "false"), ("force_backup", "false")):
            block = self.on[self.on.index(f"      {name}:\n"):]
            block = block[:block.index("default:") + len("default: ") + len(default)]
            self.assertIn("type: boolean", block, name)
            self.assertTrue(block.endswith(f"default: {default}"), name)

    def test_a_push_waits_in_the_dry_group_and_cancels_nothing(self):
        self.assertIn("  group: ${{ (github.ref != 'refs/heads/master' || (github.event_name == "
                      "'workflow_dispatch' && inputs.dry_run)) && 'nightly-dryrun' || 'nightly-data' }}\n",
                      self.y)
        self.assertIn("  cancel-in-progress: false", self.y)
        # a push's ref is refs/heads/dry/..., never master: the first operand is true
        self.assertTrue("refs/heads/dry/x" != "refs/heads/master")
        self.assertIn("      FPL_DRY_RUN: ${{ (github.ref != 'refs/heads/master' || ", self.y)

    def test_every_dry_run_is_named_so_the_cap_can_count_it(self):
        self.assertIn("\nrun-name: ${{ (github.event_name == 'push' || (github.event_name == "
                      "'workflow_dispatch' && (github.ref != 'refs/heads/master' || inputs.dry_run))) "
                      "&& format('dry run {0}', github.ref_name) || 'nightly' }}\n", self.y)
        self.assertEqual(D.TITLE, "dry run ")

    def test_the_key_is_not_passed_to_a_push_run(self):
        key = "          ODDS_API_KEY: ${{ github.event_name != 'push' && secrets.ODDS_API_KEY || '' }}\n"
        self.assertEqual(self.y.count(key), 2)
        self.assertEqual(self.y.count("secrets."), 2)
        self.assertIn("          FPL_ODDS_LIVE: ${{ inputs.odds_live }}\n", self.y)   # empty on a push

    def test_the_one_job_reads_actions_and_the_due_step_has_the_token(self):
        self.assertIn("\npermissions: {}", self.y)
        perms = self.y[self.y.index("    permissions:\n"):self.y.index("    env:\n")]
        self.assertEqual(sorted(l.split("#")[0].strip() for l in perms.splitlines()[1:] if l.strip()),
                         ["actions: read", "contents: write", "issues: write"])
        due = self.y[self.y.index("name: Is this run due"):self.y.index("name: Install requirements")]
        self.assertIn("          GH_TOKEN: ${{ github.token }}\n", due)
        self.assertIn("run: python fpl_nightly.py --due", due)


class ResultBranch(unittest.TestCase):
    """Point 3: data-dryrun-<item> for a push, data-dryrun for a dispatch;
    nothing else is ever force-pushed."""

    def test_names(self):
        rb = PUB.result_branch
        self.assertEqual(rb(PUSH), "data-dryrun-S16")
        self.assertEqual(rb(dict(PUSH, GITHUB_REF="refs/heads/dry/S16-2")), "data-dryrun-S16-2")
        self.assertEqual(rb(dict(PUSH, GITHUB_EVENT_NAME="workflow_dispatch")), "data-dryrun")
        self.assertEqual(rb({"GITHUB_EVENT_NAME": "workflow_dispatch", "GITHUB_REF": "refs/heads/master"}),
                         "data-dryrun")
        self.assertEqual(rb(dict(PUSH, GITHUB_REF="refs/heads/dry/")), "data-dryrun")
        self.assertEqual(rb(dict(PUSH, GITHUB_REF="refs/heads/s2b-wip")), "data-dryrun")

    def test_only_data_dryrun_and_data_dryrun_star_are_targets(self):
        for ok in ("data-dryrun", "data-dryrun-S16", "data-dryrun-S16-2"):
            self.assertTrue(PUB.dry_target(ok), ok)
        for bad in ("data", "master", "data-dryrun-", "data-dryrunx", "lane-b", "dry/S16", ""):
            self.assertFalse(PUB.dry_target(bad), bad)

    def test_push_dry_refuses_anything_else_without_calling_git(self):
        calls, said = [], []
        saved = PUB._git
        PUB._git = lambda repo, *a: calls.append(a)
        try:
            for bad in ("data", "master", "lane-b"):
                self.assertFalse(PUB.push_dry("x", say=said.append, branch=bad))
        finally:
            PUB._git = saved
        self.assertEqual(calls, [])
        self.assertTrue(all(s.startswith("PUSH REFUSED") for s in said))


class _NoInheritedTests(TF.Publish):
    pass


for _name in dir(TF.Publish):
    if _name.startswith("test"):
        setattr(_NoInheritedTests, _name, None)          # only the tests below run here


class PushRunPublishes(_NoInheritedTests):
    """Point 3 end to end with a bare remote: a push run's result lands on
    data-dryrun-<item>, never data and never data-dryrun."""

    def test_a_push_run_goes_to_its_own_branch(self):
        before = self._remote_head()
        self._add_prices(self.run_dir)
        code, out = self._publish(dict(PUSH, GITHUB_SHA="0123456789abcdef"))
        self.assertEqual(code, 0, out)
        self.assertIn("the result goes to data-dryrun-S16 only, never to data", out)
        self.assertEqual(self._remote_head(), before)
        self.assertIsNotNone(self._remote_ref("data-dryrun-S16"))
        self.assertIsNone(self._remote_ref("data-dryrun"))
        msg = self._git(self.remote, "log", "-1", "--format=%s", "data-dryrun-S16").stdout.strip()
        self.assertRegex(msg, r"^dry run \d{4}-\d{2}-\d{2} dry/S16 0123456 \[skip ci\]$")

    def test_a_manual_dry_run_still_goes_to_data_dryrun(self):
        self._add_prices(self.run_dir)
        code, out = self._publish({"GITHUB_EVENT_NAME": "workflow_dispatch", "GITHUB_REF": "refs/heads/dry/S16"})
        self.assertEqual(code, 0, out)
        self.assertIsNotNone(self._remote_ref("data-dryrun"))
        self.assertIsNone(self._remote_ref("data-dryrun-S16"))


class Windows(unittest.TestCase):
    """Point 5 (and reading (b) in prereg/W1b.md: the 21:30 window closes at
    03:17 UTC at the latest)."""

    NIGHTLY = at("2026-10-19T21:58:09")         # tonight's nightly commit
    LAST = at("2026-10-18T21:58:09")            # last night's
    DLS = {"8": at("2026-10-23T17:30")}

    def q(self, now, tip):
        return D.quiet(at(now), self.DLS, tip)

    def test_the_night(self):
        self.assertIsNone(self.q("2026-10-19T21:29", self.LAST))
        self.assertIn("nightly", self.q("2026-10-19T21:30", self.LAST))
        self.assertIn("nightly", self.q("2026-10-19T21:57", self.LAST))
        self.assertIsNone(self.q("2026-10-19T21:59", self.NIGHTLY))
        self.assertIsNone(self.q("2026-10-20T02:00", self.NIGHTLY))
        self.assertIn("nightly", self.q("2026-10-20T02:00", self.LAST))    # tonight's never committed
        self.assertIn("nightly", self.q("2026-10-20T03:16", self.LAST))
        self.assertIsNone(self.q("2026-10-20T03:17", self.LAST))
        self.assertIn("nightly", self.q("2026-10-19T22:10", None))         # tip unknown

    def test_a_deadline(self):
        self.assertIsNone(self.q("2026-10-23T16:30", self.LAST))
        self.assertIn("GW8 deadline", self.q("2026-10-23T16:31", self.LAST))
        self.assertIn("GW8 deadline", self.q("2026-10-23T18:29", self.LAST))
        self.assertIsNone(self.q("2026-10-23T18:30", self.LAST))


def _run(i, title, created, step=("completed", "success")):
    return {"id": i, "display_title": title, "created_at": created,
            "_steps": [] if step is None else [{"name": "Nightly run", "status": step[0], "conclusion": step[1]}]}


def _api(runs, total=None, fail=None):
    """A fake Actions API: the runs list and each run's jobs."""
    seen = []

    def get(path):
        seen.append(path)
        if fail:
            raise D.CannotCount(fail)
        if "/jobs" in path:
            rid = int(path.split("/runs/")[1].split("/")[0])
            run = next(r for r in runs if r["id"] == rid)
            return {"jobs": [{"name": "nightly", "steps": run["_steps"]}]}
        return {"total_count": len(runs) if total is None else total,
                "workflow_runs": [{k: v for k, v in r.items() if k != "_steps"} for r in runs]}
    return get, seen


NOW = at("2026-10-19T14:00")
TODAY = "2026-10-19T"


class Cap(unittest.TestCase):
    """Point 4: 6 a UTC day, push and manual together, counted once their
    "Nightly run" step started; this run left out; cannot count = skip."""

    def runs(self, n):
        return [_run(i, f"dry run dry/X{i}", f"{TODAY}0{i}:00:00Z") for i in range(1, n + 1)]

    def test_counting(self):
        runs = self.runs(3) + [
            _run(10, "nightly", f"{TODAY}03:17:00Z"),                                  # the backup cron
            _run(11, "dry run master", f"{TODAY}10:00:00Z"),                           # a manual dry run
            _run(12, "dry run dry/Y", f"{TODAY}11:00:00Z", ("completed", "skipped")),  # it skipped
            _run(13, "dry run dry/Y", f"{TODAY}11:05:00Z", None),                      # cancelled pending
            _run(14, "dry run dry/Z", "2026-10-18T23:00:00Z"),                         # yesterday
            _run(900, "dry run dry/S16", f"{TODAY}13:59:00Z", ("in_progress", None)),  # this run
            _run(15, "dry run dry/W", f"{TODAY}12:00:00Z", ("completed", "failure")),
        ]
        get, seen = _api(runs)
        self.assertEqual(D.count_dry_runs("o/r", "nightly.yml", NOW, "900", get), 5)
        self.assertIn("/repos/o/r/actions/workflows/nightly.yml/runs?created=%3E%3D2026-10-19&per_page=100",
                      seen[0])
        self.assertNotIn("/repos/o/r/actions/runs/14/jobs", seen)
        self.assertNotIn("/repos/o/r/actions/runs/900/jobs", seen)

    def _gate(self, runs, env=PUSH, **kw):
        get, _ = _api(runs, **kw)
        return D.decide(env, NOW, {"8": at("2026-10-23T17:30")}, at("2026-10-18T21:58"), get)

    def test_the_sixth_runs_and_the_seventh_skips_green(self):
        self.assertEqual(self._gate(self.runs(5)),
                         (True, "DRY RUN      6 of 6 today; the result goes to data-dryrun-S16"))
        self.assertEqual(self._gate(self.runs(6)), (False, "DRY RUN SKIPPED: 6 of 6 today"))
        self.assertEqual(self._gate(self.runs(7))[0], False)

    def test_a_manual_dry_run_counts_and_is_capped_too(self):
        manual = {"GITHUB_EVENT_NAME": "workflow_dispatch", "GITHUB_REF": "refs/heads/master",
                  "FPL_DRY_RUN": "true", "GITHUB_REPOSITORY": "o/r", "GITHUB_RUN_ID": "900"}
        self.assertEqual(self._gate(self.runs(6), env=manual), (False, "DRY RUN SKIPPED: 6 of 6 today"))
        self.assertEqual(self._gate(self.runs(2), env=manual),
                         (True, "DRY RUN      3 of 6 today; the result goes to data-dryrun"))

    def test_when_it_cannot_count_it_skips(self):
        for kw, why in (({"fail": "HTTP 403"}, "HTTP 403"), ({"total": 101}, "more than one page")):
            run, line = self._gate(self.runs(1), **kw)
            self.assertFalse(run)
            self.assertTrue(line.startswith("DRY RUN SKIPPED: cannot count today's dry runs"), line)
            self.assertIn(why, line)
        run, line = D.decide(dict(PUSH, GITHUB_REPOSITORY=""), NOW, {}, at("2026-10-18T21:58"), None)
        self.assertFalse(run)
        self.assertIn("cannot count", line)

    def test_no_token_means_no_count_and_the_token_is_never_shown(self):
        env = dict(PUSH, GH_TOKEN="")
        run, line = D.decide(env, NOW, {}, at("2026-10-18T21:58"), None)
        self.assertEqual((run, line), (False, "DRY RUN SKIPPED: cannot count today's dry runs (no token)"))
        _, line = self._gate(self.runs(6))
        self.assertNotIn(PUSH["GH_TOKEN"], line)

    def test_a_quiet_window_skips_before_any_api_call(self):
        get, seen = _api(self.runs(0))
        run, line = D.decide(PUSH, at("2026-10-19T21:45"), {}, at("2026-10-18T21:58"), get)
        self.assertFalse(run)
        self.assertTrue(line.startswith("DRY RUN SKIPPED: the nightly's window"), line)
        self.assertEqual(seen, [])

    def test_the_workflow_file_comes_from_the_ref(self):
        self.assertEqual(D.workflow(PUSH), "nightly.yml")
        self.assertEqual(D.workflow({}), "nightly.yml")


class DueGate(unittest.TestCase):
    """--due end to end: a data checkout (git, fpl.sqlite), GITHUB_OUTPUT, a
    fake Actions API. A real run never reaches the gate."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.data = os.path.join(self.tmp, "data")
        os.makedirs(self.data)
        con = sqlite3.connect(os.path.join(self.data, "fpl.sqlite"))
        con.execute("CREATE TABLE events (id INTEGER PRIMARY KEY, deadline_time TEXT)")
        con.execute("INSERT INTO events VALUES (8, '2026-10-23T17:30:00Z')")
        con.commit()
        con.close()
        env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t",
                   GIT_COMMITTER_EMAIL="t@t", GIT_COMMITTER_DATE="2026-10-18T21:58:09Z",
                   GIT_AUTHOR_DATE="2026-10-18T21:58:09Z")
        for args in (["init", "-q"], ["add", "-A"], ["-c", "core.autocrlf=false", "commit", "-q", "-m", "nightly"]):
            subprocess.run(["git", "-C", self.data, *args], env=env, check=True, capture_output=True)
        self.out = os.path.join(self.tmp, "github_output")

    def _due(self, env, now, runs=()):
        get, seen = _api(list(runs))
        saved = D._GET
        D._GET = get
        lines = []
        try:
            N.due_main(self.data, env=dict(env, GITHUB_OUTPUT=self.out), now=now, say=lines.append)
        finally:
            D._GET = saved
        with open(self.out, encoding="utf-8") as fh:
            return fh.read().splitlines()[-1], lines, seen

    def test_the_tip_and_the_deadlines_come_from_the_checkout(self):
        self.assertEqual(D.data_tip(self.data), at("2026-10-18T21:58:09"))
        self.assertIsNone(D.data_tip(self.tmp))

    def test_a_push_below_the_cap_runs(self):
        out, lines, _ = self._due(PUSH, NOW)
        self.assertEqual(out, "run=true")
        self.assertEqual(lines, ["DUE          not the backup cron",
                                 "DRY RUN      1 of 6 today; the result goes to data-dryrun-S16"])

    def test_a_push_at_the_cap_skips_green(self):
        runs = [_run(i, f"dry run dry/X{i}", f"{TODAY}0{i}:00:00Z") for i in range(1, 7)]
        out, lines, _ = self._due(PUSH, NOW, runs)
        self.assertEqual(out, "run=false")
        self.assertEqual(lines[-1], "DRY RUN SKIPPED: 6 of 6 today")

    def test_near_a_deadline_it_skips(self):
        out, lines, seen = self._due(PUSH, at("2026-10-23T17:00"))
        self.assertEqual(out, "run=false")
        self.assertIn("GW8 deadline", lines[-1])
        self.assertEqual(seen, [])

    def test_without_the_deadlines_it_skips(self):
        os.remove(os.path.join(self.data, "fpl.sqlite"))
        out, lines, seen = self._due(PUSH, NOW)
        self.assertEqual(out, "run=false")
        self.assertEqual(lines[-1], "DRY RUN SKIPPED: cannot read the deadlines (no fpl.sqlite in the data checkout)")
        self.assertEqual(seen, [])

    def test_real_runs_never_reach_the_gate(self):
        for env, now in (({"GITHUB_EVENT_NAME": "schedule", "GITHUB_REF": "refs/heads/master",
                           "FPL_SCHEDULE": "40 21 * * *"}, at("2026-10-19T21:45")),
                         ({"GITHUB_EVENT_NAME": "workflow_dispatch", "GITHUB_REF": "refs/heads/master",
                           "FPL_DRY_RUN": "false"}, at("2026-10-23T17:10"))):
            out, lines, seen = self._due(env, now)
            self.assertEqual(out, "run=true", lines)
            self.assertEqual(seen, [])
            self.assertFalse(any(l.startswith("DRY RUN") for l in lines), lines)


class Hook(unittest.TestCase):
    """Point 3 and 7: the pre-push hook allows dry/* pushes and the deletion
    of data-dryrun-*; master stays guarded."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t",
                   GIT_COMMITTER_EMAIL="t@t")
        run = lambda *a: subprocess.run(["git", "-C", self.tmp, *a], env=env, check=True,
                                        capture_output=True, text=True).stdout.strip()
        run("init", "-q")
        with open(os.path.join(self.tmp, "tool.py"), "w", encoding="utf-8") as fh:
            fh.write("x = 1\n")
        run("add", "-A")
        run("-c", "core.autocrlf=false", "commit", "-q", "-m", "code")
        self.code = run("rev-parse", "HEAD")
        with open(os.path.join(self.tmp, "fpl.sqlite"), "wb") as fh:
            fh.write(b"data")
        run("add", "-A")
        run("-c", "core.autocrlf=false", "commit", "-q", "-m", "data")
        self.data = run("rev-parse", "HEAD")

    def test_dry_pushes_and_dryrun_deletions_pass(self):
        lines = [f"refs/heads/w1b-wip {self.code} refs/heads/dry/W1b {PP.ZERO}",
                 f"refs/heads/w1b-wip {self.code} refs/heads/dry/W1b-2 {PP.ZERO}",
                 f"(delete) {PP.ZERO} refs/heads/data-dryrun-W1b {self.code}",
                 f"(delete) {PP.ZERO} refs/heads/dry/W1b {self.code}"]
        self.assertEqual(PP.check(self.tmp, lines), [])

    def test_master_is_still_guarded(self):
        bad = PP.check(self.tmp, [f"refs/heads/x {self.data} refs/heads/master {PP.ZERO}"])
        self.assertEqual([p for _, p in bad], ["fpl.sqlite"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
