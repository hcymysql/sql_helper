import re

def check_percent_position(string):
    string = string.lower()
    pattern = r".*like\s+'%|.*like\s+concat\(+'%"
    matches = re.findall(pattern, string)
    if matches:
        return True
    else:
        return False