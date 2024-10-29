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
    #Query that will be inserted into the MovieCollection table
    query = """
    INSERT INTO moviecollection (name, madeby)
    VALUES(%s, %s)
    """
    #A query that will insert the movie_ID the user selected into the incollection table with associated collection_ID
    query_two = """
    INSERT INTO incollection (movieid, collectionid)
    VALUES(%s, %s)
    """

    #Query that gets the last collection ID in the moviecollection table
    collection_ID_query = """
    Select collectionid FROM moviecollection AS mc
    ORDER BY mc.collectionid DESC LIMIT 1
    """
    collection_ID = 0
    collection_Name = ""
    loop_state = True
    with conn.cursor() as curs:
        user_ID = str(user_ID)
        #Loop that prompts user for information
        print("\ncreate_collection function running...")
        decision = int(input_utils.get_input_matching("\n1 - Create an empty collection \n2 - Create a new collection that will be filled with movies: ", regex='[12]'))
        #Creates an empty collection
        if decision == 1:
            collection_Name = input("What would you like to name your new collection?\n")
            curs.execute("INSERT INTO moviecollection (name, madeby) VALUES(%s, %s)", (collection_Name, user_ID))
        elif decision == 2:
            collection_Name = input("What would you like to name your new collection?\n")
            curs.execute("INSERT INTO moviecollection (name, madeby) VALUES(%s, %s)", (collection_Name, user_ID))
            curs.execute(collection_ID_query, ())
            collection_ID_results = int(curs.fetchone()[0])
            collection_ID = str(collection_ID_results)
            print(collection_ID_results)
            movie_id = 0
            while loop_state:
                #adding movies that are in the database to a collection when making a new collection
                break_loop = 0
                print("what movie would you like to add?")
                movie_id = movie_funcs.browse_movies(conn)
                if movie_id == -1:
                    print("Was not able to get movieID to add to collection.\nWill Exit...")
                    loop_state = False
                    break
                else:
                    movie_ID = str(movie_id)
                    curs.execute(query_two, (movie_ID, collection_ID))
                break_loop = int(input_utils.get_input_matching("""\n0 - Continue adding movies
                                                                \n1 - Stop adding movies: """))
                if break_loop != 1 or 0:
                    while True:
                        print(f"Invalid Input of {break_loop}, please enter a valid input")
                        break_loop = int(input_utils.get_input_matching("""\n0 - Continue adding movies
                                                                    \n1 - Stop adding movies: """))
                        if break_loop == "0" or "1":
                            break
                elif break_loop == 0:
                    pass
                else:
                    break
            else:
                print("Not an acceptable answer for decision! Ending function")
                return
    print(f"Finished create_collection function!!")



def modify_collection(conn, user_ID) -> None:
    """
    modify a current collection that is in the incollection table 

    :param conn: The connection to the database
    :param user_ID: The ID of the user
    :param movie_ID: The ID of the current movie
    :return: Nothing
    """
    # A Query to get the collection ID for a certain User ID
    query = """
    SELECT collectionid FROM moviecollection WHERE madeby = %s
    """
    # A query to remove a movie from a collection
    remove_movie_query = """
    DELETE FROM incollection WHERE movieid = %s AND collectionid = %s
    """
    # A query to add a movie into a collection
    add_movie_query = """
    INSERT INTO incollections (movieid, collectionid)
    VALUES(%s, %s)
    """
    #
    delete_incollection_query = """
    DELETE FROM incollection 
    WHERE movieid = %s AND collectionid = %s
    """
    #
    delete_moviecollection_query = """
    DELETE FROM moviecollection 
    WHERE collectionid = %s
    """
    #
    change_name_query = """
    UPDATE moviecollection
    SET name = %s
    WHERE collectionid = %s
    """
    collection_ID = ""
    movie_ID = movie_funcs.browse_movies(conn)
    with conn.cursor() as curs:
        curs.execute(query, (user_ID,))
        collection_ID_list = curs.fetchall()
        for i in range(0, len(collection_ID_list)-1):
            if collection_ID_list[i] is None:
                print("Collection ID was not found for correlated User ID!! Ending function...")
                return
            print("what action would you like to do?")
            action = input_utils.get_input_matching("""1 - remove a movie\n2 - add a movie
                                                    \n3 - modify name of collection\n4 - delete collection
                                                    \n5 - exit function: """)
            if action is not "1" or "2" or "3" or "4" or "5":
                while True:
                    print("action is not the correct input. Please input the right number")
                    action = input_utils.get_input_matching("""1 - remove a movie\n2 - add a movie
                                                        \n3 - modify name of collection\n4 - delete collection:
                                                        \n5 - exit function: """)
                    if action is "1" or "2" or "3" or "4" or "5":
                        break
            match action:
                # action for removing a movie
                case "1":
                    curs.execute(remove_movie_query, (movie_ID, collection_ID_list[i]))
                    # action for adding a movie
                case "2":
                    curs.execute(add_movie_query, (movie_ID, collection_ID_list[i]))
                case "3":
                    new_name = input("what would you like to name your collection: ")
                    curs.execute(change_name_query, (new_name, collection_ID_list[i]))
                case "4":
                      curs.execute(delete_moviecollection_query, (collection_ID_list[i]))
                case "5":
                    return
    if movie_ID == -1:
        return
    return

def browse_collections(conn, user_ID) -> None:
    """
    A different version to print all information of a users collection/
    list of collections

    :param conn: Connection to the database
    :param user_ID: The ID of the user
    :return: Nothing
    """
    #
    browse_query = """
    SELECT name FROM moviecollection 
    WHERE madeby = %s ORDER BY name ASC
    """
     # A Query to get the collection ID for a certain User ID
    query = """
    SELECT collectionid FROM moviecollection WHERE madeby = %s
    """
    # A Query to get the name of the collection to be displayed
    get_name_query = """
    SELECT name FROM moviecollection
    WHERE collectionid = %s 
    ORDER BY ASC
    """
    # A query to copunt the number of movies in a collection
    count_movie_query = """
    SELECT COUNT(movieid) FROM incollection
    WHERE collectionid = %s
    """
    # A query to get all lengths of all movies in a collection
    get_length_movie_query = """
    SELECT SUM(length) FROM movie as m
    WHERE m.movieid in (
    SELECT movieid FROM incollection
    WHERE collectionid = %s
    )
    """
    print(f"Printing all collections belong to the user...")
    collection_ID = ""
    with conn.cursor() as curs:
        curs.execute(query, (user_ID,))
        #Get list of collection IDs for a user and iterate through them
        collection_ID_list = curs.fetchall()
        for i in range (0, len(collection_ID_list)-1):

            #Get name of current collection ID
            collection_ID = collection_ID_list[i]
            curs.execute(browse_query, (collection_ID))
            collection_name = curs.fectone()[0]
            print(collection_name)

            #Get number of movies for current collection ID
            curs.execute(count_movie_query, (collection_ID))
            num_movie = int(curs.fetchone()[0])

            #Get total length of all movies in the collection (in minutes)
            curs.execute(get_length_movie_query, (collection_ID))
            total_movie_length = int(curs.fetchone()[0])
            movie_length_hours = total_movie_length/60
            movie_length_mins = total_movie_length%60
            #print a formated string of each collection
            print(f"Name of collection: {collection_name}\n\tTotal number of movies {num_movie}\n\tTotal length of all movies in collection: {movie_length_hours}:{movie_length_mins}")


    
    return ""

def display_collection(conn, user_ID) -> None:
    """
    The list of collections 
    """
     # A Query to get the collection ID for a certain User ID
    query = """
    SELECT collectionid FROM moviecollection WHERE madeby = %s
    """
    # A Query to get the name of the collection to be displayed
    get_name_query = """
    SELECT name FROM moviecollection
    WHERE collectionid = %s
    """
    # A query to copunt the number of movies in a collection
    count_movie_query = """
    SELECT COUNT(movieid) FROM incollection
    WHERE collectionid = %s
    """
    # A query to get all lengths of all movies in a collection
    get_length_movie_query = """
    SELECT length FROM movie as m
    WHERE m.movieid in (
    SELECT movieid FROM incollection
    WHERE collectionid = %s
    )
    """


    collection_ID = ""
    loop_state = True
    with conn.cursor() as curs:
        curs.execute(query, (user_ID))
        collection_ID = curs.fetchall()
        while loop_state:
            display_name = curs.execute(get_name_query, (collection_ID))
            print("Name:" + display_name)
            curs.execute(count_movie_query, (collection_ID))
            num_movies = int(curs.fetchone()[0])
            print("Number of movies in " + display_name + " is: " + str(num_movies))
            curs.execute(get_length_movie_query, (collection_ID))
            length = curs.fetchone()
            total_collection_length = 0
            list_length = list(length.keys())
            for i in range(len(list_length)):
                total_collection_length += int(list_length[i])
            print("total length of all movies in the collection is Hours:" + str(total_collection_length/60) + 
                  " Minutes:" + str(total_collection_length%60))
            finish_loop_decider = input_utils.get_input_matching("""1 - keep displaying collections \
                                                                 \n2 - end displaying collections""")
            if int(finish_loop_decider) != 1 or 2:
                while True:
                    print("loop decider is not the correct input. Please input the right number")
                    finish_loop_decider = input_utils.get_input_matching("""1 - keep displaying collections \
                                                            \n2 - end displaying collections """)
                    if int(finish_loop_decider) == 1 or 2:
                        break
            match finish_loop_decider:
                case "1":
                    pass
                case "2":
                    loop_state = False
    return