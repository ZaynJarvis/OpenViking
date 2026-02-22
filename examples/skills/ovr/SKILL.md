---
name: ovr
description: Add resources to OpenViking (ov add-resource). Use when importing files, URLs, or directories into the knowledge base.
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

# OpenViking Add Resource (`/ovr`)

The `/ovr` command imports external resources into OpenViking's context database — supporting local files, directories, URLs, and remote repositories.

## Usage

```
/ovr <path-or-url> [options]
```

## Examples

### Import a URL:
```
/ovr https://raw.githubusercontent.com/volcengine/OpenViking/main/README.md
```

### Import a local file:
```
/ovr ./docs/api-spec.md
```

### Import with context:
```
/ovr ./project-source --reason "API documentation for v2 endpoints"
```

## How It Works

This command executes:
```bash
ov add-resource <your-input>
```

All arguments are passed directly to the `ov add-resource` CLI command.

## Prerequisites

- `ov` CLI installed and configured
- `~/.openviking/ovcli.conf` configured
- Read permissions for local files/directories
