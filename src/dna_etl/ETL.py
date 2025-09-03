import json
import sys
from typing import Tuple, List
from pathlib import Path
from json_processor import (is_patient_at_least_40, dates_valid,
                            remove_sensitive_data, values_length_valid)
from txt_processor import (calculate_per_sequence, most_common_codon,
                           lcs, build_txt_output)

# validate input file
# process txt file -> return dict
# merge all into one json file


def open_input_file(input_file_path: str) -> Tuple[Path, Path, Path]:
    """
    Opens the input JSON file, reads context_path and results_path,
    finds the patient's json and txt files inside the context_path.
    :param input_file_path: Path to the input.json file
    :return: (json_file_path, txt_file_path, results_path) as Paths (absolute)
    """
    # load input file
    with open(input_file_path, "r", encoding="utf-8") as input_file:
        input_data = json.load(input_file)

    context_path = Path(input_data["context_path"]).resolve()
    results_path = Path(input_data["results_path"]).resolve()

    # find json and txt files
    json_file_path = next(context_path.glob("*.json")).resolve()
    txt_file_path  = next(context_path.glob("*.txt")).resolve()
    # TODO: add input format validation
    # return absolute paths
    return json_file_path, txt_file_path, results_path


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


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python ETL.py <input.json>")
        sys.exit(2)

    json_path, txt_path, result_path = open_input_file(sys.argv[1])

    # json processing:
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

    # txt processing:
    seq_lst = extract_txt_sequences(txt_path)

    # calculate GC% and codon frequencies per sequence
    per_sequence_results = calculate_per_sequence(seq_lst)
    # find most common codon(s)
    common_codon = most_common_codon(per_sequence_results)
    # find LCS (value, length, indexes)
    lcs_result = lcs(seq_lst)
    # combine TXT results into the expected JSON structure
    txt_block = build_txt_output(per_sequence_results, common_codon, lcs_result)

    print(json.dumps(json_block, indent=2, ensure_ascii=False))  # TODO: remove
    print(json.dumps(txt_block, indent=2, ensure_ascii=False))  # TODO: remove



