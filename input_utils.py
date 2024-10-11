#!/bin/python3

"""
Some functions to help with input validation
"""

import re

def get_input_matching(prompt: str, max_len: int = -1, regex: str = None, failure: str = "Invalid input!") -> str:
    """
    Gets non-null input from the user until it matches the regular expression.

    :param prompt: Prompt to display.
    :param max_len: Maximimum length of the string. Leave -1 for no limit.
    :param regex: Regular expression to use. Leave blank for none.
    :param failure: Text to print on failure.
    :return: The user's input.
    """

    invalid = True
    sanitized_input = ""

    while invalid:
        invalid = False
        sanitized_input = input(prompt).strip()

        # must NOT be blank
        if sanitized_input == "":
            invalid = True

        if max_len != -1 and len(sanitized_input) > max_len:
            invalid = True

        if regex and re.match(regex, sanitized_input) == None:
            invalid = True

        if invalid and failure != None:
            print(failure)

    return sanitized_input