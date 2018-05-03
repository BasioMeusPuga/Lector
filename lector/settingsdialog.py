# This file is a part of Lector, a Qt based ebook reader
# Copyright (C) 2017-2018 BasioMeusPuga

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
import pathlib

from PyQt5 import QtWidgets, QtCore, QtGui

from lector import database
from lector.annotations import AnnotationsUI
from lector.models import MostExcellentFileSystemModel
from lector.threaded import BackGroundBookSearch, BackGroundBookAddition
from lector.resources import settingswindow
from lector.settings import Settings


class SettingsUI(QtWidgets.QDialog, settingswindow.Ui_Dialog):
    def __init__(self, parent=None):
        super(SettingsUI, self).__init__()
        self.setupUi(self)
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self._translate = QtCore.QCoreApplication.translate

        self.main_window = parent
        self.database_path = self.main_window.database_path
        self.image_factory = self.main_window.QImageFactory

        # The annotation dialog will use the settings dialog as its parent
        self.annotationsDialog = AnnotationsUI(self)

        self.resize(self.main_window.settings['settings_dialog_size'])
        self.move(self.main_window.settings['settings_dialog_position'])

        install_dir = os.path.realpath(__file__)
        install_dir = pathlib.Path(install_dir).parents[1]
        aboutfile_path = os.path.join(install_dir, 'lector', 'resources', 'about.html')
        with open(aboutfile_path) as about_html:
            self.aboutBox.setHtml(about_html.read())

        self.paths = None
        self.thread = None
        self.filesystemModel = None
        self.tag_data_copy = None

        english_string = self._translate('SettingsUI', 'English')
        spanish_string = self._translate('SettingsUI', 'Spanish')
        hindi_string = self._translate('SettingsUI', 'Hindi')
        languages = [english_string, spanish_string, hindi_string]

        self.languageBox.addItems(languages)
        current_language = self.main_window.settings['dictionary_language']
        if current_language == 'en':
            self.languageBox.setCurrentIndex(0)
        elif current_language == 'es':
            self.languageBox.setCurrentIndex(1)
        else:
            self.languageBox.setCurrentIndex(2)
        self.languageBox.activated.connect(self.change_dictionary_language)

        self.okButton.setToolTip(
            self._translate('SettingsUI', 'Save changes and start library scan'))
        self.okButton.clicked.connect(self.start_library_scan)
        self.cancelButton.clicked.connect(self.cancel_pressed)

        # Radio buttons
        if self.main_window.settings['icon_theme'] == 'DarkIcons':
            self.darkIconsRadio.setChecked(True)
        else:
            self.lightIconsRadio.setChecked(True)
        self.darkIconsRadio.clicked.connect(self.change_icon_theme)
        self.lightIconsRadio.clicked.connect(self.change_icon_theme)

        # Check boxes
        self.autoTags.setChecked(self.main_window.settings['auto_tags'])
        self.coverShadows.setChecked(self.main_window.settings['cover_shadows'])
        self.refreshLibrary.setChecked(self.main_window.settings['scan_library'])
        self.fileRemember.setChecked(self.main_window.settings['remember_files'])
        self.performCulling.setChecked(self.main_window.settings['perform_culling'])
        self.cachingEnabled.setChecked(self.main_window.settings['caching_enabled'])
        self.hideScrollBars.setChecked(self.main_window.settings['hide_scrollbars'])
        self.scrollSpeedSlider.setValue(self.main_window.settings['scroll_speed'])
        self.readAtPercent.setValue(self.main_window.settings['consider_read_at'])

        self.autoTags.clicked.connect(self.manage_checkboxes)
        self.coverShadows.clicked.connect(self.manage_checkboxes)
        self.refreshLibrary.clicked.connect(self.manage_checkboxes)
        self.fileRemember.clicked.connect(self.manage_checkboxes)
        self.performCulling.clicked.connect(self.manage_checkboxes)
        self.cachingEnabled.clicked.connect(self.manage_checkboxes)
        self.hideScrollBars.clicked.connect(self.manage_checkboxes)
        self.scrollSpeedSlider.valueChanged.connect(self.change_scroll_speed)
        self.readAtPercent.valueChanged.connect(self.change_read_at)

        # Generate the QStandardItemModel for the listView
        self.listModel = QtGui.QStandardItemModel()

        library_string = self._translate('SettingsUI', 'Library')
        switches_string = self._translate('SettingsUI', 'Switches')
        annotations_string = self._translate('SettingsUI', 'Annotations')
        about_string = self._translate('SettingsUI', 'About')
        list_options = [
            library_string, switches_string, annotations_string, about_string]

        icon_dict = {
            0: 'view-readermode',
            1: 'switches',
            2: 'annotate',
            3: 'about'}

        for count, i in enumerate(list_options):
            item = QtGui.QStandardItem()
            item.setText(i)
            this_icon = icon_dict[count]
            item.setIcon(
                self.main_window.QImageFactory.get_image(this_icon))
            self.listModel.appendRow(item)
        self.listView.setModel(self.listModel)
        self.listView.clicked.connect(self.page_switch)

        # Annotation related buttons
        # Icon names
        self.newAnnotation.setIcon(self.image_factory.get_image('add'))
        self.deleteAnnotation.setIcon(self.image_factory.get_image('remove'))
        self.editAnnotation.setIcon(self.image_factory.get_image('edit-rename'))
        self.moveUp.setIcon(self.image_factory.get_image('arrow-up'))
        self.moveDown.setIcon(self.image_factory.get_image('arrow-down'))

        # Icon sizes
        self.newAnnotation.setIconSize(QtCore.QSize(24, 24))
        self.deleteAnnotation.setIconSize(QtCore.QSize(24, 24))
        self.editAnnotation.setIconSize(QtCore.QSize(24, 24))
        self.moveUp.setIconSize(QtCore.QSize(24, 24))
        self.moveDown.setIconSize(QtCore.QSize(24, 24))

        self.annotationsList.clicked.connect(self.load_annotation)
        self.annotationsList.doubleClicked.connect(self.editAnnotation.click)
        self.newAnnotation.clicked.connect(self.add_annotation)
        self.deleteAnnotation.clicked.connect(self.delete_annotation)
        self.editAnnotation.clicked.connect(self.load_annotation)
        self.moveUp.clicked.connect(self.move_annotation)
        self.moveDown.clicked.connect(self.move_annotation)

        # Generate annotation settings
        self.annotationModel = QtGui.QStandardItemModel()
        self.generate_annotations()

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

        self.main_window.generate_library_filter_menu(paths)
        directory_data = {}
        if not paths:
            print('Database: No paths for settings...')
        else:
            # Convert to the dictionary format that is
            # to be fed into the QFileSystemModel
            for i in paths:
                directory_data[i[0]] = {
                    'name': i[1],
                    'tags': i[2],
                    'check_state': i[3]}

        self.filesystemModel = MostExcellentFileSystemModel(directory_data)
        self.filesystemModel.setFilter(QtCore.QDir.NoDotAndDotDot | QtCore.QDir.Dirs)
        self.treeView.setModel(self.filesystemModel)

        # TODO
        # This here might break on them pestilent non unixy OSes
        # Check and see

        root_directory = QtCore.QDir().rootPath()
        self.treeView.setRootIndex(
            self.filesystemModel.setRootPath(root_directory))

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
            this_index = self.filesystemModel.index(i)
            self.treeView.expand(this_index)

        header_sizes = self.main_window.settings['settings_dialog_headers']
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
        self.hide()

        data_pairs = []
        for i in self.filesystemModel.tag_data.items():
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

            database.DatabaseFunctions(
                self.database_path).delete_from_database('*', '*')

            self.main_window.lib_ref.generate_model('build')
            self.main_window.lib_ref.generate_proxymodels()
            self.main_window.generate_library_filter_menu()

            return

        # Update the main window library filter menu
        self.main_window.generate_library_filter_menu(data_pairs)
        self.main_window.set_library_filter()

        # Disallow rechecking until the first check completes
        self.okButton.setEnabled(False)
        self.main_window.libraryToolBar.reloadLibraryButton.setEnabled(False)
        self.okButton.setToolTip(
            self._translate('SettingsUI', 'Library scan in progress...'))

        # Traverse directories looking for files
        self.main_window.statusMessage.setText(
            self._translate('SettingsUI', 'Checking library folders'))
        self.thread = BackGroundBookSearch(data_pairs)
        self.thread.finished.connect(self.finished_iterating)
        self.thread.start()

    def finished_iterating(self):
        # The books the search thread has found
        # are now in self.thread.valid_files
        if not self.thread.valid_files:
            self.main_window.move_on()
            return

        # Hey, messaging is important, okay?
        self.main_window.statusBar.setVisible(True)
        self.main_window.sorterProgress.setVisible(True)
        self.main_window.statusMessage.setText(
            self._translate('SettingsUI', 'Parsing files'))

        # We now create a new thread to put those files into the database
        self.thread = BackGroundBookAddition(
            self.thread.valid_files, self.database_path, 'automatic', self.main_window)
        self.thread.finished.connect(self.main_window.move_on)
        self.thread.start()

    def page_switch(self, index):
        self.stackedWidget.setCurrentIndex(index.row())
        if index.row() == 0:
            self.okButton.setVisible(True)
        else:
            self.okButton.setVisible(False)

    def cancel_pressed(self):
        self.filesystemModel.tag_data = copy.deepcopy(self.tag_data_copy)
        self.hide()

    def hideEvent(self, event):
        self.no_more_settings()
        event.accept()

    def showEvent(self, event):
        self.format_preview()
        self.tag_data_copy = copy.deepcopy(self.filesystemModel.tag_data)
        event.accept()

    def no_more_settings(self):
        self.main_window.libraryToolBar.settingsButton.setChecked(False)
        self.gather_annotations()
        Settings(self.main_window).save_settings()
        Settings(self.main_window).read_settings()
        self.main_window.settings['last_open_tab'] = None  # Needed to allow focus change
                                                           # to newly opened book
        self.resizeEvent()

    def resizeEvent(self, event=None):
        self.main_window.settings['settings_dialog_size'] = self.size()
        self.main_window.settings['settings_dialog_position'] = self.pos()
        table_headers = []
        for i in [0, 4]:
            table_headers.append(self.treeView.columnWidth(i))
        self.main_window.settings['settings_dialog_headers'] = table_headers

    def change_icon_theme(self):
        if self.sender() == self.darkIconsRadio:
            self.main_window.settings['icon_theme'] = 'DarkIcons'
        else:
            self.main_window.settings['icon_theme'] = 'LightIcons'

    def change_dictionary_language(self, event):
        language_dict = {
            0: 'en',
            1: 'es',
            2: 'hi'}
        self.main_window.settings[
            'dictionary_language'] = language_dict[self.languageBox.currentIndex()]

    def change_scroll_speed(self, event=None):
        self.main_window.settings['scroll_speed'] = self.scrollSpeedSlider.value()

    def change_read_at(self, event=None):
        self.main_window.settings['consider_read_at'] = self.readAtPercent.value()

    def manage_checkboxes(self, event=None):
        sender = self.sender().objectName()

        sender_dict = {
            'coverShadows': 'cover_shadows',
            'autoTags': 'auto_tags',
            'refreshLibrary': 'scan_library',
            'fileRemember': 'remember_files',
            'performCulling': 'perform_culling',
            'cachingEnabled': 'caching_enabled',
            'hideScrollBars': 'hide_scrollbars'}

        self.main_window.settings[
            sender_dict[sender]] = not self.main_window.settings[sender_dict[sender]]

        if not self.performCulling.isChecked():
            self.main_window.cover_functions.load_all_covers()

    def generate_annotations(self):
        saved_annotations = self.main_window.settings['annotations']

        for i in saved_annotations:
            item = QtGui.QStandardItem()
            item.setText(i['name'])
            item.setData(i, QtCore.Qt.UserRole)
            self.annotationModel.appendRow(item)

        self.annotationsList.setModel(self.annotationModel)

    def format_preview(self):
        # Needed to clear the preview of annotation ickiness
        cursor = QtGui.QTextCursor()
        self.previewView.setTextCursor(cursor)

        self.previewView.setText('Vidistine nuper imagines moventes bonas?')
        profile_index = self.main_window.bookToolBar.profileBox.currentIndex()
        current_profile = self.main_window.bookToolBar.profileBox.itemData(
            profile_index, QtCore.Qt.UserRole)

        if not current_profile:
            return

        font = current_profile['font']
        self.foreground = current_profile['foreground']
        background = current_profile['background']
        font_size = current_profile['font_size']

        self.previewView.setStyleSheet(
            "QTextEdit {{font-family: {0}; font-size: {1}px; color: {2}; background-color: {3}}}".format(
                font, font_size, self.foreground.name(), background.name()))

        block_format = QtGui.QTextBlockFormat()
        block_format.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)

        cursor = self.previewView.textCursor()
        while True:
            old_position = cursor.position()
            cursor.mergeBlockFormat(block_format)
            cursor.movePosition(QtGui.QTextCursor.NextBlock, 0, 1)
            new_position = cursor.position()
            if old_position == new_position:
                break

    def add_annotation(self):
        self.annotationsDialog.show_dialog('add')

    def delete_annotation(self):
        selected_index = self.annotationsList.currentIndex()
        if not selected_index.isValid():
            return

        self.annotationModel.removeRow(
            self.annotationsList.currentIndex().row())
        self.format_preview()
        self.annotationsList.clearSelection()

    def load_annotation(self):
        selected_index = self.annotationsList.currentIndex()
        if not selected_index.isValid():
            return

        if self.sender() == self.annotationsList:
            self.annotationsDialog.show_dialog('preview', selected_index)

        elif self.sender() == self.editAnnotation:
            self.annotationsDialog.show_dialog('edit', selected_index)

    def move_annotation(self):
        current_row = self.annotationsList.currentIndex().row()

        if self.sender() == self.moveUp:
            new_row = current_row - 1
            if new_row < 0:
                return

        elif self.sender() == self.moveDown:
            new_row = current_row + 1
            if new_row == self.annotationModel.rowCount():
                return

        row_out = self.annotationModel.takeRow(current_row)
        self.annotationModel.insertRow(new_row, row_out)
        new_index = self.annotationModel.index(new_row, 0)

        self.annotationsList.setCurrentIndex(new_index)

    def gather_annotations(self):
        annotations_out = []
        for i in range(self.annotationModel.rowCount()):
            annotation_item = self.annotationModel.item(i, 0)
            annotation_data = annotation_item.data(QtCore.Qt.UserRole)
            annotations_out.append(annotation_data)

        self.main_window.settings['annotations'] = annotations_out
