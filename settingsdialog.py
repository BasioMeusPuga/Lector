#!/usr/bin/env python3

import os
import collections

from PyQt5 import QtWidgets, QtGui, QtCore

import database
from resources import settingswindow
from models import MostExcellentTableModel, TableProxyModel
from threaded import BackGroundBookSearch, BackGroundBookAddition


class SettingsUI(QtWidgets.QDialog, settingswindow.Ui_Dialog):
    def __init__(self, parent_window):
        super(SettingsUI, self).__init__()
        self.setupUi(self)

        # These are just for declarative purposes
        self.window_size = None
        self.window_position = None
        self.table_headers = []

        self.last_open_directory = None
        self.parent_window = parent_window
        self.database_path = self.parent_window.database_path
        self.resize(self.parent_window.settings_dialog_settings['size'])
        self.move(self.parent_window.settings_dialog_settings['position'])

        self.table_model = None
        self.table_proxy_model = None

        self.thread = None

        self.tableFilterEdit.textChanged.connect(self.update_table_proxy_model)
        self.addButton.clicked.connect(self.add_directories)

        self.generate_table()
        header_sizes = self.parent_window.settings_dialog_settings['headers']
        if header_sizes:
            for count, i in enumerate(header_sizes):
                self.tableView.horizontalHeader().resizeSection(count, int(i))

        self.tableView.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Interactive)
        self.tableView.horizontalHeader().setHighlightSections(False)
        self.tableView.horizontalHeader().setStretchLastSection(True)

        # self.tableView.horizontalHeader().setSectionResizeMode(3, QtWidgets.QHeaderView.Stretch)

        # self.database_data = collections.OrderedDict()
        # self.database_modification = False

    def generate_table(self):
        # Fetch all directories in the database
        paths = database.DatabaseFunctions(
            self.database_path).fetch_data(
                ('Path', 'Name', 'Tags'),
                'directories',
                {'Path': ''},
                'LIKE')

        if not paths:
            print('Database returned no paths for settings...')

        table_header = ['Path', 'Name', 'Tags']
        self.table_model = MostExcellentTableModel(
            table_header, paths, None)

        self.create_table_proxy_model()

    def create_table_proxy_model(self):
        self.table_proxy_model = TableProxyModel()
        self.table_proxy_model.setSourceModel(self.table_model)
        self.table_proxy_model.setSortCaseSensitivity(False)
        self.table_proxy_model.sort(1, QtCore.Qt.AscendingOrder)
        self.tableView.setModel(self.table_proxy_model)
        self.tableView.horizontalHeader().setSortIndicator(
            1, QtCore.Qt.AscendingOrder)

    def update_table_proxy_model(self):
        self.table_proxy_model.invalidateFilter()
        self.table_proxy_model.setFilterParams(
            self.tableFilterEdit.text(), [0, 1, 2])
        self.table_proxy_model.setFilterFixedString(
            self.tableFilterEdit.text())

    def add_directories(self):
        add_directory = QtWidgets.QFileDialog.getExistingDirectory(
            self, 'Select Directory', self.last_open_directory,
            QtWidgets.QFileDialog.ShowDirsOnly)

        data_pair = [[add_directory, None, None]]
        database.DatabaseFunctions(self.database_path).set_library_paths(data_pair)

        self.generate_table()

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

    def parse_all(self, directories):
        add_directory = None
        self.thread = BackGroundBookSearch(self, add_directory)
        self.thread.finished.connect(self.do_something)
        self.thread.start()

    def do_something(self):
        print('Book search completed')

    def closeEvent(self, event):
        self.no_more_settings()
        event.accept()

    def hideEvent(self, event):
        self.no_more_settings()
        event.accept()

    def no_more_settings(self):
        self.parent_window.libraryToolBar.settingsButton.setChecked(False)
        self.window_size = self.size()
        self.window_position = self.pos()
        self.table_headers = []
        for i in range(2):
            self.table_headers.append(self.tableView.horizontalHeader().sectionSize(i))
