#!/usr/bin/env python3
# Keep in mind that all integer / boolean settings are returned as strings

import os
from ast import literal_eval
from PyQt5 import QtCore, QtGui


class Settings:
    def __init__(self, parent):
        self.parent = parent
        self.settings = QtCore.QSettings('Lector', 'Lector')

        default_profile1 = {
            'font': 'Noto Sans Fallback',
            'foreground': QtGui.QColor().fromRgb(0, 0, 0),
            'background': QtGui.QColor().fromRgb(216, 216, 216),
            'padding': 150,
            'font_size': 30,
            'line_spacing': 110,
            'text_alignment': 'justify'}

        default_profile2 = {
            'font': 'Roboto',
            'foreground': QtGui.QColor().fromRgb(194, 194, 194),
            'background': QtGui.QColor().fromRgb(22, 22, 22),
            'padding': 150,
            'font_size': 30,
            'line_spacing': 110,
            'text_alignment': 'justify'}

        default_profile3 = {
            'font': 'Clear Sans',
            'foreground': QtGui.QColor().fromRgb(101, 123, 131),
            'background': QtGui.QColor().fromRgb(0, 43, 54),
            'padding': 150,
            'font_size': 30,
            'line_spacing': 110,
            'text_alignment': 'justify'}

        self.default_profiles = [
            default_profile1, default_profile2, default_profile3]

        self.default_comic_profile = {
            'padding': 100,  # pixel padding on either size
            'background': QtGui.QColor().fromRgb(0, 0, 0),
            'zoom_mode': 'bestFit'}

    def read_settings(self):
        self.settings.beginGroup('mainWindow')
        self.parent.resize(self.settings.value('windowSize', QtCore.QSize(1299, 748)))
        self.parent.move(self.settings.value('windowPosition', QtCore.QPoint(0, 0)))
        self.parent.settings['current_view'] = int(self.settings.value('currentView', 0))
        self.parent.settings['main_window_headers'] = self.settings.value('tableHeaders', None)
        self.parent.settings['listview_background'] = self.settings.value(
            'listViewBackground', QtGui.QColor().fromRgb(76, 76, 76))
        self.settings.endGroup()

        self.settings.beginGroup('runtimeVariables')
        self.parent.settings['last_open_path'] = self.settings.value(
            'lastOpenPath', os.path.expanduser('~'))
        self.parent.database_path = self.settings.value(
            'databasePath',
            QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.AppDataLocation))
        self.parent.display_profiles = self.settings.value(
            'displayProfiles', self.default_profiles)
        self.parent.current_profile_index = int(self.settings.value(
            'currentProfileIndex', 0))
        self.parent.comic_profile = self.settings.value(
            'comicProfile', self.default_comic_profile)
        self.settings.endGroup()

        self.settings.beginGroup('lastOpen')
        self.parent.settings['last_open_books'] = self.settings.value('lastOpenBooks', [])
        self.parent.settings['last_open_tab'] = self.settings.value('lastOpenTab', 'library')
        self.settings.endGroup()

        self.settings.beginGroup('settingsWindow')
        self.parent.settings['settings_dialog_size'] = self.settings.value(
            'windowSize', QtCore.QSize(700, 500))
        self.parent.settings['settings_dialog_position'] = self.settings.value(
            'windowPosition', QtCore.QPoint(0, 0))
        self.parent.settings['settings_dialog_headers'] = self.settings.value(
            'tableHeaders', [200, 150])
        self.settings.endGroup()

        self.settings.beginGroup('settingsSwitches')
        # The default is string true because literal eval will convert it anyway
        self.parent.settings['cover_shadows'] = literal_eval(self.settings.value(
            'coverShadows', 'True').capitalize())
        self.parent.settings['auto_tags'] = literal_eval(self.settings.value(
            'autoTags', 'True').capitalize())
        self.parent.settings['scan_library'] = literal_eval(self.settings.value(
            'scanLibraryAtStart', 'False').capitalize())
        self.parent.settings['remember_files'] = literal_eval(self.settings.value(
            'rememberFiles', 'True').capitalize())
        self.parent.settings['perform_culling'] = literal_eval(self.settings.value(
            'performCulling', 'True').capitalize())
        self.parent.settings['dictionary_language'] = self.settings.value(
            'dictionaryLanguage', 'en')
        self.settings.endGroup()

        self.settings.beginGroup('dialogSettings')
        self.parent.settings['dialog_background'] = self.settings.value(
            'dialogBackground', QtGui.QColor().fromRgb(0, 0, 0))
        self.settings.endGroup()

    def save_settings(self):
        print('Saving settings...')
        current_settings = self.parent.settings

        self.settings.beginGroup('mainWindow')
        self.settings.setValue('windowSize', self.parent.size())
        self.settings.setValue('windowPosition', self.parent.pos())
        self.settings.setValue('currentView', self.parent.stackedWidget.currentIndex())
        self.settings.setValue(
            'listViewBackground', self.parent.settings['listview_background'])

        table_headers = []
        for i in range(3):
            table_headers.append(self.parent.tableView.horizontalHeader().sectionSize(i))
        self.settings.setValue('tableHeaders', table_headers)
        self.settings.endGroup()

        self.settings.beginGroup('runtimeVariables')
        self.settings.setValue('lastOpenPath', self.parent.settings['last_open_path'])
        self.settings.setValue('databasePath', self.parent.database_path)

        current_profile1 = self.parent.bookToolBar.profileBox.itemData(
            0, QtCore.Qt.UserRole)
        current_profile2 = self.parent.bookToolBar.profileBox.itemData(
            1, QtCore.Qt.UserRole)
        current_profile3 = self.parent.bookToolBar.profileBox.itemData(
            2, QtCore.Qt.UserRole)
        current_profile_index = self.parent.bookToolBar.profileBox.currentIndex()
        self.settings.setValue('displayProfiles', [
            current_profile1,
            current_profile2,
            current_profile3])
        self.settings.setValue('currentProfileIndex', current_profile_index)
        self.settings.setValue('comicProfile', self.parent.comic_profile)
        self.settings.endGroup()

        current_tab_index = self.parent.tabWidget.currentIndex()
        if current_tab_index == 0:
            last_open_tab = 'library'
        else:
            last_open_tab = self.parent.tabWidget.widget(current_tab_index).metadata['path']

        self.settings.beginGroup('lastOpen')
        self.settings.setValue('lastOpenBooks', current_settings['last_open_books'])
        self.settings.setValue('lastOpenTab', last_open_tab)
        self.settings.endGroup()

        self.settings.beginGroup('settingsWindow')
        self.settings.setValue('windowSize', current_settings['settings_dialog_size'])
        self.settings.setValue('windowPosition', current_settings['settings_dialog_position'])
        self.settings.setValue('tableHeaders', current_settings['settings_dialog_headers'])
        self.settings.endGroup()

        self.settings.beginGroup('settingsSwitches')
        self.settings.setValue('rememberFiles', current_settings['remember_files'])
        self.settings.setValue('coverShadows', current_settings['cover_shadows'])
        self.settings.setValue('autoTags', current_settings['auto_tags'])
        self.settings.setValue('scanLibraryAtStart', current_settings['scan_library'])
        self.settings.setValue('performCulling', current_settings['perform_culling'])
        self.settings.setValue('dictionaryLanguage', current_settings['dictionary_language'])
        self.settings.endGroup()

        self.settings.beginGroup('dialogSettings')
        self.settings.setValue('dialogBackground', current_settings['dialog_background'])
        self.settings.endGroup()
