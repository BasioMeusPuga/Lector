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

import logging

from PyQt5 import QtWidgets, QtGui, QtCore

from lector.resources import pie_chart

logger = logging.getLogger(__name__)


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
        position_percent = index.data(QtCore.Qt.UserRole + 7)

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
            painter.setOpacity(1)
            read_icon = pie_chart.pixmapper(
                -1, None, self.parent.settings['consider_read_at'], 36)
            x_draw = option.rect.bottomRight().x() - 30
            y_draw = option.rect.bottomRight().y() - 35
            painter.drawPixmap(x_draw, y_draw, read_icon)
            return

        QtWidgets.QStyledItemDelegate.paint(self, painter, option, index)

        if position_percent:
            read_icon = pie_chart.pixmapper(
                position_percent, self.temp_dir, self.parent.settings['consider_read_at'], 36)

            x_draw = option.rect.bottomRight().x() - 30
            y_draw = option.rect.bottomRight().y() - 35
            painter.drawPixmap(x_draw, y_draw, read_icon)
