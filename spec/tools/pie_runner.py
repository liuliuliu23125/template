#!/usr/bin/env python3
import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime
from pathlib import Path

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 12463
DEFAULT_HTTP_TIMEOUT = 30.0
FACE_MARKERS = ("人脸识别", "FaceRecognition", "face verification")
AUTOTEST_STATUS_RE = re.compile(
    r"AUTOTEST\|([0-9a-f]+)\|running=(true|false)\|total=(\d+)\|passed=(\d+)\|failed=(\d+)"
)
TEST_DONE_RE = re.compile(r"\[TestManager\] 测试完成:\s*(\d+)/(\d+)")
LOG_PATTERNS = {
    "lua_exception": re.compile(r"\[LuaException\]|\bLuaException:"),
    "lua_attempt": re.compile(r"attempt to (index|call|compare|perform arithmetic on|concatenate)"),
    "lua_runtime": re.compile(
        r"attempt to (index|call|compare|perform arithmetic on|concatenate)"
        r"|stack overflow|bad argument #\d+|snippet:\d+:"
        r"|\[LuaException\] lua_check_failed:"
        r"|LogScriptPlugin: Error: \[LuaException\]"
    ),
    "api_env": re.compile(r"\[UGCApiEnvCheck\] API 调用环境错误"),
    "pie_failed": re.compile(r"PIE debug failed|DS Failed|PIE 调试失败"),
    "test_failed": re.compile(r"\[TestManager DEBUG\].*passed=false"),
    "test_done": re.compile(r"\[TestManager\] 测试完成:\s*(\d+)/(\d+)"),
}
AUTOTEST_START = """
local run_id = "{run_id}"
local function emit(line)
    print(line)
    if ugcprint then ugcprint(line) end
end
local key = {player_key}
local pc = nil
if key and key > 0 then
    pc = UGCGameSystem.GetPlayerControllerByPlayerKey(key)
end
if not pc then
    local pcs = UGCGameSystem.GetAllPlayerController(true)
    if pcs then
        for _, candidate in ipairs(pcs) do
            pc = candidate
            break
        end
    end
end
if not pc then
    emit("AUTOTEST_NO_PC|" .. run_id)
    return "AUTOTEST_NO_PC"
end
if not Global_AutoTestKit then
    emit("AUTOTEST_NO_KIT|" .. run_id)
    return "AUTOTEST_NO_KIT"
end
local ok, started
if {all_suites} then
    ok, started = pcall(Global_AutoTestKit.RunAll, pc)
else
    ok, started = pcall(Global_AutoTestKit.RunSuite, pc, {suite})
end
if not ok then
    emit("AUTOTEST_ERROR|" .. run_id .. "|" .. tostring(started))
    return "AUTOTEST_ERROR"
end
if not started then
    emit("AUTOTEST_NOT_STARTED|" .. run_id)
    return "AUTOTEST_NOT_STARTED"
end
emit("AUTOTEST_STARTED|" .. run_id)
return "AUTOTEST_STARTED"
"""
AUTOTEST_STATUS = """
local run_id = "{run_id}"
local function emit(line)
    print(line)
    if ugcprint then ugcprint(line) end
end
local tm = package.loaded["Script.Core.AutoTestKit.TestRunner.TestManager"]
if not tm then
    emit("AUTOTEST_NO_TM|" .. run_id)
    return "AUTOTEST_NO_TM"
end
local total, passed, failed = tm.GetSummary()
local running = tm.IsQueueRunning()
emit(string.format("AUTOTEST|%s|running=%s|total=%d|passed=%d|failed=%d", run_id, tostring(running), total, passed, failed))
return "AUTOTEST_STATUS"
"""


class McpError(RuntimeError):
    pass


class McpClient:
    def __init__(self, host, port, http_timeout=DEFAULT_HTTP_TIMEOUT):
        self.url = f"http://{host}:{port}/mcp"
        self.http_timeout = http_timeout
        self.session_id = None
        self.request_id = 0

    def _post(self, payload):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        request = urllib.request.Request(self.url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=self.http_timeout) as response:
                session_id = response.headers.get("Mcp-Session-Id")
                if session_id:
                    self.session_id = session_id
                body = response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise McpError(f"HTTP {exc.code}: {body[:500]}") from exc
        except urllib.error.URLError as exc:
            raise McpError(f"cannot reach {self.url}: {exc.reason}") from exc
        if not body.strip():
            return None
        stripped = body.lstrip()
        if stripped.startswith("event:") or stripped.startswith("data:"):
            return self._parse_sse(body)
        return json.loads(body)

    @staticmethod
    def _parse_sse(body):
        events = []
        for block in body.replace("\r\n", "\n").split("\n\n"):
            lines = [line[5:].lstrip() for line in block.splitlines() if line.startswith("data:")]
            if not lines:
                continue
            try:
                events.append(json.loads("\n".join(lines)))
            except json.JSONDecodeError:
                continue
        return events[-1] if events else None

    def initialize(self):
        response = self._post(
            {
                "jsonrpc": "2.0",
                "id": 0,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "pie-runner", "version": "1.0"},
                },
            }
        )
        if not response or "result" not in response:
            raise McpError(f"initialize failed: {json.dumps(response, ensure_ascii=False)[:500]}")
        self._post({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
        return response["result"]

    def call_tool(self, name, arguments):
        self.request_id += 1
        response = self._post(
            {
                "jsonrpc": "2.0",
                "id": self.request_id,
                "method": "tools/call",
                "params": {"name": name, "arguments": arguments},
            }
        )
        if response is None:
            raise McpError(f"{name} returned an empty response")
        if "error" in response:
            raise McpError(json.dumps(response["error"], ensure_ascii=False))
        result = response.get("result") or {}
        content = result.get("content") or []
        text = ""
        if content and isinstance(content, list):
            text = content[0].get("text", "")
        if not text:
            return {}
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"raw": text}


def editor_root():
    return Path(__file__).resolve().parents[2]


def read_mcp_config(root):
    path = root / "ShadowTrackerExtra/Saved/Config/WindowsUGCEditor/UGCSettings.ini"
    host = DEFAULT_HOST
    port = DEFAULT_PORT
    if not path.is_file():
        return host, port, path
    section = None
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            section = stripped[1:-1].strip()
            continue
        if section != "AskQMCPServer" or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip().lower()
        value = value.strip()
        if key == "host" and value:
            host = value
        elif key == "port":
            try:
                port = int(value)
            except ValueError:
                pass
    return host, port, path


def payload_text(payload):
    return json.dumps(payload, ensure_ascii=False)


def alert_state(payload):
    return payload.get("alert") or {}


def has_face_gate(payload):
    text = payload_text(payload)
    return any(marker in text for marker in FACE_MARKERS)


def has_blocking_dialog(payload):
    alert = alert_state(payload)
    return bool(
        alert.get("present")
        or alert.get("blocking")
        or alert.get("dialogs")
        or payload.get("status") == "needs_confirmation"
    )


def session_active(payload):
    data = payload.get("data") or {}
    session = data.get("session") or {}
    players = data.get("players") or []
    return session.get("state") == "active" and any(
        player.get("state") == "available" for player in players
    )


def session_state(payload):
    data = payload.get("data") or {}
    return (data.get("session") or {}).get("state")


def collect_operation(client, payload, timeout):
    deadline = time.time() + timeout
    while payload.get("status") == "pending" and time.time() < deadline:
        next_call = payload.get("next") or {}
        arguments = dict(next_call.get("arguments") or {})
        if not arguments.get("operation_id"):
            break
        remaining = max(1, int((deadline - time.time()) * 1000))
        arguments["timeout_ms"] = min(15000, remaining)
        payload = client.call_tool("ue_pie", arguments)
        if payload.get("status") != "pending":
            break
    return payload


def pie_status(client):
    return client.call_tool("ue_pie", {"action": "status", "timeout_ms": 3000})


def log_offset(path):
    try:
        return path.stat().st_size
    except OSError:
        return 0


def log_contains(path, offset, markers):
    try:
        size = path.stat().st_size
        if offset > size:
            offset = 0
        with path.open("rb") as handle:
            handle.seek(offset)
            text = handle.read(8_000_000).decode("utf-8", errors="ignore")
    except OSError:
        return False
    return any(marker in text for marker in markers)


def wait_for_active(client, timeout, editor_log, offset):
    deadline = time.time() + timeout
    payload = pie_status(client)
    while time.time() < deadline:
        if has_face_gate(payload) or log_contains(editor_log, offset, FACE_MARKERS):
            return payload, "face_verification"
        if has_blocking_dialog(payload):
            return payload, "dialog"
        if session_active(payload):
            return payload, None
        if session_state(payload) in ("idle", "stopped"):
            return payload, "not_running"
        time.sleep(2)
        payload = pie_status(client)
    return payload, "timeout"


def start_pie(client, start_arguments, timeout, editor_log, offset):
    arguments = dict(start_arguments)
    arguments["timeout_ms"] = 0
    payload = client.call_tool("ue_pie", arguments)
    deadline = time.time() + timeout
    while time.time() < deadline:
        if has_face_gate(payload) or log_contains(editor_log, offset, FACE_MARKERS):
            return payload, "face_verification"
        if has_blocking_dialog(payload):
            return payload, "dialog"
        if session_active(payload):
            return payload, None
        next_call = payload.get("next") or {}
        if next_call.get("arguments", {}).get("operation_id"):
            arguments = dict(next_call.get("arguments") or {})
            remaining = max(1, int((deadline - time.time()) * 1000))
            arguments["timeout_ms"] = min(15000, remaining)
            payload = client.call_tool("ue_pie", arguments)
        else:
            time.sleep(2)
            payload = pie_status(client)
    return payload, "timeout"


def stop_pie(client, timeout):
    payload = client.call_tool("ue_pie", {"action": "stop", "timeout_ms": 0})
    return collect_operation(client, payload, timeout)


def lua_call(client, target, code, player_key=None, timeout=45):
    arguments = {"action": "doluastring", "target": target, "code": code}
    if player_key is not None:
        arguments["player_key"] = player_key
    payload = client.call_tool("ue_pie", arguments)
    return collect_operation(client, payload, timeout)


def ds_log_base(root, client_log_path):
    if client_log_path:
        parts = Path(client_log_path).parts
        if "Clientlog" in parts:
            index = parts.index("Clientlog")
            return Path(*parts[:index]) / "DSlog/FullLog"
    logs_root = root / "ShadowTrackerExtra/Saved/Logs"
    candidates = [path for path in logs_root.glob("*/DSlog/FullLog") if path.is_dir()]
    candidates.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def find_ds_log(root, client_log_path, started_at):
    debug_id = None
    if client_log_path:
        match = re.search(r"_client__([A-Za-z0-9]+)_p\d+\.log$", Path(client_log_path).name)
        if match:
            debug_id = match.group(1)
    base = ds_log_base(root, client_log_path)
    if base is None:
        return None
    candidates = []
    if debug_id:
        candidates.extend(base.glob(f"*_ds__{debug_id}_realtime.log"))
    if not candidates:
        candidates.extend(base.glob("*_ds_*_realtime.log"))
    candidates = [
        path
        for path in candidates
        if path.is_file() and path.stat().st_mtime >= started_at - 5
    ]
    candidates.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def read_log_from(path, offset):
    try:
        size = path.stat().st_size
        if offset > size:
            offset = 0
        with path.open("rb") as handle:
            handle.seek(offset)
            return handle.read(4_000_000).decode("utf-8", errors="ignore")
    except OSError:
        return ""


def render_template(template, values):
    for key, value in values.items():
        template = template.replace("{" + key + "}", str(value))
    return template


def build_autotest_start(player_key, suite, all_suites, run_id, template=AUTOTEST_START):
    suite_literal = json.dumps(suite or "", ensure_ascii=False)
    return render_template(
        template,
        {
            "player_key": int(player_key or 0),
            "all_suites": "true" if all_suites else "false",
            "suite": suite_literal,
            "run_id": run_id,
        },
    )


def run_tests(
    client,
    target,
    player_key,
    suite,
    all_suites,
    timeout,
    poll,
    root,
    client_log_path,
    started_at,
    start_template=AUTOTEST_START,
    status_template=AUTOTEST_STATUS,
):
    run_id = uuid.uuid4().hex[:8]
    code = build_autotest_start(player_key, suite, all_suites, run_id, start_template)
    start = lua_call(client, target, code, player_key if target == "client" else None)
    start_text = payload_text(start)
    if "snippet:" in start_text or "Lua error" in start_text:
        return {"ok": False, "reason": "lua_error", "run_id": run_id, "start": start}
    log_path = None
    if target == "client" and client_log_path:
        log_path = Path(client_log_path)
    if log_path is None or not log_path.is_file():
        log_path = find_ds_log(root, client_log_path, started_at)
    if log_path is None:
        return {"ok": False, "reason": "log_not_found", "run_id": run_id, "start": start}
    offset = log_offset(log_path)
    start_deadline = time.time() + 20
    start_seen = False
    while time.time() < start_deadline:
        content = read_log_from(log_path, offset)
        if f"AUTOTEST_STARTED|{run_id}" in content:
            start_seen = True
            break
        for reason in ("NO_PC", "NO_KIT", "NOT_STARTED", "ERROR"):
            if f"AUTOTEST_{reason}|{run_id}" in content:
                return {
                    "ok": False,
                    "reason": reason.lower(),
                    "run_id": run_id,
                    "start": start,
                    "log": str(log_path),
                }
        time.sleep(1)
    deadline = time.time() + timeout
    polls = []
    summary = None
    content = ""
    while time.time() < deadline:
        lua_call(
            client,
            target,
            render_template(status_template, {"run_id": run_id}),
            player_key if target == "client" else None,
        )
        content = read_log_from(log_path, offset)
        matches = [match for match in AUTOTEST_STATUS_RE.findall(content) if match[0] == run_id]
        if matches:
            current = matches[-1]
            summary = {
                "running": current[1] == "true",
                "total": int(current[2]),
                "passed": int(current[3]),
                "failed": int(current[4]),
            }
            polls.append(summary)
            if not summary["running"] and summary["total"] > 0:
                break
        else:
            done = TEST_DONE_RE.findall(content)
            if done:
                total = int(done[-1][1])
                passed = int(done[-1][0])
                summary = {
                    "running": False,
                    "total": total,
                    "passed": passed,
                    "failed": total - passed,
                }
                polls.append(summary)
                break
        if f"AUTOTEST_NO_TM|{run_id}" in content:
            return {
                "ok": False,
                "reason": "test_manager_not_loaded",
                "run_id": run_id,
                "start": start,
                "log": str(log_path),
                "polls": polls,
            }
        time.sleep(poll)
    if summary is None:
        return {
            "ok": False,
            "reason": "test_timeout",
            "run_id": run_id,
            "start": start,
            "log": str(log_path),
            "log_offset": offset,
            "polls": polls,
            "start_seen": start_seen,
            "log_tail": content[-8000:],
        }
    failed_cases = re.findall(r"\[TestManager DEBUG\].*passed=false.*", content)
    return {
        "ok": summary["failed"] == 0 and summary["total"] > 0 and not summary["running"],
        "reason": "tests_failed" if summary["failed"] else None,
        "run_id": run_id,
        "start": start,
        "summary": summary,
        "polls": polls,
        "failed_cases": failed_cases[-20:],
        "log": str(log_path),
        "log_offset": offset,
        "start_seen": start_seen,
    }


def scan_log(path, limit=2_000_000, offset=None):
    result = {name: [] for name in LOG_PATTERNS}
    if not path.is_file():
        return result
    try:
        with path.open("rb") as handle:
            if offset is not None:
                size = path.stat().st_size
                if offset > size:
                    offset = 0
                handle.seek(offset)
                data = handle.read(8_000_000)
            else:
                handle.seek(0, 2)
                size = handle.tell()
                handle.seek(max(0, size - limit))
                data = handle.read()
    except OSError:
        return result
    text = data.decode("utf-8", errors="ignore")
    for line in text.splitlines():
        for name, pattern in LOG_PATTERNS.items():
            if pattern.search(line) and len(result[name]) < 50:
                result[name].append(line.strip()[:300])
    return result


def capture_window(path):
    try:
        from PIL import ImageGrab
    except ImportError:
        return None
    import ctypes
    from ctypes import wintypes

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        pass

    user32 = ctypes.windll.user32
    matches = []
    enum_proc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)

    def callback(hwnd, _):
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        title = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, title, length + 1)
        if "PIEPlayer" not in title.value:
            return True
        rect = wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        matches.append((hwnd, title.value, rect))
        return False

    user32.EnumWindows(enum_proc(callback), 0)
    if not matches:
        return None
    hwnd, title, rect = matches[0]
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.5)
    image = ImageGrab.grab(
        bbox=(rect.left, rect.top, rect.right, rect.bottom),
        all_screens=True,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)
    return {
        "path": str(path),
        "title": title,
        "rect": [rect.left, rect.top, rect.right, rect.bottom],
    }


def write_report(report_dir, report):
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / "report.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def default_report_dir(root):
    return root / "spec" / "pie-runs" / datetime.now().strftime("%Y%m%d-%H%M%S")


def emit(report, path=None):
    if path:
        report["report_path"] = str(path)
    print(json.dumps(report, ensure_ascii=False, indent=2))


def build_start_arguments(args):
    arguments = {
        "action": "start",
        "team_count": args.team_count,
        "players_per_team": args.players_per_team,
        "spectators_per_team": args.spectators_per_team,
        "submode_id": args.submode_id,
    }
    if args.simulation_platform:
        arguments["simulation_platform"] = args.simulation_platform
    return arguments


def run_status(args, root, client):
    status = pie_status(client)
    report = {
        "started_at": datetime.now().isoformat(timespec="seconds"),
        "editor_root": str(root),
        "mcp": {"url": client.url, "session_id": client.session_id},
        "result": "ok",
        "status": status,
        "session_state": session_state(status),
    }
    path = write_report(Path(args.report_dir) if args.report_dir else default_report_dir(root), report)
    emit(report, path)
    return 0


def run_stop(args, root, client):
    stopped = stop_pie(client, args.stop_timeout)
    report = {
        "started_at": datetime.now().isoformat(timespec="seconds"),
        "editor_root": str(root),
        "mcp": {"url": client.url, "session_id": client.session_id},
        "result": "ok",
        "stop": stopped,
        "session_state": session_state(stopped),
    }
    path = write_report(Path(args.report_dir) if args.report_dir else default_report_dir(root), report)
    emit(report, path)
    return 0


def run_pie(args, root, client):
    report_dir = Path(args.report_dir) if args.report_dir else default_report_dir(root)
    editor_log = root / "ShadowTrackerExtra/Saved/Logs/ShadowTrackerExtra.log"
    report = {
        "started_at": datetime.now().isoformat(timespec="seconds"),
        "editor_root": str(root),
        "mcp": {"url": client.url, "session_id": client.session_id},
        "options": {
            "suite": args.suite,
            "all_suites": args.all_suites,
            "test_target": args.test_target,
            "keep_running": args.keep_running,
            "resume": args.resume,
        },
        "events": [],
        "result": "error",
    }

    started_epoch = time.time()
    initial = pie_status(client)
    editor_log = Path((initial.get("data") or {}).get("editor", {}).get("log_path") or editor_log)
    offset = log_offset(editor_log)

    started = False
    gate = None
    try:
        if args.resume:
            start_payload, gate = wait_for_active(client, args.timeout, editor_log, offset)
        else:
            start_payload, gate = start_pie(
                client, build_start_arguments(args), args.timeout, editor_log, offset
            )
        started = True
        report["start"] = start_payload
        report["events"].append({"step": "start", "status": start_payload.get("status"), "gate": gate})

        if gate:
            report["result"] = "blocked" if gate in ("face_verification", "dialog") else "timeout"
            report["gate"] = {
                "kind": gate,
                "alert": alert_state(start_payload),
                "message": start_payload.get("message"),
            }
            if not args.no_screenshot:
                shot = capture_window(report_dir / "blocked.png")
                if shot:
                    report["screenshot"] = shot
            if gate == "face_verification":
                report["guidance"] = "PIE 客户端出现人脸识别，请账号本人扫码并点完成后，用 run --resume 继续。"
            else:
                report["guidance"] = "编辑器有阻塞对话框，请人工处理后用 run --resume 继续。"
            path = write_report(report_dir, report)
            emit(report, path)
            return 3 if gate in ("face_verification", "dialog") else 5

        status = pie_status(client)
        report["status"] = status
        data = status.get("data") or {}
        players = data.get("players") or []
        player_key = args.player_key
        if not player_key and players:
            player_key = players[0].get("player_key")
        client_log_path = players[0].get("log_path") if players else None
        client_log_offset = log_offset(Path(client_log_path)) if client_log_path else 0
        report["player_key"] = player_key

        if not args.no_screenshot:
            shot = capture_window(report_dir / "screenshot.png")
            if shot:
                report["screenshot"] = shot

        start_template = AUTOTEST_START
        status_template = AUTOTEST_STATUS
        if args.test_start_lua:
            start_template = Path(args.test_start_lua).read_text(encoding="utf-8")
        if args.test_status_lua:
            status_template = Path(args.test_status_lua).read_text(encoding="utf-8")

        all_suites = args.all_suites or (args.suite or "").lower() == "all"
        suite = None if all_suites else args.suite
        tests_requested = not args.no_tests and bool(suite or all_suites)
        if tests_requested:
            test_result = run_tests(
                client,
                args.test_target,
                player_key,
                suite,
                all_suites,
                args.test_timeout,
                args.poll,
                root,
                client_log_path,
                started_epoch,
                start_template,
                status_template,
            )
            report["tests"] = test_result
            report["events"].append(
                {
                    "step": "tests",
                    "ok": test_result.get("ok"),
                    "reason": test_result.get("reason"),
                    "summary": test_result.get("summary"),
                }
            )
        else:
            report["tests"] = {"requested": False}

        client_logs = []
        startup_logs = []
        for player in players:
            log_path = player.get("log_path")
            if not log_path:
                continue
            path = Path(log_path)
            client_logs.append(scan_log(path, offset=client_log_offset))
            startup_logs.append(scan_log(path, offset=0))
        report["client_logs"] = client_logs
        report["editor_log"] = scan_log(editor_log, offset=offset)
        tests_result = report.get("tests") or {}
        ds_log = find_ds_log(root, client_log_path, started_epoch)
        ds_scan = {}
        ds_tested = "log_offset" in tests_result
        if ds_log:
            ds_offset = tests_result.get("log_offset")
            ds_scan = scan_log(ds_log, offset=ds_offset) if ds_offset is not None else scan_log(ds_log)
            report["ds_log"] = {"path": str(ds_log), "scan": ds_scan}

        warnings = {}
        if ds_scan.get("api_env"):
            warnings["ds_api_env"] = ds_scan.get("api_env")
        startup_lua = []
        for log in startup_logs:
            startup_lua.extend(log.get("lua_exception") or [])
            startup_lua.extend(log.get("lua_attempt") or [])
        if startup_lua:
            warnings["client_startup_lua"] = startup_lua[:50]
        client_lua_warnings = []
        for log in client_logs:
            for line in log.get("lua_exception") or []:
                if not LOG_PATTERNS["lua_runtime"].search(line):
                    client_lua_warnings.append(line)
        if client_lua_warnings:
            warnings["client_lua_exception"] = client_lua_warnings[:50]
        if warnings:
            report["warnings"] = warnings

        def scan_failed(scan):
            return bool(
                scan.get("lua_runtime")
                or scan.get("api_env")
                or scan.get("pie_failed")
                or scan.get("test_failed")
            )

        test_failed = tests_result.get("ok") is False
        log_failed = bool(
            scan_failed(report["editor_log"])
            or any(scan_failed(log) for log in client_logs)
            or (ds_tested and scan_failed(ds_scan))
        )
        if args.strict_startup and startup_lua:
            log_failed = True
        if test_failed or log_failed:
            report["result"] = "failed"
        elif not tests_requested:
            report["result"] = "smoke_passed"
        else:
            report["result"] = "passed"
    finally:
        if started and not args.keep_running and not gate:
            stopped = stop_pie(client, args.stop_timeout)
            report["stop"] = stopped
            report["events"].append({"step": "stop", "state": session_state(stopped)})
        report["finished_at"] = datetime.now().isoformat(timespec="seconds")
        path = write_report(report_dir, report)

    emit(report, path)
    if report["result"] in ("passed", "smoke_passed"):
        return 0
    if report["result"] == "failed":
        return 4
    return 1


BENIGN_LOG_SAMPLE = """\
[2026.11.26-21.31.05:211][282][31340]LogScriptPlugin: Warning: [LuaException] FetchUStructFromTable: Fetch UStruct[/Script/ShadowTrackerExtra.UGCCameraOffsetDataSimpleEntry] PropertyCount[11] too much ( > 10);:
IsGameThread=1, IsLuaCheckThread=1
>> LuaException Lua Stack: (可控制台关闭: lua.EnableLuaStack 0)
stack traceback:
	[C]: in method 'AddCameraOffsetDataSimpleEntry'
	ugc/UGCGame/GamePart/TopDown/BP_TopDown_PlayerComponent.lua:201: in local 'f'
[2026.11.26-21.30.38:214][  0][31340]LogNula: LuaLog: ----------UGCSingleDownloader:StopAllDownloading----traceback = stack traceback:
	client/logic/ugc/logic_ugc_single_download.lua:646: in method 'StopAllDownloading'
	client/umg/bp_global.lua:740: in function <client/umg/bp_global.lua:657>
[2026.11.26-21.31.01:274][281][31340]LogScriptPlugin: Warning: [LuaException] LuaCacheConflict: class_export_index function cache conflict: Func=[ReceiveBeginPlay]: ud_object[BP_BackpackUIComponentV2_C /Game/UGC/UGCGame/GamePart/BackpackV2/BP_BackpackUIComponentV2.Default__BP_BackpackUIComponentV2_C @0x00000001eda34180], automatically use cache in self instead of parent
[2026.11.26-21.31.00:076][281][31340]LogScriptPlugin: Warning: [LuaException] OperationStatistic: LuaBind Function has reference Params: /Script/ShadowTrackerExtra.VehicleControlPanelUI:UpdateGUIVehicle2HpNativeEvent.MaintenanceVehicleShow;:
[2026.11.26-20.55:45][  0][  1]LogNula: LuaLog: LuaExceptions.ReportFileMsgToServer /Game/Example MissingFile
"""

RUNTIME_LOG_SAMPLE = """\
[2026.11.24-21.12.36:388][24249][30136]LogScriptPlugin: Warning: [LuaException] lua_check_failed: stack overflow:
IsGameThread=1, IsLuaCheckThread=1
>> LuaException Lua Stack: (可控制台关闭: lua.EnableLuaStack 0)
stack traceback:
	[C]: in field '?'
	ugc/ugc_env.lua:12: in function <ugc/ugc_env.lua:11>
	ugc/UGCAPI/UGCItemSystemV2.lua:1156: in field 'GetEquipSlotEnable'
	(...tail calls...)
"""

PROJECT_FAILURE_SAMPLE = """\
[2026.11.26-20.56.07:284][  0][ 29]LogUGCServer: [TagLog] [Core_Registry] Tick 失败，已停用: Script.Core.TipCore.Global_TipSystem | ugc/UGCAPI/UGCWidgetManagerSystem.lua:564: attempt to index a nil value (global 'PopUpNoticeUI')
"""


def run_self_test(root):
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        benign_log = base / "benign.log"
        benign_log.write_text(BENIGN_LOG_SAMPLE, encoding="utf-8")
        benign = scan_log(benign_log)
        runtime_log = base / "runtime.log"
        runtime_log.write_text(RUNTIME_LOG_SAMPLE, encoding="utf-8")
        runtime = scan_log(runtime_log)
        project_log = base / "project.log"
        project_log.write_text(PROJECT_FAILURE_SAMPLE, encoding="utf-8")
        project = scan_log(project_log)

        benign_ok = (
            bool(benign["lua_exception"])
            and not benign["lua_runtime"]
            and not benign["lua_attempt"]
        )
        runtime_ok = (
            bool(runtime["lua_runtime"])
            and any("lua_check_failed" in line for line in runtime["lua_runtime"])
            and not any("LuaExceptions." in line for line in runtime["lua_runtime"])
        )
        project_ok = bool(project["lua_attempt"]) and bool(project["lua_runtime"])

        project_dir = base / "ShadowTrackerExtra/Saved/Logs/Alpha"
        client_dir = project_dir / "Clientlog/FullLog"
        ds_dir = project_dir / "DSlog/FullLog"
        client_dir.mkdir(parents=True)
        ds_dir.mkdir(parents=True)
        client_log = client_dir / "2026.11.26-00.00.00_client__abc123_p10001.log"
        ds_log = ds_dir / "2026.11.26-00.00.00_ds__abc123_realtime.log"
        client_log.write_text("", encoding="utf-8")
        ds_log.write_text("", encoding="utf-8")
        found = find_ds_log(base, str(client_log), time.time() - 10)
        path_ok = found == ds_log
        passed = benign_ok and runtime_ok and project_ok and path_ok
        print(
            json.dumps(
                {
                    "result": "passed" if passed else "failed",
                    "benign_no_block": benign_ok,
                    "runtime_blocks": runtime_ok,
                    "project_failure_blocks": project_ok,
                    "ds_log_derivation": path_ok,
                    "ds_log": str(found),
                    "benign_scan": benign,
                    "runtime_scan": runtime,
                    "project_scan": project,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0 if passed else 1


def build_parser():
    parser = argparse.ArgumentParser(prog="pie_runner")
    parser.add_argument("--host")
    parser.add_argument("--port", type=int)
    parser.add_argument("--http-timeout", type=float, default=DEFAULT_HTTP_TIMEOUT)
    parser.add_argument("--report-dir")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("self-test")

    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("--report-dir", default=argparse.SUPPRESS)

    stop_parser = subparsers.add_parser("stop")
    stop_parser.add_argument("--stop-timeout", type=float, default=60)
    stop_parser.add_argument("--report-dir", default=argparse.SUPPRESS)

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--report-dir", default=argparse.SUPPRESS)
    run_parser.add_argument("--timeout", type=float, default=300)
    run_parser.add_argument("--stop-timeout", type=float, default=60)
    run_parser.add_argument("--poll", type=float, default=5)
    run_parser.add_argument("--team-count", type=int, default=1)
    run_parser.add_argument("--players-per-team", type=int, default=1)
    run_parser.add_argument("--spectators-per-team", type=int, default=0)
    run_parser.add_argument("--submode-id", type=int, default=0)
    run_parser.add_argument("--simulation-platform", choices=("mobile", "pchd"))
    run_parser.add_argument("--player-key", type=int)
    run_parser.add_argument("--suite")
    run_parser.add_argument("--all-suites", action="store_true")
    run_parser.add_argument("--test-target", choices=("ds", "client"), default="ds")
    run_parser.add_argument("--test-timeout", type=float, default=600)
    run_parser.add_argument("--test-start-lua")
    run_parser.add_argument("--test-status-lua")
    run_parser.add_argument("--strict-startup", action="store_true")
    run_parser.add_argument("--no-tests", action="store_true")
    run_parser.add_argument("--keep-running", action="store_true")
    run_parser.add_argument("--resume", action="store_true")
    run_parser.add_argument("--no-screenshot", action="store_true")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    root = editor_root()
    if args.command == "self-test":
        return run_self_test(root)
    host, port, config_path = read_mcp_config(root)
    if args.host:
        host = args.host
    if args.port:
        port = args.port
    client = McpClient(host, port, args.http_timeout)
    try:
        info = client.initialize()
    except (McpError, json.JSONDecodeError) as exc:
        report = {
            "started_at": datetime.now().isoformat(timespec="seconds"),
            "editor_root": str(root),
            "mcp": {"url": client.url, "config": str(config_path)},
            "result": "mcp_unavailable",
            "error": str(exc),
            "guidance": "确认编辑器已启动、[AskQMCPServer] bAutoStart=True；或在 窗口→开发者工具→命令行→MCP Server 点 Start Server。",
        }
        emit(report)
        return 2
    try:
        if args.command == "status":
            return run_status(args, root, client)
        if args.command == "stop":
            return run_stop(args, root, client)
        return run_pie(args, root, client)
    except McpError as exc:
        report = {
            "started_at": datetime.now().isoformat(timespec="seconds"),
            "editor_root": str(root),
            "mcp": {"url": client.url, "session_id": client.session_id, "server": info.get("serverInfo")},
            "result": "error",
            "error": str(exc),
        }
        emit(report)
        return 1


if __name__ == "__main__":
    sys.exit(main())
