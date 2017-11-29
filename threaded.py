#!/usr/bin/env python3

import os
from multiprocessing.dummy import Pool
from PyQt5 import QtCore

import sorter
import database


class BackGroundTabUpdate(QtCore.QThread):
    def __init__(self, database_path, all_metadata, parent=None):
        super(BackGroundTabUpdate, self).__init__(parent)
        self.database_path = database_path
        self.all_metadata = all_metadata

    def run(self):
        hash_position_pairs = []
        for i in self.all_metadata:
            file_hash = i['hash']
            position = i['position']
            hash_position_pairs.append([file_hash, position])

        database.DatabaseFunctions(
            self.database_path).modify_position(hash_position_pairs)


class BackGroundBookAddition(QtCore.QThread):
    def __init__(self, parent_window, file_list, database_path, parent=None):
        super(BackGroundBookAddition, self).__init__(parent)
        self.parent_window = parent_window
        self.file_list = file_list
        self.database_path = database_path

    def run(self):
        books = sorter.BookSorter(
            self.file_list,
            'addition',
            self.database_path)
        parsed_books = books.initiate_threads()
        database.DatabaseFunctions(self.database_path).add_to_database(parsed_books)
        self.parent_window.lib_ref.generate_model('addition', parsed_books)


class BackGroundBookSearch(QtCore.QThread):
    def __init__(self, parent_window, data_list, parent=None):
        super(BackGroundBookSearch, self).__init__(parent)
        self.parent_window = parent_window
        self.data_list = data_list
        self.valid_files = []  # A tuple should get added to this containing the
                               # file path and the folder name / tags

    def run(self):

        def traverse_directory(incoming_data):
            root_directory = incoming_data[0]
            folder_name = incoming_data[1]
            folder_tags = incoming_data[2]

            for directory, subdir, files in os.walk(root_directory):
                for filename in files:
                    if os.path.splitext(filename)[1][1:] in sorter.available_parsers:
                        self.valid_files.append(
                            (os.path.join(directory, filename), folder_name, folder_tags))

        def initiate_threads():
            _pool = Pool(5)
            _pool.map(traverse_directory, self.data_list)
            _pool.close()
            _pool.join()

        initiate_threads()

        # TODO
        # Change existing sorter module functionality to handle
        # preset tags
        # Change database to accomodate User Tags, Folder Name, Folder Tags

        # self.valid_files will now be added to the database
        # and models will be rebuilt accordingly
        # Coming soon to a commit near you
