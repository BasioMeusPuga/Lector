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

import requests
from PyQt5 import QtWidgets, QtCore, QtGui

from resources import definitions


class DefinitionsUI(QtWidgets.QDialog, definitions.Ui_Dialog):
    def __init__(self, parent):
        super(DefinitionsUI, self).__init__()
        self.setupUi(self)

        self.setWindowFlags(
            QtCore.Qt.Popup |
            QtCore.Qt.FramelessWindowHint)

        radius = 15
        path = QtGui.QPainterPath()
        path.addRoundedRect(QtCore.QRectF(self.rect()), radius, radius)
        mask = QtGui.QRegion(path.toFillPolygon().toPolygon())
        self.setMask(mask)

        foreground = QtGui.QColor().fromRgb(230, 230, 230)
        background = QtGui.QColor().fromRgb(0, 0, 0)

        self.setStyleSheet(
            "QDialog {{background-color: {0}}}".format(background.name()))
        self.definitionView.setStyleSheet(
            "QTextBrowser {{color: {0}; background-color: {1}}}".format(
                foreground.name(), background.name()))

        self.app_id = 'bb7a91f9'
        self.app_key = 'fefacdf6775c347b52e9efa2efe642ef'
        self.language = 'en'

        self.root_url = 'https://od-api.oxforddictionaries.com:443/api/v1/inflections/'
        self.define_url = 'https://od-api.oxforddictionaries.com:443/api/v1/entries/'

        self.root_url += self.language + '/'
        self.define_url += self.language + '/'

    def api_call(self, url, word):
        url = url + word.lower()

        r = requests.get(
            url,
            headers={'app_id': self.app_id, 'app_key': self.app_key})

        if r.status_code != 200:
            print('A firm nope on the dictionary finding thing')
            return None

        return r.json()

    def find_definition(self, word):
        word_root_json = self.api_call(self.root_url, word)
        if not word_root_json:
            return
        word_root = word_root_json['results'][0]['lexicalEntries'][0]['inflectionOf'][0]['id']

        definition_json = self.api_call(self.define_url, word_root)

        definitions = {}
        for i in definition_json['results'][0]['lexicalEntries']:
            category = i['lexicalCategory']
            this_sense = i['entries'][0]['senses']
            for j in this_sense:

                try:
                    this_definition = j['definitions'][0].capitalize()
                except KeyError:
                    # The API also reports crossReferenceMarkers here
                    pass

                try:
                    definitions[category].add(this_definition)
                except KeyError:
                    definitions[category] = set()
                    definitions[category].add(this_definition)

        self.set_text(word, word_root, definitions)

    def set_text(self, word, word_root, definitions):
        html_string = ''

        # Word heading
        html_string += f'<h2><em><strong>{word}</strong></em></h2>\n'

        # Word root
        html_string += f'<p><em>Word root: <em>{word_root}</p>\n'

        for i in definitions.items():
            category = i[0]
            html_string += f'<p><strong>{category}</strong>:</p>\n<ol>\n'

            for j in i[1]:
                html_string += f'<li>{j}</li>\n'

            html_string += '</ol>\n'

        self.definitionView.setHtml(html_string)
        self.show()
