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
        # TODO
        # The setData method
        super(TableProxyModel, self).__init__(parent)
        self.header_data = [None, 'Title', 'Author', 'Status', 'Year', 'Tags']
        self.temp_dir = temp_dir
        self.filter_text = None
        self.active_library_filters = None
        self.sorting_box_position = None
        self.common_functions = ProxyModelsCommonFunctions(self)

    def columnCount(self, parent):
        return 6

    def headerData(self, column, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            return self.header_data[column]

    def flags(self, index):
        # This means only the Tags column is editable
        if index.column() == 4:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable
        else:
            # These are standard select but don't edit values
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def data(self, index, role):
        source_index = self.mapToSource(index)
        item = self.sourceModel().item(source_index.row(), 0)

        if role == QtCore.Qt.DecorationRole:
            if index.column() == 3:
                return_pixmap = None

                file_exists = item.data(QtCore.Qt.UserRole + 5)
                position = item.data(QtCore.Qt.UserRole + 7)

                if not file_exists:
                    return_pixmap = pie_chart.pixmapper(
                        -1, None, None, QtCore.Qt.SizeHintRole + 10)

                if position:
                    current_chapter = position['current_chapter']
                    total_chapters = position['total_chapters']

                    return_pixmap = pie_chart.pixmapper(
                        current_chapter, total_chapters, self.temp_dir,
                        QtCore.Qt.SizeHintRole + 10)

                return return_pixmap

        elif role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:

            if index.column() in (0, 3):    # Cover and Status
                return QtCore.QVariant()

            role_dictionary = {
                1: QtCore.Qt.UserRole,      # Title
                2: QtCore.Qt.UserRole + 1,  # Author
                4: QtCore.Qt.UserRole + 2,  # Year
                5: QtCore.Qt.UserRole + 4}  # Tags

            return item.data(role_dictionary[index.column()])

        else:
            return QtCore.QVariant()

    def setFilterParams(self, filter_text, active_library_filters, sorting_box_position):
        self.common_functions.setFilterParams(
            filter_text, active_library_filters, sorting_box_position)

    def filterAcceptsRow(self, row, parent):
        output = self.common_functions.filterAcceptsRow(row, parent)
        return output


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


class MostExcellentTableModel(QtCore.QAbstractTableModel):
    # Sorting is taken care of by the QSortFilterProxy model
    # which has an inbuilt sort method

    # Modifying data in the table model is a case of modifying the
    # data sent to it as a list
    # In this case, that's self.data_list

    def __init__(self, header_data, display_data, temp_dir=None, parent=None):
        super(MostExcellentTableModel, self).__init__(parent)
        self.header_data = header_data
        self.display_data = display_data
        self.temp_dir = temp_dir

    def rowCount(self, parent):
        if self.display_data:
            return len(self.display_data)
        else:
            return 0

    def columnCount(self, parent):
        return len(self.header_data)

    def data(self, index, role):
        if not index.isValid():
            return None

        # This block specializes this function for the library
        # Not having a self.temp_dir allows for its reuse elsewhere
        if self.temp_dir:
            if role == QtCore.Qt.DecorationRole and index.column() == 2:
                return_pixmap = None
                file_exists = self.display_data[index.row()][5]['file_exists']
                position = self.display_data[index.row()][5]['position']

                if not file_exists:
                    return_pixmap = pie_chart.pixmapper(
                        -1, None, None, QtCore.Qt.SizeHintRole + 10)

                if position:
                    current_chapter = position['current_chapter']
                    total_chapters = position['total_chapters']

                    return_pixmap = pie_chart.pixmapper(
                        current_chapter, total_chapters, self.temp_dir,
                        QtCore.Qt.SizeHintRole + 10)

                return return_pixmap

            # The rest of the roles can be accomodated here.
            elif role == QtCore.Qt.UserRole:
                value = self.display_data[index.row()][5]  # File metadata
                return value

            elif role == QtCore.Qt.UserRole + 1:
                value = self.display_data[index.row()][6]  # File hash
                return value

        #_________________________________
        # The EditRole is so that editing a cell doesn't clear its contents
        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            value = self.display_data[index.row()][index.column()]
            return value

        else:
            return QtCore.QVariant()

    def headerData(self, col, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.header_data[col]
        return None

    def flags(self, index):
        # This means only the Tags column is editable
        if self.temp_dir and index.column() == 4:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable
        else:
            # These are standard select but don't edit values
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        # We don't need to connect this to dataChanged since the underlying
        # table model (not the proxy model) is the one that's being updated

        # Database tags for files should not be updated each time
        # a new folder gets added or deleted from the directory
        # This will be done @ runtime
        # Individually set file tags will be preserved
        # Duplicate file tags will be removed

        row = index.row()
        col = index.column()
        self.display_data[row][col] = value
        return True


class TableProxyModel2(QtCore.QSortFilterProxyModel):
    def __init__(self, parent=None):
        super(TableProxyModel2, self).__init__(parent)
        self.filter_string = None
        self.filter_columns = None
        self.active_library_filters = None

    def setFilterParams(self, filter_text, filter_columns, active_library_filters):
        self.filter_string = filter_text.lower()
        self.filter_columns = filter_columns
        self.active_library_filters = [i.lower() for i in active_library_filters]

    def filterAcceptsRow(self, row_num, parent):
        if self.filter_string is None or self.filter_columns is None:
            return True

        model = self.sourceModel()

        valid_indices = [model.index(row_num, i) for i in self.filter_columns]
        valid_data = [
            model.data(i, QtCore.Qt.DisplayRole).lower() for i in valid_indices if model.data(
                i, QtCore.Qt.DisplayRole) is not None]

        try:
            valid_data.extend([model.display_data[row_num][7], model.display_data[row_num][8]])
        except IndexError:  # Columns 7 and 8 are added after creation of the model
            pass

        # Filter out all books not in the active library filters
        if self.active_library_filters:
            current_library_name = valid_data[-2].lower()
            if current_library_name not in self.active_library_filters:
                return False
        else:
            return False

        for i in valid_data:
            if i:
                if self.filter_string in i:
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
