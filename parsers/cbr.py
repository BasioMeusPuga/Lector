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

# TODO
# Account for files with passwords

import os
import time
import collections
from rarfile import rarfile


class ParseCBR:
    def __init__(self, filename, temp_dir, file_md5):
        self.filename = filename
        self.book = None
        self.temp_dir = temp_dir
        self.file_md5 = file_md5

    def read_book(self):
        try:
            self.book = rarfile.RarFile(self.filename)
        except:  # Specifying no exception types might be warranted here
            print('Cannot parse ' + self.filename)
            return

    def get_title(self):
        filename = os.path.basename(self.filename)
        filename_proper = os.path.splitext(filename)[0]
        return filename_proper

    def get_author(self):
        return None

    def get_year(self):
        creation_time = time.ctime(os.path.getctime(self.filename))
        creation_year = creation_time.split()[-1]
        return creation_year

    def get_cover_image(self):
        # The first image in the archive may not be the cover
        # It is implied, however, that the first image in order
        # will be the cover

        image_list = [i.filename for i in self.book.infolist() if not i.isdir()]
        image_list.sort()
        cover_image_filename = image_list[0]

        for i in self.book.infolist():
            if not i.isdir():
                if i.filename == cover_image_filename:
                    cover_image = self.book.read(i)
                    return cover_image

    def get_isbn(self):
        return

    def get_tags(self):
        return

    def get_contents(self):
        file_settings = {
            'images_only': True}

        extract_path = os.path.join(self.temp_dir, self.file_md5)
        contents = []

        # I'm currently choosing not to keep multiple files in memory
        self.book.extractall(extract_path)

        found_images = []
        for i in os.walk(extract_path):
            if i[2]:  # Implies files were found
                image_dir = i[0]
                add_path_to_file = [
                    os.path.join(image_dir, j) for j in i[2]]
                found_images.extend(add_path_to_file)

        if not found_images:
            print('Found nothing in ' + self.filename)
            return None, file_settings

        found_images.sort()

        for count, i in enumerate(found_images):
            page_name = 'Page ' + str(count + 1)
            image_path = os.path.join(extract_path, i)

            contents.append((page_name, image_path))

        return contents, file_settings
