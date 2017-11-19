#!/usr/bin/env python3

import os
import collections

from PyQt5 import QtWidgets, QtGui, QtCore

import database
from resources import settingswindow


class SettingsUI(QtWidgets.QDialog, settingswindow.Ui_Dialog):
    def __init__(self):
        super(SettingsUI, self).__init__()
        self.setupUi(self)

        # Will be overwritten by settings
        self.last_open_directory = None
        self.database_path = None

        self.database_data = collections.OrderedDict()
        self.database_modification = False

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

        # Directories will NOT be added recursively

