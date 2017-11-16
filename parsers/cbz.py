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
        except FileNotFoundError:
            print('Invalid path for ' + self.filename)
            return
        except (KeyError, AttributeError, zipfile.BadZipFile):
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
        # The first image in the archive may not be the cover
        # It is implied, however, that the first image in order
        # will be the cover

        image_list = [i.filename for i in self.book.infolist() if not i.is_dir()]
        image_list.sort()
        cover_image_filename = image_list[0]

        for i in self.book.infolist():
            if not i.is_dir():
                if i.filename == cover_image_filename:
                    cover_image = self.book.read(i)
                    return cover_image

    def get_isbn(self):
        return None

    def get_contents(self):
        # TODO
        # Image resizing, formatting
        # Include this as a collection of absolute paths only
        # Post processing can be carried out by the program
        # CBZ files containing multiple directories for multiple chapters

        file_settings = {
            'temp_dir': self.temp_dir,
            'images_only': True}

        extract_path = os.path.join(self.temp_dir, self.file_md5)
        contents = collections.OrderedDict()
        # This is a brute force approach
        # Maybe try reading from the file as everything
        # matures a little bit more

        contents = collections.OrderedDict()

        # I'm currently choosing not to keep multiple files in memory
        self.book.extractall(extract_path)

        found_images = []
        for i in os.walk(extract_path):
            if i[2]:  # Implies files were found
                image_dir = i[0]
                found_images = i[2]
                break

        if not found_images:
            print('Found nothing in ' + self.filename)
            return None, file_settings

        found_images.sort()

        for count, i in enumerate(found_images):
            page_name = 'Page ' + str(count)
            image_path = os.path.join(extract_path, image_dir, i)

            # contents[page_name] = image_path
            contents[page_name] = "<img src='%s' align='middle'/>" % image_path

        return contents, file_settings
