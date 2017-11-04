#!/usr/bin/env python3

import os
import zipfile
import tempfile
import xmltodict


class ePUB:
    def __init__(self, filename):
        self.filename = filename
        self.tmpdir = None

    def extract(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        with zipfile.ZipFile(self.filename, 'r') as zip_ref:
            zip_ref.extractall(self.tmpdir.name)

    def parse(self):
        with open(self.tmpdir.name + os.sep + 'content.opf') as fd:
            xml_dict = xmltodict.parse(fd.read())

        metadata = xml_dict['package']['metadata']
        book_title = metadata['dc:title']
        book_description = metadata['dc:description']
        book_author = metadata['dc:creator']['#text']

        print(book_author)
        print(book_title)
        print(book_description)