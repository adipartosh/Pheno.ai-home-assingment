# tests/test_pipeline.py
import pytest
import sys
import json
from pathlib import Path
from typing import Dict, Any, List

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))


# --- Imports from the package under test ---
from dna_etl.valid_input import (
    valid_input_format,
    valid_context_path,
    valid_results_path,
    valid_context_files,
    valid_file_names,
)
from dna_etl.txt_processor import (
    gc_content,
    codons_freq,
    calculate_per_sequence,
    most_common_codon,
    lcs,
    build_txt_output,
)
from dna_etl.json_processor import (

    is_patient_at_least_40,
    dates_valid,
    values_length_valid,
    remove_sensitive_data,
)
from dna_etl.ETL import (
    extract_json_data,
    open_input_file,              # (context_path, json_path, txt_path, results_path, participant_id)
    build_results_block,
    build_final_output,
)

# write_output
write_output = pytest.importorskip("dna_etl.ETL", reason="write_output not found").write_output


# ------------------------------
# Helpers to build sample inputs
# ------------------------------

def make_sample_metadata(valid_dates: bool = True, long_string: bool = False) -> Dict[str, Any]:
    """Return a sample metadata JSON (as dict)."""
    date_req = "2024-12-01" if valid_dates else "2013-12-01"
    date_comp = "2024-12-10" if valid_dates else "2025-12-10"
    coll_date = "2024-12-01" if valid_dates else "2010-01-01"

    long_val = "X" * 65 if long_string else "ok"

    return {
        "test_metadata": {
            "test_id": "DNA123456",
            "test_type": "Genetic Analysis",
            "date_requested": date_req,
            "date_completed": date_comp,
            "status": "Completed",
            "laboratory_info": {"name": "Genomics Lab Inc.", "certification": "CLIA Certified"},
        },
        "sample_metadata": {
            "sample_id": "SAMP987654",
            "sample_type": "Saliva",
            "collection_date": coll_date,
            "data_file": long_val,
        },
        "analysis_metadata": {
            "platform": "Illumina NovaSeq 6000",
            "methodology": "Whole Genome Sequencing",
            "coverage": "30x",
            "reference_genome": "GRCh38",
            "variants_detected": {"total": 5000, "pathogenic": 15, "likely_pathogenic": 8, "benign": 4977},
        },
        "individual_metadata": {
            "date_of_birth": "1970-01-01",
            "gender": "Male",
            "_id": "IND000001",
            "_internal_flag": True
        },
    }


def write_context_pair(dirpath: Path, stem: str, meta: Dict[str, Any], txt_lines: List[str]) -> Path:
    """Create <stem>.json and <stem>.txt under dirpath."""
    dirpath.mkdir(parents=True, exist_ok=True)
    j = dirpath / f"{stem}.json"
    t = dirpath / f"{stem}.txt"
    j.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    t.write_text("\n".join(txt_lines) + "\n", encoding="utf-8")
    return dirpath


def make_input_json(path: Path, context_path: Path, results_path: Path) -> Path:
    """Create input.json with required two keys."""
    d = {"context_path": str(context_path), "results_path": str(results_path)}
    path.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


# ------------------------------
# valid_input.py tests
# ------------------------------

def test_valid_input_format_exact_two_fields_ok(tmp_path: Path):
    context = tmp_path / "ctx"
    results = tmp_path / "out"
    inp = {"context_path": str(context), "results_path": str(results)}
    assert valid_input_format(inp) is True


def test_valid_input_format_reject_extra_field(tmp_path: Path):
    context = tmp_path / "ctx"
    results = tmp_path / "out"
    inp = {"context_path": str(context), "results_path": str(results), "extra": 1}
    assert valid_input_format(inp) is False


def test_valid_context_path_dir_ok(tmp_path: Path):
    ctx = tmp_path / "ctx"
    ctx.mkdir()
    in_data = {"context_path": str(ctx), "results_path": str(tmp_path / "out")}
    assert valid_context_path(in_data) is True


def test_valid_context_path_rejects_file(tmp_path: Path):
    ctx_file = tmp_path / "ctx.json"
    ctx_file.write_text("{}", encoding="utf-8")
    in_data = {"context_path": str(ctx_file), "results_path": str(tmp_path / "out")}
    assert valid_context_path(in_data) is False


def test_valid_results_path_ok_existing_dir(tmp_path: Path):
    out = tmp_path / "out"
    out.mkdir()
    in_data = {"context_path": str(tmp_path / "ctx"), "results_path": str(out)}
    assert valid_results_path(in_data) is True


def test_valid_results_path_ok_non_existing_dir(tmp_path: Path):
    out = tmp_path / "new_out"
    in_data = {"context_path": str(tmp_path / "ctx"), "results_path": str(out)}
    assert valid_results_path(in_data) is True


def test_valid_context_files_ok(tmp_path: Path):
    ctx = tmp_path / "ctx"
    meta = make_sample_metadata()
    txt_lines = [
        "ATCGATCGTAGCTAGCTAGCTGATCGATCGAT",
        "ATCGGTAAATGCCTGAAAGATG",
    ]
    write_context_pair(ctx, "IND123456_dna", meta, txt_lines)
    in_data = {"context_path": str(ctx), "results_path": str(tmp_path / "out")}
    assert valid_context_files(in_data) is True


def test_valid_context_files_reject_wrong_ext_or_count(tmp_path: Path):
    ctx = tmp_path / "bad_ctx"
    ctx.mkdir()
    (ctx / "IND.json").write_text("{}", encoding="utf-8")
    (ctx / "IND.txt").write_text("", encoding="utf-8")
    (ctx / "notes.md").write_text("# nope", encoding="utf-8")
    in_data = {"context_path": str(ctx), "results_path": str(tmp_path / "out")}
    assert valid_context_files(in_data) is False


def test_valid_file_names_ok(tmp_path: Path):
    ctx = tmp_path / "ctx2"
    meta = make_sample_metadata()
    write_context_pair(ctx, "ABCDEF_dna", meta, ["AAA", "CCC"])
    in_data = {"context_path": str(ctx), "results_path": str(tmp_path / "out")}
    assert valid_file_names(in_data) is True


def test_valid_file_names_reject_mismatch(tmp_path: Path):
    ctx = tmp_path / "ctx3"
    ctx.mkdir()
    (ctx / "A_dna.json").write_text("{}", encoding="utf-8")
    (ctx / "B_dna.txt").write_text("", encoding="utf-8")
    in_data = {"context_path": str(ctx), "results_path": str(tmp_path / "out")}
    assert valid_file_names(in_data) is False


# ------------------------------
# json_processor.py tests
# ------------------------------


def test_extract_json_data_and_validations(tmp_path: Path):
    meta = make_sample_metadata(valid_dates=True, long_string=False)
    p = tmp_path / "m.json"
    p.write_text(json.dumps(meta), encoding="utf-8")
    loaded = extract_json_data(p)
    assert isinstance(loaded, dict)
    assert is_patient_at_least_40(loaded) is True
    assert dates_valid(loaded) is True
    assert values_length_valid(loaded) is True


def test_dates_valid_rejects_out_of_range(tmp_path: Path):
    meta = make_sample_metadata(valid_dates=False, long_string=False)
    p = tmp_path / "m.json"
    p.write_text(json.dumps(meta), encoding="utf-8")
    loaded = extract_json_data(p)
    assert dates_valid(loaded) is False


def test_values_length_valid_rejects_over_64(tmp_path: Path):
    meta = make_sample_metadata(valid_dates=True, long_string=True)
    p = tmp_path / "m.json"
    p.write_text(json.dumps(meta), encoding="utf-8")
    loaded = extract_json_data(p)
    assert values_length_valid(loaded) is False


def test_remove_sensitive_data_strips_leading_underscore_keys():
    meta = make_sample_metadata()
    cleaned = remove_sensitive_data(meta)
    assert "_id" not in cleaned.get("individual_metadata", {})
    assert "_internal_flag" not in cleaned.get("individual_metadata", {})


# ------------------------------
# txt_processor.py tests
# ------------------------------

def test_gc_content_and_codons_freq_basic():
    s = "ATCGATCG"  # GC = 4/8 = 50.0
    assert pytest.approx(gc_content(s), rel=0, abs=0.01) == 50.0
    cf = codons_freq(s)
    assert cf == {"ATC": 1, "GAT": 1}


def test_calculate_per_sequence_and_most_common_codon_and_lcs(tmp_path: Path):
    seqs = [
        "ATCGATCGTAGCTAGCTAGCTGATCGATCGAT",
        "ATCGGTAAATGCCTGAAAGATG",
    ]
    per_seq = calculate_per_sequence(seqs)
    assert isinstance(per_seq, list) and len(per_seq) == 2
    assert pytest.approx(per_seq[0]["gc_content"], abs=0.01) == 46.88
    assert pytest.approx(per_seq[1]["gc_content"], abs=0.01) == 40.91

    most = most_common_codon(per_seq)
    assert isinstance(most, str) and most == "GAT"

    lcs_out = lcs(seqs)
    assert isinstance(lcs_out, dict)
    assert lcs_out["value"] == "ATCG"
    assert lcs_out["length"] == 4
    assert lcs_out["sequences"] == [1, 2]


def test_lcs_tie_returns_all_winners():
    seqs = ["XXAAA", "YAAA", "QGGGQ", "WGGGZ"]
    out = lcs(seqs)
    assert isinstance(out, list)
    values = {d["value"] for d in out}
    lengths = {d["length"] for d in out}
    assert values == {"AAA", "GGG"}
    assert lengths == {3}
    for d in out:
        assert all(isinstance(x, int) and x >= 1 for x in d["sequences"])


def test_build_txt_output_shape():
    per_seq = [{"gc_content": 50.0, "codons": {"ATC": 1}}]
    most = "ATC"
    lcs_info = {"value": "ATC", "sequences": [1], "length": 3}
    block = build_txt_output(per_seq, most, lcs_info)
    assert block.keys() == {"sequences", "most_common_codon", "lcs"}
    assert block["sequences"] == per_seq
    assert block["most_common_codon"] == most
    assert block["lcs"] == lcs_info


# ------------------------------
# ETL assembly tests
# ------------------------------

def test_open_input_file_extracts_paths_and_id(tmp_path: Path):
    ctx = tmp_path / "ctx"
    meta = make_sample_metadata()
    seqs = ["ATCGATCG", "ATCGGTAAATG"]
    write_context_pair(ctx, "IND123456_dna", meta, seqs)

    # input.json
    out_dir = tmp_path / "out"
    input_json = tmp_path / "input.json"
    make_input_json(input_json, ctx, out_dir)

    context_path, json_path, txt_path, results_path, participant_id = open_input_file(str(input_json))
    assert context_path == ctx.resolve()
    assert json_path.name == "IND123456_dna.json"
    assert txt_path.name == "IND123456_dna.txt"
    assert results_path == out_dir.resolve()
    assert participant_id == "IND123456"


def test_build_results_and_final_output_blocks(tmp_path: Path):
    metadata_block = {
        "start_at": "2024-05-01T13:37:39.000000+00:00",
        "end_at":   "2024-05-01T13:37:40.000000+00:00",
        "context_path": str(tmp_path / "ctx"),
        "results_path": str(tmp_path / "out"),
    }
    txt_block = {"sequences": [], "most_common_codon": "AAA", "lcs": {"value": "", "sequences": [], "length": 0}}
    json_block = {"some": "metadata"}
    participant_id = "IND999999"

    item = build_results_block(participant_id, json_block, txt_block)
    assert item["participant"]["_id"] == participant_id
    assert "txt" in item and "JSON" in item

    final = build_final_output(metadata_block, [item])
    assert final["metadata"] == metadata_block
    assert isinstance(final["results"], list) and final["results"][0] == item


def test_write_output_overwrites(tmp_path: Path):
    # Arrange
    out_dir = tmp_path / "outdir"
    participant_id = "IND000001"
    data_v1 = {"v": 1}
    data_v2 = {"v": 2}

    # First write
    p1 = write_output(out_dir, participant_id, data_v1)
    assert p1.exists() and p1.is_file()
    assert json.loads(p1.read_text(encoding="utf-8")) == data_v1

    # Second write (overwrite)
    p2 = write_output(out_dir, participant_id, data_v2)
    assert p2 == p1
    assert json.loads(p2.read_text(encoding="utf-8")) == data_v2
