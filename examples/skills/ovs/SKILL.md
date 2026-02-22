---
name: ovs
description: Search OpenViking context (ov search). Use when retrieving memories or finding information in the knowledge base.
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

# OpenViking Search (`/ovs`)

The `/ovs` command searches across all memories and resources in OpenViking — combining semantic understanding with directory recursive retrieval.

## Usage

```
/ovs <query> [options]
```

## Examples

### Basic search:
```
/ovs "how to handle API rate limits"
```

### Search with scope:
```
/ovs "authentication flow" --uri "viking://resources/my-project"
```

### Limit results:
```
/ovs "error handling" --limit 5
```

## How It Works

This command executes:
```bash
ov search <your-input>
```

All arguments are passed directly to the `ov search` CLI command.

## Other Search Commands

You can also use the underlying `ov` commands directly:
- `ov grep "pattern"` — literal pattern matching
- `ov glob "**/*.md"` — file path pattern matching
- `ov ls` — browse directory structure
- `ov tree` — visualize directory hierarchy

## Prerequisites

- `ov` CLI installed and configured
- `~/.openviking/ovcli.conf` configured
- Resources or memories previously added to OpenViking
