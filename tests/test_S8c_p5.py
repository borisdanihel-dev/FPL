"""tests/test_S8c_p5.py - S8c point 5 (Ruling, Fri 6 Nov, verbatim in prereg/S8c.md): "The 68 tests that fail with
commit signing on: make the tests' temporary repos disable signing locally (git -c commit.gpgsign=false or
per-repo config). Tests only, no behaviour change."

Each temporary repository the suite creates sets commit.gpgsign false in its own config. This test runs one test
for each place that creates such a repository, in a child process whose global git config turns signing on
with a signing program that does not exist, so that any repository still reading the global setting fails its
commit. CLAUDE.md's hermetic rule: no test may rely on global git config. Standard library only.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# one test per repository-creating site (prereg/S8c.md point 5; the patch's twelve lines)
SITES = (
    ("test_fpl.py, NightlyRunner._data_repo", "test_fpl.NightlyRunner.test_restore_writes_only_the_working_exports_and_commits_nothing"),
    ("test_fpl.py, DataGate.setUp", "test_fpl.DataGate.test_a_changed_frozen_forecast_is_rejected"),
    ("test_fpl.py, Publish._ident (seed and runner clones)", "test_fpl.Publish.test_a_dry_run_on_master_goes_to_data_dryrun_only"),
    ("test_fpl.py, PrePush.setUp", "test_fpl.PrePush.test_a_code_push_and_the_migration_delete_pass"),
    ("tests/test_S3.py, PublishOnAFail.setUp (seed and run clone)",
     "tests.test_S3.PublishOnAFail.test_a_dry_run_with_a_fail_still_reports_to_data_dryrun"),
    ("tests/test_W1.py, OddsAppendOnly.setUp", "tests.test_W1.OddsAppendOnly.test_a_deleted_odds_file_fails_the_gate"),
    ("tests/test_W1.py, OddsNeverCostsTheNight (seed and data clone)",
     "tests.test_W1.OddsNeverCostsTheNight.test_a_crashing_collector_and_the_night_still_commits"),
    ("tests/test_W1b.py, DueGate.setUp", "tests.test_W1b.DueGate.test_a_manual_dry_run_is_gated_too"),
    ("tests/test_W1b.py, Hook.setUp", "tests.test_W1b.Hook.test_dry_pushes_and_dryrun_deletions_pass"),
)
# tests/test_S3.py ChecksMain.setUp also sets it, but its helper does not check the commit's exit code, so no
# ChecksMain test fails without it: it is not one of the guarded sites (prereg/S8c.md point 5; the report).


class SigningOffInEveryTestRepo(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.cfg = os.path.join(self.tmp, "hostile.gitconfig")
        missing = os.path.join(self.tmp, "no-such-gpg")
        with open(self.cfg, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("[commit]\n\tgpgsign = true\n[gpg]\n\tprogram = "
                     + missing.replace("\\", "/") + "\n")

    def _run(self, ids):
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_") and k not in ("ODDS_API_KEY", "FPL_DATA_DIR")}
        env["GIT_CONFIG_GLOBAL"] = self.cfg
        return subprocess.run([sys.executable, "-m", "unittest", *ids], cwd=ROOT, env=env,
                              capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)

    def test_the_hostile_config_really_breaks_an_unprotected_commit(self):
        repo = os.path.join(self.tmp, "bare")
        subprocess.run(["git", "init", "-q", repo], check=True, capture_output=True)
        with open(os.path.join(repo, "f"), "w", encoding="utf-8") as fh:
            fh.write("x\n")
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        env["GIT_CONFIG_GLOBAL"] = self.cfg
        git = ["git", "-C", repo, "-c", "user.name=t", "-c", "user.email=t@t"]
        subprocess.run(git + ["add", "f"], check=True, env=env, capture_output=True)
        self.assertNotEqual(subprocess.run(git + ["commit", "-q", "-m", "x"], env=env, capture_output=True).returncode, 0)
        subprocess.run(git + ["config", "commit.gpgsign", "false"], check=True, env=env, capture_output=True)
        self.assertEqual(subprocess.run(git + ["commit", "-q", "-m", "x"], env=env, capture_output=True).returncode, 0)

    def test_one_test_per_site_passes_with_signing_on_globally(self):
        r = self._run([test for _, test in SITES])
        self.assertEqual(r.returncode, 0, r.stderr[-3000:])
        self.assertIn(f"Ran {len(SITES)} test", r.stderr)


if __name__ == "__main__":
    unittest.main()
