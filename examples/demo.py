"""
Usage:
    python examples/demo.py path/to/file.pdf --size 200 --overlap 30
"""

import argparse
import sys
from pathlib import Path
import ollama

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

#Chunk any supported file and print the results.

from chunker import Chunker  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Sentence/token-aware chunker")
    parser.add_argument("file", help=".txt, .md, .pdf, .docx, .csv or .json")
    parser.add_argument("--size", type=int, default=200, help="max tokens per chunk")
    parser.add_argument("--overlap", type=int, default=30, help="overlap in tokens")
    args = parser.parse_args()

    chunker = Chunker(chunk_size=args.size, overlap=args.overlap)
    chunks = chunker.split_file(args.file)

    print(f"{len(chunks)} chunks (size={args.size}, overlap={args.overlap})\n")
    for i, chunk in enumerate(chunks):
        print(f"--- chunk {i} | {chunker.count(chunk)} tokens ---")
        print(chunk, end="\n\n")

    #Creating Emdedding for each chunk and storing them in a vector database is left as an exercise for the reader.

    for i, chunk in enumerate(chunks, start=1):
        response = ollama.embeddings(
            model="nomic-embed-text",
            prompt=chunk
        )

        embedding = response["embedding"]

        print(f"\n{'='*80}")
        print(f"Chunk #{i}")
        print(f"Text: {chunk}")
        print(f"Embedding Dimension: {len(embedding)}")
        print(f"First 10 Values: {embedding[:10]}")


if __name__ == "__main__":
    main()

