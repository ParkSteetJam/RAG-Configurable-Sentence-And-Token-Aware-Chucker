"""Token counting helpers (wraps tiktoken). No LLM or API calls are made."""

import tiktoken


class TokenCounter:
    def __init__(self, encoding="cl100k_base"):
        self._enc = tiktoken.get_encoding(encoding)

    def encode(self, text):
        return self._enc.encode(text)

    def decode(self, tokens):
        return self._enc.decode(tokens)

    def count(self, text):
        return len(self._enc.encode(text))
