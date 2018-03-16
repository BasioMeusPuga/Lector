#!/usr/bin/env python3

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

import io
from PyQt5 import QtCore
from bs4 import BeautifulSoup

proceed = True
try:
    import popplerqt5
except ImportError:
    print('python-poppler-qt5 is not installed. Pdf files will not work.')
    proceed = False

class ParsePDF:
    def __init__(self, filename, *args):
        self.filename = filename
        self.book = None
        self.metadata = None

    def read_book(self):
        if not proceed:
            return

        self.book = popplerqt5.Poppler.Document.load(self.filename)
        if not self.book:
            return

        self.metadata = BeautifulSoup(self.book.metadata(), 'xml')

    def get_title(self):
        try:
            title = self.metadata.find('title').text
            return title.replace('\n', '')
        except AttributeError:
            return 'Unknown'

    def get_author(self):
        try:
            author = self.metadata.find('creator').text
            return author.replace('\n', '')
        except AttributeError:
            return 'Unknown'

    def get_year(self):
        try:
            year = self.metadata.find('MetadataDate').text
            return year.replace('\n', '')
        except AttributeError:
            return 9999

    def get_cover_image(self):
        self.book.setRenderHint(
            popplerqt5.Poppler.Document.Antialiasing
            and popplerqt5.Poppler.Document.TextAntialiasing)

        cover_page = self.book.page(0)
        cover_image = cover_page.renderToImage(300, 300)
        return resize_image(cover_image)

    def get_isbn(self):
        return None

    def get_tags(self):
        try:
            tags = self.metadata.find('Keywords').text
            return tags.replace('\n', '')
        except AttributeError:
            return None

    def get_contents(self):
        file_settings = {'images_only': True}
        contents = [(f'Page {i + 1}', i) for i in range(self.book.numPages())]

        return contents, file_settings


def resize_image(cover_image):
    cover_image = cover_image.scaled(
        420, 600, QtCore.Qt.IgnoreAspectRatio)

    byte_array = QtCore.QByteArray()
    buffer = QtCore.QBuffer(byte_array)
    buffer.open(QtCore.QIODevice.WriteOnly)
    cover_image.save(buffer, 'jpg', 75)

    cover_image_final = io.BytesIO(byte_array)
    cover_image_final.seek(0)
    return cover_image_final.getvalue()
