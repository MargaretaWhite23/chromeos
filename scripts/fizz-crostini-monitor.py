#!/usr/bin/env python3
"""Poll successful GitHub builds from Crostini and stage one host test at a time.

No privileged shell or network listener is started on ChromeOS.
"""
import argparse
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

REPO = "MargaretaWhite23/chromeos"
WORKFLOW = "fizz-minimal-no-sdk-build.yml"
NAME = "fizz-runtime-capabilities"
ARTIFACTS = Path.home() / "fizz-github-artifacts"
DEFAULT_SPOOL = Path("/mnt/chromeos/MyFiles/Downloads/fizz-automation")
DEFAULT_STATE = Path.home() / ".local/state/fizz-automation/state.json"
HEX64 = re.compile(r"^[a-f0-9]{64}$")


def command(argv, timeout=120):
    return subprocess.run(argv, text=True, capture_output=True,
                          timeout=timeout, check=True).stdout


def atomic_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name("." + path.name + ".tmp-" + str(os.getpid()))
    try:
        temp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)


def valid_request(request):
    return (
        type(request) is dict
        and type(request.get("run_id")) is int
        and request["run_id"] > 0
        and request.get("binary") == NAME
        and isinstance(request.get("sha256"), str)
        and HEX64.fullmatch(request["sha256"]) is not None
        and isinstance(request.get("head_sha"), str)
        and HEX64.fullmatch(request["head_sha"]) is not None
    )


def get_runs():
    data = command([
        "gh", "run", "list", "-R", REPO, "--workflow", WORKFLOW,
        "--branch", "main", "--limit", "20",
        "--json", "databaseId,status,conclusion,headSha,url",
    ])
    runs = json.loads(data)
    return [r for r in runs if r.get("status") == "completed"
            and r.get("conclusion") == "success"
            and type(r.get("databaseId")) is int
            and isinstance(r.get("headSha"), str)
            and HEX64.fullmatch(r["headSha"]) is not None]


def stage(run):
    run_id = run["databaseId"]
    cmd = ["bash", str(Path(__file__).with_name("fizz-stage-github-artifact.sh")),
           str(run_id), NAME]
    output = command(cmd, timeout=180)
    if "FIZZ_ARTIFACT_STAGED" not in output:
        raise RuntimeError("stager did not confirm artifact staging: " + output[-1000:])
    binary = ARTIFACTS / ("run-" + str(run_id)) / "output" / NAME
    checksum = hashlib.sha256(binary.read_bytes()).hexdigest()
    staged = Path("/mnt/chromeos/MyFiles/Downloads") / (
        "fizz-" + str(run_id) + "-" + NAME)
    if hashlib.sha256(staged.read_bytes()).hexdigest() != checksum:
        raise RuntimeError("staging checksum mismatch")
    return {
        "run_id": run_id, "binary": NAME, "sha256": checksum,
        "head_sha": run["headSha"], "workflow_url": run.get("url", ""),
    }


def github_status(head_sha, status, description, url):
    if status not in ("pending", "success", "failure", "error"):
        raise ValueError("Invalid GitHub status")
    return command([
        "gh", "api", "-X", "POST",
        "repos/" + REPO + "/statuses/" + head_sha,
        "-f", "state=" + status,
        "-f", "context=fizz/real-chromeos-host",
        "-f", "description=" + description[:140],
        "-f", "target_url=" + url,
    ])


def one_cycle(spool, state_path, allow_publish=True):
    (spool / "requests").mkdir(parents=True, exist_ok=True)
    (spool / "results").mkdir(parents=True, exist_ok=True)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    lock = state_path.with_suffix(".lock")
    with lock.open("a") as lock_handle:
        try:
            fcntl.flock(lock_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("FIZZ_MONITOR_ALREADY_RUNNING")
            return
        state = json.loads(state_path.read_text()) if state_path.exists() else {}
        current = state.get("current")
        if current:
            run_id = current["run_id"]
            result_file = spool / "results" / ("run-" + str(run_id) + ".json")
            if not result_file.exists():
                print("FIZZ_HOST_RESULT_PENDING RUN_ID=" + str(run_id))
                return
            result = json.loads(result_file.read_text())
            if (result.get("run_id") != run_id
                    or result.get("binary") != current["binary"]
                    or result.get("sha256") != current["sha256"]):
                raise ValueError("Host result does not match staged run")
            passed = (
                result.get("exit_code") == 0
                and result.get("passed") is True
                and "FIZZ_HOST_TEST_PASS" in result.get("stdout", "")
            )
            status = "success" if passed else "failure"
            if allow_publish:
                github_status(current["head_sha"], status,
                              "ChromeOS Fizz host test " + status + " (run " + str(run_id) + ")",
                              current["workflow_url"])
            print("FIZZ_HOST_RESULT_" + status.upper() + " RUN_ID=" + str(run_id))
            state["last_completed"] = run_id
            state["current"] = None
            atomic_json(state_path, state)
        runs = get_runs()
        if not runs:
            print("FIZZ_NO_SUCCESSFUL_RUNS")
            return
        # Never backfill all historical builds; monitor the newest successful main run.
        latest = max(runs, key=lambda r: r["databaseId"])
        if latest["databaseId"] <= state.get("last_completed", 0):
            print("FIZZ_NO_NEW_RUN")
            return
        request = stage(latest)
        if not valid_request(request):
            raise ValueError("Invalid staged request")
        path = spool / "requests" / ("run-" + str(request["run_id"]) + ".json")
        atomic_json(path, request)
        state["current"] = request
        atomic_json(state_path, state)
        print("FIZZ_HOST_TEST_REQUESTED RUN_ID=" + str(request["run_id"]))
        if allow_publish:
            try:
                github_status(request["head_sha"], "pending",
                              "ChromeOS Fizz host execution pending", request["workflow_url"])
            except subprocess.CalledProcessError as exc:
                # Staging was successful. GitHub status permission errors are visible
                # but must not cause duplicate host executions.
                print("FIZZ_GITHUB_PENDING_STATUS_FAILED " + (exc.stderr or "")[:500])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--spool", type=Path, default=DEFAULT_SPOOL)
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--no-publish", action="store_true")
    args = parser.parse_args()
    one_cycle(args.spool, args.state, not args.no_publish)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("FIZZ_MONITOR_ERROR " + str(exc), file=sys.stderr)
        sys.exit(1)
