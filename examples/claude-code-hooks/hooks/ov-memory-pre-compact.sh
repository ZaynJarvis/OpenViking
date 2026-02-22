#!/bin/bash
# ov-memory-pre-compact.sh
# Hook: PreCompact
# Before context compaction, snapshot the conversation into OpenViking memory
# so details aren't lost when the context window is trimmed.

set -euo pipefail

INPUT=$(cat)
TRANSCRIPT=$(echo "$INPUT" | jq -r '.transcript_path // empty')
TRIGGER=$(echo "$INPUT" | jq -r '.trigger // "auto"')
LOG=/tmp/ov-hooks.log

if [ -z "$TRANSCRIPT" ] || [ ! -f "$TRANSCRIPT" ]; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] PreCompact/memory: no transcript (trigger=$TRIGGER)" >> "$LOG"
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
' "$TRANSCRIPT")

COUNT=$(echo "$MESSAGES" | jq 'length')

if [ "$COUNT" -eq 0 ]; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] PreCompact/memory: nothing to snapshot (trigger=$TRIGGER)" >> "$LOG"
  exit 0
fi

ov add-memory "$MESSAGES" >> "$LOG" 2>&1
echo "[$(date '+%Y-%m-%d %H:%M:%S')] PreCompact/memory: snapshotted $COUNT msgs before $TRIGGER compaction" >> "$LOG"
