#!/bin/python3

"""
Runs a bunch of sql statements then makes sure our data set is ok.

usage: data_loader.py <in_file>
"""

import sys
import psycopg2
from sshtunnel import SSHTunnelForwarder
import json

pass_file = "credentials.json"

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

                lines_seen = set()
                with conn.cursor() as curs, open(sys.argv[1]) as f:
                    for line in f:
                        if line not in lines_seen:
                            try:
                                lines_seen.add(line)
                                curs.execute(line)
                                conn.commit()
                            except Exception as e:
                                print(e)
                                conn.commit()
                with conn.cursor() as curs:
                    curs.execute("delete from watched as w where w.watchduration > (select m.length from movie as m where m.movieid = w.movieid)")

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
