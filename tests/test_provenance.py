"""Provenance: run.txt in every output folder (tools/provenance.py; RULING S8
verifier FAIL item (e), prereg/provenance.md). Hermetic: temporary folders;
git is asked only for the hash of this checkout (no identity, no network)."""
import io
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import provenance as PV                                           # noqa: E402


class RunFile(unittest.TestCase):
    def test_run_txt_holds_commit_times_and_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "out")
            run = PV.Run("tools/example.py", out, ["--test", "--last", "6"])
            p = os.path.join(out, "result.txt")
            os.makedirs(out)
            with open(p, "wb") as fh:
                fh.write(b"hello\n")
            run.wrote(p)
            path = run.close()
            self.assertEqual(os.path.basename(path), PV.RUN_FILE)
            rec = PV.read_run(out)
            self.assertEqual(rec["tool"], "tools/example.py")
            self.assertEqual(rec["args"], "--test --last 6")
            head = subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"], capture_output=True, text=True)
            if head.returncode == 0:
                self.assertEqual(rec["commit"], head.stdout.strip())                    # the commit of this checkout, 40 hex characters
                self.assertEqual(len(rec["commit"]), 40)
            else:
                self.assertEqual(rec["commit"], "unknown (git unavailable)")
            start = datetime.fromisoformat(rec["start_utc"]); end = datetime.fromisoformat(rec["end_utc"])
            self.assertEqual(str(start.tzinfo), "UTC"); self.assertGreaterEqual(end, start)
            self.assertEqual(rec["outputs"]["result.txt"], PV.sha256_of(p))
            self.assertEqual(PV.sha256_of(p), "5891b5b522d5df086d0ff0b110fbd9d21bb4fc7163af34d08286a2e846f6be03")   # sha256 of "hello\n"
            self.assertIn("modified tracked files at the run", rec)
            self.assertIsNone(PV.read_run(tmp))                                           # no run.txt there

    def test_git_unavailable_is_said_not_guessed(self):
        with mock.patch.object(PV.subprocess, "run", side_effect=OSError("no git")):
            commit, dirty = PV.git_state(ROOT)
        self.assertEqual(commit, "unknown (git unavailable)"); self.assertIsNone(dirty)
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(PV.subprocess, "run", side_effect=OSError("no git")):
            PV.Run("tools/x.py", tmp, []).close()
            self.assertEqual(PV.read_run(tmp)["commit"], "unknown (git unavailable)")

    def test_context_manager_and_missing_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            with PV.Run("tools/x.py", tmp, []) as run:
                run.wrote(os.path.join(tmp, "never_written.txt"))
            with open(os.path.join(tmp, PV.RUN_FILE), encoding="utf-8") as fh:
                text = fh.read()
            self.assertIn("never_written.txt  (missing)", text)
            with self.assertRaises(ValueError):
                with PV.Run("tools/x.py", os.path.join(tmp, "b"), []):
                    raise ValueError("the tool failed")
            self.assertFalse(os.path.exists(os.path.join(tmp, "b", PV.RUN_FILE)))        # a failed run writes no provenance

    def test_every_tool_main_writes_run_txt(self):
        """The wiring: each tool's main holds the Run and closes it after writing."""
        for name in ("backtest", "planner", "odds_lambda", "chips", "xp_v2", "league", "minutes_v2", "defcon", "shares"):
            with open(os.path.join(ROOT, "tools", name + ".py"), encoding="utf-8") as fh:
                src = fh.read()
            self.assertIn(f'run = Run("tools/{name}.py"', src, name)
            self.assertIn("run.close()", src, name)
            self.assertIn("run.wrote(path)", src, name)


if __name__ == "__main__":
    unittest.main()
