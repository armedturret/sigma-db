#!/bin/python3

"""
Some functions to help with input validation
"""

import re
import getpass

def get_input_matching(prompt: str, max_len: int = -1, regex: str = None, failure: str = "Invalid input!", hide_input: bool = False) -> str:
    """
    Gets non-null input from the user until it matches the regular expression.

    :param prompt: Prompt to display.
    :param max_len: Maximimum length of the string. Leave -1 for no limit.
    :param regex: Regular expression to use. Leave blank for none.
    :param failure: Text to print on failure.
    :param hide_input: Whether the input is sensitive and should be hidden.
    :return: The user's input.
    """

    invalid = True
    sanitized_input = ""

    while invalid:
        invalid = False
        if hide_input:
            sanitized_input = getpass.getpass(prompt).strip()
        else:
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