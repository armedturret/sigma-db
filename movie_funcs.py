#!/bin/python3

def rating(conn, stars):
    """
    Assigns a movie a rating given by a user.

    :param stars: The number of stars for the rating.
    """

    with conn.cursor() as curs:
        # if rating already exists for given user, update rating

        # otherwise create new rating for user
        return
