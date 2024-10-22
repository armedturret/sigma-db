#!/bin/python3

"""
Functions to help with movies
"""

from datetime import date

import input_utils

def browse_movies(conn):
    print("What would you like to search by?")

    search_type = input_utils.get_input_matching("1 - Title\n2 - Release Date\n3 - Cast Member\n4 - Studio Name\n5 - Genre\n> ", regex="[12345]")

    with conn.cursor() as curs:
        # This query concatenates genres together, but it only lists the earlieast release date
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