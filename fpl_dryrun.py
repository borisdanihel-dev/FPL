"""
fpl_dryrun.py  -  the gate in front of every dry run (RULING W1b).

A push to a branch dry/<item> starts the nightly workflow as a dry run
(nightly.yml, `on: push: branches: ["dry/**"]`); its result goes to
data-dryrun-<item> (fpl_publish.result_branch). A manual dispatch with dry_run
ticked, or on any branch but master, is a dry run too, as before, with its
result on data-dryrun. Before either does anything, `fpl_nightly.py --due`
calls gate(), and the run skips - green, with one line saying why - when:

  * it is in a quiet window (point 5): from 21:30 UTC until the data branch
    holds a commit made at or after that 21:30 (the night's nightly), and at
    the latest until 03:17 UTC, the backup run's slot, so a night whose
    nightly never commits cannot block the next day's dry runs; or within
    1 hour either side of any deadline (events.deadline_time in the data
    checkout);
  * CAP dry runs have already run this UTC day (point 4), push-triggered and
    manual together: "DRY RUN SKIPPED: 6 of 6 today". They are counted with
    the Actions API (actions: read, the one job's token): a run counts once
    its "Nightly run" step has started, this run left out. Every dry run is
    named "dry run <ref>" (the workflow's run-name) so the count can find it.
    When the count cannot be made the run skips as well.

A real run - master with dry_run unticked, or the schedule - never comes here.
The token is never printed. Standard library only.
"""

import json
import os
import sqlite3
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, time, timedelta, timezone

import fpl_publish

UTC = timezone.utc
CAP = 6                         # dry runs a UTC day, push and manual together (S2 amendment 2, point 9)
NIGHT_START = time(21, 30)      # the nightly's window opens (the nightly starts 21:40)
NIGHT_END = time(3, 17)         # ... and closes at the latest at the backup run's slot
DEADLINE_GAP = timedelta(hours=1)
STEP = "Nightly run"            # a dry run counts once this step has started
TITLE = "dry run "              # every dry run's run-name starts so (nightly.yml)
WORKFLOW = "nightly.yml"
API = "https://api.github.com"
_urlopen = urllib.request.urlopen
_GET = None                     # tests put a fake Actions API here


class CannotCount(Exception):
    """Today's dry runs could not be counted; the run skips."""


def night_start(now):
    """The 21:30 UTC that opened the quiet night `now` falls in, or None."""
    if now.time() >= NIGHT_START:
        return datetime.combine(now.date(), NIGHT_START, UTC)
    if now.time() < NIGHT_END:
        return datetime.combine(now.date() - timedelta(days=1), NIGHT_START, UTC)
    return None


def quiet(now, deadlines, tip):
    """Why a dry run starting at `now` must skip, or None. deadlines:
    {gameweek: aware UTC datetime}; tip: the data branch's last commit time,
    None when unknown."""
    for gw, dl in sorted(deadlines.items(), key=lambda kv: kv[1]):
        if abs(now - dl) < DEADLINE_GAP:
            return f"within 1 hour of the GW{gw} deadline ({dl:%Y-%m-%d %H:%M} UTC)"
    start = night_start(now)
    if start is not None and (tip is None or tip < start):
        last = f"{tip:%Y-%m-%d %H:%M} UTC" if tip else "unknown"
        return (f"the nightly's window: {start:%H:%M} UTC until that night's nightly has "
                f"committed, {NIGHT_END:%H:%M} UTC at the latest (data last committed {last})")
    return None


def counted(jobs):
    """True when a run's "Nightly run" step has started: running, or
    finished any way but skipped."""
    for job in jobs:
        for step in job.get("steps") or []:
            if step.get("name") != STEP:
                continue
            if step.get("status") == "in_progress":
                return True
            if step.get("status") == "completed" and step.get("conclusion") not in (None, "skipped"):
                return True
    return False


def count_dry_runs(repo, workflow, now, this_run, get):
    """How many dry runs of `workflow` ran today (UTC), this run left out."""
    today = now.date().isoformat()
    query = urllib.parse.urlencode({"created": f">={today}", "per_page": 100})
    page = get(f"/repos/{repo}/actions/workflows/{workflow}/runs?{query}") or {}
    runs = page.get("workflow_runs") or []
    if (page.get("total_count") or 0) > len(runs):
        raise CannotCount("more than one page of runs today")
    n = 0
    for run in runs:
        if str(run.get("id")) == str(this_run) or (run.get("created_at") or "")[:10] != today:
            continue
        if not (run.get("display_title") or "").startswith(TITLE):
            continue
        n += counted((get(f"/repos/{repo}/actions/runs/{run['id']}/jobs") or {}).get("jobs") or [])
    return n


def _getter(token):
    def get(path):
        req = urllib.request.Request(API + path, headers={
            "Accept": "application/vnd.github+json", "User-Agent": "fpl-dryrun",
            "X-GitHub-Api-Version": "2022-11-28", "Authorization": f"Bearer {token}"})
        try:
            with _urlopen(req, timeout=30) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            code = e.code
            e.close()
            raise CannotCount(f"HTTP {code}") from None
        except (OSError, ValueError) as e:
            raise CannotCount(type(e).__name__) from None
    return get


def workflow(env):
    """nightly.yml, from GITHUB_WORKFLOW_REF (owner/repo/.github/workflows/<file>@<ref>)."""
    ref = (env.get("GITHUB_WORKFLOW_REF") or "").split("@")[0]
    return os.path.basename(ref) or WORKFLOW


def decide(env, now, deadlines, tip, get=None):
    """(run, line) for a dry run starting at `now`: the quiet windows first,
    then the cap."""
    why = quiet(now, deadlines, tip)
    if why:
        return False, f"DRY RUN SKIPPED: {why}"
    try:
        repo = env.get("GITHUB_REPOSITORY") or ""
        if not repo:
            raise CannotCount("no repository")
        if get is None:
            token = env.get("GH_TOKEN") or ""
            if not token:
                raise CannotCount("no token")
            get = _getter(token)
        n = count_dry_runs(repo, workflow(env), now, env.get("GITHUB_RUN_ID", ""), get)
    except CannotCount as e:
        return False, f"DRY RUN SKIPPED: cannot count today's dry runs ({e})"
    if n >= CAP:
        return False, f"DRY RUN SKIPPED: {n} of {CAP} today"
    return True, f"DRY RUN      {n + 1} of {CAP} today; the result goes to {fpl_publish.result_branch(env)}"


def data_tip(data):
    """The data checkout's last commit time, None when it has none."""
    r = subprocess.run(["git", "-C", data, "log", "-1", "--format=%cI"], stdout=subprocess.PIPE,
                       stderr=subprocess.DEVNULL, encoding="utf-8")
    text = r.stdout.strip() if r.returncode == 0 else ""
    return datetime.fromisoformat(text).astimezone(UTC) if text else None


def gate(env, now, data):
    """(run, line) for the dry run about to start on the data checkout `data`.
    Without the deadlines the 1-hour rule cannot be checked: skip."""
    import fpl_gate
    db = os.path.join(data, fpl_gate.DB)
    try:
        deadlines = fpl_gate.deadlines(db) if os.path.exists(db) else None
    except (sqlite3.Error, ValueError, TypeError, AttributeError) as e:
        deadlines, problem = None, type(e).__name__
    else:
        problem = "no fpl.sqlite in the data checkout"
    if deadlines is None:
        return False, f"DRY RUN SKIPPED: cannot read the deadlines ({problem})"
    return decide(env, now, deadlines, data_tip(data), _GET)
