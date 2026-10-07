# Requirements: Sentence- and Token-Aware Document Chunker

## 1. Overview

Build a Python library that splits a long text document into smaller pieces ("chunks"). The splitting must respect two rules:

1. **Sentence-aware:** chunks are made of whole sentences, so text is not cut mid-sentence.
2. **Token-aware:** chunk size is measured in **tokens** (the units AI models read), not characters or words.

Both the **chunk size** and the **overlap** between consecutive chunks must be configurable by the user.

### Why this exists

Embedding models, search systems, and LLMs accept only a limited amount of text at once. Long documents must be split before they can be processed. Cutting at random points breaks meaning, so the chunker cuts at sentence boundaries and uses overlap to preserve context between chunks. This is a common preprocessing step in RAG (retrieval-augmented generation) pipelines.

### What this project is not

- It does **not** call any LLM or external API.
- It does **not** create embeddings, store vectors, or answer questions.
- It only turns one text into a list of chunks.

---

## 2. Terminology

| Term | Meaning |
|------|---------|
| **Chunk** | A piece of the original document, made of one or more consecutive sentences. |
| **Token** | The unit a language model reads. Roughly a word or part of a word. |
| **Chunk size** | Maximum number of tokens allowed in one chunk. |
| **Overlap** | Maximum number of tokens (rounded down to whole sentences) repeated from the end of one chunk at the start of the next. |
| **Tokenizer** | A library that converts text into tokens (here: `tiktoken`). |

---

## 3. Functional Requirements

### FR-1: Input

- **FR-1.1** Accept a plain-text string as input (`split(text)`).
- **FR-1.4** Accept a file path (`split_file(path)`) for these formats: `.txt`, `.md`, `.pdf`, `.docx`, `.csv`, `.json`, `.jsonl`. The file is first converted to plain text by a loader, then chunked.
- **FR-1.5** Choose the loader from the file extension (case-insensitive). Raise `ValueError` for unsupported extensions and `FileNotFoundError` for missing files.
- **FR-1.2** Treat an empty or whitespace-only string as valid input and return an empty list.
- **FR-1.3** Raise a clear error (`TypeError`) if the input is not a string.

### FR-2: Sentence splitting

- **FR-2.1** Split the text into sentences at `.`, `!`, and `?` followed by whitespace.
- **FR-2.2** Strip leading and trailing whitespace from each sentence and discard empty results.
- **FR-2.3** Keep sentence order exactly as in the original document.
- **FR-2.4** *(Improvement)* Handle common abbreviations (e.g. "Dr.", "e.g.", "U.S.") without treating them as sentence ends. This can be done by swapping the regex for `nltk.sent_tokenize` or `spacy`.

### FR-3: Token counting

- **FR-3.1** Count tokens using `tiktoken` with a configurable encoding (default: `cl100k_base`).
- **FR-3.2** Expose a `count(text)` method that returns the number of tokens in any string.
- **FR-3.3** All size decisions (chunk size, overlap) must use token counts, never character or word counts.

### FR-4: Configurable chunk size

- **FR-4.1** The user sets `chunk_size` (in tokens) when creating the chunker. Default: `200`.
- **FR-4.2** No chunk may exceed `chunk_size` tokens.
- **FR-4.3** `chunk_size` must be a positive integer; otherwise raise `ValueError`.

### FR-5: Configurable overlap

- **FR-5.1** The user sets `overlap` (in tokens) when creating the chunker. Default: `30`.
- **FR-5.2** `overlap` must be zero or greater, and **strictly smaller** than `chunk_size`; otherwise raise `ValueError`.
- **FR-5.3** When a new chunk starts, carry over the trailing sentences of the previous chunk, as many whole sentences as fit within `overlap` tokens.
- **FR-5.4** If no whole sentence fits within `overlap` tokens, the next chunk starts with no overlap.
- **FR-5.5** If the carried-over overlap plus the next sentence would exceed `chunk_size`, drop the overlap for that chunk.
- **FR-5.6** `overlap=0` must produce chunks with no repeated text.

### FR-6: Chunk building

- **FR-6.1** Add sentences to the current chunk one at a time, in order.
- **FR-6.2** Before adding a sentence, check whether it would push the chunk over `chunk_size`. If so, close the current chunk and start a new one (applying FR-5).
- **FR-6.3** After the last sentence, flush any remaining sentences as the final chunk.
- **FR-6.4** Join the sentences in a chunk with a single space.
- **FR-6.5** Every sentence of the document must appear in at least one chunk (no text is lost).

### FR-7: Oversized sentences

- **FR-7.1** If a single sentence is longer than `chunk_size` tokens, split it by tokens into pieces of at most `chunk_size` tokens.
- **FR-7.2** Treat each piece as its own sentence in the chunking process.
- **FR-7.3** This is the only case in which text is cut mid-sentence.

### FR-8: Output

- **FR-8.1** Return a `list[str]`, one string per chunk, in document order.
- **FR-8.2** *(Optional)* Provide a richer output option that returns, for each chunk: the text, its index, and its token count.

### FR-9: File loaders

- **FR-9.1** `.txt`: read as UTF-8 text.
- **FR-9.2** `.md`: strip Markdown syntax (heading markers, bold/italic, links, images, list bullets, blockquotes, code fences) and keep the readable text.
- **FR-9.3** `.pdf`: extract text page by page. If no text can be extracted (e.g. a scanned PDF), raise a `ValueError` that suggests OCR.
- **FR-9.4** `.docx`: extract paragraphs and table rows.
- **FR-9.5** `.csv`: the first row is the header. Each data row becomes one sentence of the form `column: value; column: value.` and empty cells are skipped.
- **FR-9.6** `.json` / `.jsonl`: extract every value as a `key: value.` line, walking nested objects and lists.
- **FR-9.7** Libraries for PDF and DOCX are imported only when needed. If missing, raise an `ImportError` that says which package to install.
- **FR-9.8** Lines produced from CSV/JSON/DOCX tables end with sentence punctuation so they split cleanly into sentences.

---

## 4. Public API

```python
from chunker import Chunker

chunker = Chunker(chunk_size=200, overlap=30, encoding="cl100k_base")

chunks = chunker.split(document_text)   # -> list[str]
chunks = chunker.split_file("report.pdf")  # -> list[str]
n = chunker.count("some text")          # -> int (token count)
```

| Method / Parameter | Description |
|--------------------|-------------|
| `Chunker(chunk_size, overlap, encoding)` | Create a chunker with the given settings. Validates arguments. |
| `split(text)` | Return the list of chunks for `text`. |
| `split_file(path)` | Load a supported file and return its chunks. |
| `load_text(path)` | (module function) Return the plain text of a supported file. |
| `count(text)` | Return the token count of `text`. |
| `sentences(text)` | Return the list of sentences in `text`. |

---

## 5. Algorithm Summary

1. Validate settings (`chunk_size > 0`, `0 <= overlap < chunk_size`).
2. Split the document into sentences.
3. For any sentence over `chunk_size` tokens, split it into token-based pieces.
4. Walk through the sentences, adding each to the current chunk.
5. When the next sentence would exceed `chunk_size`:
   1. Save the current chunk.
   2. Build the overlap from the trailing sentences that fit in `overlap` tokens.
   3. Start a new chunk with that overlap (or empty, per FR-5.4 and FR-5.5).
6. Save the last chunk.
7. Return all chunks.

---

## 6. Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| **NFR-1** | **No LLM or network use at run time.** Everything runs locally. (`tiktoken` may download its vocabulary file once on first use, then works offline.) |
| **NFR-2** | **Deterministic.** The same input and settings always produce the same chunks. |
| **NFR-3** | **Readable code.** Small functions, clear names, docstrings on public methods. |
| **NFR-4** | **Reasonable performance.** Handle a document of about 1 MB of text in a few seconds. Cache per-sentence token counts to avoid repeated work. |
| **NFR-5** | **Python 3.9 or newer.** |
| **NFR-6** | **Clear errors.** Invalid settings fail fast with a helpful message. |

---

## 7. Dependencies

| Package | Purpose | Required? |
|---------|---------|-----------|
| `tiktoken` | Token counting | Yes |
| `pypdf` | Reading `.pdf` files | Only for PDF input |
| `python-docx` | Reading `.docx` files | Only for DOCX input |
| `pytest` | Running tests | Yes (development) |
| `nltk` or `spacy` | Better sentence splitting | Optional |

`requirements.txt`:

```
tiktoken>=0.5.0
pypdf>=4.0.0
python-docx>=1.0.0
pytest>=7.0.0
```

Setup:

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## 8. Edge Cases to Handle

| Case | Expected behavior |
|------|-------------------|
| Empty string or only whitespace | Return `[]` |
| Document shorter than `chunk_size` | Return one chunk containing the whole text |
| One sentence longer than `chunk_size` | Split that sentence by tokens (FR-7) |
| `overlap = 0` | No repeated text between chunks |
| `overlap >= chunk_size` | Raise `ValueError` |
| `chunk_size <= 0` | Raise `ValueError` |
| Text with no punctuation | Treated as one sentence, then split by tokens if too long |
| Multiple spaces or newlines between sentences | Normalized to a single space within chunks |
| Abbreviations like "Dr." | May be mis-split with regex; handled with FR-2.4 |
| Non-English or emoji text | Counted correctly by `tiktoken`; sentence splitting may be less accurate |

---

## 9. Testing Requirements

Write tests with `pytest`. At minimum:

1. **Size limit:** no chunk exceeds `chunk_size` tokens.
2. **Sentence integrity:** chunks end at sentence boundaries (except for oversized sentences).
3. **Overlap works:** the start of chunk *n+1* repeats the end of chunk *n* when `overlap > 0`.
4. **No overlap:** with `overlap=0`, no sentence appears in two chunks.
5. **No text lost:** every sentence from the input appears in at least one chunk.
6. **Oversized sentence:** a very long sentence is split and each piece is within `chunk_size`.
7. **Empty input:** returns `[]`.
8. **Invalid settings:** bad `chunk_size` or `overlap` raises `ValueError`.
9. **Determinism:** two runs on the same input give identical output.
10. **Configurability:** changing `chunk_size` changes the number of chunks as expected.

---

## 10. Suggested Project Structure

```
document-chunker/
├── src/
│   └── chunker/
│       ├── __init__.py
│       ├── chunker.py        # Chunker class
│       ├── loaders.py        # .txt .md .pdf .docx .csv .json readers
│       ├── sentences.py      # sentence splitting
│       └── tokens.py         # token counting helpers
├── tests/
│   ├── conftest.py
│   ├── test_chunker.py
│   └── test_loaders.py
├── examples/
│   ├── sample.txt
│   └── demo.py
├── requirements.txt
├── requirements.md
├── README.md
├── .gitignore
└── pyproject.toml
```

---

## 11. Deliverables

- Working source code in `src/chunker/`
- Test suite in `tests/` that passes with `pytest`
- A sample document and demo script in `examples/`
- `README.md` with installation steps and a usage example
- This `requirements.md`

---

## 12. Acceptance Criteria

The project is complete when:

- [ ] `Chunker(chunk_size=..., overlap=...)` can be configured by the user.
- [ ] Files in all supported formats can be loaded and chunked with `split_file`.
- [ ] Running the chunker on `examples/sample.txt` prints chunks with their token counts, all at or below `chunk_size`.
- [ ] Chunks consist of whole sentences (except oversized sentences).
- [ ] Overlap between consecutive chunks behaves as described in FR-5.
- [ ] All tests pass.
- [ ] The code runs with no API keys and no LLM calls.
- [ ] The README explains how to install and use it.

---

## 13. Out of Scope

- Calling LLMs or embedding models
- Storing chunks in a database or vector store
- Reading HTML, PPTX, XLSX, or EPUB files
- OCR for scanned PDFs or images
- Paragraph, heading, or markdown-structure-aware chunking
- A command-line interface or web UI

These can be added later as extensions.

---

## 14. Possible Future Extensions

- Add more formats (HTML, PPTX, XLSX, EPUB) and OCR for scanned PDFs
- Export chunks to JSON/JSONL/CSV
- Return metadata per chunk (index, token count, start and end character positions)
- Support multiple tokenizers (e.g. Hugging Face tokenizers)
- Paragraph-aware chunking before sentence-level splitting
- Use `nltk` or `spacy` for higher-quality sentence detection
