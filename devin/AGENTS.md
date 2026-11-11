# Global Rules

## Lingshu long-term memory (灵枢 · mdcg)

A persistent memory store is available via the `lingshu` MCP server
(`python -m md_cg.mcp_server`, tools `cg` / `stg` / `mdcg_recall` …).
Memory lives as plain-md cards under `~/.lingshu/cogmap` and survives across
sessions. If the server is not connected, skip this section silently.

### Session start — route first
- For any non-trivial task (multi-step, code changes, research), call
  `cg(op=route, intent="<one-line task intent>")` BEFORE acting.
- If it returns relevant knowledge/discipline, follow it and mention the hit.
- Skip for small talk and trivial one-liners.

### Task end — archive the core (required)
Archiving is part of finishing. A task that made real changes without an
archive (or an explicit "nothing worth keeping" statement) is INCOMPLETE.
When a task produces a durable result (fix, setup, decision, learned fact):
1. Distill ONLY the core: what changed / why / where / how verified.
   Never archive process noise (trial-and-error, debugging steps, chit-chat).
2. Write with `cg(op=write, layer="contextual", content_kind="text", …)`.
   `text` content MUST be a CCG six-element card — six lines, each starting
   with its header, all six required or the write gate REJECTs:

   ```
   # 功能名：<feature name>
   # 生效条件：<when it applies>
   # 子功能：<what it does>
   # 执行：<how to do it>
   # 验证方式：<how verified>
   # 不适用条件：<when it does not apply>
   ```

3. Success means `committed: true` in the response — nothing else counts.
4. Read back once (`cg(op=read, query=…)`) to confirm it is retrievable.

### Recall mid-task
- `cg(op=read, query=…)` — search memory; `mdcg_recall` — packed recall;
  `stg(op=timeline)` — recent events timeline; `cg(op=recent)` — recent window.

### Verdict semantics (do not fight the gate)
- `committed:false` + `moved_to:"review_queue"` / `DEFER` → normal, do NOT
  retry; the item awaits adjudication.
- `REJECT` with missing CCG elements → fix the missing lines and rewrite as a
  NEW entry (the rejected copy stays in negative memory).
- `REJECT` on policy violation → content should not be stored; do not retry.

### Limits on this host
- No cross-session isolation (DSH-only feature): memories from all sessions
  share one graph; keep `summary`/`tags` descriptive for retrieval.
- Write token = recorder role: contextual/knowledge layers OK;
  self/anchor layer writes are out of scope — do not attempt.
