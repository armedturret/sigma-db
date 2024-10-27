#!/bin/python3

"""
Functions to help with movies
"""

import datetime
from enum import IntEnum

import input_utils

class SortOrder(IntEnum):
    ASCENDING = 0
    DESCENDING = 1
    NONE = 2

class SortParameter():
    def __init__(self, name: str, sql_name: str, initial_order: SortOrder):
        self.name = name
        self.sql_name = sql_name
        self.order = initial_order

    def display_text(self) -> str:
        """
        The text to display to the user
        """
        order_text = "none"
        match self.order:
            case SortOrder.ASCENDING:
                order_text = "ascending"
            case SortOrder.DESCENDING:
                order_text = "descending"

        return "({}){}: {}".format(self.name[0], self.name[1:], order_text)

    def query_text(self) -> str:
        """
        The sql query to pass to an order clause
        """
        match self.order:
            case SortOrder.ASCENDING:
                return self.sql_name + " ASC"
            case SortOrder.DESCENDING:
                return self.sql_name + " DESC"
        return ""


def browse_movies(conn) -> int:
    """
    Browses the list of movies and optionally gives the user the opportunity
    to select a movie to rate/view it.

    Rating and viewing are not handled in this method.

    :param conn: Connection to database.
    :return: The movie id the user wants to view or -1 if they exited.
    """

    print("What would you like to search by?")

    search_type = input_utils.get_input_matching("1 - Title\n2 - Release Date\n3 - Cast Member\n4 - Studio Name\n5 - Genre\n> ", regex="[12345]")

    with conn.cursor() as curs:
        # This query concatenates genres together, but it only lists the earlieast release date
        query = """
        SELECT
            movieid, title, length, mpaarating,
            (
                SELECT
                    MIN(releasedate)
                FROM
                    "movierelease"
                WHERE
                    movierelease.movieid = m.movieid
            ) AS first_release,
            (
                SELECT
                    STRING_AGG(g.genrename, ', ' ORDER BY g.genrename)
                FROM
                    "genre" AS g
                WHERE
                    g.genreid IN
                    (
                        SELECT genreid FROM "moviegenre" WHERE moviegenre.movieid = m.movieid
                    )
            ) as genres,
            (
                SELECT
                    STRING_AGG(CONCAT(c.firstname, ' ', c.lastname), ', ' ORDER BY CONCAT(c.firstname, ' ', c.lastname))
                FROM
                    "crewmember" AS c
                WHERE
                    c.crewid IN
                    (
                        SELECT crewid FROM "actsin" WHERE actsin.movieid = m.movieid
                    )
            ) AS crew,
            (
                SELECT
                    STRING_AGG(CONCAT(c.firstname, ' ', c.lastname), ', ' ORDER BY CONCAT(c.firstname, ' ', c.lastname))
                FROM
                    "crewmember" AS c
                WHERE
                    c.crewid IN
                    (
                        SELECT crewid FROM "directed" WHERE directed.movieid = m.movieid
                    )
            ) AS directors,
            (
                SELECT
                    STRING_AGG(s.name, ', ' ORDER BY s.name)
                FROM
                    "studio" AS s
                WHERE
                    s.studioid IN
                    (
                        SELECT studioid FROM "produced" WHERE produced.movieid = m.movieid
                    )
            ) AS studios,
            (
                SELECT
                    AVG(rating)
                FROM
                    "rated"
                WHERE
                    rated.movieid = m.movieid
            ) AS avg_rating
        FROM "movie" AS m
        """
        args = []
        match search_type:
            case "1":
                query += "WHERE LOWER(m.title) LIKE LOWER(%s)"
                args.append("%{}%".format(input_utils.get_input_matching("Movie Name: ")))
            case "2":
                year = input_utils.get_input_matching("Year: ", regex="^\d+$")
                month = input_utils.get_input_matching("Month (1-12): ", regex="^(0?[1-9]|1[0-2])$")
                day = input_utils.get_input_matching("Day (1-31): ", regex="^(0?[1-9]|[12][0-9]|3[01])$")
                query += """
                    WHERE m.movieid IN
                    (
                        SELECT
                            mr.movieid
                        FROM
                            "movierelease" AS mr
                        WHERE
                            mr.releasedate = %s
                    )
                """
                args.append(datetime.date(int(year), int(month), int(day)))
            case "3":
                query += """
                    WHERE m.movieid IN
                    (
                        SELECT
                            a.movieid
                        FROM
                            "actsin" AS a
                        LEFT JOIN
                            "crewmember" AS c ON (a.crewid = c.crewid)
                        WHERE
                            LOWER(c.firstname) LIKE LOWER(%s) AND LOWER(c.lastname) LIKE LOWER(%s)
                    )
                """
                args.append("%{}%".format(input_utils.get_input_matching("Cast Member's First Name: ")))
                args.append("%{}%".format(input_utils.get_input_matching("Cast Member's Last Name: ")))
            case "4":
                query += """
                    WHERE m.movieid IN
                    (
                        SELECT
                            p.movieid
                        FROM
                            "produced" AS p
                        LEFT JOIN
                            "studio" AS s ON (p.studioid = s.studioid)
                        WHERE
                            LOWER(s.name) LIKE LOWER(%s)
                    )
                """
                args.append("%{}%".format(input_utils.get_input_matching("Studio Name: ")))
            case "5":
                query += """
                    WHERE m.movieid IN
                    (
                        SELECT
                            mg.movieid
                        FROM
                            "moviegenre" AS mg
                        LEFT JOIN
                            "genre" AS g ON (mg.genreid = g.genreid)
                        WHERE
                            LOWER(g.genrename) LIKE LOWER(%s)
                    )
                """
                args.append("%{}%".format(input_utils.get_input_matching("Genre: ")))

        output_format_rating = "%s - Title: '%s', Runtime (min): %s, MPAA Rating: %s, Release Date: %s, Genres: %s, Crew Member(s): '%s', Director(s): '%s', Studios(s): '%s', Average User Rating: %.1f"
        output_format_norating = "%s - Title: '%s', Runtime (min): %s, MPAA Rating: %s, Release Date: %s, Genres: %s, Crew Member(s): '%s', Director(s): '%s', Studios(s): '%s', Average User Rating: N/A"

        sort_parameters = [SortParameter("title", "title", SortOrder.ASCENDING),\
                    SortParameter("release", "first_release", SortOrder.ASCENDING),\
                    SortParameter("studios", "studios", SortOrder.NONE),\
                    SortParameter("genres", "genres", SortOrder.NONE)]

        skip_query = False
        while True:
            sort_params_string = ", ".join([param.query_text() for param in sort_parameters if param.query_text() != ""])
            display_sorting = ""
            if sort_params_string != "":
                display_sorting = " ORDER BY " + sort_params_string

            if not skip_query:
                curs.execute(query + display_sorting, args)
                results = curs.fetchall()

                for i in range(0, len(results)):
                    result = results[i]
                    if result[-1] != None:
                        print(output_format_rating % ((i,) + result[1:]))
                    else:
                        print(output_format_norating %  ((i,) + result[1:-1]))

            skip_query = False

            print("\nFound %s result(s)" % len(results))
            input_text = "\nSorted by " + ", ".join([order.display_text() for order in sort_parameters]) + "\nSelect a movie by its number to view more actions, 'e' to go back to the menu, or any of the sort actions above\n> "
            user_input = input_utils.get_input_matching(input_text, regex='^(?:\d+|[etrsg])$')

            if user_input.isdigit():
                selected_film = int(user_input)
                if selected_film >= len(results):
                    print("Movie not in list!")
                    skip_query = True

                # user input is not the actual movie id, need to convert here
                return results[selected_film][0]

            elif user_input == 'e':
                return -1
            else:
                for sort_param in sort_parameters:
                    if sort_param.name[0] == user_input:
                        sort_param.order += 1
                        # wrap around sort orders
                        sort_param.order %= 3


def rate_movie(conn, user_id, movie_id):
    """
    Assigns a movie a (0-5 star) rating given by a user.

    :param conn: Connection to the database.
    :param user_id: The ID of the user rating a movie.
    :param movie_id: The ID of the movie being rated.
    """

    rating = int(input_utils.get_input_matching("Enter a rating (0-5): ", regex="^[0-5]$"))

    with conn.cursor() as curs:

        # Check if the user already rated this movie
        curs.execute("SELECT rating FROM rated WHERE userid = %s AND movieid = %s", (user_id, movie_id))
        existing_rating = curs.fetchone()

        if existing_rating:
            # If the user has already rated this movie, update their rating
            curs.execute("UPDATE rated SET rating = %s WHERE userid = %s AND movieid = %s", (rating, user_id, movie_id))
            print(f"Updated your rating for this movie to {rating} stars!")
        else:
            # Otherwise, assign the movie a new rating
            curs.execute("INSERT INTO rated (userid, movieid, rating) VALUES (%s, %s, %s)", (user_id, movie_id, rating))
            print(f"You gave this movie a {rating} star rating!")

        conn.commit()

        return


def watch_movie(conn, user_id, movie_id):
    """
    Allows the user to watch a movie and record when 
    they started and stopped watching.

    :param conn: Connection to the database.
    :param user_id: The ID of the user watching a movie.
    :param movie_id: The ID of the movie being watched.
    """

    date_watched = datetime.datetime.now()

    with conn.cursor() as curs:

        # Get the movie's length
        curs.execute("SELECT length FROM movie WHERE movieid = %s", (movie_id,))
        movie_length = curs.fetchone()[0]

        curs.execute("INSERT INTO watched (userid, movieid, dateTime, watchDuration) VALUES (%s, %s, %s, %s)", 
                     (user_id, movie_id, date_watched, movie_length))

        conn.commit()

    date_and_time = date_watched.strftime("%m/%d/%Y at %I:%M %p")

    print(f"You watched this movie on {date_and_time} for {movie_length} minutes!")

    return
