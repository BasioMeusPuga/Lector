#!/usr/bin/env python3

import os
import time
import zipfile
import collections


class ParseCBZ:
    def __init__(self, filename, temp_dir, file_md5):
        self.filename = filename
        self.book = None
        self.temp_dir = temp_dir
        self.file_md5 = file_md5

    def read_book(self):
        try:
            self.book = zipfile.ZipFile(self.filename, mode='r', allowZip64=True)
        except (KeyError, AttributeError, FileNotFoundError, zipfile.BadZipFile):
            print('Cannot parse ' + self.filename)
            return

    def get_title(self):
        filename = os.path.basename(self.book.filename)
        filename_proper = os.path.splitext(filename)[0]
        return filename_proper

    def get_author(self):
        return None

    def get_year(self):
        creation_time = time.ctime(os.path.getctime(self.filename))
        creation_year = creation_time.split()[-1]
        return creation_year

    def get_cover_image(self):
        cover_image_info = self.book.infolist()[0]
        cover_image = self.book.read(cover_image_info)
        return cover_image

    def get_isbn(self):
        return None

    def get_contents(self):
        extract_path = os.path.join(self.temp_dir, self.file_md5)
        contents = collections.OrderedDict()
        # This is a brute force approach
        # Maybe try reading from the file as everything
        # matures a little bit more

        contents = collections.OrderedDict()
        for count, i in enumerate(self.book.infolist()):
            self.book.extract(i, path=extract_path)
            page_name = 'Page ' + str(count + 1)
            image_path = os.path.join(extract_path, i.filename)
            # This does image returns.

            # TODO
            # Image resizing, formatting
            # Include this as a collection of absolute paths only
            # Post processing can be carried out by the program

            contents[page_name] = "<img src='%s' align='middle'/>" % image_path

        file_settings = {
            'temp_dir': self.temp_dir,
            'images_only': True}

        return contents, file_settings
