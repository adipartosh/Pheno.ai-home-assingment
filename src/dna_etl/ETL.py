import json
import sys
from typing import Tuple, List, Dict, Any
from pathlib import Path
from datetime import datetime, timezone
from json_processor import (is_patient_at_least_40, dates_valid,
                            remove_sensitive_data, values_length_valid)
from txt_processor import (calculate_per_sequence, most_common_codon,
                           lcs, build_txt_output)

# validate input file
# process txt file -> return dict
# merge all into one json file


def utc_now_iso() -> str:
    """Return current UTC time as ISO-8601 (e.g., 2024-05-01T13:37:39.348785+00:00)."""
    return datetime.now(timezone.utc).isoformat()


def open_input_file(input_file_path: str) -> Tuple[Path, Path, Path, Path, str]:
    """
    Opens the input JSON file, reads context_path and results_path,
    finds the single JSON/TXT files inside the context_path,
    and derives participant_id from the JSON filename.
    Returns:
      (context_path, json_file_path, txt_file_path, results_path, participant_id)
    """
    # load input file
    with open(input_file_path, "r", encoding="utf-8") as input_file:
        input_data = json.load(input_file)

    context_path = Path(input_data["context_path"]).resolve()
    results_path = Path(input_data["results_path"]).resolve()

    # find json and txt files
    json_file_path = next(context_path.glob("*.json")).resolve()
    txt_file_path  = next(context_path.glob("*.txt")).resolve()

    # derive participant_id from JSON filename, e.g. "IND123456_dna.json" -> "IND123456"
    stem = json_file_path.stem
    participant_id = stem[:-4] if stem.endswith("_dna") else stem

    # TODO: add input format validation
    # return absolute paths
    return context_path, json_file_path, txt_file_path, results_path, participant_id


def extract_json_data(json_file_path: Path) -> dict:
    """
    Extracts data from the given JSON file.
    :param json_file_path: Path to the JSON file
    :return: Parsed JSON data as a dictionary
    """
    with json_file_path.open("r", encoding="utf-8") as json_file:
        metadata = json.load(json_file)
    return metadata


def extract_txt_sequences(txt_file_path: Path) -> List[str]:
    """
    Read the DNA TXT file and returns all non-empty lines as strings.
    :param txt_file_path: Path to the TXT file
    :return: List of non-empty lines from the TXT file
    """
    sequences_lst = []

    with txt_file_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            sequences_lst.append(line.upper())
    return sequences_lst


def build_metadata_block(context_path: Path, results_path: Path,
                         start_at: str, end_at: str) -> Dict[str, Any]:
    """
    Assemble the metadata block in the required format.
    :param context_path: Path to the context directory
    :param results_path: Path to the results directory
    :param start_at: Start time in ISO-8601 format
    :param end_at: End time in ISO-8601 format
    :return: Metadata dictionary

    """
    return {
        "start_at":     start_at,
        "end_at":       end_at,
        "context_path": str(context_path),
        "results_path": str(results_path),
    }


def build_results_block(participant_id: str,
                        json_block: Dict[str, Any],
                        txt_block: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a single 'results' item as required by the assignment.
    """
    return {
        "participant": {"_id": participant_id},
        "txt": txt_block,
        "JSON": json_block
    }


def build_final_output(metadata_block: Dict[str, Any],
                       results_block: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Assemble the final top-level JSON:
    {
      "metadata": {...},
      "results": [ {...}, {...}, ... ]
    }
    """
    return {
        "metadata": metadata_block,
        "results": results_block
    }


def write_output(results_path: Path, participant_id: str, final_output: Dict[str, Any]) -> Path:
    results_path.mkdir(parents=True, exist_ok=True)  # ensure dir exists
    out_path = results_path / f"{participant_id}.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(final_output, f, ensure_ascii=False, indent=2)
    return out_path


if __name__ == "__main__":
    # save start time
    start_time = utc_now_iso()

    if len(sys.argv) != 2:
        print("Usage: python ETL.py <input.json>")
        sys.exit(2)

    context_path, json_path, txt_path, result_path, participant_id = open_input_file(sys.argv[1])

    # JSON PROCESSING:

    metadata_to_process = extract_json_data(json_path)

    # validations
    if not is_patient_at_least_40(metadata_to_process):
        print(f"Validation error: participant must be at least 40 years old.")
        sys.exit(1)

    if not dates_valid(metadata_to_process):
        print("Validation error: one or more dates are out of the allowed range [2014-01-01..2024-12-31].")
        sys.exit(1)

    if not values_length_valid(metadata_to_process):
        print("Validation error: one or more string values exceed 64 characters.")
        sys.exit(1)

    # remove sensitive data
    json_block = remove_sensitive_data(metadata_to_process)

    # TXT PROCESSING:

    seq_lst = extract_txt_sequences(txt_path)

    # calculate GC% and codon frequencies per sequence
    per_sequence_results = calculate_per_sequence(seq_lst)

    # find most common codon(s)
    common_codon = most_common_codon(per_sequence_results)

    # find LCS (value, length, indexes)
    lcs_result = lcs(seq_lst)

    # combine TXT results into the expected JSON structure
    txt_block = build_txt_output(per_sequence_results, common_codon, lcs_result)

    # BUILD OUTPUT

    # build results block
    result_block = build_results_block(participant_id, json_block, txt_block)

    # save end time
    end_time = utc_now_iso()

    # build metadata block
    metadata_block = build_metadata_block(context_path, result_path, start_time, end_time)

    # combine all blocks into the final output structure
    final_output = build_final_output(metadata_block, [result_block])

    # write output file
    write_output(result_path, participant_id, final_output)


