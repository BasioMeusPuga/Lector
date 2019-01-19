# This file is a part of Lector, a Qt based ebook reader
# Copyright (C) 2017-2019 BasioMeusPuga

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

# Keep in mind that all integer / boolean settings are returned as strings

import os
import logging
from ast import literal_eval

from PyQt5 import QtCore, QtGui

logger = logging.getLogger(__name__)


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
            'listViewBackground', QtGui.QColor().fromRgb(33, 33, 33))
        self.parent.settings['icon_theme'] = self.settings.value('iconTheme', 'DarkIcons')
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
        self.parent.settings['caching_enabled'] = literal_eval(self.settings.value(
            'cachingEnabled', 'True').capitalize())
        self.parent.settings['hide_scrollbars'] = literal_eval(self.settings.value(
            'hideScrollBars', 'False').capitalize())
        self.parent.settings['toc_with_bookmarks'] = literal_eval(self.settings.value(
            'tocWithBookmarks', 'False').capitalize())
        self.parent.settings['scroll_speed'] = int(self.settings.value('scrollSpeed', 7))
        self.parent.settings['consider_read_at'] = int(self.settings.value('considerReadAt', 95))
        self.parent.settings['small_increment'] = int(self.settings.value('smallIncrement', 4))
        self.parent.settings['large_increment'] = int(self.settings.value('largeIncrement', 2))
        self.parent.settings['attenuate_titles'] = literal_eval(self.settings.value(
            'attenuateTitles', 'False').capitalize())
        self.parent.settings['double_page_mode'] = literal_eval(self.settings.value(
            'doublePageMode', 'False').capitalize())
        self.parent.settings['manga_mode'] = literal_eval(self.settings.value(
            'mangaMode', 'False').capitalize())
        self.settings.endGroup()

        self.settings.beginGroup('dialogSettings')
        self.parent.settings['dialog_background'] = self.settings.value(
            'dialogBackground', QtGui.QColor().fromRgb(0, 0, 0))
        self.settings.endGroup()

        self.settings.beginGroup('annotations')
        self.parent.settings['annotations'] = self.settings.value(
            'annotationList', list())
        if self.parent.settings['annotations'] is None:
            self.parent.settings['annotations'] = list()
        self.settings.endGroup()

        logger.info('Settings loaded')

    def save_settings(self):
        current_settings = self.parent.settings

        self.settings.beginGroup('mainWindow')
        self.settings.setValue('windowSize', self.parent.size())
        self.settings.setValue('windowPosition', self.parent.pos())
        self.settings.setValue('currentView', self.parent.stackedWidget.currentIndex())
        self.settings.setValue('iconTheme', self.parent.settings['icon_theme'])
        self.settings.setValue(
            'listViewBackground', self.parent.settings['listview_background'])

        table_headers = []
        for i in range(7):
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
        self.settings.setValue('rememberFiles', str(current_settings['remember_files']))
        self.settings.setValue('coverShadows', str(current_settings['cover_shadows']))
        self.settings.setValue('autoTags', str(current_settings['auto_tags']))
        self.settings.setValue('scanLibraryAtStart', str(current_settings['scan_library']))
        self.settings.setValue('performCulling', str(current_settings['perform_culling']))
        self.settings.setValue('dictionaryLanguage', str(current_settings['dictionary_language']))
        self.settings.setValue('cachingEnabled', str(current_settings['caching_enabled']))
        self.settings.setValue('hideScrollBars', str(current_settings['hide_scrollbars']))
        self.settings.setValue('attenuateTitles', str(current_settings['attenuate_titles']))
        self.settings.setValue('tocWithBookmarks', str(current_settings['toc_with_bookmarks']))
        self.settings.setValue('scrollSpeed', current_settings['scroll_speed'])
        self.settings.setValue('considerReadAt', current_settings['consider_read_at'])
        self.settings.setValue('mangaMode', str(current_settings['manga_mode']))
        self.settings.setValue('doublePageMode', str(current_settings['double_page_mode']))
        self.settings.setValue('smallIncrement', current_settings['small_increment'])
        self.settings.setValue('largeIncrement', current_settings['large_increment'])
        self.settings.endGroup()

        self.settings.beginGroup('dialogSettings')
        self.settings.setValue('dialogBackground', current_settings['dialog_background'])
        self.settings.endGroup()

        self.settings.beginGroup('annotations')
        self.settings.setValue('annotationList', current_settings['annotations'])
        self.settings.endGroup()

        logger.info('Settings saved')
