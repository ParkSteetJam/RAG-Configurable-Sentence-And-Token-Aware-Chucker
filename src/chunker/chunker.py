"""Sentence- and token-aware chunker with configurable size and overlap."""

from .loaders import load_text
from .sentences import split_sentences
from .tokens import TokenCounter


class Chunker:
    def __init__(self, chunk_size=200, overlap=30, encoding="cl100k_base"):
        if not isinstance(chunk_size, int) or chunk_size <= 0:
            raise ValueError("chunk_size must be a positive integer")
        if not isinstance(overlap, int) or overlap < 0:
            raise ValueError("overlap must be an integer >= 0")
        if overlap >= chunk_size:
            raise ValueError("overlap must be smaller than chunk_size")
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.tokens = TokenCounter(encoding)

    # ----- public helpers -----

    def count(self, text):
        return self.tokens.count(text)

    def sentences(self, text):
        return split_sentences(text)

    # ----- main entry points -----

    def split(self, text):
        """Split a string into a list of chunks."""
        if not isinstance(text, str):
            raise TypeError("text must be a string")

        units = self._to_units(text)  # list of (sentence, token_count)
        chunks = []
        current, current_tokens = [], 0

        for sentence, n in units:
            if current and current_tokens + n > self.chunk_size:
                chunks.append(self._join(current))
                current, current_tokens = self._overlap_tail(current)
                # Overlap + new sentence too big? Drop the overlap.
                if current_tokens + n > self.chunk_size:
                    current, current_tokens = [], 0
            current.append((sentence, n))
            current_tokens += n

        if current:
            chunks.append(self._join(current))
        return chunks

    def split_file(self, path):
        """Load a .txt/.md/.pdf/.docx/.csv/.json file and split its text."""
        return self.split(load_text(path))

    # ----- internals -----

    def _to_units(self, text):
        """Sentences with token counts; oversized sentences are cut by tokens."""
        units = []
        for s in split_sentences(text):
            n = self.tokens.count(s)
            if n <= self.chunk_size:
                units.append((s, n))
            else:
                ids = self.tokens.encode(s)
                for i in range(0, len(ids), self.chunk_size):
                    piece = ids[i:i + self.chunk_size]
                    units.append((self.tokens.decode(piece), len(piece)))
        return units

    def _overlap_tail(self, current):
        """Trailing whole sentences that fit within `overlap` tokens."""
        tail, total = [], 0
        for sentence, n in reversed(current):
            if total + n > self.overlap:
                break
            tail.insert(0, (sentence, n))
            total += n
        return tail, total

    @staticmethod
    def _join(units):
        return " ".join(s for s, _ in units)
