# Document Chunker

Splits a long document into chunks that are **sentence-aware** (no sentence is cut in half) and **token-aware** (size is measured in tokens). Chunk size and overlap are configurable. No LLM or API is called; everything runs locally.

## Supported input formats

`.txt`, `.md`, `.pdf`, `.docx`, `.csv`, `.json`, `.jsonl`

## Install

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

```python
from chunker import Chunker

chunker = Chunker(chunk_size=200, overlap=30)

chunks = chunker.split("Your long text here. It has many sentences.")
chunks = chunker.split_file("report.pdf")   # also .txt .md .docx .csv .json
```

Command line demo:

```bash
python examples/demo.py examples/sample.txt --size 60 --overlap 15
```

## Run the tests

```bash
pytest
```

## How it works

1. Load the file into plain text (`loaders.py`).
2. Split the text into sentences (`sentences.py`).
3. Count tokens with `tiktoken` (`tokens.py`).
4. Group whole sentences into chunks up to `chunk_size` tokens, repeating trailing sentences (up to `overlap` tokens) at the start of the next chunk (`chunker.py`).

A single sentence longer than `chunk_size` is the only thing that gets cut mid-sentence; it is split by tokens.

See `requirements.md` for the full specification.
