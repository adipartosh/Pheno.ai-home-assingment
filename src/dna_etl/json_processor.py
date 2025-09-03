from datetime import date
from typing import Any, Dict, List, Union, cast

MAX_VALUE_LEN = 64
# ALL FUNCTIONS WORKING ON DICT (THAT WAS PARSED FROM JSON)


def is_patient_at_least_40(metadata: Dict[str, Any]) -> bool:
    """
    Checks if the patient is at least 40 years old.
    :param metadata: Dictionary containing patient metadata
    :return: True if the patient is at least 40 years old, False otherwise
    """
    # extract birthdate
    birth_date_str = metadata["individual_metadata"]["date_of_birth"]
    birth_date = date.fromisoformat(birth_date_str)
    today = date.today()
    # calculate age
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    return age >= 40


def dates_valid(metadata: Dict[str, Any]) -> bool:
    """ check if all dates are between [2014-2024]
    :param metadata: Dictionary containing patient metadata
    :return: True if all dates are valid, False otherwise
    """
    min_date = date(2014, 1, 1)
    max_date = date(2024, 12, 31)

    date_requested = date.fromisoformat(metadata["test_metadata"]["date_requested"])
    date_completed = date.fromisoformat(metadata["test_metadata"]["date_completed"])
    collection_date = date.fromisoformat(metadata["sample_metadata"]["collection_date"])

    for d in (date_requested, date_completed, collection_date):
        if not (min_date <= d <= max_date):
            return False
    return True


# Generic JSON-like value type
JSONVal = Union[Dict[str, Any], List[Any], str, int, float, bool, None]


def remove_sensitive_data(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Removes all sensitive data related to patient -
    specifically, every field which starts with "_" recursively.
    Returns a NEW dict
    :param metadata: Dictionary containing patient metadata
    :return: Metadata dictionary with sensitive fields removed
    """
    def _clean(obj: JSONVal) -> JSONVal:
        # If it's a dict: drop keys starting with "_" and clean values recursively
        if isinstance(obj, dict):
            return {k: _clean(v) for k, v in obj.items() if not k.startswith("_")}
        # If it's a list: clean each item
        if isinstance(obj, list):
            return [_clean(x) for x in obj]
        # Primitive types are returned as-is
        return obj
    # Clean and cast back to Dict[str, Any] since the top-level is a dict
    cleaned = _clean(metadata)
    return cast(Dict[str, Any], cleaned)


def values_length_valid(metadata: Dict[str, Any], max_len: int = MAX_VALUE_LEN) -> bool:
    """
    passes recursively through the dict and checks that all string values are at most 64 characters long.
    :param metadata: Dictionary containing patient metadata
    :param max_len: Maximum allowed length for string values
    :return: True if all string values are within the allowed length, False otherwise
    """
    def _valid_length(obj: Any) -> bool:
        if isinstance(obj, dict):
            for v in obj.values():
                if not _valid_length(v):
                    return False
            return True

        if isinstance(obj, (list, tuple)):
            for x in obj:
                if not _valid_length(x):
                    return False
            return True

        if isinstance(obj, str):
            return len(obj) <= max_len

        return True

    return _valid_length(metadata)
