"""Offline tests: no GitHub credentials or real ChromeOS host required."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, str(ROOT / "scripts" / path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


monitor = load_module("fizz_crostini_monitor", "fizz-crostini-monitor.py")
worker = load_module("fizz_host_worker", "fizz-host-worker.py")
SHA = "a" * 64
HEAD = "b" * 40
RUN = 42306108497


def sample():
    return {
        "run_id": RUN, "binary": "fizz-runtime-capabilities",
        "sha256": SHA, "head_sha": HEAD,
        "workflow_url": "https://github.com/MargaretaWhite23/chromeos/actions/runs/" + str(RUN),
    }


class AutomationTests(unittest.TestCase):
    def test_request_schema(self):
        self.assertTrue(monitor.valid_request(sample()))
        self.assertTrue(worker.valid_request(sample()))
        for field, value in (("run_id", "1"), ("run_id", 0),
                             ("binary", "anything-else"), ("sha256", "invalid"),
                             ("head_sha", "c" * 64)):
            changed = sample()
            changed[field] = value
            with self.subTest(field=field, value=value):
                self.assertFalse(monitor.valid_request(changed))
                self.assertFalse(worker.valid_request(changed))

    def test_atomic_output(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "results" / "run-1.json"
            worker.atomic_result(path, sample())
            self.assertEqual(json.loads(path.read_text()), sample())
            self.assertEqual(path.stat().st_mode & 0o777, 0o644)
            monitor.atomic_json(path, {"a": 1})
            self.assertEqual(json.loads(path.read_text()), {"a": 1})

    def test_monitor_enqueue_and_verified_result(self):
        with tempfile.TemporaryDirectory() as folder:
            spool = Path(folder) / "spool"
            state = Path(folder) / "state.json"
            runs = [{
                "databaseId": RUN, "status": "completed",
                "conclusion": "success", "headSha": HEAD,
                "url": sample()["workflow_url"]
            }]
            with patch.object(monitor, "get_runs", return_value=runs), \
                 patch.object(monitor, "stage", return_value=sample()), \
                 patch.object(monitor, "github_status") as publish:
                monitor.one_cycle(spool, state)
                self.assertTrue((spool / "requests" / ("run-" + str(RUN) + ".json")).exists())
                self.assertEqual(publish.call_args.args[1], "pending")
                monitor.one_cycle(spool, state)
                self.assertEqual(publish.call_count, 1)
                worker.atomic_result(
                    spool / "results" / ("run-" + str(RUN) + ".json"),
                    {**sample(), "exit_code": 0, "passed": True,
                     "stdout": "FIZZ_RUNTIME_CAPABILITIES_COMPLETE\nRUNTIME_UID=1000\nRUNTIME_EUID=1000"}
                )
                monitor.one_cycle(spool, state)
                self.assertEqual(publish.call_args.args[1], "success")
                self.assertEqual(json.loads(state.read_text())["last_completed"], RUN)
                self.assertIsNone(json.loads(state.read_text())["current"])
                monitor.one_cycle(spool, state)
                self.assertEqual(publish.call_count, 2)

    def test_reject_result_with_different_binary_digest(self):
        with tempfile.TemporaryDirectory() as folder:
            spool = Path(folder) / "spool"
            state = Path(folder) / "state.json"
            monitor.atomic_json(state, {"current": sample()})
            worker.atomic_result(
                spool / "results" / ("run-" + str(RUN) + ".json"),
                {**sample(), "sha256": "0" * 64,
                 "exit_code": 0, "passed": True,
                 "stdout": "FIZZ_RUNTIME_CAPABILITIES_COMPLETE\nRUNTIME_UID=1000\nRUNTIME_EUID=1000"}
            )
            with self.assertRaises(ValueError), \
                 patch.object(monitor, "github_status"):
                monitor.one_cycle(spool, state)


if __name__ == "__main__":
    unittest.main()
