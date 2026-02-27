import re

def remove_ANSI_color_codes(input_line: str) -> str:
    '''
    Cleans the input string by removing ANSI color codes.
    
    :param input_line: line of text including ANSI color codes
    :return: line free of ANSI color codes
    :rtype: str
    '''
    # UPDATED: Now includes \x1b to catch the Escape character too
    ansi_code_pattern = re.compile(r'\x1b\[\d+(?:;\d+)*m')
    return ansi_code_pattern.sub('', input_line)