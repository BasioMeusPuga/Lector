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
from PyQt5 import QtWidgets, QtCore, QtGui, QtMultimedia

from resources import definitions


class DefinitionsUI(QtWidgets.QDialog, definitions.Ui_Dialog):
    def __init__(self, parent):
        super(DefinitionsUI, self).__init__()
        self.setupUi(self)

        self.parent = parent

        self.setWindowFlags(
            QtCore.Qt.Popup |
            QtCore.Qt.FramelessWindowHint)

        radius = 15
        path = QtGui.QPainterPath()
        path.addRoundedRect(QtCore.QRectF(self.rect()), radius, radius)
        mask = QtGui.QRegion(path.toFillPolygon().toPolygon())
        self.setMask(mask)

        self.app_id = 'bb7a91f9'
        self.app_key = 'fefacdf6775c347b52e9efa2efe642ef'

        self.root_url = 'https://od-api.oxforddictionaries.com:443/api/v1/inflections/'
        self.define_url = 'https://od-api.oxforddictionaries.com:443/api/v1/entries/'

        self.pronunciation_mp3 = None

        self.okButton.clicked.connect(self.hide)
        self.pronounceButton.clicked.connect(self.play_pronunciation)

    def api_call(self, url, word):
        language = self.parent.settings['dictionary_language']
        url = url + language + '/' + word.lower()

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
            self.set_text(word, None, None, True)
            return

        word_root = word_root_json['results'][0]['lexicalEntries'][0]['inflectionOf'][0]['id']
        self.pronounceButton.setToolTip(f'Pronounce "{word_root}"')

        definition_json = self.api_call(self.define_url, word_root)
        if not definition_json:
            return

        definitions = {}
        for i in definition_json['results'][0]['lexicalEntries']:
            category = i['lexicalCategory']

            try:
                self.pronunciation_mp3 = i['pronunciations'][0]['audioFile']
            except KeyError:
                self.pronounceButton.setEnabled(False)

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

    def set_text(self, word, word_root, definitions, nothing_found=False):
        html_string = ''

        # Word heading
        html_string += f'<h2><em><strong>{word}</strong></em></h2>\n'

        if nothing_found:
            language = self.parent.settings['dictionary_language'].upper()
            html_string += f'<p><em>No definitions found in {language}<em></p>\n'
        else:
            # Word root
            html_string += f'<p><em>Word root: <em>{word_root}</p>\n'

            # Definitions per category as an ordered list
            for i in definitions.items():
                category = i[0]
                html_string += f'<p><strong>{category}</strong>:</p>\n<ol>\n'

                for j in i[1]:
                    html_string += f'<li>{j}</li>\n'

                html_string += '</ol>\n'

        self.definitionView.setHtml(html_string)
        self.show()

    def color_background(self, set_initial=False):
        if set_initial:
            background = self.parent.settings['dialog_background']
        else:
            self.previous_position = self.pos()
            background = self.parent.get_color()

        self.setStyleSheet(
            "QDialog {{background-color: {0}}}".format(background.name()))
        self.definitionView.setStyleSheet(
            "QTextBrowser {{background-color: {0}}}".format(background.name()))

        if not set_initial:
            self.show()

    def play_pronunciation(self):
        if not self.pronunciation_mp3:
            return

        media_content = QtMultimedia.QMediaContent(
            QtCore.QUrl(self.pronunciation_mp3))

        player = QtMultimedia.QMediaPlayer(self)
        player.setMedia(media_content)
        player.play()

    def showEvent(self, event):
        self.color_background(True)

        size = self.size()
        desktop_size = QtWidgets.QDesktopWidget().screenGeometry()
        top = (desktop_size.height() / 2) - (size.height() / 2)
        left = (desktop_size.width() / 2) - (size.width() / 2)
        self.move(left, top)
