import re

def check_percent_position(string):
    string = string.lower()
    pattern = r".*like\s+'%|.*like\s+concat\(+'%|.*regexp\s+"
    matches = re.findall(pattern, string)
    if matches:
        like_pattern = r"like\s+(?:concat\(.*?\)|'%%'|\'.*?%(?:.*?)?\')"
        like_match = re.search(like_pattern, string)
        if like_match:
            return True, like_match.group()
        #return True
    return False, None


def extract_function_index(string):
    #pattern = r'\b(\w+)\('
    #pattern = r'\b(\w+)\(.*\).*[>=<!=<>]'
    pattern = r'\b(\w+(\(.*\).*[>=<!=<>]))'
    matches = re.findall(pattern, string)
    #function_indexes = set(matches)
    function_indexes = [match[0] for match in matches]
    if function_indexes:
        return ', '.join(function_indexes)
    else:
        return False
