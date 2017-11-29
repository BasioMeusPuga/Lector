#!/usr/bin/env python3

import os
import collections

from PyQt5 import QtWidgets, QtGui, QtCore

import database
from resources import settingswindow
from models import MostExcellentTableModel, TableProxyModel
from threaded import BackGroundBookSearch, BackGroundBookAddition


class SettingsUI(QtWidgets.QDialog, settingswindow.Ui_Dialog):
    # TODO
    # Deletion from table
    # Cancel behavior
    # Update database on table model update

    def __init__(self, parent_window):
        super(SettingsUI, self).__init__()
        self.setupUi(self)

        self.last_open_directory = None
        self.parent_window = parent_window
        self.database_path = self.parent_window.database_path

        self.resize(self.parent_window.settings_dialog_settings['size'])
        self.move(self.parent_window.settings_dialog_settings['position'])

        self.table_model = None
        self.old_table_model = None
        self.table_proxy_model = None
        self.paths = None

        self.thread = None

        self.tableFilterEdit.textChanged.connect(self.update_table_proxy_model)
        self.addButton.clicked.connect(self.add_directories)
        self.cancelButton.clicked.connect(self.cancel_pressed)
        self.okButton.clicked.connect(self.ok_pressed)

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

    def generate_table(self):
        # Fetch all directories in the database
        self.paths = database.DatabaseFunctions(
            self.database_path).fetch_data(
                ('Path', 'Name', 'Tags'),
                'directories',
                {'Path': ''},
                'LIKE')

        if not self.paths:
            print('Database returned no paths for settings...')
        else:
            # Convert to a list because tuples, well, they're tuples
            self.paths = [list(i) for i in self.paths]

        table_header = ['Path', 'Name', 'Tags']
        self.table_model = MostExcellentTableModel(
            table_header, self.paths, None)

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
        # Directories will be added recursively
        # Sub directory addition is not allowed
        # In case it is to be allowed eventually, files will not
        # be duplicated. However, any additional tags will get
        # added to file tags

        add_directory = QtWidgets.QFileDialog.getExistingDirectory(
            self, 'Select Directory', self.last_open_directory,
            QtWidgets.QFileDialog.ShowDirsOnly)
        add_directory = os.path.realpath(add_directory)

        # TODO
        # Account for a parent folder getting added after a subfolder
        # Currently this does the inverse only

        for i in self.paths:
            already_present = os.path.realpath(i[0])
            if already_present == add_directory or already_present in add_directory:
                QtWidgets.QMessageBox.critical(
                    self,
                    'Error',
                    'Duplicate or sub folder: ' + already_present + ' ',
                    QtWidgets.QMessageBox.Ok)
                return

        # Set default name for the directory
        directory_name = os.path.basename(add_directory).title()
        data_pair = [[add_directory, directory_name, None]]
        database.DatabaseFunctions(self.database_path).set_library_paths(data_pair)
        self.generate_table()

    def ok_pressed(self):
        # Traverse directories looking for files
        self.thread = BackGroundBookSearch(self, self.table_model.display_data)
        self.thread.finished.connect(self.do_something)
        self.thread.start()

    def do_something(self):
        print('Book search completed')

    def cancel_pressed(self):
        self.hide()

    # TODO
    # Implement cancel by restoring the table model to an older version
    # def showEvent(self, event):
    #     event.accept()

    def hideEvent(self, event):
        self.no_more_settings()
        event.accept()

    def no_more_settings(self):
        self.table_model = self.old_table_model
        self.parent_window.libraryToolBar.settingsButton.setChecked(False)
        self.resizeEvent()

    def resizeEvent(self, event=None):
        self.parent_window.settings_dialog_settings['size'] = self.size()
        self.parent_window.settings_dialog_settings['position'] = self.pos()
        table_headers = []
        for i in range(2):
            table_headers.append(self.tableView.horizontalHeader().sectionSize(i))
        self.parent_window.settings_dialog_settings['headers'] = table_headers
