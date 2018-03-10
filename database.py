#!/usr/bin/env python3

# This file is a part of Lector, a Qt based ebook reader
# Copyright (C) 2017 BasioMeusPuga

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import pickle
import sqlite3
from PyQt5 import QtCore


class DatabaseInit:
    def __init__(self, location_prefix):
        os.makedirs(location_prefix, exist_ok=True)
        database_path = os.path.join(location_prefix, 'Lector.db')

        if not os.path.exists(database_path):
            self.database = sqlite3.connect(database_path)
            self.create_database()

    def create_database(self):
        # TODO
        # Add separate columns for:
        # addition mode
        self.database.execute(
            "CREATE TABLE books \
            (id INTEGER PRIMARY KEY, Title TEXT, Author TEXT, Year INTEGER, DateAdded BLOB, \
            Path TEXT, Position BLOB, ISBN TEXT, Tags TEXT, Hash TEXT, LastAccessed BLOB,\
            Bookmarks BLOB, CoverImage BLOB)")

        # CheckState is the standard QtCore.Qt.Checked / Unchecked
        self.database.execute(
            "CREATE TABLE directories (id INTEGER PRIMARY KEY, Path TEXT, \
            Name TEXT, Tags TEXT, CheckState INTEGER)")
        self.database.commit()
        self.database.close()


class DatabaseFunctions:
    def __init__(self, location_prefix):
        database_path = os.path.join(location_prefix, 'Lector.db')
        self.database = sqlite3.connect(database_path)

    def set_library_paths(self, data_iterable):
        # TODO
        # INSERT OR REPLACE is not working
        # So this is the old fashion kitchen sink approach

        self.database.execute("DELETE FROM directories")

        for i in data_iterable:
            path = i[0]
            name = i[1]
            tags = i[2]
            is_checked = i[3]

            sql_command = (
                "INSERT OR REPLACE INTO directories (ID, Path, Name, Tags, CheckState)\
                 VALUES ((SELECT ID FROM directories WHERE Path = ?), ?, ?, ?, ?)")
            self.database.execute(sql_command, [path, path, name, tags, is_checked])

        self.database.commit()
        self.database.close()

    def add_to_database(self, data):
        # data is expected to be a dictionary
        # with keys corresponding to the book hash
        # and corresponding items containing
        # whatever else needs insertion
        # Haha I said insertion

        # Add the current datetime value to each file's database entry
        # current_time = datetime.datetime.now()
        current_datetime = QtCore.QDateTime().currentDateTime()
        current_datetime_bin = sqlite3.Binary(pickle.dumps(current_datetime))

        for i in data.items():
            book_hash = i[0]
            title = i[1]['title']
            author = i[1]['author']
            year = i[1]['year']
            path = i[1]['path']
            cover = i[1]['cover_image']
            isbn = i[1]['isbn']
            tags = i[1]['tags']
            if tags:
                # Is a list. Needs to be a string
                tags = ', '.join([str(j) for j in tags])
            else:
                # Is still a list. Needs to be None.
                tags = None

            sql_command_add = (
                "INSERT OR REPLACE INTO \
                books (Title, Author, Year, DateAdded, Path, ISBN, Tags, Hash, CoverImage) \
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)")

            cover_insert = None
            if cover:
                cover_insert = sqlite3.Binary(cover)

            self.database.execute(
                sql_command_add,
                [title, author, year, current_datetime_bin,
                 path, isbn, tags, book_hash, cover_insert])

        self.database.commit()
        self.database.close()

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
            data = self.database.execute(sql_command_fetch).fetchall()
            self.database.close()

            if data:
                # Because this is the result of a fetchall(), we need an
                # ugly hack (tm) to get correct results
                if fetch_one:
                    return data[0][0]

                return data
            else:
                return None

        except (KeyError, sqlite3.OperationalError):
            print('SQLite is in wretched rebellion @ data fetching handling')

    def fetch_covers_only(self, hash_list):
        parameter_marks = ','.join(['?' for i in hash_list])
        sql_command = f"SELECT Hash, CoverImage from books WHERE Hash IN ({parameter_marks})"
        data = self.database.execute(sql_command, hash_list).fetchall()
        self.database.close()
        return data

    def modify_metadata(self, metadata_dict, book_hash):
        def generate_binary(column, data):
            if column in ('Position', 'LastAccessed', 'Bookmarks'):
                return sqlite3.Binary(pickle.dumps(data))
            elif column == 'CoverImage':
                return sqlite3.Binary(data)
            else:
                return data

        sql_command = 'UPDATE books SET '
        update_data = []
        for i in metadata_dict.items():
            sql_command += i[0] + ' = ?, '
            bin_data = generate_binary(i[0], i[1])
            update_data.append(bin_data)

        sql_command = sql_command[:-2]
        sql_command += ' WHERE Hash = ?'
        update_data.append(book_hash)

        try:
            self.database.execute(
                sql_command, update_data)
        except sqlite3.OperationalError:
            print('SQLite is in wretched rebellion @ metadata handling')

        self.database.commit()
        self.database.close()

    def delete_from_database(self, column_name, target_data):
        # target_data is an iterable

        if column_name == '*':
            self.database.execute('DELETE FROM books')
        else:
            sql_command = f'DELETE FROM books WHERE {column_name} = ?'
            for i in target_data:
                self.database.execute(sql_command, (i,))

        self.database.commit()
        self.database.close()

    def vacuum_database(self):
        self.database.execute("VACUUM")
        return True
