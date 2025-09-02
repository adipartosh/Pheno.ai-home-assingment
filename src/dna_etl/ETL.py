import json
import os
import json_processor
from typing import Tuple
from pathlib import Path



# validate input file
# get path to json file
# get path to txt file
# proccess json file -> return dict
# process txt file -> return dict
# merge all into one json file


def open_input_file(input_file_path: str) -> Tuple[Path, Path]:
    """
    Opens the input JSON file, reads context_path
    finds the patient's json and txt files inside that directory.
    :param input_file_path: Path to the input.json file
    :return: (json_file_path, txt_file_path)
    """
    # load input file
    with open(input_file_path, "r", encoding="utf-8") as input_file:
        input_data = json.load(input_file)

    context_path = input_data["context_path"]
    # TODO: error handling

    # find json and txt files
    p = Path(context_path)
    json_file_path = next((fp for fp in p.glob("*.json")))
    txt_file_path = next((fp for fp in p.glob("*.txt")))
    """
    json_file_path = next((str(fp) for fp in p.glob("*.json")), None)
    txt_file_path  = next((str(fp) for fp in p.glob("*.txt")), None)
    if json_file_path is None or txt_file_path is None:
        raise FileNotFoundError("Could not find both JSON and TXT files in the specified context path.")
    """
    # return absolute paths
    return json_file_path, txt_file_path


def extract_json_data(json_file_path: Path) -> dict:
    """
    Extracts data from the given JSON file.
    :param json_file_path: Path to the JSON file
    :return: Parsed JSON data as a dictionary
    """
    with json_file_path.open("r", encoding="utf-8") as json_file:
        metadata = json.load(json_file)
    return metadata


if __name__ == "__main__":
    # open input file
    json_path, txt_path = open_input_file("C:/Users/adipa/DNA_ETL/src/data/input_exmpl.json")
    print(f"JSON: {json_path.resolve()}")  # TODO: remove
    print(f"TXT:  {txt_path.resolve()}")  # TODO: remove

    metadata_to_process = extract_json_data(json_path)
    print(metadata_to_process)  # TODO: remove
    print(json_processor.is_patient_at_least_40(metadata_to_process))  # TODO: remove