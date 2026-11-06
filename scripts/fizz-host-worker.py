#!/usr/bin/env python3
"""Unprivileged ChromeOS host worker. No TCP listener or general shell API.

The worker runs as chronos (UID/EUID 1000) and can execute only allowlisted
artifact names copied to a chronos-owned directory on the executable filesystem.
"""
import argparse
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

NAME = "fizz-runtime-capabilities"
SPOOL = Path("/home/chronos/user/MyFiles/Downloads/fizz-automation")
DOWNLOADS = Path("/home/chronos/user/MyFiles/Downloads")
RUN_DIRECTORY = Path("/usr/local/fizz-testing/chronos-run")
LOCK = RUN_DIRECTORY / ".fizz-host-worker.lock"
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
        # Never follow an attacker-controlled symlink in the shared directory.
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
        with os.fdopen(fd, "w") as out:
            json.dump(data, out, sort_keys=True, indent=2)
            out.write("\n")
        tmp.replace(path)
    finally:
        tmp.unlink(missing_ok=True)


def check_run_directory(path):
    if os.geteuid() != 1000:
        raise RuntimeError("Host worker must run as chronos EUID 1000, not root")
    if not path.is_dir() or path.is_symlink():
        raise RuntimeError("Missing chronos-owned executable work directory")
    stat = path.stat()
    if stat.st_uid != 1000 or stat.st_mode & 0o077:
        raise RuntimeError("Work directory must be owned by chronos and mode 0700")


def execute_verified(binary, sha256, work_directory=RUN_DIRECTORY):
    with tempfile.TemporaryDirectory(prefix="fizz-", dir=work_directory) as folder:
        target = Path(folder) / NAME
        # Read the supplied source once and verify exactly the bytes copied
        # to an executable filesystem. SHA is integrity, not publisher auth.
        digest = hashlib.sha256()
        with binary.open("rb") as source, target.open("xb") as out:
            while True:
                chunk = source.read(65536)
                if not chunk:
                    break
                digest.update(chunk)
                out.write(chunk)
        if digest.hexdigest() != sha256:
            raise ValueError("Target artifact checksum mismatch")
        if hashlib.sha256(target.read_bytes()).hexdigest() != sha256:
            raise ValueError("Executable copy checksum mismatch")
        target.chmod(0o700)
        try:
            p = subprocess.run([str(target)], capture_output=True,
                               text=True, timeout=120, check=False)
            return p.returncode, p.stdout, p.stderr
        except subprocess.TimeoutExpired:
            return 124, "", "HOST_TEST_TIMEOUT\n"


def process_request(request_file, result_file, work_directory=RUN_DIRECTORY):
    request = json.loads(request_file.read_text())
    if not valid_request(request):
        raise ValueError("Request schema rejected")
    if request_file.name != "run-" + str(request["run_id"]) + ".json":
        raise ValueError("Request filename mismatch")
    if result_file.exists():
        return None
    check_run_directory(work_directory)
    binary = DOWNLOADS / ("fizz-" + str(request["run_id"]) + "-" + NAME)
    if not binary.is_file():
        exit_code, stdout, stderr = 1, "", "STAGED_FILE_MISSING\n"
    else:
        try:
            exit_code, stdout, stderr = execute_verified(
                binary, request["sha256"], work_directory)
        except (OSError, ValueError) as exc:
            exit_code, stdout, stderr = 1, "", "HOST_EXECUTION_REJECTED " + str(exc)
    passed = (
        exit_code == 0
        and "FIZZ_RUNTIME_CAPABILITIES_COMPLETE" in stdout
        and "RUNTIME_UID=1000" in stdout
        and "RUNTIME_EUID=1000" in stdout
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


def once(spool=SPOOL, work_directory=RUN_DIRECTORY):
    requests = spool / "requests"
    results = spool / "results"
    if not requests.is_dir() or requests.is_symlink():
        print("FIZZ_NO_VALID_REQUEST_DIRECTORY")
        return 0
    for request in sorted(requests.iterdir()):
        if not REQUEST_FILE.fullmatch(request.name) or request.is_symlink():
            continue
        result = results / request.name
        if result.exists():
            continue
        try:
            response = process_request(request, result, work_directory)
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
    if not 10 <= args.interval <= 3600:
        parser.error("interval must be 10..3600 seconds")
    check_run_directory(RUN_DIRECTORY)
    with LOCK.open("a") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("FIZZ_HOST_WORKER_ALREADY_RUNNING")
            return
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
