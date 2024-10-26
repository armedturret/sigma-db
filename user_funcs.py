#!/bin/python3

"""
Functions to handle queries related to users
"""

from datetime import datetime

import input_utils
import hashlib

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
                return results[0]

            print("Username or password incorrect!")
    conn.commit()

def follow_user(conn, userid):
    """
    Guides user through following another user

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
    Guides user through unfollowing another user

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

def following_menu(conn, userid):
    """
    Give the user the option to either follow/unfollow a user or view who they are following

    :param conn: Connection to database
    :param userid: ID of currently logged in user
    """
    print("following submenu: What would you like to do?")
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
                #TODO
                print("view who you follow function!")
        
    print("Back to menu!")
