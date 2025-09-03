from pathlib import Path
from typing import Any, Dict, List
ALLOWED_EXTENSIONS = {".json", ".txt"}
ALLOWED_KEY_SETS = [{"context_path", "results_path"}]


def valid_input_format(input_data: Dict[str, Any]) -> bool:
    """
    Validate input.json has exactly two fields and both are non-empty strings:
      - context_path
      - results_path (or result_path)
    """
    if not isinstance(input_data, dict):
        return False

    # Check for exact key sets
    keys = set(input_data.keys())
    if keys not in ALLOWED_KEY_SETS:
        return False

    # Extract values
    cp = input_data.get("context_path")
    rp = input_data.get("results_path", input_data.get("result_path"))

    # Check both are non-empty strings
    if not isinstance(cp, str) or not cp.strip():
        return False
    if not isinstance(rp, str) or not rp.strip():
        return False

    return True


def valid_context_path(input_data: Dict[str, Any]) -> bool:
    """
    'context_path' must be an existing directory.
    """
    p = Path(input_data["context_path"])
    return p.exists() and p.is_dir()


def valid_results_path(input_data: Dict[str, Any]) -> bool:
    """
    Ensure the results_path points to a directory we can write into.
    :param input_data: Dict with 'results_path'/'result_path'
    :return: True if path is an existing directory OR a creatable directory (parent exists)
    """
    p = Path(input_data["results_path"])

    if p.exists():
        return p.is_dir()  # p must be a directory

    # path doesn't exist yet -> parent directory must exist
    return p.parent.exists() and p.parent.is_dir()


def valid_context_files(input_data: Dict[str, Any]) -> bool:
    """
    Ensure the context directory contains exactly two files,
    and all files present are .json or .txt.
    """
    p = Path(input_data["context_path"])
    files: List[Path] = [f for f in p.iterdir() if f.is_file()]
    if len(files) != 2:
        return False

    # All files must be allowed extensions
    if any(f.suffix.lower() not in ALLOWED_EXTENSIONS for f in files):
        return False

    # Must be one .json and one .txt
    extensions = {f.suffix.lower() for f in files}
    return extensions == {".json", ".txt"}


def valid_file_names(input_data: Dict[str, Any]) -> bool:
    """
    Ensure the two files share the same base filename (same participant id),
    and that there is exactly one .json and one .txt.
    """
    p = Path(input_data["context_path"])
    # Get all files in the directory
    files: List[Path] = [f for f in p.iterdir() if f.is_file()]
    if len(files) != 2:
        return False
    # Exactly one .json and one .txt
    jsons = [f for f in files if f.suffix.lower() == ".json"]
    txts = [f for f in files if f.suffix.lower() == ".txt"]
    if len(jsons) != 1 or len(txts) != 1:
        return False
    # Same stem for both (e.g., "IND123456_dna.json" & "IND123456_dna.txt")
    return jsons[0].stem == txts[0].stem
