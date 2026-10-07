import json

import pytest

from chunker import Chunker, load_text


def test_txt(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("Hello world. Second sentence.")
    assert load_text(f) == "Hello world. Second sentence."


def test_md_strips_syntax(tmp_path):
    f = tmp_path / "a.md"
    f.write_text("# Title\n\nSome **bold** text with a [link](http://x.com).\n\n- item one\n")
    text = load_text(f)
    assert "#" not in text and "**" not in text and "http" not in text
    assert "bold" in text and "link" in text and "item one" in text


def test_csv_rows_become_sentences(tmp_path):
    f = tmp_path / "a.csv"
    f.write_text("name,city\nAnna,Paris\nBen,Rome\n")
    text = load_text(f)
    assert "name: Anna; city: Paris." in text
    assert "name: Ben; city: Rome." in text


def test_json_values_extracted(tmp_path):
    f = tmp_path / "a.json"
    f.write_text(json.dumps({"title": "Report", "items": [{"note": "First"}, {"note": "Second"}]}))
    text = load_text(f)
    assert "title: Report." in text and "note: First." in text and "note: Second." in text


def test_docx(tmp_path):
    docx = pytest.importorskip("docx")
    d = docx.Document()
    d.add_paragraph("First paragraph.")
    d.add_paragraph("Second paragraph.")
    f = tmp_path / "a.docx"
    d.save(str(f))
    text = load_text(f)
    assert "First paragraph." in text and "Second paragraph." in text


def test_unsupported_extension(tmp_path):
    f = tmp_path / "a.xyz"
    f.write_text("hi")
    with pytest.raises(ValueError):
        load_text(f)


def test_missing_file():
    with pytest.raises(FileNotFoundError):
        load_text("does_not_exist.txt")


def test_split_file_end_to_end(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text(" ".join(f"Sentence {i} is here." for i in range(50)))
    chunks = Chunker(chunk_size=30, overlap=5).split_file(f)
    assert len(chunks) > 1
