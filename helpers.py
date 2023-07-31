import re


def find_nested_dict_key(dictionary, key):
    """
    Finds a key in a dictionary with arbitrary depth of nesting.

    Args:
        dictionary (dict): The dictionary to search.
        key (str): The key to look for.

    Returns:
        Any: The value associated with the key if found, otherwise None.
    """
    if isinstance(dictionary, dict):
        for k, v in dictionary.items():
            if k == key:
                return v
            elif isinstance(v, dict):
                result = find_nested_dict_key(v, key)
                if result is not None:
                    return result
            elif isinstance(v, list):
                for index, item in enumerate(v):
                    if isinstance(item, dict):
                        result = find_nested_dict_key(item, key)
                        if result is not None:
                            return result
    return None


def extract_string_between(text, start, end):
    pattern = re.escape(start) + "(.*?)" + re.escape(end)
    match = re.search(pattern, text)
    if match:
        return match.group(1)
    else:
        return None
