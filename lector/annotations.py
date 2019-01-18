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

import logging

from PyQt5 import QtWidgets, QtCore, QtGui

from lector.resources import annotationswindow

logger = logging.getLogger(__name__)


class AnnotationsUI(QtWidgets.QDialog, annotationswindow.Ui_Dialog):
    def __init__(self, parent=None):
        super(AnnotationsUI, self).__init__()
        self.setupUi(self)

        self.parent = parent
        self._translate = QtCore.QCoreApplication.translate

        # Current annotation
        self.modelIndex = None  # The index of the annotations list model in the parent dialog
        self.current_annotation = {}

        # Populate annotation type
        textmarkup_string = self._translate('AnnotationsUI', 'Text markup')
        all_types = [textmarkup_string]
        for i in all_types:
            self.typeBox.addItem(i)

        # Init defaults
        self.default_stylesheet = self.foregroundCheck.styleSheet()
        self.foregroundColor = QtGui.QColor.fromRgb(0, 0, 0)
        self.underlineColor = QtGui.QColor.fromRgb(255, 0, 0)
        self.highlightColor = QtGui.QColor.fromRgb(66, 209, 56)
        self.underline_styles = {
            'Solid': QtGui.QTextCharFormat.SingleUnderline,
            'Dashes': QtGui.QTextCharFormat.DashUnderline,
            'Dots': QtGui.QTextCharFormat.DotLine,
            'Wavy': QtGui.QTextCharFormat.WaveUnderline}

        # Push buttons
        self.foregroundColorButton.clicked.connect(self.modify_annotation)
        self.highlightColorButton.clicked.connect(self.modify_annotation)
        self.underlineColorButton.clicked.connect(self.modify_annotation)

        self.okButton.clicked.connect(self.ok_pressed)
        self.cancelButton.clicked.connect(self.hide)

        # Underline combo box
        underline_items = ['Solid', 'Dashes', 'Dots', 'Wavy']
        self.underlineType.addItems(underline_items)
        self.underlineType.currentIndexChanged.connect(self.modify_annotation)

        # Text markup related checkboxes
        self.foregroundCheck.clicked.connect(self.modify_annotation)
        self.highlightCheck.clicked.connect(self.modify_annotation)
        self.boldCheck.clicked.connect(self.modify_annotation)
        self.italicCheck.clicked.connect(self.modify_annotation)
        self.underlineCheck.clicked.connect(self.modify_annotation)

    def show_dialog(self, mode, index=None):
        # TODO
        # Account for annotation type here
        # and point to a relevant set of widgets accordingly

        if mode == 'edit' or mode == 'preview':
            self.modelIndex = index
            this_annotation = self.parent.annotationModel.data(
                index, QtCore.Qt.UserRole)

            annotation_name = this_annotation['name']
            self.nameEdit.setText(annotation_name)

            annotation_components = this_annotation['components']

            if 'foregroundColor' in annotation_components:
                self.foregroundCheck.setChecked(True)
                self.set_button_background_color(
                    self.foregroundColorButton, annotation_components['foregroundColor'])
            else:
                self.foregroundCheck.setChecked(False)

            if 'highlightColor' in annotation_components:
                self.highlightCheck.setChecked(True)
                self.set_button_background_color(
                    self.highlightColorButton, annotation_components['highlightColor'])
            else:
                self.highlightCheck.setChecked(False)

            if 'bold' in annotation_components:
                self.boldCheck.setChecked(True)
            else:
                self.boldCheck.setChecked(False)

            if 'italic' in annotation_components:
                self.italicCheck.setChecked(True)
            else:
                self.italicCheck.setChecked(False)

            if 'underline' in annotation_components:
                self.underlineCheck.setChecked(True)
                underline_params = annotation_components['underline']
                self.underlineType.setCurrentText(underline_params[0])
                self.set_button_background_color(
                    self.underlineColorButton, underline_params[1])
            else:
                self.underlineCheck.setChecked(False)

        elif mode == 'add':
            new_annotation_string = self._translate('AnnotationsUI', 'New annotation')
            self.nameEdit.setText(new_annotation_string)

            all_checkboxes = (
                self.foregroundCheck, self.highlightCheck,
                self.boldCheck, self.italicCheck, self.underlineCheck)
            for i in all_checkboxes:
                i.setChecked(False)

            self.modelIndex = None
            self.set_button_background_color(
                self.foregroundColorButton, self.foregroundColor)
            self.set_button_background_color(
                self.highlightColorButton, self.highlightColor)
            self.set_button_background_color(
                self.underlineColorButton, self.underlineColor)

        self.update_preview()
        if mode != 'preview':
            self.show()

    def set_button_background_color(self, button, color):
        button.setStyleSheet(
            "QPushButton {{background-color: {0}}}".format(color.name()))

    def update_preview(self):
        cursor = self.parent.previewView.textCursor()
        cursor.setPosition(0)
        cursor.movePosition(QtGui.QTextCursor.End, QtGui.QTextCursor.KeepAnchor)

        # TODO
        # Other kinds of text markup
        previewCharFormat = QtGui.QTextCharFormat()

        if self.foregroundCheck.isChecked():
            previewCharFormat.setForeground(self.foregroundColor)

        highlight = QtCore.Qt.transparent
        if self.highlightCheck.isChecked():
            highlight = self.highlightColor
        previewCharFormat.setBackground(highlight)

        font_weight = QtGui.QFont.Normal
        if self.boldCheck.isChecked():
            font_weight = QtGui.QFont.Bold
        previewCharFormat.setFontWeight(font_weight)

        if self.italicCheck.isChecked():
            previewCharFormat.setFontItalic(True)

        if self.underlineCheck.isChecked():
            previewCharFormat.setFontUnderline(True)
            previewCharFormat.setUnderlineColor(self.underlineColor)
            previewCharFormat.setUnderlineStyle(
                self.underline_styles[self.underlineType.currentText()])

        previewCharFormat.setFontStyleStrategy(
            QtGui.QFont.PreferAntialias)

        cursor.setCharFormat(previewCharFormat)
        cursor.clearSelection()
        self.parent.previewView.setTextCursor(cursor)

    def modify_annotation(self):
        sender = self.sender()
        if isinstance(sender, QtWidgets.QCheckBox):
            if not sender.isChecked():
                self.update_preview()
                return

        new_color = None

        if sender == self.foregroundColorButton:
            new_color = self.get_color(self.foregroundColor)
            self.foregroundColor = new_color

        if sender == self.highlightColorButton:
            new_color = self.get_color(self.highlightColor)
            self.highlightColor = new_color

        if sender == self.underlineColorButton:
            new_color = self.get_color(self.underlineColor)
            self.underlineColor = new_color

        if new_color:
            self.set_button_background_color(sender, new_color)
        self.update_preview()

    def get_color(self, current_color):
        color_dialog = QtWidgets.QColorDialog()
        new_color = color_dialog.getColor(current_color)
        if new_color.isValid():  # Returned in case cancel is pressed
            return new_color
        else:
            return current_color

    def ok_pressed(self):
        annotation_name = self.nameEdit.text()
        if annotation_name == '':
            self.nameEdit.setText('Why do you like bugs? WHY?')
            return

        annotation_components = {}
        if self.foregroundCheck.isChecked():
            annotation_components['foregroundColor'] = self.foregroundColor
        if self.highlightCheck.isChecked():
            annotation_components['highlightColor'] = self.highlightColor
        if self.boldCheck.isChecked():
            annotation_components['bold'] = True
        if self.italicCheck.isChecked():
            annotation_components['italic'] = True
        if self.underlineCheck.isChecked():
            annotation_components['underline'] = (
                self.underlineType.currentText(), self.underlineColor)

        self.current_annotation = {
            'name': annotation_name,
            'applicable_to': 'text',
            'type': 'text_markup',
            'components': annotation_components}

        if self.modelIndex:
            self.parent.annotationModel.setData(
                self.modelIndex, annotation_name, QtCore.Qt.DisplayRole)
            self.parent.annotationModel.setData(
                self.modelIndex, self.current_annotation, QtCore.Qt.UserRole)
        else:  # New annotation
            new_annotation_item = QtGui.QStandardItem()
            new_annotation_item.setText(annotation_name)
            new_annotation_item.setData(self.current_annotation, QtCore.Qt.UserRole)
            self.parent.annotationModel.appendRow(new_annotation_item)

        self.hide()


class AnnotationPlacement:
    def __init__(self):
        self.annotation_type = None
        self.annotation_components = None
        self.underline_styles = {
            'Solid': QtGui.QTextCharFormat.SingleUnderline,
            'Dashes': QtGui.QTextCharFormat.DashUnderline,
            'Dots': QtGui.QTextCharFormat.DotLine,
            'Wavy': QtGui.QTextCharFormat.WaveUnderline}

    def set_current_annotation(self, annotation_type, annotation_components):
        # Components expected to be a dictionary
        self.annotation_type = annotation_type  # This is currently unused
        self.annotation_components = annotation_components

    def format_text(self, cursor, start_here, end_here):
        # This is applicable only to the PliantQTextBrowser
        # for the text_markup style of annotation

        # The cursor is the textCursor of the QTextEdit
        # containing the text that has to be modified

        if not self.annotation_components:
            return

        cursor.setPosition(start_here)
        cursor.setPosition(end_here, QtGui.QTextCursor.KeepAnchor)

        newCharFormat = QtGui.QTextCharFormat()

        if 'foregroundColor' in self.annotation_components:
            newCharFormat.setForeground(
                self.annotation_components['foregroundColor'])

        if 'highlightColor' in self.annotation_components:
            newCharFormat.setBackground(
                self.annotation_components['highlightColor'])

        if 'bold' in self.annotation_components:
            newCharFormat.setFontWeight(QtGui.QFont.Bold)

        if 'italic' in self.annotation_components:
            newCharFormat.setFontItalic(True)

        if 'underline' in self.annotation_components:
            newCharFormat.setFontUnderline(True)
            newCharFormat.setUnderlineStyle(
                self.underline_styles[self.annotation_components['underline'][0]])
            newCharFormat.setUnderlineColor(
                self.annotation_components['underline'][1])

        newCharFormat.setFontStyleStrategy(
            QtGui.QFont.PreferAntialias)

        cursor.setCharFormat(newCharFormat)
        cursor.clearSelection()
        return cursor
