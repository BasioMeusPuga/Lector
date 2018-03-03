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

from PyQt5 import QtWidgets, QtCore, QtGui
from resources import metadata

class MetadataUI(QtWidgets.QDialog, metadata.Ui_Dialog):
    def __init__(self, parent):
        super(MetadataUI, self).__init__()
        self.setupUi(self)

        self.parent = parent
        self.setWindowFlags(
            QtCore.Qt.Window |
            QtCore.Qt.WindowCloseButtonHint)
        self.setFixedSize(self.width(), self.height())

        self.coverView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.coverView.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

    def load_book(self, cover, title, author, year, tags, index):
        image_pixmap = cover.pixmap(self.coverView.size())
        graphics_scene = QtWidgets.QGraphicsScene()
        graphics_scene.addPixmap(image_pixmap)
        self.coverView.setScene(graphics_scene)

        self.titleLine.setText(title)
        self.authorLine.setText(author)
        self.yearLine.setText(year)
        self.tagsLine.setText(tags)

    def showEvent(self, event):
        size = self.size()
        desktop_size = QtWidgets.QDesktopWidget().screenGeometry()
        top = (desktop_size.height() / 2) - (size.height() / 2)
        left = (desktop_size.width() / 2) - (size.width() / 2)
        self.move(left, top)
        self.parent.setEnabled(False)

    def hideEvent(self, event):
        self.parent.setEnabled(True)

    def closeEvent(self, event):
        self.parent.setEnabled(True)
        event.accept()
