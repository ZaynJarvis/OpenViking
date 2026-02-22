#!/bin/bash
# ov-memory-subagent-stop.sh
# Hook: SubagentStop
# When a subagent finishes, extract its transcript into OpenViking memory.

set -euo pipefail

INPUT=$(cat)
AGENT_TYPE=$(echo "$INPUT" | jq -r '.agent_type // "unknown"')
AGENT_TRANSCRIPT=$(echo "$INPUT" | jq -r '.agent_transcript_path // empty')
LOG=/tmp/ov-hooks.log

if [ -z "$AGENT_TRANSCRIPT" ] || [ ! -f "$AGENT_TRANSCRIPT" ]; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] SubagentStop/memory: no transcript for $AGENT_TYPE" >> "$LOG"
  exit 0
fi

# Extract user/assistant text turns from JSONL transcript
MESSAGES=$(jq -sc '
  map(select(.type == "user" or .type == "assistant"))
  | map({
      role: .message.role,
      content: (
        .message.content
        | if type == "string" then .
          elif type == "array" then (map(select(.type == "text") | .text) | join("\n"))
          else ""
          end
      )
    })
  | map(select(.content != "" and .content != null))
' "$AGENT_TRANSCRIPT")

COUNT=$(echo "$MESSAGES" | jq 'length')

if [ "$COUNT" -eq 0 ]; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] SubagentStop/memory: no text messages for $AGENT_TYPE" >> "$LOG"
  exit 0
fi

ov add-memory "$MESSAGES" >> "$LOG" 2>&1
echo "[$(date '+%Y-%m-%d %H:%M:%S')] SubagentStop/memory: saved $COUNT msgs from $AGENT_TYPE to ov" >> "$LOG"
