#!/usr/bin/env python3

import sqlite3
import os

class DatabaseInit:
    def __init__(self, location_prefix):
        os.makedirs(location_prefix, exist_ok=True)
        database_path = os.path.join(location_prefix, 'Lector.db')

        if not os.path.exists(database_path):
            self.database = sqlite3.connect(database_path)
            self.create_database()
        else:
            self.database = sqlite3.connect(database_path)

    def create_database(self):
        self.database.execute(
            "CREATE TABLE books \
            (id INTEGER PRIMARY KEY, Title TEXT, Path TEXT, \
            ISBN TEXT, Tags TEXT, Hash TEXT, CoverImage BLOB)")
        self.database.execute(
            "CREATE TABLE cache \
            (id INTEGER PRIMARY KEY, Name TEXT, Path TEXT, CachedDict BLOB)")
        # It's assumed that any cached books will be pickled and put into the
        # database at time of closing

        self.database.commit()


class DatabaseFunctions:
    def __init__(self, location_prefix):
        database_path = os.path.join(location_prefix, 'Lector.db')
        self.database = sqlite3.connect(database_path)

    def add_to_database(self, book_data):
        # book_data is expected to be a dictionary
        # with keys corresponding to the book hash
        # and corresponding items containing
        # whatever else needs insertion
        # Haha I said insertion

        for i in book_data.items():
            book_hash = i[0]
            book_title = i[1]['title'].replace("'", "")
            book_path = i[1]['path']
            book_cover = i[1]['cover_image']
            book_isbn = i[1]['isbn']

            # Check if the file might not already be in the database
            hash_from_database = self.fetch_data(
                ('Title',),
                'books',
                {'Hash': book_hash},
                'EQUALS',
                True)

            sql_command_add = (
                "INSERT INTO books (Title,Path,ISBN,Hash,CoverImage) VALUES(?, ?, ?, ?, ?)")

            # TODO
            # This is a placeholder. You will need to generate book covers
            # in case none are found
            if not hash_from_database and book_cover:
                self.database.execute(
                    sql_command_add,
                    [book_title, book_path, book_isbn, book_hash, sqlite3.Binary(book_cover)])

        self.database.commit()

    def fetch_data(self, columns, table, selection_criteria, equivalence, fetch_one=False):
        # columns is a tuple that will be passed as a comma separated list
        # table is a string that will be used as is
        # selection_criteria is a dictionary which contains the name of a column linked
        # to a corresponding value for selection

        # Example:
        # Name and AltName are expected to be the same
        # sel_dict = {
        #     'Name': 'sav',
        #     'AltName': 'sav'
        # }
        # data = DatabaseFunctions().fetch_data(('Name',), 'books', sel_dict)
        try:
            column_list = ','.join(columns)
            sql_command_fetch = f"SELECT {column_list} FROM {table}"
            if selection_criteria:
                sql_command_fetch += " WHERE"

                if equivalence == 'EQUALS':
                    for i in selection_criteria.keys():
                        search_parameter = selection_criteria[i]
                        sql_command_fetch += f" {i} = '{search_parameter}' OR"

                elif equivalence == 'LIKE':
                    for i in selection_criteria.keys():
                        search_parameter = "'%" + selection_criteria[i] + "%'"
                        sql_command_fetch += f" {i} LIKE {search_parameter} OR"

                sql_command_fetch = sql_command_fetch[:-3]  # Truncate the last OR

            # book data is returned as a list of tuples
            book_data = self.database.execute(sql_command_fetch).fetchall()

            if book_data:
                # Because this is the result of a fetchall(), we need an
                # ugly hack (tm) to get correct results
                if fetch_one:
                    return book_data[0][0]

                return book_data
            else:
                return None

        # except sqlite3.OperationalError:
        except KeyError:
            print('SQLite is in rebellion, Commander')
