#!/usr/bin/env python3
"""Restricted ChromeOS worker. Polls a shared-file queue; opens no network port.

The installed host-test shell script copies the binary to /usr/local and
executes it as chronos (UID 1000). Never accepts shell commands or paths.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

NAME = "fizz-runtime-capabilities"
HOST_SCRIPT = Path("/usr/local/fizz-testing/fizz-test-on-chromeos.sh")
SPOOL = Path("/home/chronos/user/MyFiles/Downloads/fizz-automation")
SHA64 = re.compile(r"^[a-f0-9]{64}$")
SHA40 = re.compile(r"^[a-f0-9]{40}$")
REQUEST_FILE = re.compile(r"^run-([1-9][0-9]*)\.json$")


def valid_request(obj):
    return (
        type(obj) is dict
        and type(obj.get("run_id")) is int
        and obj["run_id"] > 0
        and obj.get("binary") == NAME
        and isinstance(obj.get("sha256"), str)
        and SHA64.fullmatch(obj["sha256"]) is not None
        and isinstance(obj.get("head_sha"), str)
        and SHA40.fullmatch(obj["head_sha"]) is not None
    )


def atomic_result(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp-" + str(os.getpid()))
    try:
        tmp.write_text(json.dumps(data, sort_keys=True, indent=2) + "\n")
        tmp.chmod(0o644)
        tmp.replace(path)
    finally:
        tmp.unlink(missing_ok=True)


def check_host_script(path):
    stat = path.stat()
    if not path.is_file() or stat.st_uid != 0 or (stat.st_mode & 0o022):
        raise RuntimeError("Refusing untrusted or writable host-test script")


def process_request(request_file, result_file, host_script=HOST_SCRIPT):
    request = json.loads(request_file.read_text())
    if not valid_request(request):
        raise ValueError("Request schema rejected")
    if request_file.name != "run-" + str(request["run_id"]) + ".json":
        raise ValueError("Request filename mismatch")
    if result_file.exists():
        return None
    check_host_script(host_script)
    binary = Path("/home/chronos/user/MyFiles/Downloads") / (
        "fizz-" + str(request["run_id"]) + "-" + NAME)
    # Hash before invoking the installed script, which independently rechecks
    # the same checksum both before and after copying to /usr/local.
    if not binary.is_file() or hashlib.sha256(binary.read_bytes()).hexdigest() != request["sha256"]:
        exit_code, stdout, stderr = 1, "HOST_STAGE_CHECKSUM_FAILED\n", ""
    else:
        try:
            result = subprocess.run(
                [str(host_script), str(request["run_id"]), NAME, request["sha256"]],
                capture_output=True, text=True, timeout=120, check=False,
            )
            exit_code, stdout, stderr = result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            exit_code, stdout, stderr = 124, "", "HOST_TEST_TIMEOUT\n"
    passed = (
        exit_code == 0
        and "FIZZ_HOST_TEST_PASS" in stdout
        and "FIZZ_RUNTIME_CAPABILITIES_COMPLETE" in stdout
        and "RUNTIME_UID=1000" in stdout
        and "RUNTIME_EUID=1000" in stdout
        and "CHROMEOS_EXIT_CODE=0" in stdout
    )
    response = {
        "run_id": request["run_id"],
        "binary": NAME,
        "sha256": request["sha256"],
        "exit_code": exit_code,
        "passed": passed,
        "stdout": stdout[-16384:],
        "stderr": stderr[-4096:],
        "finished_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    atomic_result(result_file, response)
    return response


def once(spool=SPOOL):
    requests = spool / "requests"
    results = spool / "results"
    if not requests.is_dir():
        print("FIZZ_NO_REQUEST_DIRECTORY")
        return 0
    for request in sorted(requests.iterdir()):
        if not REQUEST_FILE.fullmatch(request.name) or request.is_symlink():
            continue
        result = results / request.name
        if result.exists():
            continue
        try:
            response = process_request(request, result)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print("FIZZ_HOST_REQUEST_REJECTED " + request.name + " " + str(exc), file=sys.stderr)
            continue
        if response is not None:
            print("FIZZ_HOST_WORKER_RESULT " + request.name + " " +
                  ("PASS" if response["passed"] else "FAIL"))
            return 1
    print("FIZZ_HOST_NO_PENDING_REQUEST")
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--interval", type=int, default=30)
    parser.add_argument("--spool", type=Path, default=SPOOL)
    args = parser.parse_args()
    if os.geteuid() != 0:
        parser.error("Run on ChromeOS host as root; probe itself runs as chronos")
    if not 10 <= args.interval <= 3600:
        parser.error("interval must be 10..3600 seconds")
    check_host_script(HOST_SCRIPT)
    if args.once:
        once(args.spool)
        return
    print("FIZZ_HOST_WORKER_STARTED", flush=True)
    while True:
        try:
            once(args.spool)
        except Exception as exc:
            print("FIZZ_HOST_WORKER_ERROR " + str(exc), file=sys.stderr)
        sys.stdout.flush()
        sys.stderr.flush()
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
