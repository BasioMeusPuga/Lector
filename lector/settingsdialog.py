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

# TODO
# Get Cancel working with the file system model

import os
import copy
from PyQt5 import QtWidgets, QtCore

from lector import database
from lector.models import MostExcellentFileSystemModel
from lector.threaded import BackGroundBookSearch, BackGroundBookAddition

from resources import settingswindow


class SettingsUI(QtWidgets.QDialog, settingswindow.Ui_Dialog):
    def __init__(self, parent):
        super(SettingsUI, self).__init__()
        self.setupUi(self)

        self.parent = parent
        self.database_path = self.parent.database_path

        self.resize(self.parent.settings['settings_dialog_size'])
        self.move(self.parent.settings['settings_dialog_position'])

        self.aboutBox.setVisible(False)
        aboutfile_path = os.path.join('resources', 'about.html')
        with open(aboutfile_path) as about_html:
            self.aboutBox.setHtml(about_html.read())

        self.paths = None
        self.thread = None
        self.filesystem_model = None
        self.tag_data_copy = None

        languages = ['English', 'Spanish', 'Hindi']
        self.languageBox.addItems(languages)
        current_language = self.parent.settings['dictionary_language']
        if current_language == 'en':
            self.languageBox.setCurrentIndex(0)
        elif current_language == 'es':
            self.languageBox.setCurrentIndex(1)
        else:
            self.languageBox.setCurrentIndex(2)
        self.languageBox.activated.connect(self.change_dictionary_language)

        self.okButton.setToolTip('Save changes and start library scan')
        self.okButton.clicked.connect(self.start_library_scan)
        self.cancelButton.clicked.connect(self.cancel_pressed)
        self.aboutButton.clicked.connect(self.about_pressed)

        # Check boxes
        self.autoTags.setChecked(self.parent.settings['auto_tags'])
        self.coverShadows.setChecked(self.parent.settings['cover_shadows'])
        self.refreshLibrary.setChecked(self.parent.settings['scan_library'])
        self.fileRemember.setChecked(self.parent.settings['remember_files'])
        self.performCulling.setChecked(self.parent.settings['perform_culling'])

        self.autoTags.clicked.connect(self.manage_checkboxes)
        self.coverShadows.clicked.connect(self.manage_checkboxes)
        self.refreshLibrary.clicked.connect(self.manage_checkboxes)
        self.fileRemember.clicked.connect(self.manage_checkboxes)
        self.performCulling.clicked.connect(self.manage_checkboxes)

        # Generate the filesystem treeView
        self.generate_tree()

    def generate_tree(self):
        # Fetch all directories in the database
        paths = database.DatabaseFunctions(
            self.database_path).fetch_data(
                ('Path', 'Name', 'Tags', 'CheckState'),
                'directories',
                {'Path': ''},
                'LIKE')

        self.parent.generate_library_filter_menu(paths)
        directory_data = {}
        if not paths:
            print('Database returned no paths for settings...')
        else:
            # Convert to the dictionary format that is
            # to be fed into the QFileSystemModel
            for i in paths:
                directory_data[i[0]] = {
                    'name': i[1],
                    'tags': i[2],
                    'check_state': i[3]}

        self.filesystem_model = MostExcellentFileSystemModel(directory_data)
        self.filesystem_model.setFilter(QtCore.QDir.NoDotAndDotDot | QtCore.QDir.Dirs)
        self.treeView.setModel(self.filesystem_model)

        # TODO
        # This here might break on them pestilent non unixy OSes
        # Check and see

        root_directory = QtCore.QDir().rootPath()
        self.treeView.setRootIndex(
            self.filesystem_model.setRootPath(root_directory))

        # Set the treeView and QFileSystemModel to its desired state
        selected_paths = [
            i for i in directory_data if directory_data[i]['check_state'] == QtCore.Qt.Checked]
        expand_paths = set()
        for i in selected_paths:

            # Recursively grind down parent paths for expansion
            this_path = i
            while True:
                parent_path = os.path.dirname(this_path)
                if parent_path == this_path:
                    break
                expand_paths.add(parent_path)
                this_path = parent_path

        # Expand all the parent paths derived from the selected path
        if root_directory in expand_paths:
            expand_paths.remove(root_directory)

        for i in expand_paths:
            this_index = self.filesystem_model.index(i)
            self.treeView.expand(this_index)

        header_sizes = self.parent.settings['settings_dialog_headers']
        if header_sizes:
            for count, i in enumerate((0, 4)):
                self.treeView.setColumnWidth(i, int(header_sizes[count]))

        # TODO
        # Set a QSortFilterProxy model on top of the existing QFileSystem model
        # self.filesystem_proxy_model = FileSystemProxyModel()
        # self.filesystem_proxy_model.setSourceModel(self.filesystem_model)
        # self.treeView.setModel(self.filesystem_proxy_model)

        for i in range(1, 4):
            self.treeView.hideColumn(i)

    def start_library_scan(self):
        # TODO
        # return in case the treeView is not edited

        self.hide()

        data_pairs = []
        for i in self.filesystem_model.tag_data.items():
            data_pairs.append([
                i[0], i[1]['name'], i[1]['tags'], i[1]['check_state']
            ])

        database.DatabaseFunctions(
            self.database_path).set_library_paths(data_pairs)

        if not data_pairs:
            try:
                if self.sender().objectName() == 'reloadLibrary':
                    self.show()
            except AttributeError:
                pass

            self.parent.lib_ref.view_model.clear()
            self.parent.lib_ref.table_rows = []

            # TODO
            # Change this to no longer include files added manually

            database.DatabaseFunctions(
                self.database_path).delete_from_database('*', '*')

            return

        # Update the main window library filter menu
        self.parent.generate_library_filter_menu(data_pairs)
        self.parent.set_library_filter()

        # Disallow rechecking until the first check completes
        self.okButton.setEnabled(False)
        self.parent.reloadLibrary.setEnabled(False)
        self.okButton.setToolTip('Library scan in progress...')

        # Traverse directories looking for files
        self.parent.statusMessage.setText('Checking library folders')
        self.thread = BackGroundBookSearch(data_pairs, self)
        self.thread.finished.connect(self.finished_iterating)
        self.thread.start()

    def finished_iterating(self):
        # The books the search thread has found
        # are now in self.thread.valid_files
        if not self.thread.valid_files:
            return

        # Hey, messaging is important, okay?
        self.parent.sorterProgress.setVisible(True)
        self.parent.statusMessage.setText('Parsing files')

        # We now create a new thread to put those files into the database
        self.thread = BackGroundBookAddition(
            self.thread.valid_files, self.database_path, True, self.parent)
        self.thread.finished.connect(self.parent.move_on)
        self.thread.start()

    def cancel_pressed(self):
        self.filesystem_model.tag_data = copy.deepcopy(self.tag_data_copy)
        self.hide()

    def hideEvent(self, event):
        self.no_more_settings()
        event.accept()

    def showEvent(self, event):
        self.tag_data_copy = copy.deepcopy(self.filesystem_model.tag_data)
        event.accept()

    def no_more_settings(self):
        self.parent.libraryToolBar.settingsButton.setChecked(False)
        self.aboutBox.hide()
        self.treeView.show()
        self.resizeEvent()

    def resizeEvent(self, event=None):
        self.parent.settings['settings_dialog_size'] = self.size()
        self.parent.settings['settings_dialog_position'] = self.pos()
        table_headers = []
        for i in [0, 4]:
            table_headers.append(self.treeView.columnWidth(i))
        self.parent.settings['settings_dialog_headers'] = table_headers

    def change_dictionary_language(self, event):
        language_dict = {
            0: 'en',
            1: 'es',
            2: 'hi'}
        self.parent.settings['dictionary_language'] = language_dict[self.languageBox.currentIndex()]

    def manage_checkboxes(self, event=None):
        sender = self.sender().objectName()

        sender_dict = {
            'coverShadows': 'cover_shadows',
            'autoTags': 'auto_tags',
            'refreshLibrary': 'scan_library',
            'fileRemember': 'remember_files',
            'performCulling': 'perform_culling'}

        self.parent.settings[sender_dict[sender]] = not self.parent.settings[sender_dict[sender]]

        if not self.performCulling.isChecked():
            self.parent.load_all_covers()

    def about_pressed(self):
        self.treeView.setVisible(not self.treeView.isVisible())
        self.aboutBox.setVisible(not self.aboutBox.isVisible())
