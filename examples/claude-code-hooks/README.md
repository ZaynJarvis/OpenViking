# Claude Code × OpenViking Memory Hooks

Auto-extract memories from [Claude Code](https://docs.anthropic.com/en/docs/claude-code) sessions into OpenViking using [Claude Code hooks](https://docs.anthropic.com/en/docs/claude-code/hooks).

## How It Works

Three hooks capture conversation transcripts at strategic lifecycle points and pipe them into OpenViking's memory system:

| Hook | Trigger | Why |
|------|---------|-----|
| `SubagentStop` | Subagent finishes | Subagent transcripts are complete and self-contained |
| `PreCompact` | Before context compaction | Last chance to save details before they're summarized away |
| `SessionEnd` | Session terminates | Full conversation is available for structured archival |

```
Claude Code Session
       │
       ├── SubagentStop ──→ ov add-memory (one-shot)
       │
       ├── PreCompact ────→ ov add-memory (one-shot)
       │
       └── SessionEnd ────→ ov session new → add-message × N → commit
```

## Prerequisites

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) installed
- [OpenViking CLI](../../README.md) configured (`~/.openviking/ovcli.conf`)
- `jq` installed (`brew install jq` / `apt install jq`)

## Setup

### 1. Copy hooks to Claude Code hooks directory

```bash
mkdir -p ~/.claude/hooks
cp hooks/*.sh ~/.claude/hooks/
chmod +x ~/.claude/hooks/*.sh
```

### 2. Register hooks in Claude Code settings

Add the following to `~/.claude/settings.json` (create if it doesn't exist):

```json
{
  "hooks": {
    "SubagentStop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "$HOME/.claude/hooks/ov-memory-subagent-stop.sh",
            "async": true
          }
        ]
      }
    ],
    "PreCompact": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "$HOME/.claude/hooks/ov-memory-pre-compact.sh",
            "async": true
          }
        ]
      }
    ],
    "SessionEnd": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "$HOME/.claude/hooks/ov-memory-session-end.sh",
            "async": true
          }
        ]
      }
    ]
  }
}
```

> **Note:** All hooks use `"async": true` so they don't block Claude's responses.

### 3. Verify

```bash
# Start Claude Code and check hooks are loaded
claude
/hooks
```

## Hook Details

### Transcript Format

Claude Code transcripts are JSONL files. Each line:

```json
{
  "type": "user",
  "message": {
    "role": "user",
    "content": [{"type": "text", "text": "actual message"}]
  }
}
```

All three hooks use the same jq pattern to extract user/assistant text turns:

```bash
jq -sc '
  map(select(.type == "user" or .type == "assistant"))
  | map({
      role: .message.role,
      content: (
        .message.content
        | if type == "string" then .
          elif type == "array" then
            (map(select(.type == "text") | .text) | join("\n"))
          else "" end
      )
    })
  | map(select(.content != "" and .content != null))
'
```

### SubagentStop & PreCompact

Use `ov add-memory` for one-shot memory extraction — creates a session, adds messages, commits, and extracts memories in a single call.

### SessionEnd

Uses the full session workflow for structured archival:

```bash
ov session new              # create session
ov session add-message ...  # add each message
ov session commit           # archive + extract memories
```

This gives OpenViking more context for richer memory extraction.

## Logs

All hooks append to `/tmp/ov-hooks.log`:

```
[2026-02-22 10:00:00] SubagentStop/memory: saved 12 msgs to ov
[2026-02-22 10:05:00] PreCompact/memory: snapshotted 34 msgs before auto compaction
[2026-02-22 10:30:00] SessionEnd/memory: committed 56 msgs (ov=abc123, reason=other)
```

## Verifying Memories

After hooks fire, search for extracted memories:

```bash
ov search "what did I work on today"
```

## Customization

- **Filter by session length**: Skip short sessions by checking `$COUNT` threshold
- **Tag memories**: Add project context via `ov session` metadata
- **Change log location**: Edit `LOG=` in each hook script
