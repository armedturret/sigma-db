#!/bin/python3

"""
Functions to handle queries related to users
"""

import input_utils

MAX_INPUT_LEN = 255

def create_account() -> str:
    """
    Guides the user through creating an account

    :return: The username of the new account
    """

    print("Just need a few things to get you started!")

    username = ""
    firstname = ""
    lastname = ""
    password = ""
    email = ""

    while username == "":
        username = input_utils.get_input_matching(f"Username (max {MAX_INPUT_LEN} characters): ", MAX_INPUT_LEN)
        
        # need to check if it's already taken in the db

