#!/usr/bin/env python3

import os
import collections

from PyQt5 import QtWidgets, QtGui, QtCore

import database
from resources import settingswindow
from threaded import BackGroundBookSearch, BackGroundBookAddition


class SettingsUI(QtWidgets.QDialog, settingswindow.Ui_Dialog):
    def __init__(self):
        super(SettingsUI, self).__init__()
        self.setupUi(self)

        # Will be overwritten by settings
        self.last_open_directory = None
        self.database_path = None

        self.database_data = collections.OrderedDict()
        self.database_modification = False

        self.thread = None

        self.addButton.clicked.connect(self.add_directories)

    def generate_table(self):
        # Fetch all directories in the database
        paths = database.DatabaseFunctions(
            self.database_path).fetch_data(
                ('*',),
                'directories',
                {'Path': ''},
                'LIKE')

        if not paths:
            print('Database returned no paths for settings...')
            return

        for i in paths:
            pass


    def add_directories(self):
        add_directory = QtWidgets.QFileDialog.getExistingDirectory(
            self, 'Select Directory', self.last_open_directory,
            QtWidgets.QFileDialog.ShowDirsOnly)

        # Directories will be added recursively
        # Sub directory addition is allowed in that files will not
        # be duplicated. However, any additional tags will get
        # added to file tags

        # Database tags for files should not be updated each time
        # a new folder gets added or deleted from the directory
        # This will be done @ runtime
        # Individually set file tags will be preserved
        # Duplicate file tags will be removed

        # Whatever code you write to recurse through directories will
        # have to go into the threaded module

        # Traverse directories looking for files
        self.thread = BackGroundBookSearch(self, add_directory)
        self.thread.finished.connect(self.do_something)
        self.thread.start()

    def do_something(self):
        print('Book search completed')
