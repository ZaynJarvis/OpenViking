---
name: ovm
description: Add memories to OpenViking (ov add-memory). Use when saving insights, learnings, or context worth remembering.
user-invocable: true
command-dispatch: tool
command-tool: exec
command-arg-mode: raw
metadata:
  {
    "openclaw":
      {
        "requires": { "bins": ["ov"] },
      },
  }
---

# OpenViking Add Memory (`/ovm`)

The `/ovm` command adds persistent memory to OpenViking — turning text and structured conversations into searchable, retrievable memories.

## Usage

```
/ovm <text or JSON conversation>
```

## Examples

### Plain text memory:
```
/ovm User's name is Bob, he participated in Global Hackathon 2025 and won Champion.
```

### Multi-turn conversation:
```
/ovm [{"role": "user", "content": "I love Python"}, {"role": "assistant", "content": "Python is great for data science"}]
```

## How It Works

This command executes:
```bash
ov add-memory <your-input>
```

The input is passed directly to the `ov add-memory` CLI command.

## Prerequisites

- `ov` CLI installed and configured
- `~/.openviking/ovcli.conf` configured
