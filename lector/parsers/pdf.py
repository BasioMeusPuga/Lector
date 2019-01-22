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

# TODO
# Error handling
# TOC parsing

import io
import os

import fitz
from PyQt5 import QtCore, QtGui


class ParsePDF:
    def __init__(self, filename, *args):
        self.filename = filename
        self.book = None

    def read_book(self):
        try:
            self.book = fitz.open(self.filename)
            return True
        except RuntimeError:
            return False

    def get_title(self):
        title = self.book.metadata['title']
        if not title:
            title = os.path.splitext(os.path.basename(self.filename))[0]
        return title

    def get_author(self):
        author = self.book.metadata['author']
        if not author:
            author = 'Unknown'
        return author

    def get_year(self):
        creation_date = self.book.metadata['creationDate']
        try:
            year = creation_date.split(':')[1][:4]
        except (ValueError, AttributeError):
            year = 9999
        return year

    def get_cover_image(self):
        # TODO
        # See if there's any way to stop this roundabout way of
        # getting a smaller QImage from a larger Pixmap
        cover_page = self.book.loadPage(0)
        coverPixmap = cover_page.getPixmap()
        imageFormat = QtGui.QImage.Format_RGB888
        if coverPixmap.alpha:
            imageFormat = QtGui.QImage.Format_RGBA8888
        coverQImage = QtGui.QImage(
            coverPixmap.samples,
            coverPixmap.width,
            coverPixmap.height,
            coverPixmap.stride,
            imageFormat)

        return resize_image(coverQImage)

    def get_isbn(self):
        return None

    def get_tags(self):
        tags = self.book.metadata['keywords']
        return tags  # Fine if it returns None

    def get_contents(self):
        # Contents are to be returned as:
        # Level, Title, Page Number
        # Increasing the level number means the
        # title is one level up in the tree

        # TODO
        # Better parsing of TOC
        # contents = self.book.getToC()
        # if not contents:
        #     contents = [
        #         (1, f'Page {i + 1}', i) for i in range(self.book.pageCount)]

        # return contents, file_settings

        file_settings = {'images_only': True}
        contents = [(f'Page {i + 1}', i) for i in range(self.book.pageCount)]
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


def render_pdf_page(page_data):
    # Draw page contents on to a pixmap
    pixmap = QtGui.QPixmap()
    zoom_matrix = fitz.Matrix(4, 4)  # Sets render quality
    pagePixmap = page_data.getPixmap(
        matrix=zoom_matrix)
    imageFormat = QtGui.QImage.Format_RGB888
    if pagePixmap.alpha:
        imageFormat = QtGui.QImage.Format_RGBA8888
    pageQImage = QtGui.QImage(
        pagePixmap.samples,
        pagePixmap.width,
        pagePixmap.height,
        pagePixmap.stride,
        imageFormat)
    pixmap.convertFromImage(pageQImage)

    # Draw page background
    # Currently going with White - any color should be possible
    finalPixmap = QtGui.QPixmap(pixmap.size())
    finalPixmap.fill(QtGui.QColor(QtCore.Qt.white))
    imagePainter = QtGui.QPainter(finalPixmap)
    imagePainter.drawPixmap(0, 0, pixmap)

    return finalPixmap
