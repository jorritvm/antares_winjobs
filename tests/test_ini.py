# tests/test_ini.py
import tempfile
import os
from utils.ini import robust_read_ini

def write_ini(contents):
    fd, path = tempfile.mkstemp(suffix=".ini")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(contents)
    return path

def test_single_section_single_key():
    ini = "[section]\nkey=value\n"
    path = write_ini(ini)
    result = robust_read_ini(path)
    assert result == {"section": {"key": "value"}}
    os.remove(path)

def test_repeated_keys():
    ini = "[section]\nkey=one\nkey=two\n"
    path = write_ini(ini)
    result = robust_read_ini(path)
    assert result == {"section": {"key": ["one", "two"]}}
    os.remove(path)

def test_multiple_sections():
    ini = "[a]\nx=1\nx=2\n[b]\ny=3\n"
    path = write_ini(ini)
    result = robust_read_ini(path)
    assert result["a"]["x"] == ["1", "2"]
    assert result["b"]["y"] == "3"
    os.remove(path)

def test_comments_and_blank_lines():
    ini = """
    ; comment
    # another comment

    [s]
    k=v
    """
    path = write_ini(ini)
    result = robust_read_ini(path)
    assert result == {"s": {"k": "v"}}
    os.remove(path)

def test_malformed_lines_are_skipped(capfd):
    ini = "[s]\nnot_a_key_value\nk=v\n"
    path = write_ini(ini)
    result = robust_read_ini(path)
    out, _ = capfd.readouterr()
    assert "Skipping line" in out
    assert result == {"s": {"k": "v"}}
    os.remove(path)
