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

import pathlib

from PyQt5 import QtCore, QtWidgets
from resources import pie_chart


class BookmarkProxyModel(QtCore.QSortFilterProxyModel):
    def __init__(self, parent=None):
        super(BookmarkProxyModel, self).__init__(parent)
        self.parent = parent
        self.filter_string = None

    def setFilterParams(self, filter_text):
        self.filter_text = filter_text

    def filterAcceptsRow(self, row, parent):
        # TODO
        # Connect this to the search bar
        return True

    def setData(self, index, value, role):
        if role == QtCore.Qt.EditRole:
            source_index = self.mapToSource(index)
            identifier = self.sourceModel().data(source_index, QtCore.Qt.UserRole + 2)

            self.sourceModel().setData(source_index, value, QtCore.Qt.DisplayRole)
            self.parent.metadata['bookmarks'][identifier]['description'] = value

            return True


class ItemProxyModel(QtCore.QSortFilterProxyModel):
    def __init__(self, parent=None):
        super(ItemProxyModel, self).__init__(parent)
        self.filter_text = None
        self.active_library_filters = None
        self.sorting_box_position = None
        self.common_functions = ProxyModelsCommonFunctions(self)

    def setFilterParams(self, filter_text, active_library_filters, sorting_box_position):
        self.common_functions.setFilterParams(
            filter_text, active_library_filters, sorting_box_position)

    def filterAcceptsRow(self, row, parent):
        output = self.common_functions.filterAcceptsRow(row, parent)
        return output


class TableProxyModel(QtCore.QSortFilterProxyModel):
    def __init__(self, temp_dir, parent=None):
        super(TableProxyModel, self).__init__(parent)
        self.header_data = [
            None, 'Title', 'Author', 'Year', '%', 'Tags']
        self.temp_dir = temp_dir
        self.filter_text = None
        self.active_library_filters = None
        self.sorting_box_position = None
        self.role_dictionary = {
            1: QtCore.Qt.UserRole,      # Title
            2: QtCore.Qt.UserRole + 1,  # Author
            3: QtCore.Qt.UserRole + 2,  # Year
            4: QtCore.Qt.UserRole + 7,  # Position percentage
            5: QtCore.Qt.UserRole + 4}  # Tags
        self.common_functions = ProxyModelsCommonFunctions(self)

    def columnCount(self, parent):
        return 6

    def headerData(self, column, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            return self.header_data[column]

    def flags(self, index):
        # Tag editing will take place by way of a right click menu
        # These tags denote clickable and that's about it
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def data(self, index, role):
        source_index = self.mapToSource(index)
        item = self.sourceModel().item(source_index.row(), 0)

        if role == QtCore.Qt.TextAlignmentRole and index.column() == 3:
            return QtCore.Qt.AlignHCenter

        if role == QtCore.Qt.DecorationRole:
            if index.column() == 4:
                return_pixmap = None

                file_exists = item.data(QtCore.Qt.UserRole + 5)
                metadata = item.data(QtCore.Qt.UserRole + 3)
                position = metadata['position']
                if position:
                    is_read = position['is_read']

                if not file_exists:
                    return pie_chart.pixmapper(
                        -1, None, None, QtCore.Qt.SizeHintRole + 10)

                if position:
                    if is_read:
                        current_chapter = total_chapters = 100
                    else:
                        try:
                            current_chapter = position['current_chapter']
                            total_chapters = position['total_chapters']

                            # TODO
                            # See if there's any rationale for this
                            if current_chapter == 1:
                                raise KeyError
                        except KeyError:
                            return

                    return_pixmap = pie_chart.pixmapper(
                        current_chapter, total_chapters, self.temp_dir,
                        QtCore.Qt.SizeHintRole + 10)

                return return_pixmap

        elif role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            if index.column() in (0, 4):    # Cover and Status
                return QtCore.QVariant()

            return item.data(self.role_dictionary[index.column()])

        else:
            return QtCore.QVariant()

    def setFilterParams(self, filter_text, active_library_filters, sorting_box_position):
        self.common_functions.setFilterParams(
            filter_text, active_library_filters, sorting_box_position)

    def filterAcceptsRow(self, row, parent):
        output = self.common_functions.filterAcceptsRow(row, parent)
        return output

    def sort_table_columns(self, column):
        sorting_order = self.sender().sortIndicatorOrder()
        self.sort(0, sorting_order)
        self.setSortRole(self.role_dictionary[column])


class ProxyModelsCommonFunctions:
    def __init__(self, parent_model):
        self.parent_model = parent_model

    def setFilterParams(self, filter_text, active_library_filters, sorting_box_position):
        self.parent_model.filter_text = filter_text
        self.parent_model.active_library_filters = [i.lower() for i in active_library_filters]
        self.parent_model.sorting_box_position = sorting_box_position

    def filterAcceptsRow(self, row, parent):
        model = self.parent_model.sourceModel()

        this_index = model.index(row, 0)

        title = model.data(this_index, QtCore.Qt.UserRole)
        author = model.data(this_index, QtCore.Qt.UserRole + 1)
        tags = model.data(this_index, QtCore.Qt.UserRole + 4)
        directory_name = model.data(this_index, QtCore.Qt.UserRole + 10)
        directory_tags = model.data(this_index, QtCore.Qt.UserRole + 11)
        last_accessed = model.data(this_index, QtCore.Qt.UserRole + 12)

        # Hide untouched files when sorting by last accessed
        if self.parent_model.sorting_box_position == 4 and not last_accessed:
            return False

        if self.parent_model.active_library_filters:
            if directory_name not in self.parent_model.active_library_filters:
                return False
        else:
            return False

        if not self.parent_model.filter_text:
            return True
        else:
            valid_data = [
                i.lower() for i in (
                    title, author, tags, directory_name, directory_tags) if i is not None]
            for i in valid_data:
                if self.parent_model.filter_text.lower() in i:
                    return True
        return False


class MostExcellentFileSystemModel(QtWidgets.QFileSystemModel):
    # Directories are tracked on the basis of their paths
    # Poll the tag_data dictionary to get User selection
    def __init__(self, tag_data, parent=None):
        super(MostExcellentFileSystemModel, self).__init__(parent)
        self.tag_data = tag_data
        self.field_dict = {
            0: 'check_state',
            4: 'name',
            5: 'tags'}

    def columnCount(self, parent):
        # The QFileSystemModel returns 4 columns by default
        # Columns 1, 2, 3 will be present but hidden
        return 6

    def headerData(self, col, orientation, role):
        # Columns not mentioned here will be hidden
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            column_dict = {
                0: 'Path',
                4: 'Name',
                5: 'Tags'}
            try:
                return column_dict[col]
            except KeyError:
                pass

    def data(self, index, role):
        if (index.column() in (4, 5)
                and (role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole)):

            read_field = self.field_dict[index.column()]
            try:
                return self.tag_data[self.filePath(index)][read_field]
            except KeyError:
                return QtCore.QVariant()

        if role == QtCore.Qt.CheckStateRole and index.column() == 0:
            return self.checkState(index)

        return QtWidgets.QFileSystemModel.data(self, index, role)

    def flags(self, index):
        if index.column() in (4, 5):
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable
        else:
            return QtWidgets.QFileSystemModel.flags(self, index) | QtCore.Qt.ItemIsUserCheckable

    def checkState(self, index):
        while index.isValid():
            index_path = self.filePath(index)
            if index_path in self.tag_data:
                return self.tag_data[index_path]['check_state']
            index = index.parent()
        return QtCore.Qt.Unchecked

    def setData(self, index, value, role):
        if (role == QtCore.Qt.EditRole or role == QtCore.Qt.CheckStateRole) and index.isValid():
            write_field = self.field_dict[index.column()]
            self.layoutAboutToBeChanged.emit()

            this_path = self.filePath(index)
            if this_path not in self.tag_data:
                self.populate_dictionary(this_path)
            self.tag_data[this_path][write_field] = value

            self.depopulate_dictionary()

            self.layoutChanged.emit()
            return True

    def populate_dictionary(self, path):
        self.tag_data[path] = {}
        self.tag_data[path]['name'] = None
        self.tag_data[path]['tags'] = None
        self.tag_data[path]['check_state'] = QtCore.Qt.Checked

    def depopulate_dictionary(self):
        # This keeps the tag_data dictionary manageable as well as preventing
        # weird ass behaviour when something is deselected and its tags are cleared
        deletable = set()
        for i in self.tag_data.items():
            all_data = [j[1] for j in i[1].items()]
            filtered_down = list(filter(lambda x: x is not None and x != 0, all_data))
            if not filtered_down:
                deletable.add(i[0])

        # Get untagged subdirectories too
        all_dirs = [i for i in self.tag_data]
        all_dirs.sort()

        def is_child(this_dir):
            this_path = pathlib.Path(this_dir)
            for i in all_dirs:
                if pathlib.Path(i) in this_path.parents:
                    # If a parent folder has tags, we only want the deletion
                    # to kick in in case the parent is also checked
                    if self.tag_data[i]['check_state'] == QtCore.Qt.Checked:
                        return True
            return False

        for i in all_dirs:
            if is_child(i):
                dir_tags = (self.tag_data[i]['name'], self.tag_data[i]['tags'])
                filtered_down = list(filter(lambda x: x is not None and x != '', dir_tags))
                if not filtered_down:
                    deletable.add(i)

        for i in deletable:
            del self.tag_data[i]


# TODO
# Unbork this
class FileSystemProxyModel(QtCore.QSortFilterProxyModel):
    def __init__(self, parent=None):
        super(FileSystemProxyModel, self).__init__(parent)

    def filterAcceptsRow(self, row_num, parent):
        model = self.sourceModel()
        filter_out = [
            'boot', 'dev', 'etc', 'lost+found', 'opt', 'pdb',
            'proc', 'root', 'run', 'srv', 'sys', 'tmp', 'twonky',
            'usr', 'var', 'bin', 'kdeinit5__0', 'lib', 'lib64', 'sbin']

        name_index = model.index(row_num, 0)
        valid_data = model.data(name_index)

        print(valid_data)

        return True

        try:
            if valid_data in filter_out:
                return False
        except AttributeError:
            pass

        return True
