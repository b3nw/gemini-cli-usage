import os
import sys
import json
import time
import subprocess
import select
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "src" / "usage_monitor.py"


def start_server(extra_env=None):
    env = os.environ.copy()
    # Ensure no OAuth creds by pointing HOME to a temp dir
    temp_home = ROOT / ".tmp_home"
    temp_home.mkdir(exist_ok=True)
    env["HOME"] = str(temp_home)
    # Simulate API key mode to verify fast-fail
    env.setdefault("GEMINI_API_KEY", "dummy-key")
    if extra_env:
        env.update(extra_env)
    proc = subprocess.Popen(
        [sys.executable, "-u", str(SCRIPT)],
        cwd=str(ROOT),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    return proc


def read_json_line(proc, timeout=2.0):
    """Read a single line of JSON from proc.stdout within timeout seconds."""
    fd = proc.stdout.fileno()
    end = time.time() + timeout
    buf = ""
    while time.time() < end:
        r, _, _ = select.select([fd], [], [], max(0, end - time.time()))
        if r:
            line = proc.stdout.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue
            # Assert stdout is JSON only
            obj = json.loads(line)
            return obj
    raise TimeoutError("Timed out waiting for JSON-RPC line on stdout")


def send_request(proc, obj):
    proc.stdin.write(json.dumps(obj) + "\n")
    proc.stdin.flush()


def test_initialize_and_tools_list_are_fast_and_flush():
    proc = start_server()
    try:
        # initialize
        t0 = time.time()
        send_request(proc, {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        resp = read_json_line(proc, timeout=2.0)
        t1 = time.time()
        assert resp.get("id") == 1
        assert "result" in resp
        # tools/list
        send_request(proc, {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        resp2 = read_json_line(proc, timeout=2.0)
        t2 = time.time()
        assert resp2.get("id") == 2
        tools = resp2.get("result", {}).get("tools", [])
        # response exists and is quick
        assert any(t.get("name") == "check_usage" for t in tools)
        assert (t2 - t1) < 1.5, "tools/list round trip took too long"
        # tools/call without OAuth should error quickly and exit after
        send_request(proc, {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "check_usage",
                "arguments": {"project_id": "dummy-project", "plan": "free"}
            }
        })
        resp3 = read_json_line(proc, timeout=2.0)
        assert resp3.get("id") == 3
        assert "error" in resp3, "Expected error when OAuth is absent"
        msg = resp3["error"].get("message", "")
        assert (
            "OAuth" in msg or "API key" in msg or "credentials" in msg
        ), f"Unexpected error message: {msg}"
        # Process should exit after one tools/call in non-interactive mode
        proc.wait(timeout=2.0)
        # stderr should contain observability logs
        stderr = proc.stderr.read()
        assert "Sent tools/list response" in stderr
    finally:
        try:
            proc.kill()
        except Exception:
            pass


def test_fast_fail_when_no_oauth_no_hang():
    # Explicitly ensure no GEMINI_API_KEY to cover alternate path
    env = os.environ.copy()
    # Ensure both key env vars are empty
    env["GEMINI_API_KEY"] = ""
    env["GOOGLE_API_KEY"] = ""
    proc = start_server(extra_env=env)
    try:
        send_request(proc, {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        _ = read_json_line(proc, timeout=2.0)
        send_request(proc, {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        _ = read_json_line(proc, timeout=2.0)
        send_request(proc, {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "check_usage",
                "arguments": {"project_id": "dummy-project", "plan": "free"}
            }
        })
        resp = read_json_line(proc, timeout=2.0)
        assert "error" in resp
        # Should exit promptly
        proc.wait(timeout=2.0)
    finally:
        try:
            proc.kill()
        except Exception:
            pass
