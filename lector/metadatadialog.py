# This file is a part of Lector, a Qt based ebook reader
# Copyright (C) 2017-2018 BasioMeusPuga

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

from lector import database
from lector.widgets import PliantQGraphicsScene
from lector.resources import metadata


class MetadataUI(QtWidgets.QDialog, metadata.Ui_Dialog):
    def __init__(self, parent):
        super(MetadataUI, self).__init__()
        self.setupUi(self)
        self._translate = QtCore.QCoreApplication.translate

        self.setWindowFlags(
            QtCore.Qt.Popup |
            QtCore.Qt.FramelessWindowHint)

        self.parent = parent

        radius = 15
        path = QtGui.QPainterPath()
        path.addRoundedRect(QtCore.QRectF(self.rect()), radius, radius)

        try:
            mask = QtGui.QRegion(path.toFillPolygon().toPolygon())
            self.setMask(mask)
        except TypeError:  # Required for older versions of Qt
            pass

        self.parent = parent
        self.database_path = self.parent.database_path

        self.book_index = None
        self.book_year = None
        self.previous_position = None
        self.cover_for_database = None

        self.coverView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.coverView.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self.okButton.clicked.connect(self.ok_pressed)
        self.cancelButton.clicked.connect(self.cancel_pressed)
        self.dialogBackground.clicked.connect(self.color_background)

        self.titleLine.returnPressed.connect(self.ok_pressed)
        self.authorLine.returnPressed.connect(self.ok_pressed)
        self.yearLine.returnPressed.connect(self.ok_pressed)
        self.tagsLine.returnPressed.connect(self.ok_pressed)

    def load_book(self, cover, title, author, year, tags, book_index):
        self.previous_position = None
        self.cover_for_database = None

        self.book_index = book_index
        self.book_year = year

        self.load_cover(cover)

        self.titleLine.setText(title)
        self.authorLine.setText(author)
        self.yearLine.setText(year)
        self.tagsLine.setText(tags)

    def load_cover(self, cover, use_as_is=False):
        if use_as_is:
            image_pixmap = cover
        else:
            image_pixmap = cover.pixmap(QtCore.QSize(140, 205))

        graphics_scene = PliantQGraphicsScene(self)
        graphics_scene.addPixmap(image_pixmap)
        self.coverView.setScene(graphics_scene)

    def ok_pressed(self, event=None):
        book_item = self.parent.lib_ref.libraryModel.item(self.book_index.row())

        title = self.titleLine.text()
        author = self.authorLine.text()
        tags = self.tagsLine.text()

        try:
            year = int(self.yearLine.text())
        except ValueError:
            year = self.book_year

        author_string = self._translate('MetadataUI', 'Author')
        year_string = self._translate('MetadataUI', 'Year')
        tooltip_string = f'{title} \n{author_string}: {author} \n{year_string}: {str(year)}'

        book_item.setData(title, QtCore.Qt.UserRole)
        book_item.setData(author, QtCore.Qt.UserRole + 1)
        book_item.setData(year, QtCore.Qt.UserRole + 2)
        book_item.setData(tags, QtCore.Qt.UserRole + 4)
        book_item.setToolTip(tooltip_string)

        book_hash = book_item.data(QtCore.Qt.UserRole + 6)
        database_dict = {
            'Title': title,
            'Author': author,
            'Year': year,
            'Tags': tags}

        if self.cover_for_database:
            database_dict['CoverImage'] = self.cover_for_database
            self.parent.cover_functions.cover_loader(
                book_item, self.cover_for_database)

        self.parent.lib_ref.update_proxymodels()
        self.hide()

        database.DatabaseFunctions(self.database_path).modify_metadata(
            database_dict, book_hash)

    def cancel_pressed(self, event=None):
        self.hide()

    def generate_display_position(self, mouse_cursor_position):
        size = self.size()
        desktop_size = QtWidgets.QDesktopWidget().screenGeometry()

        display_x = mouse_cursor_position.x()
        display_y = mouse_cursor_position.y()

        if display_x + size.width() > desktop_size.width():
            display_x = desktop_size.width() - size.width()

        if display_y + size.height() > desktop_size.height():
            display_y = desktop_size.height() - size.height()

        return QtCore.QPoint(display_x, display_y)

    def color_background(self, set_initial=False):
        if set_initial:
            background = self.parent.settings['dialog_background']
        else:
            self.previous_position = self.pos()
            self.parent.get_color()
            background = self.parent.settings['dialog_background']

        self.setStyleSheet(
            "QDialog {{background-color: {0}}}".format(background.name()))
        self.coverView.setStyleSheet(
            "QGraphicsView {{background-color: {0}}}".format(background.name()))

        if not set_initial:
            self.show()

    def showEvent(self, event):
        if self.previous_position:
            self.move(self.previous_position)
        else:
            display_position = self.generate_display_position(QtGui.QCursor.pos())
            self.move(display_position)

        self.titleLine.setFocus()
        self.color_background(True)
