#!/bin/python3

"""
Functions to help with movies
"""

import datetime

import input_utils

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
        # TODO: Update this to display the following (at a minimum): name, cast members, director, length, rating
        # TODO: Actually sort this shit (required and options)
        # TODO: Format this list
        query = """
        SELECT
            movieid, title, length,
            (
                SELECT
                    STRING_AGG(g.genrename, ', ')
                FROM
                    "genre" AS g
                WHERE
                    g.genreid IN
                    (
                        SELECT genreid FROM "moviegenre" WHERE moviegenre.movieid = m.movieid
                    )
            ),
            (
                SELECT
                    MIN(releasedate)
                FROM
                    "movierelease"
                WHERE
                    movierelease.movieid = m.movieid
            )
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
                print(args)
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

        curs.execute(query, args)
        print(curs.fetchall())