#!/usr/bin/env python3

import os

from PyQt5 import QtCore, QtGui
from resources import pie_chart


class LibraryItemModel(QtGui.QStandardItemModel, QtCore.QAbstractItemModel):
    def __init__(self, parent=None):
        # We're using this to be able to access the match() method
        super(LibraryItemModel, self).__init__(parent)


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

        # This block specializaes this function for the library
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
        if role == QtCore.Qt.DisplayRole:
            value = self.display_data[index.row()][index.column()]
            return value

        else:
            return QtCore.QVariant()

    def headerData(self, col, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.header_data[col]
        return None

    def flags(self, index):
        # In case of the settings model, model column index 1+ are editable
        if not self.temp_dir and index.column() != 0:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable
        else:
            # These are standard select but don't edit values
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable


class TableProxyModel(QtCore.QSortFilterProxyModel):
    def __init__(self, parent=None):
        super(TableProxyModel, self).__init__(parent)
        self.filter_string = None
        self.filter_columns = None

    def setFilterParams(self, filter_text, filter_columns):
        self.filter_string = filter_text.lower()
        self.filter_columns = filter_columns

    def filterAcceptsRow(self, row_num, parent):
        if self.filter_string is None or self.filter_columns is None:
            return True

        model = self.sourceModel()

        valid_indices = [model.index(row_num, i) for i in self.filter_columns]
        valid_data = [model.data(i, QtCore.Qt.DisplayRole).lower() for i in valid_indices if model.data(i, QtCore.Qt.DisplayRole) is not None]

        for i in valid_data:
            if self.filter_string in i:
                return True

        return False
