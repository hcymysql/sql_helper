import re

def check_percent_position(string):
    string = string.lower()
    pattern = r".*like\s+'%|.*like\s+concat\(+'%|.*regexp\s+"
    matches = re.findall(pattern, string)
    if matches:
        return True
    else:
        return False


def extract_function_index(string):
    pattern = r'\b(\w+)\('
    matches = re.findall(pattern, string)
    function_indexes = set(matches)
    if function_indexes:
        return ', '.join(function_indexes)
    else:
        return False
