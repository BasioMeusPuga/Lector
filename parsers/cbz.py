#!/usr/bin/env python3

import os
import time
import zipfile
import tempfile
import collections


class ParseCBZ:
    def __init__(self, filename):
        # TODO
        # Maybe also include book description
        self.filename = filename
        self.book = None

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
        contents = collections.OrderedDict()
        # This is a brute force approach
        # Maybe try reading from the file as everything
        # matures a little bit more
        tmp_dir = tempfile.mkdtemp()

        contents = collections.OrderedDict()
        for count, i in enumerate(self.book.infolist()):
            self.book.extract(i, path=tmp_dir)
            page_name = 'Page ' + str(count + 1)
            image_path = os.path.join(tmp_dir, i.filename)
            # This does image returns.
            # TODO
            # Image resizing, formatting
            # Cleanup after exit
            contents[page_name] = "<img src='%s'/>" % image_path
        return contents, tmp_dir
