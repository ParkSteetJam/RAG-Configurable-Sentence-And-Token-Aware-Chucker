import pytest

from chunker import Chunker

TEXT = " ".join(f"This is sentence number {i} in the test document." for i in range(40))


def test_no_chunk_exceeds_size():
    c = Chunker(chunk_size=50, overlap=10)
    for chunk in c.split(TEXT):
        assert c.count(chunk) <= 50


def test_empty_input():
    assert Chunker().split("") == []
    assert Chunker().split("   \n  ") == []


def test_short_text_is_one_chunk():
    assert len(Chunker(chunk_size=200, overlap=20).split("Hello there. How are you?")) == 1


def test_overlap_repeats_text():
    c = Chunker(chunk_size=50, overlap=20)
    chunks = c.split(TEXT)
    assert len(chunks) > 1
    last_sentence = c.sentences(chunks[0])[-1]
    assert last_sentence in chunks[1]


def test_zero_overlap_has_no_repeats():
    c = Chunker(chunk_size=50, overlap=0)
    seen = []
    for chunk in c.split(TEXT):
        for s in c.sentences(chunk):
            assert s not in seen
            seen.append(s)


def test_no_text_lost():
    c = Chunker(chunk_size=50, overlap=10)
    joined = " ".join(c.split(TEXT))
    for s in c.sentences(TEXT):
        assert s in joined


def test_oversized_sentence_is_split():
    c = Chunker(chunk_size=20, overlap=5)
    long_sentence = "word " * 200 + "end."
    chunks = c.split(long_sentence)
    assert len(chunks) > 1
    assert all(c.count(ch) <= 20 for ch in chunks)


def test_deterministic():
    c = Chunker(chunk_size=50, overlap=10)
    assert c.split(TEXT) == c.split(TEXT)


def test_invalid_settings():
    with pytest.raises(ValueError):
        Chunker(chunk_size=0)
    with pytest.raises(ValueError):
        Chunker(chunk_size=50, overlap=50)
    with pytest.raises(ValueError):
        Chunker(chunk_size=50, overlap=-1)


def test_non_string_input():
    with pytest.raises(TypeError):
        Chunker().split(123)
