#!usr/bin/env python3

# This file is a part of Lector, a Qt based ebook reader
# Copyright (C) 2018 BasioMeusPuga

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

from PyQt5 import QtGui
from resources import resources


class QImageFactory:
    def __init__(self, parent):
        self.parent = parent

    def get_image(self, image_name):
        icon_theme = self.parent.settings['icon_theme']
        icon_path = f':/images/{icon_theme}/{image_name}.svg'

        this_qicon = QtGui.QIcon(icon_path)
        return this_qicon
