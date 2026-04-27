import json
import os
import tempfile

import pandas as pd
import pytest

SAMPLE_RECORDS = [
    {"name": "Jane Doe",  "title": "CEO", "location": "San Francisco"},
    {"name": "John Smith","title": "CTO", "location": "New York"},
]


@pytest.fixture
def exporter():
    from export.exporter import Exporter
    return Exporter()
# File export tests 
def test_export_csv(exporter, tmp_path):
    out = str(tmp_path / "out.csv")
    exporter.export(SAMPLE_RECORDS, out, "csv")
    assert os.path.exists(out)
    df = pd.read_csv(out)
    assert len(df) == 2
    assert "name" in df.columns and "title" in df.columns
def test_export_json(exporter, tmp_path):
    out = str(tmp_path / "out.json")
    exporter.export(SAMPLE_RECORDS, out, "json")
    assert os.path.exists(out)
    with open(out) as f:
        data = json.load(f)
    assert len(data) == 2
    assert data[0]["name"] == "Jane Doe"
def test_export_excel(exporter, tmp_path):
    out = str(tmp_path / "out.xlsx")
    exporter.export(SAMPLE_RECORDS, out, "excel")
    assert os.path.exists(out)
    df = pd.read_excel(out)
    assert len(df) == 2
    assert "title" in df.columns
def test_export_invalid_format(exporter, tmp_path):
    with pytest.raises(ValueError, match="Unsupported format"):
        exporter.export(SAMPLE_RECORDS, str(tmp_path / "out.xml"), "xml")
def test_export_empty_records(exporter, tmp_path):
    with pytest.raises(ValueError, match="No records"):
        exporter.export([], str(tmp_path / "out.csv"), "csv")
def test_to_bytes_csv(exporter):
    raw = exporter.to_bytes(SAMPLE_RECORDS, "csv")
    assert isinstance(raw, bytes)
    assert b"Jane Doe" in raw


def test_to_bytes_json(exporter):
    raw = exporter.to_bytes(SAMPLE_RECORDS, "json")
    data = json.loads(raw.decode())
    assert len(data) == 2


def test_to_bytes_excel(exporter):
    raw = exporter.to_bytes(SAMPLE_RECORDS, "excel")
    assert isinstance(raw, bytes)
    assert len(raw) > 0


def test_to_bytes_empty(exporter):
    assert exporter.to_bytes([], "csv") == b""
