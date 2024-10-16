import re
from typing import Union


def extract_bus_number(message: str) -> Union[str, None]:
    """Returns number only i.e.
    jt-100 -> 100
    JT100 -> 100
    100 -> 100
    pc200 -> 200
    returns None if not found
    """

    replace = ["-", "jt", "ac", "lc", "pw"]

    match = re.search(r"\b(jt|ac|pw|lc)?-?(\d+)\b", message, re.IGNORECASE)

    if match:
        matched_str = match.group(0)
        for query in replace:
            matched_str = matched_str.lower().replace(query, "")
        return matched_str

    return None
