"""
fpl_alert.py  -  the one GitHub issue "Nightly run failed" (BUILD_PLAN.md
Step 3.3; ruling S3, points 3 and 7). The workflow runs it last, whatever
happened before:

    python fpl_alert.py DATA_DIR

  * red run (RUN_OUTCOMES names a step that did not succeed): open the issue,
    or, when one is open, update its body and add a comment - GitHub Mobile
    notifies Boris of either. The body lists the failing checks from tonight's
    reports/status.txt and the steps that failed;
  * green run: close the open issue, with a comment naming the run;
  * dry run: nothing at all - a dry run never opens or closes the issue.

At most one issue with that title is ever open: a second one found open is
closed as a duplicate. RUN_OUTCOMES is "step=outcome ..." from the workflow
(success, failure, cancelled or skipped; skipped counts as fine). The token
(GH_TOKEN) is sent to the API and never printed or written.

Standard library only.
"""

import json
import os
import sys
import urllib.request

import fpl_publish

TITLE = "Nightly run failed"
API = "https://api.github.com"
_urlopen = urllib.request.urlopen


def outcomes(text):
    """{step: outcome} from "nightly=success publish=failure ..."."""
    return dict(part.split("=", 1) for part in (text or "").split() if "=" in part)


def failing_checks(data):
    """The FAIL and WARN lines of tonight's reports/status.txt (its status line
    first), or a note that none was written."""
    path = os.path.join(data, "reports", "status.txt")
    if not os.path.exists(path):
        return ["no reports/status.txt: the run stopped before the checks"]
    with open(path, encoding="utf-8", newline="") as fh:
        lines = fh.read().splitlines()
    return lines[:1] + [l.strip() for l in lines[1:] if l.split()[1:2] in (["FAIL"], ["WARN"])]


class GitHub:
    def __init__(self, repo, token):
        self.repo, self.token = repo, token

    def call(self, method, path, body=None):
        req = urllib.request.Request(
            f"{API}/repos/{self.repo}{path}", method=method,
            data=None if body is None else json.dumps(body).encode("utf-8"),
            headers={"Accept": "application/vnd.github+json", "User-Agent": "fpl-alert",
                     "Authorization": f"Bearer {self.token}",
                     "Content-Type": "application/json"})
        with _urlopen(req, timeout=30) as r:
            raw = r.read()
        return json.loads(raw) if raw else None

    def open_issues(self):
        found = self.call("GET", "/issues?state=open&per_page=100") or []
        return sorted((i for i in found if i.get("title") == TITLE and "pull_request" not in i),
                      key=lambda i: i["number"])


def main(argv=None, env=None, say=print, gh=None):
    argv = sys.argv[1:] if argv is None else argv
    env = os.environ if env is None else env
    data = argv[0] if argv else "."
    mode, why = fpl_publish.run_mode(env)
    if mode == "dry":
        say(f"ALERT skipped: dry run ({why}) - a dry run never opens or closes the issue")
        return 0
    steps = outcomes(env.get("RUN_OUTCOMES"))
    bad = {s: o for s, o in steps.items() if o not in ("success", "skipped")}
    run_url = (f"{env.get('GITHUB_SERVER_URL', 'https://github.com')}/"
               f"{env.get('GITHUB_REPOSITORY', '')}/actions/runs/{env.get('GITHUB_RUN_ID', '')}")
    if gh is None:
        if not env.get("GITHUB_REPOSITORY") or not (env.get("GH_TOKEN") or env.get("GITHUB_TOKEN")):
            say("ALERT skipped: no GITHUB_REPOSITORY or token (a local run)")
            return 0
        gh = GitHub(env["GITHUB_REPOSITORY"], env.get("GH_TOKEN") or env.get("GITHUB_TOKEN"))
    try:
        found = gh.open_issues()
        for extra in found[1:]:                       # at most one open
            gh.call("POST", f"/issues/{extra['number']}/comments",
                    {"body": f"Closed as a duplicate of #{found[0]['number']}."})
            gh.call("PATCH", f"/issues/{extra['number']}", {"state": "closed"})
        issue = found[0] if found else None
        if bad:
            body = "\n".join(
                [f"The nightly run failed: {run_url}", "",
                 "Failed steps: " + ", ".join(f"{s} ({o})" for s, o in sorted(bad.items())), "",
                 "Checks (reports/status.txt):", "```"] + failing_checks(data) + ["```"])
            if issue is None:
                made = gh.call("POST", "/issues", {"title": TITLE, "body": body})
                say(f"ALERT OPENED issue #{made['number']} '{TITLE}'")
            else:
                gh.call("PATCH", f"/issues/{issue['number']}", {"body": body})
                gh.call("POST", f"/issues/{issue['number']}/comments", {"body": body})
                say(f"ALERT UPDATED issue #{issue['number']} '{TITLE}'")
        elif issue is not None:
            gh.call("POST", f"/issues/{issue['number']}/comments",
                    {"body": f"Closed by the green run {run_url}"})
            gh.call("PATCH", f"/issues/{issue['number']}", {"state": "closed"})
            say(f"ALERT CLOSED issue #{issue['number']}: the run is green")
        else:
            say("ALERT none: the run is green and no issue is open")
    except Exception as e:  # noqa: BLE001
        say(f"ALERT FAILED {type(e).__name__}: {e}")
        if bad:
            return 1                                  # a red run must not lose its alarm silently
        print(f"::warning title=Failure issue not closed::{type(e).__name__}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
