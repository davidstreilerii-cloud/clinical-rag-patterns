"""
Ingestion tests.

Two properties, and both exist because their absence is expensive.

**Idempotency.** Re-running ingestion must update in place rather than duplicate.
Without it, a corpus silently accumulates near-identical chunks, retrieval starts
returning the same document three times, and the only symptom is that answers get
subtly worse. The fix is a deterministic id derived from content and position.

**Provenance survives ingestion.** The corpus files carry a four-field header —
Source, Retrieved, Published, Subset. If ingestion drops it, every downstream
answer becomes unciteable and there is no way to tell a sourced claim from an
invented one after the fact.
"""
import pytest

from example.ingest import chunk_id, parse_provenance, tag_document


def test_chunk_id_is_stable_across_calls():
    doc = {"source": "cms_msdrg_national_utilization_2024", "text": "MS-DRG 871 sepsis"}
    assert chunk_id(doc, 0) == chunk_id(doc, 0)


def test_chunk_id_differs_by_position():
    doc = {"source": "cms_msdrg_national_utilization_2024", "text": "MS-DRG 871 sepsis"}
    assert chunk_id(doc, 0) != chunk_id(doc, 1)


def test_chunk_id_differs_by_content():
    a = {"source": "s", "text": "MS-DRG 871"}
    b = {"source": "s", "text": "MS-DRG 872"}
    assert chunk_id(a, 0) != chunk_id(b, 0)


def test_tagging_extracts_a_drg_code():
    assert "871" in tag_document("MS-DRG 871 had the most discharges")["drg"]


def test_tagging_extracts_an_hcc_code():
    assert "37" in tag_document("HCC 37 Diabetes with Chronic Complications")["hcc"]


def test_tagging_extracts_an_ncd_section():
    assert "20.4" in tag_document("NCD 20.4 covers implantable defibrillators")["ncd"]


def test_tagging_returns_empty_lists_not_none():
    """
    An empty list says "we looked and found none". None says "we did not look".
    Downstream code that filters on tags must be able to tell those apart.
    """
    assert tag_document("no codes in this sentence at all") == {
        "drg": [], "hcc": [], "ncd": [], "lcd": []
    }


def test_provenance_header_is_parsed():
    header = (
        "# Source: https://data.cms.gov/example\n"
        "# Retrieved: 2026-08-20\n"
        "# Published/effective: 2024-01-01\n"
        "# Subset: all 14 national rows\n"
        "\nBODY TEXT\n"
    )
    prov = parse_provenance(header)
    assert prov["source"] == "https://data.cms.gov/example"
    assert prov["retrieved"] == "2026-08-20"
    assert prov["subset"].startswith("all 14")


def test_document_without_provenance_raises():
    """
    A corpus file with no provenance header is a document nobody can cite. It does
    not get ingested with an empty source field — that would put an unciteable
    chunk in the index and let it be returned as though it were sourced.
    """
    with pytest.raises(ValueError, match="provenance"):
        parse_provenance("just some text with no header\n")


def test_tagging_reads_a_table_row_not_just_prose():
    """
    The MS-DRG corpus file lists codes as line-anchored table rows -- `871` then
    a discharge count -- not as the prose form `MS-DRG 871`. A tagger that only
    knows the prose form finds 1 code in a file listing 30.
    """
    row = "871        578,073             90,296.54    SEPTICEMIA OR SEVERE SEPSIS"
    assert "871" in tag_document(row)["drg"]


def test_tagging_does_not_treat_any_three_digit_number_as_a_drg():
    """
    The obvious way to make the test above pass is to match any 3-digit number,
    which would tag payment amounts, years and row counts as DRG codes. A wrong
    code attached to a passage makes it retrievable for a question it does not
    answer -- worse than no code at all.
    """
    assert tag_document("The average payment was 578 dollars in 2024.")["drg"] == []
    assert tag_document("Table 5 lists 760 codes across 25,000 diagnoses.")["drg"] == []
