#!/usr/bin/env python3

import os
from PyQt5 import QtCore, QtGui


class Settings:
    def __init__(self, parent):
        self.parent_window = parent
        self.settings = QtCore.QSettings('Lector', 'Lector')

        default_profile1 = {
            'font': 'Noto Sans',
            'foreground': '#000000',
            'background': '#d8d8d8',
            'padding': 140,
            'font_size': 20,
            'line_spacing': 1.5}

        default_profile2 = {
            'font': 'Roboto',
            'foreground': '#c2c2c2',
            'background': '#161616',
            'padding': 140,
            'font_size': 20,
            'line_spacing': 1.5}

        default_profile3 = {
            'font': 'Roboto',
            'foreground': '#657b83',
            'background': '#002b36',
            'padding': 140,
            'font_size': 20,
            'line_spacing': 1.5}

        self.default_profiles = [
            default_profile1, default_profile2, default_profile3]

        self.default_comic_profile = {
            'padding': 100,  # pixel padding on either size
            'background': QtGui.QColor().fromRgb(0, 0, 0),
            'zoom_mode': 'bestFit'}

    def read_settings(self):
        self.settings.beginGroup('mainWindow')
        self.parent_window.resize(self.settings.value(
            'windowSize',
            QtCore.QSize(1299, 748)))
        self.parent_window.move(self.settings.value(
            'windowPosition',
            QtCore.QPoint(0, 0)))
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

    def save_settings(self):
        print('Saving settings...')
        self.settings.beginGroup('mainWindow')
        self.settings.setValue('windowSize', self.parent_window.size())
        self.settings.setValue('windowPosition', self.parent_window.pos())
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
