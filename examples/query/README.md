# OpenViking RAG Query Tool

Simple RAG (Retrieval-Augmented Generation) example using OpenViking + LLM.

## Quick Start

```bash
# 0. install dependencies
uv sync

# 1. Add documents to database
uv run add.py ~/xxx/document.pdf
uv run add.py https://raw.githubusercontent.com/volcengine/OpenViking/refs/heads/main/README.md

# 2. Query with LLM
uv run query.py "What do we have here?"
# or
./q "What do we have here?" # add to .bashrc alias if you like. alias q=${pwd}/q

# 3. redo
mv data/ data.bak/ # or rm -rf if you want
```

## Usage

### Add Resources

```bash
# Add PDF
uv run add.py document.pdf

# Add URL
uv run add.py https://example.com/README.md

# Add directory
uv run add.py ~/Documents/research/
```

### Query

```bash
# Quick query (recommended)
./q "Your question here"

# With options
uv run query.py "Your question" --top-k 10 --temperature 0.3

# Verbose output
./q "Your question" --verbose
```

### Query Options

| Option | Default | Description |
|--------|---------|-------------|
| `--top-k` | 5 | Number of search results to use |
| `--temperature` | 0.7 | LLM creativity (0.0-1.0) |
| `--max-tokens` | 2048 | Maximum response length |
| `--verbose` | false | Show detailed information |

**Temperature Guide:**
- `0.0-0.3` → Factual, consistent
- `0.4-0.7` → Balanced (default)
- `0.8-1.0` → Creative, exploratory

## Debug Mode

Enable detailed logging:

```bash
OV_DEBUG=1 uv run query.py "question"
OV_DEBUG=1 uv run add.py file.pdf
```

## Configuration

Edit `ov.conf` to configure:
- Embedding model
- LLM model (VLM)
- API keys

## Files

```
rag.py              # RAG pipeline library
add.py     # Add documents CLI
query.py            # Query CLI
q                   # Quick query wrapper
logging_config.py   # Logging configuration
ov.conf             # OpenViking config
data/               # Database storage
```

## Tips

- Use `./q` for quick queries (clean output)
- Use `uv run query.py` for more control
- Set `OV_DEBUG=1` only when debugging
- Resources are indexed once, query unlimited times
