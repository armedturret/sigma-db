#!/bin/python3

"""
Functions to handle queries related to users
"""

from datetime import datetime
import math

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

        conn.commit()

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
                conn.commit()

                return results[0]

            print("Username or password incorrect!")


def follow_user(conn, userid):
    """
    Guides user through following another user specified by email

    :param conn: Connection to database
    :param userid: ID of currently logged in user
    """
    with conn.cursor() as curs:
        # prompt for email to follow
        print("Who would you like to follow?")
        email = input_utils.get_input_matching("Email: ", MAX_INPUT_LEN,  "^\S+@\S+\.\S+$", "Not a valid email address")

        # check if user exists
        curs.execute("SELECT userid, username FROM \"user\" WHERE email=%s", (email,))
        results = curs.fetchall()
        if len(results) == 0:
            print(f"\nUser with email {email} doesn't exist!")
        else:
            followingid = results[0][0]
            following_username = results[0][1]

            # check if trying to follow self
            if userid == followingid:
                print("\nCan't follow self!")
                return

            # check if already following
            curs.execute("SELECT * FROM \"following\" WHERE followerid = %s AND followingid = %s", (userid, followingid))
            results = curs.fetchall()
            if len(results) > 0:
                print(f"\nAlready following {following_username}!")
                # follow user if not already followed
            else:
                answer = input_utils.get_input_matching(f"follow {following_username}? y/n\n", regex="[yn]")
                match answer:
                    case "y":
                        curs.execute("INSERT INTO \"following\" (followerid, followingid) VALUES (%s, %s)", (userid, followingid))
                        print(f"\nNow following {following_username}!")
    conn.commit()


def unfollow_user(conn, userid):
    """
    Guides user through unfollowing another user specified by email

    :param conn: Connection to database
    :param userid: ID of currently logged in user
    """
    with conn.cursor() as curs:
        # prompt for email to unfollow
        print("Who would you like to unfollow?")
        email = input_utils.get_input_matching("Email: ", MAX_INPUT_LEN,  "^\S+@\S+\.\S+$", "Not a valid email address")

        # check if user exists
        curs.execute("SELECT userid, username FROM \"user\" WHERE email=%s", (email,))
        results = curs.fetchall()
        if len(results) == 0:
            print(f"\nUser with email {email} doesn't exist!")
        else:
            followingid = results[0][0]
            following_username = results[0][1]

            # check if already following
            curs.execute("SELECT * FROM \"following\" WHERE followerid = %s AND followingid = %s", (userid, followingid))
            results = curs.fetchall()
            # unfollow user
            if len(results) > 0:
                answer = input_utils.get_input_matching(f"unfollow {following_username}? y/n\n", regex="[yn]")
                match answer:
                    case "y":
                        curs.execute("DELETE FROM \"following\" WHERE followerid = %s AND followingid = %s", (userid, followingid))
                        print(f"\nUnfollowed {following_username}!")
            else:
                print(f"\nNot following {following_username}!")
    conn.commit()


def view_following(conn, userid):
    """
    Displays 10 other users that the current user follows at a time and gives
    the option to either return to following submenu, view more users, or unfollow a listed user

    :param conn: Connection to database
    :param userid: ID of currently logged in user
    """
    with conn.cursor() as curs:

        action = ""
        start_index = 0
        end_index = 10
        while action != "1":
            # get next 10 users that are followed
            curs.execute("SELECT username, email, userid FROM \"user\" WHERE userid IN (SELECT followingid FROM \"following\" WHERE followerid = %s LIMIT %s OFFSET %s)", (userid, end_index, start_index))
            results = curs.fetchall()

            # if following anyone, display them
            if len(results) > 0:
                # print user number range being shown
                num_diff = 10 - len(results)
                print("\nFollowed users %s-%s:" % (start_index + 1, end_index - num_diff))
                # print 10 users at a time
                for i in range(len(results)):
                    print("\t%s. Username: %s\tEmail: %s" % (i, results[i][0], results[i][1]))

                if len(results) < 10:
                    print("End of following list!")

                # prompt if user wants to go back or see more users
                action = input_utils.get_input_matching("\n1 - back to manage following menu\n2 - view more\n3 - view previous\n4 - unfollow user\n", regex="[1234]")

                match action:
                    # move indexes for next page if available, else repeat page
                    case "2":
                        if len(results) == 10:
                            start_index += 10
                            end_index += 10

                    case "3":
                        if start_index >= 10:
                            start_index -= 10
                            end_index -= 10
                        else:
                            print("Can't go back any further!")

                    # prompts for what user to unfollow
                    case "4":
                        selection = input_utils.get_input_matching("Enter in the number of who to unfollow, 'b' for back\n", regex="[0123456789b]")
                        if selection != "b":
                            selection_index = int(selection)
                            # check if selection is in bounds
                            if selection_index < len(results):
                                selection_id = results[selection_index][2]
                                selection_username = results[selection_index][0]
                                # unfollow user
                                curs.execute("DELETE FROM \"following\" WHERE followerid = %s AND followingid = %s", (userid, selection_id))
                                print(f"Unfollowed %s!\n" % (selection_username))
                            else:
                                print("\nInvalid selection!")

            else:
                print("\nNot following anyone!")
                break
        print("\nBack to manage following submenu!")

    conn.commit()


def following_menu(conn, userid):
    """
    Give the user the option to either follow/unfollow a user or view who they are following

    :param conn: Connection to database
    :param userid: ID of currently logged in user
    """
    print("manage following submenu: What would you like to do?")
    action = ""
    while action != "1":
        action = input_utils.get_input_matching("1 - back to menu\n2 - follow user\n3 - unfollow user\n4 - view who you're following\n", regex="[1234]")

        match action:
            # follow a user
            case "2":
                follow_user(conn, userid)
            # unfollow a user
            case "3":
                unfollow_user(conn, userid)
            # view who you follow
            case "4":
                view_following(conn, userid)

    print("Back to menu!")


def create_collection(conn, user_id) -> None:
    """
    Creates a new empty collection for the user.

    :param conn: The connection to the database to execute SQL statements
    :param user_id: The ID of the user for their movie collection
    """

    collection_name = ""
    with conn.cursor() as curs:
        user_id = str(user_id)
        #Creates an empty collection
        collection_name = input_utils.get_input_matching("What would you like to name your new collection?\n")
        curs.execute("INSERT INTO moviecollection (name, madeby) VALUES (%s, %s)", (collection_name, user_id))

    print("Collection created!")

    conn.commit()


def modify_collection(conn, user_id, collection_id) -> None:
    """
    Modify a collection or view movies in it

    :param conn: The connection to the database
    :param user_id: The ID of the user
    :param collection_id: The ID of the collection
    """

    # A query to remove a movie from a collection
    remove_movie_query = """
    DELETE FROM incollection
    WHERE movieid = %s AND collectionid = %s
    """
    # A query to add a movie into a collection
    add_movie_query = """
    INSERT INTO incollection (movieid, collectionid)
    VALUES (%s, %s)
    """
    # Deletes a collection from the table
    delete_moviecollection_query = """
    DELETE FROM moviecollection
    WHERE collectionid = %s
    """

    # Deletes all movie IDs associated with the collection ID
    delete_all_movie_query = """
    DELETE FROM incollection
    WHERE collectionid = %s
    """

    # Changes the name of the collection
    change_name_query = """
    UPDATE moviecollection
    SET name = %s
    WHERE collectionid = %s
    """

    watch_collection_query = """
    WITH viewing(userid, datetime) AS (VALUES (%s, %s))
    INSERT INTO watched (userid, movieid, datetime, watchduration)
    SELECT viewing.userid, ic.movieid, viewing.datetime, m.length
    FROM incollection AS ic
    LEFT JOIN movie AS m
    ON (m.movieid = ic.movieid)
    CROSS JOIN viewing
    WHERE ic.collectionid = %s
    """

    with conn.cursor() as curs:
        while True:
            curs.execute("SELECT ic.movieid, title, length FROM incollection AS ic LEFT JOIN movie ON (ic.movieid = movie.movieid) WHERE ic.collectionid = %s ORDER BY title", (collection_id,))
            results = curs.fetchall()

            print("\nMovies in collection: ")
            for i in range(0, len(results)):
                result = results[i]
                print("%d - %s (%s min) " % ((i,) + result[1:]))

            print("\nWhat would you like to do?")
            action = int(input_utils.get_input_matching("1 - exit to main menu\n2 - watch all movies\n3 - remove a movie\n4 - add a movie \n5 - modify name of collection\n6 - delete collection\n", regex="^[123456]"))
            match action:
                case 1:
                    return
                case 2:
                    curs.execute(watch_collection_query, (user_id, datetime.now(), collection_id,))
                    conn.commit()
                    print("Watched all movies!")
                case 3:
                    selected_movie = int(input_utils.get_input_matching("Select a movie above to remove: ", regex="^(?:\d+)$"))
                    if selected_movie >= 0 and selected_movie < len(results):
                        curs.execute(remove_movie_query, (results[selected_movie][0], collection_id))
                        conn.commit()
                        print("Movie removed!")
                    else:
                        print("Not a movie in the collection.")
                case 4:
                    movie_id = movie_funcs.browse_movies(conn)
                    if movie_id == -1:
                        print("No movie added!")
                    else:
                        # check if the movie is already in the collection
                        curs.execute("SELECT COUNT(*) FROM incollection WHERE movieid = %s AND collectionid = %s", (movie_id, collection_id))
                        if int(curs.fetchone()[0]) > 0:
                            print("Movie already in collection!")
                        else:
                            curs.execute(add_movie_query, (movie_id, collection_id))
                            print("Movie added!")
                    conn.commit()
                case 5:
                    new_name = input_utils.get_input_matching("What would you like to name your collection: ")
                    curs.execute(change_name_query, (new_name, collection_id))
                    conn.commit()
                case 6:
                    curs.execute(delete_all_movie_query, (collection_id,))
                    curs.execute(delete_moviecollection_query, (collection_id,))
                    conn.commit()
                    print("Collection deleted!")
                    return


def browse_collections(conn, user_id) -> None:
    """
    Displays all the user's collections

    :param conn: Connection to the database
    :param user_id: The ID of the user
    :return: The collection id to modify or -1 if none selected
    """

    get_collections_query = """
    SELECT collectionid, name,
    (
        SELECT COUNT(movieid) FROM incollection AS ic
        WHERE ic.collectionid = mc.collectionid
    ) AS movie_count,
    (
        SELECT SUM(length) FROM movie as m
        WHERE m.movieid in
        (
            SELECT movieid FROM incollection AS ic
            WHERE ic.collectionid = mc.collectionid
        )
    ) AS total_length
    FROM moviecollection AS mc
    WHERE mc.madeby = %s
    ORDER BY name ASC
    """

    with conn.cursor() as curs:
        while True:
            curs.execute(get_collections_query, (user_id,))
            results = curs.fetchall()

            print("\nFound %s collection(s)" % len(results))
            for i in range(0, len(results)):
                result = results[i]
                if result[-1] != None:
                    minutes = int(result[-1])
                    hours = math.floor(minutes / 60)
                    minutes %= 60
                else:
                    minutes = 0
                    hours = 0
                print("%d - %s: %s Movies (%s:%s hrs:min) " % ((i,) + result[1:-1] + (hours,) + (minutes,)))

            user_input = input_utils.get_input_matching("\nSelect a collection number to view it or 'e' to return to menu\n", regex='^(?:\d+|[e])$')

            if user_input == 'e':
                return -1
            elif int(user_input) >= 0 and int(user_input) < len(results):
                return results[int(user_input)][0]
            else:
                print("Not a valid id!")

    conn.commit()

def view_profile(conn, userid) -> None:
    """
    Displays a users profile information of following, number of collections
    and top ten rated movies
    
    :param conn: Connection to the database
    :param userid: The ID of the user
    :return: Nothing since it displays viewer profile.
    """
    # gets the number of collections for a user
    get_num_collections = """
    SELECT COUNT(collectionid) 
    FROM moviecollection
    WHERE madeby = %s
    """

    # get number of followers a user is following 
    get_num_followers = """
    SELECT COUNT(followingid)
    FROM following AS fw
    WHERE fw.followerid = %s
    """

    # Get number of users following a specific user
    get_num_following = """
    SELECT COUNT(*)
    FROM following as fw
    WHERE fw.followingid = %s 
    """

    # Gets the movie names of the top ten highest rated movies for the user
    ten_highest_ratings = """
    SELECT m.title FROM rated as r
    LEFT JOIN movie AS m
    ON m.movieid = r.movieid
    WHERE r.userid = %s
    ORDER BY r.rating DESC
    LIMIT 10
    """
    with conn.cursor() as curs:
        curs.execute(get_num_collections, (userid,))
        num_collections = curs.fetchone()[0]
        print(f"Number of collections: {num_collections}")
        curs.execute(get_num_followers, (userid,))
        num_followers = curs.fetchone()[0]
        print(f"Number of followers: {num_followers}")
        curs.execute(get_num_following, (userid,))
        num_following = curs.fetchone()[0]
        print(f"Number of users followed: {num_following}")
        curs.execute(ten_highest_ratings, (userid,))
        top_ten = curs.fetchall()
        print("Top 10 rated movies: ")
        for i in range(len(top_ten)):
            print(f"{i+1}: {top_ten[i][0]}")
    return
