#!/usr/bin/env python3

import os

from PyQt5 import QtCore, QtGui
from resources import pie_chart


class LibraryItemModel(QtGui.QStandardItemModel, QtCore.QAbstractItemModel):
    def __init__(self, parent=None):
        # We're using this to be able to access the match() method
        super(LibraryItemModel, self).__init__(parent)


class LibraryTableModel(QtCore.QAbstractTableModel):
    # Sorting is taken care of by the QSortFilterProxy model
    # which has an inbuilt sort method

    def __init__(self, header_data, display_data, temp_dir=None, parent=None):
        super(LibraryTableModel, self).__init__(parent)
        self.header_data = header_data
        self.display_data = display_data
        self.temp_dir = temp_dir  # Is only needed for the main table
                                  # This model is otherwise reusable if this remains None

    def rowCount(self, parent):
        return len(self.display_data)

    def columnCount(self, parent):
        return len(self.header_data)

    def data(self, index, role):
        if not index.isValid():
            return None

        if role == QtCore.Qt.DecorationRole and index.column() == 2 and self.temp_dir:
            return_pixmap = None
            file_exists = self.display_data[index.row()][5]['file_exists']
            position = self.display_data[index.row()][5]['position']

            if not file_exists:
                return_pixmap = QtGui.QIcon(':/images/error.svg').pixmap(
                    QtCore.Qt.SizeHintRole + 10)

            if position:
                current_chapter = position['current_chapter']
                total_chapters = position['total_chapters']
                progress_percent = int(current_chapter * 100 / total_chapters)

                if current_chapter == total_chapters:
                    return_pixmap = QtGui.QIcon(':/images/checkmark.svg').pixmap(
                        QtCore.Qt.SizeHintRole + 10)
                else:
                    pie_chart.GeneratePie(progress_percent, self.temp_dir).generate()
                    svg_path = os.path.join(self.temp_dir, 'lector_progress.svg')
                    return_pixmap = QtGui.QIcon(svg_path).pixmap(
                        QtCore.Qt.SizeHintRole + 10)

            return return_pixmap

        elif role == QtCore.Qt.DisplayRole:
            value = self.display_data[index.row()][index.column()]
            return value

        elif role == QtCore.Qt.UserRole:
            # The rest of the roles can be accomodated here.
            value = self.display_data[index.row()][5]
            return value

        elif role == QtCore.Qt.UserRole + 1:
            value = self.display_data[index.row()][6]
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
