#!/usr/bin/env python3

import sqlite3
import os


class DatabaseFunctions:
    def __init__(self, location_prefix):
        os.makedirs(location_prefix, exist_ok=True)
        self.database_path = os.path.join(
            location_prefix, 'Lector.db')

        self.database = sqlite3.connect(self.database_path)
        if not os.path.exists(self.database_path):
            self.create_database()

    def create_database(self):
        self.database.execute(
            "CREATE TABLE books \
            (id INTEGER PRIMARY KEY, Name TEXT, Path TEXT, ISBN TEXT, CoverImage BLOB)")
        self.database.execute(
            "CREATE TABLE cache \
            (id INTEGER PRIMARY KEY, Name TEXT, Path TEXT, CachedDict BLOB)")
        # It's assumed that any cached books will be pickled and put into the
        # database at time of closing

        self.database.commit()
    
    def add_to_database(self, book_data, image_data):
        pass
