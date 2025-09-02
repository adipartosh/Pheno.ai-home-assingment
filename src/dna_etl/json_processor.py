from datetime import date
from typing import Any, Dict

def is_patient_at_least_40(metadata: Dict[str, Any]) -> bool:
    """
    Checks if the patient is at least 40 years old.
    :param metadata: Dictionary containing patient metadata
    :return: True if the patient is at least 40 years old, False otherwise
    """
    # extract birth date
    birth_date_str = metadata["individual_metadata"]["date_of_birth"]
    birth_date = date.fromisoformat(birth_date_str)
    today = date.today()
    # calculate age
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    return age >= 40
