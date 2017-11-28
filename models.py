#!/usr/bin/env python3

from PyQt5 import QtCore, QtGui


class LibraryItemModel(QtGui.QStandardItemModel, QtCore.QAbstractItemModel):
    def __init__(self, parent=None):
        # We're using this to be able to access the match() method
        super(LibraryItemModel, self).__init__(parent)


class LibraryTableModel(QtCore.QAbstractTableModel):
    # Sorting is taken care of by the QSortFilterProxy model
    # which has an inbuilt sort method

    def __init__(self, header_data, display_data, parent=None):
        super(LibraryTableModel, self).__init__(parent)
        self.header_data = header_data
        self.display_data = display_data

    def rowCount(self, parent):
        return len(self.display_data)

    def columnCount(self, parent):
        return len(self.header_data)

    def data(self, index, role):
        if not index.isValid():
            return None

        if role == QtCore.Qt.DisplayRole:
            value = self.display_data[index.row()][index.column()]
            file_exists = self.display_data[index.row()][4]['file_exists']
            return value
        elif role == QtCore.Qt.UserRole:
            # The rest of the roles can be accomodated here.
            value = self.display_data[index.row()][4]
            return value
        else:
            return QtCore.QVariant()

    def headerData(self, col, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.header_data[col]
        return None


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
