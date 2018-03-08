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

from PyQt5 import QtWidgets, QtGui, QtCore
from resources import pie_chart


class LibraryDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, temp_dir, parent=None):
        super(LibraryDelegate, self).__init__(parent)
        self.temp_dir = temp_dir
        self.parent = parent

    def paint(self, painter, option, index):
        # This is a hint for the future
        # Color icon slightly red
        # if option.state & QtWidgets.QStyle.State_Selected:
            # painter.fillRect(option.rect, QtGui.QColor().fromRgb(255, 0, 0, 20))

        option = option.__class__(option)
        file_exists = index.data(QtCore.Qt.UserRole + 5)
        metadata = index.data(QtCore.Qt.UserRole + 3)

        position = metadata['position']
        if position:
            is_read = position['is_read']

        # The shadow pixmap currently is set to 420 x 600
        # Only draw the cover shadow in case the setting is enabled
        if self.parent.settings['cover_shadows']:
            shadow_pixmap = QtGui.QPixmap()
            shadow_pixmap.load(':/images/gray-shadow.png')
            shadow_pixmap = shadow_pixmap.scaled(160, 230, QtCore.Qt.IgnoreAspectRatio)
            shadow_x = option.rect.topLeft().x() + 10
            shadow_y = option.rect.topLeft().y() - 5
            painter.setOpacity(.7)
            painter.drawPixmap(shadow_x, shadow_y, shadow_pixmap)
            painter.setOpacity(1)

        if not file_exists:
            painter.setOpacity(.7)
            QtWidgets.QStyledItemDelegate.paint(self, painter, option, index)
            read_icon = pie_chart.pixmapper(-1, None, None, 36)
            x_draw = option.rect.bottomRight().x() - 30
            y_draw = option.rect.bottomRight().y() - 35
            painter.drawPixmap(x_draw, y_draw, read_icon)
            painter.setOpacity(1)
            return

        QtWidgets.QStyledItemDelegate.paint(self, painter, option, index)
        if position:
            if is_read:
                current_chapter = total_chapters = 100
            else:
                try:
                    current_chapter = position['current_chapter']
                    total_chapters = position['total_chapters']
                except KeyError:
                    return

            read_icon = pie_chart.pixmapper(
                current_chapter, total_chapters, self.temp_dir, 36)

            x_draw = option.rect.bottomRight().x() - 30
            y_draw = option.rect.bottomRight().y() - 35
            if current_chapter != 1:
                painter.drawPixmap(x_draw, y_draw, read_icon)


class BookmarkDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent=None):
        super(BookmarkDelegate, self).__init__(parent)
        self.parent = parent

    def sizeHint(self, *args):
        dockwidget_width = self.parent.width() - 20
        return QtCore.QSize(dockwidget_width, 50)

    def paint(self, painter, option, index):
        # TODO
        # Alignment of the painted item

        option = option.__class__(option)

        chapter_index = index.data(QtCore.Qt.UserRole)
        chapter_name = self.parent.window().bookToolBar.tocBox.itemText(chapter_index - 1)
        if len(chapter_name) > 25:
            chapter_name = chapter_name[:25] + '...'

        QtWidgets.QStyledItemDelegate.paint(self, painter, option, index)
        painter.drawText(
            option.rect,
            QtCore.Qt.AlignBottom | QtCore.Qt.AlignRight | QtCore.Qt.TextWordWrap,
            '   ' + chapter_name)
