#!/bin/python3

"""
The entry point for SigmaDB, the BEST movie database.

usage: sigmadb.py
"""

import sys
import psycopg2

import user_funcs
import input_utils

sigma_title = """Welcome to:

======================================================
   _____ _____ _____ __  __            _____  ____
  / ____|_   _/ ____|  \/  |   /\     |  __ \|  _ \
 | (___   | || |  __| \  / |  /  \    | |  | | |_) |
  \___ \  | || | |_ | |\/| | / /\ \   | |  | |  _ <
  ____) |_| || |__| | |  | |/ ____ \  | |__| | |_) |
 |_____/|_____\_____|_|  |_/_/    \_\ |_____/|____/

======================================================
"""

def main():
    """
    The entry point for the program

    :return: 0 on success
    """

    print(sigma_title)

    login_choice = input_utils.get_input_matching("Would you like create an account (1) or login (2): ", regex="[12]")
    if login_choice == "1":
        user_funcs.create_account()
    elif login_choice == "2":
        print("TODO: Not implemented!")

    return 0


if __name__ == '__main__':
    sys.exit(main())
