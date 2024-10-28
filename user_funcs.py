#!/bin/python3

"""
Functions to handle queries related to users
"""

from datetime import datetime

import input_utils
import hashlib
import movie_funcs

MAX_INPUT_LEN = 255

def pass_to_hash(password: str, username: str) -> str:
    """
    Converts a password to a hash stored in the database.

    :param password: Plaintext password
    :param username: Plaintext username (used for salt)
    :return: The hash of the password
    """
    saltfunc = hashlib.md5()
    saltfunc.update(bytearray(username.encode('utf-8')))

    hashfunc = hashlib.sha512()
    hashfunc.update(bytearray(password.encode('utf-8')))
    hashfunc.update(saltfunc.digest())
    return hashfunc.hexdigest()

def create_account(conn) -> tuple[str, int]:
    """
    Guides the user through creating an account.

    :param conn: Connection to database.
    :return: A tuple (username, userid) of the new account.
    """

    print("Just need a few things to get you started!")

    username = ""
    first_name = ""
    last_name = ""
    password = ""
    email = ""

    with conn.cursor() as curs:
        while username == "":
            username = input_utils.get_input_matching(f"Username: ", MAX_INPUT_LEN)

            # need to check if usernam already taken in the db
            curs.execute("SELECT * FROM \"user\" WHERE username = %s", (username,))
            results = curs.fetchall()

            if len(results) > 0:
                print("Username already taken!")
                username = ""


        while email == "":
            email = input_utils.get_input_matching(f"Email: ", MAX_INPUT_LEN, "^\S+@\S+\.\S+$", "Not a valid email address.")

            # need to check if email already taken in the db
            curs.execute("SELECT * FROM \"user\" WHERE email=%s", (email,))
            results = curs.fetchall()

            if len(results) > 0:
                print("Email already in use!")
                email = ""

        password = pass_to_hash(input_utils.get_input_matching(f"Password: ", MAX_INPUT_LEN, hide_input=True), username)
        first_name = input_utils.get_input_matching(f"First Name: ", MAX_INPUT_LEN)
        last_name = input_utils.get_input_matching(f"Last Name: ", MAX_INPUT_LEN)

        curs.execute("INSERT INTO \"user\"(firstname, lastname, username, password, email, creationdate, lastaccessdate) VALUES (%s, %s, %s, %s, %s, %s, %s)",\
                    (first_name,\
                    last_name,\
                    username,\
                    password,\
                    email,\
                    datetime.now(),\
                    datetime.now()))

        curs.execute("SELECT userid FROM \"user\" WHERE username = %s", (username,))
        results = curs.fetchall()
        if len(results) != 1:
            raise RuntimeError("User not found after being created!")

        return (username, results[0][0])


def login(conn) -> tuple[str, int]:
    """
    Logins the user to their account

    :param conn: Connection to database.
    :return: A tuple (username, userid) of the logged in account.
    """

    username = ""
    password = ""

    with conn.cursor() as curs:
        while True:
            username = input_utils.get_input_matching(f"Username: ", MAX_INPUT_LEN)
            password = pass_to_hash(input_utils.get_input_matching(f"Password: ", MAX_INPUT_LEN, hide_input=True), username)

            curs.execute("SELECT username, userid FROM \"user\" WHERE username = %s AND password = %s", (username, password))
            results = curs.fetchall()

            if len(results) > 1:
                raise RuntimeError("Duplicate users detected!")

            if len(results) == 1:
                # update last login time to now
                curs.execute("UPDATE \"user\" SET lastaccessdate = %s WHERE userid = %s", (datetime.now(), (results[0][1])))
                return results[0]

            print("Username or password incorrect!")

def create_collection(conn, user_ID) -> None:
    """
    creates a new collection for the user and puts the new collection
    in the movie collection table

    modifying the collection and listing the collection are not in this method

    :param conn: The connection to the database to execute SQL statements
    :param user_ID: The ID of the user for their movie collection
    :return: Nothing
    """
    collection_ID = 0
    collection_Name = ""
    loop_state = True
    with conn.cursor() as curs:
        #Query that will be inserted into the MovieCollection table
        query = """
        INSERT INTO moviecollection (collectionid, name, madeby)
        VALUES(collection_ID, collcection_Name, user_ID)
        """
        #A query that will insert the movie_ID the user selected into the incollection table with associated collection_ID
        query_two = """
        INSERT INTO incollection (movieid, collectionid)
        VALUES(movie_ID, collection_ID)
        """

        #Query that gets the last collection ID in the moviecollection table
        collection_ID_query = """
        Select LAST(collectionid) FROM moviecollection
        """

        #Loop that prompts user for information
        print("\ncreate_collection function running...")
        decision = int(input_utils.get_input_matching("""\nTo start creating a new collection, would you like to
                    \nCreate a new collection that will be filled with movies (type 1)
                    \nCreate an empty collection (Type 0): """), regex="[01]")
        if decision == 0:
            curs.execute(collection_ID_query, ())
            collection_ID_results = int(curs.fetchone()[0]) + 1
            collection_ID = str(collection_ID_results)
            collection_Name = input("What would you like to name your new collection?\n")
            curs.execute(query, (collection_ID, collection_Name, user_ID))
        elif decision == 1:
            curs.execute(collection_ID_query, ())
            collection_ID_results = int(curs.fetchone()[0])
            collection_ID_results += 1
            collection_ID = str(collection_ID_results)
            collection_Name = input("What would you like to name your new collection?\n")
            curs.execute(query, (collection_ID, collection_Name, user_ID))
            movie_id = 0
            while loop_state:
                #adding movies that are in the database to a collection when making a new collection
                break_loop = 0
                print("what movie would you like to add?")
                movie_id = movie_funcs.browse_movies(conn)
                if movie_id == -1:
                    print("Was not able to get movieID to add to collectio.\nWill Exit...")
                    loop_state = False
                    break
                else:
                    # Not going to work since you are making a single new collection with movies connected to that collection
                    # Movies have to be looped to connect the collection to that specific movie
                    movie_ID = str(movie_id)
                    curs.execute(query_two, (movie_ID, collection_ID))
            else:
                print("Not an acceptable answer for decision! Ending function")
                return
    return
"""

"""
def modify_collection(conn) -> None:
    pass
"""

"""
def display_collection(conn) -> None:
    pass