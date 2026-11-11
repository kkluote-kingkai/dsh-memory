#!/usr/bin/env python3
"""Lingshu (灵枢) auto-memory hooks for Devin CLI.

Subcommands:
  session-start  — inject recent-memory digest as additionalContext
  post-tool      — record per-session tool activity (stdin: hook payload)
  stop-check     — nudge once if the session mutated things but never archived
  post-compact   — remind to re-route memory after context compaction

Fails silently: hooks must never break or block a session on their own errors.
"""
import json
import os
import subprocess
import sys
import time

_here = os.path.dirname(os.path.abspath(__file__))
# devin/hooks/<this file> → repo root; override with LINGSHU_REPO when installed elsewhere
REPO = os.environ.get("LINGSHU_REPO") or os.path.normpath(os.path.join(_here, "..", ".."))
MCP_CONFIG = os.environ.get("DEVIN_MCP_CONFIG") or os.path.expanduser("~/.config/devin/mcp_config.json")
STATE_DIR = os.path.expanduser("~/.lingshu/state")
MUTATING_TOOLS = {"exec", "edit", "write", "apply_patch", "notebook_edit", "todo_write"}
MIN_MUTATIONS = 6


def _env_and_cmd():
    """Pull lingshu server env from the devin mcp config (avoids duplicating the token)."""
    try:
        cfg = json.load(open(MCP_CONFIG))
        srv = cfg["mcpServers"]["lingshu"]
        return srv["command"], srv["args"], {**os.environ, **srv.get("env", {})}
    except Exception:
        return None, None, None


def _rpc(lines, timeout=15):
    """One-shot stdio session against the md_cg server; returns parsed responses by id."""
    cmd, args, env = _env_and_cmd()
    if not cmd:
        return {}
    proc = subprocess.run(
        [cmd, *args], input="\n".join(lines), capture_output=True,
        text=True, timeout=timeout, env=env, cwd=REPO,
    )
    out = {}
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
            if "id" in msg:
                out[msg["id"]] = msg
        except Exception:
            continue
    return out


def _call(name, arguments, rid=2):
    msgs = [
        json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                    "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                               "clientInfo": {"name": "devin-hook", "version": "1.0"}}}),
        json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}),
        json.dumps({"jsonrpc": "2.0", "id": rid, "method": "tools/call",
                    "params": {"name": name, "arguments": arguments}}),
    ]
    resp = _rpc(msgs).get(rid, {})
    content = resp.get("result", {}).get("content", [])
    if content and "text" in content[0]:
        try:
            return json.loads(content[0]["text"])
        except Exception:
            return {"raw": content[0]["text"]}
    return None


def _context(text):
    return {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": text}}


def session_start():
    if not os.path.isdir(os.path.expanduser("~/.lingshu/cogmap")):
        return
    tl = _call("stg", {"op": "timeline", "limit": 8})
    items = (tl or {}).get("items") or []
    if not items:
        print(json.dumps(_context(
            "灵枢(lingshu)记忆服务已接入。近期无已归档记忆；"
            "非琐碎任务先 cg(op=route, intent=…) 查记忆，任务收尾按 CCG 六要素归档。")))
        return
    lines = []
    for it in items:
        if not isinstance(it, dict) or it.get("layer") == "rejected":
            continue
        try:
            ts = time.strftime("%m-%d %H:%M", time.localtime(float(it.get("start", 0))))
        except Exception:
            ts = ""
        prev = str(it.get("preview") or it.get("id") or "").split("\n")[0]
        prev = prev.removeprefix("# 功能名：").removeprefix("# ")[:100]
        lines.append(f"- [{ts}] {prev}")
        if len(lines) >= 8:
            break
    digest = "\n".join(lines)[:1800]
    print(json.dumps(_context(
        "灵枢(lingshu)记忆服务已接入。近期记忆时间线：\n" + digest +
        "\n非琐碎任务先 cg(op=route, intent=…) 查记忆；收尾按 CCG 六要素归档并读回确认。"),
        ensure_ascii=False))


def _state_file(session_id):
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in str(session_id))[:80]
    return os.path.join(STATE_DIR, f"{safe}.jsonl")


def post_tool():
    payload = json.loads(sys.stdin.read() or "{}")
    sid = payload.get("session_id")
    tool = payload.get("tool_name", "")
    if not sid:
        return
    mutating = tool in MUTATING_TOOLS
    cg_write = "lingshu" in tool and '"write"' in json.dumps(
        payload.get("tool_input", {}))
    if not (mutating or cg_write):
        return
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(_state_file(sid), "a") as f:
        f.write(json.dumps({"t": time.time(), "tool": tool,
                            "cg_write": cg_write}) + "\n")


def stop_check():
    payload = json.loads(sys.stdin.read() or "{}")
    if payload.get("stop_hook_active"):
        return  # already nudged this stop sequence — allow
    sid = payload.get("session_id")
    if not sid:
        return
    mutating = cg_writes = 0
    try:
        for line in open(_state_file(sid)):
            try:
                ev = json.loads(line)
            except Exception:
                continue
            mutating += ev["tool"] in MUTATING_TOOLS
            cg_writes += bool(ev.get("cg_write"))
    except OSError:
        return
    if mutating >= MIN_MUTATIONS and cg_writes == 0:
        print(json.dumps({
            "decision": "block",
            "reason": (
                "本会话有实质改动但未归档灵枢记忆。若产出值得长期保留"
                "（修复/设置/决策/经验），请按 CCG 六要素 cg(op=write) 归档并读回确认；"
                "若确无值得归档的内容，回复一句说明后直接结束。")}, ensure_ascii=False))


def post_compact():
    print(json.dumps({
        "hookSpecificOutput": {"hookEventName": "PostCompaction", "additionalContext":
            "上下文已压缩。若任务仍在进行，用 cg(op=route, intent=…) 重建记忆视野，"
            "再用 stg(op=timeline)/cg(op=recent) 找回近期状态。"}}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        {"session-start": session_start,
         "post-tool": post_tool,
         "stop-check": stop_check,
         "post-compact": post_compact}[sys.argv[1]]()
    except SystemExit:
        raise
    except Exception:
        pass  # hooks must never break a session
