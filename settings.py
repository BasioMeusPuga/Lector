#!/usr/bin/env python3
# Keep in mind that all integer settings are returned as strings

import os
from PyQt5 import QtCore, QtGui


class Settings:
    def __init__(self, parent):
        self.parent_window = parent
        self.settings = QtCore.QSettings('Lector', 'Lector')

        default_profile1 = {
            'font': 'Noto Sans',
            'foreground': QtGui.QColor().fromRgb(0, 0, 0),
            'background': QtGui.QColor().fromRgb(216, 216, 216),
            'padding': 140,
            'font_size': 20,
            'line_spacing': 1.5}

        default_profile2 = {
            'font': 'Roboto',
            'foreground': QtGui.QColor().fromRgb(194, 194, 194),
            'background': QtGui.QColor().fromRgb(22, 22, 22),
            'padding': 140,
            'font_size': 20,
            'line_spacing': 1.5}

        default_profile3 = {
            'font': 'Clear Sans',
            'foreground': QtGui.QColor().fromRgb(101, 123, 131),
            'background': QtGui.QColor().fromRgb(0, 43, 54),
            'padding': 140,
            'font_size': 30,
            'line_spacing': 1.5}

        self.default_profiles = [
            default_profile1, default_profile2, default_profile3]

        self.default_comic_profile = {
            'padding': 100,  # pixel padding on either size
            'background': QtGui.QColor().fromRgb(0, 0, 0),
            'zoom_mode': 'bestFit'}

    def read_settings(self):
        self.settings.beginGroup('mainWindow')
        self.parent_window.resize(self.settings.value('windowSize', QtCore.QSize(1299, 748)))
        self.parent_window.move(self.settings.value('windowPosition', QtCore.QPoint(0, 0)))
        self.parent_window.current_view = int(self.settings.value('currentView', 0))
        self.parent_window.table_header_sizes = self.settings.value('tableHeaders', None)
        self.settings.endGroup()

        self.settings.beginGroup('runtimeVariables')
        self.parent_window.last_open_path = self.settings.value(
            'lastOpenPath', os.path.expanduser('~'))
        self.parent_window.database_path = self.settings.value(
            'databasePath',
            QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.AppDataLocation))
        self.parent_window.display_profiles = self.settings.value(
            'displayProfiles', self.default_profiles)
        self.parent_window.current_profile_index = int(self.settings.value(
            'currentProfileIndex', 0))
        self.parent_window.comic_profile = self.settings.value(
            'comicProfile', self.default_comic_profile)
        self.settings.endGroup()

        self.settings.beginGroup('lastOpen')
        self.parent_window.last_open_books = self.settings.value('lastOpenFiles', [])
        self.parent_window.last_open_tab = self.settings.value('lastOpenTab', 'library')
        self.settings.endGroup()

        self.settings.beginGroup('settingsWindow')
        self.parent_window.settings_dialog_settings = {}
        self.parent_window.settings_dialog_settings['size'] = self.settings.value(
            'windowSize', QtCore.QSize(700, 500))
        self.parent_window.settings_dialog_settings['position'] = self.settings.value(
            'windowPosition', QtCore.QPoint(0, 0))
        self.parent_window.settings_dialog_settings['headers'] = self.settings.value(
            'tableHeaders', [200, 150])
        self.settings.endGroup()

    def save_settings(self):
        print('Saving settings...')

        self.settings.beginGroup('mainWindow')
        self.settings.setValue('windowSize', self.parent_window.size())
        self.settings.setValue('windowPosition', self.parent_window.pos())
        self.settings.setValue('currentView', self.parent_window.stackedWidget.currentIndex())

        table_headers = []
        for i in range(3):
            table_headers.append(self.parent_window.tableView.horizontalHeader().sectionSize(i))
        self.settings.setValue('tableHeaders', table_headers)
        self.settings.endGroup()

        self.settings.beginGroup('runtimeVariables')
        self.settings.setValue('lastOpenPath', self.parent_window.last_open_path)
        self.settings.setValue('databasePath', self.parent_window.database_path)

        current_profile1 = self.parent_window.bookToolBar.profileBox.itemData(
            0, QtCore.Qt.UserRole)
        current_profile2 = self.parent_window.bookToolBar.profileBox.itemData(
            1, QtCore.Qt.UserRole)
        current_profile3 = self.parent_window.bookToolBar.profileBox.itemData(
            2, QtCore.Qt.UserRole)
        current_profile_index = self.parent_window.bookToolBar.profileBox.currentIndex()
        self.settings.setValue('displayProfiles', [
            current_profile1,
            current_profile2,
            current_profile3])
        self.settings.setValue('currentProfileIndex', current_profile_index)
        self.settings.setValue('comicProfile', self.parent_window.comic_profile)
        self.settings.endGroup()

        current_tab_index = self.parent_window.tabWidget.currentIndex()
        if current_tab_index == 0:
            last_open_tab = 'library'
        else:
            last_open_tab = self.parent_window.tabWidget.widget(current_tab_index).metadata['path']

        self.settings.beginGroup('lastOpen')
        self.settings.setValue('lastOpenFiles', self.parent_window.last_open_books)
        self.settings.setValue('lastOpenTab', last_open_tab)
        self.settings.endGroup()

        self.settings.beginGroup('settingsWindow')
        these_settings = self.parent_window.settings_dialog_settings
        self.settings.setValue('windowSize', these_settings['size'])
        self.settings.setValue('windowPosition', these_settings['position'])
        self.settings.setValue('tableHeaders', these_settings['headers'])
