#!/bin/python3

"""
The entry point for SigmaDB, the BEST movie database.

usage: sigmadb.py
"""

import sys
import psycopg2
import getpass
from sshtunnel import SSHTunnelForwarder
import json

import user_funcs
import movie_funcs
import input_utils

pass_file = "credentials.json"

sigma_title = """
Welcome to:

======================================================
   _____ _____ _____ __  __            _____  ____
  / ____|_   _/ ____|  \/  |   /\     |  __ \|  _ \\
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
    try:
        with open('credentials.json', 'r') as cf:
            credentials = json.load(cf)

        if not "username" in credentials:
            print("Missing CS account username")
            return 1
        if not "password" in credentials:
            print("Missing CS account password")
            return 1
        dbuser = credentials["username"]
        dbpass = credentials["password"]

        with SSHTunnelForwarder(
            ('starbug.cs.rit.edu', 22),
            ssh_username=dbuser,
            ssh_password=dbpass,
            remote_bind_address=('127.0.0.1', 5432)) as server:

            server.start()
            print("Connected to server!")

            params = {
                'database': 'p320_10',
                'user': dbuser,
                'password': dbpass,
                'host': '127.0.0.1',
                'port': server.local_bind_port
                }

            with psycopg2.connect(**params) as conn:
                print("Connected to database!")

                print(sigma_title)

                login_choice = input_utils.get_input_matching("Would you like create an account (1) or login (2): ", regex="[12]")
                username = ""
                userid = -1
                if login_choice == "1":
                    username, userid = user_funcs.create_account(conn)
                elif login_choice == "2":
                    username, userid = user_funcs.login(conn)

                # Login failed (somehow), this shouldn't be possible (normally)
                if username == "" or userid == -1:
                    return 1

                print(f"\nWelcome {username}!\n")

                print("What would you like to do?")

                action = ""
                while action != "1":
                    action = input_utils.get_input_matching("1 - exit\n2 - browse movies\n> ", regex="[12]")

                    match action:
                        case "2":
                            movie_funcs.browse_movies(conn)

                print("Goodbye!")

    except KeyboardInterrupt:
        # Keyboard interrupt is not a failure
        print("Goodbye!")
        return 0
    except Exception as e:
        print(e)
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
