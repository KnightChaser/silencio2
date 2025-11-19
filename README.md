# `silencio2`

A CLI-based Python tool made with `typer` for automated text redaction and sanitization using large language models (for now, `Qwen/Qwen3-4B-Instruct-2507`), running locally.

## Installation

### Prerequisites

- Python 3.12 or higher
- `uv` package manager

### Install Dependencies

```bash
uv venv
source .venv/bin/activate
uv sync
uv pip install -U vllm --torch-backend auto
```

## Usage

You can use `--help` flag to obtain full usage information.

### Command Line Interface

silencio2 provides a CLI for automated easy text redaction:

```bash
python3 ./app.py redact --policy-file custom_policy.txt --src-dir ./src_dir --out-dir ./out_dir
```
- Source directory(`--src-dir`) must be an accessible directory filled with text files only. (e.g., `*.txt` or `*.md`).
- Output directory(`--out-dir`) must be a non-existing directory; so `silencio2` can create the new directory and store redaction output.

## Testing

### Run Tests

In CLI:
```bash
uv run pytest --verbose
```

### Generate Coverage Report

In formatted HTML report:
```bash
uv run pytest --cov=src/silencio2 --cov-report html
```

## Project Structure

- `src/silencio2/` - Main package
  - `automaton.py` - State machine for redaction
  - `badges.py` - Badge generation
  - `cli.py` - Command line interface
  - `models.py` - Data models
  - `patterns.py` - Pattern matching
  - `redact.py` - Redaction logic
  - `store.py` - Data storage
  - `unredact.py` - Unredaction logic
  - `llm/` - LLM integration
    - `autoredact_core.py` - Core LLM redaction
    - `engine.py` - LLM engine
  - `tests/` - Unit tests