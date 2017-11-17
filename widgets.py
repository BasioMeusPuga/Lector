#!usr/bin/env python3

import os
from PyQt5 import QtWidgets, QtGui, QtCore

import sorter
import database
from resources import resources, pie_chart


class BookToolBar(QtWidgets.QToolBar):
    def __init__(self, parent=None):
        super(BookToolBar, self).__init__(parent)

        # Spacer
        spacer = QtWidgets.QWidget()
        spacer.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.setMovable(False)
        self.setIconSize(QtCore.QSize(22, 22))
        self.setFloatable(False)
        self.setObjectName("LibraryToolBar")

        # Buttons
        self.fullscreenButton = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('view-fullscreen'), 'Fullscreen', self)
        self.fontButton = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('gtk-select-font'), 'Font settings', self)
        self.settingsButton = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('settings'), 'Settings', self)
        self.resetProfile = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('view-refresh'), 'Reset profile', self)

        # Add buttons
        self.addAction(self.fontButton)
        self.fontButton.setCheckable(True)
        self.fontButton.triggered.connect(self.toggle_font_settings)
        self.addSeparator()
        self.addAction(self.fullscreenButton)
        self.addAction(self.settingsButton)
        self.settingsButton.setCheckable(True)

        # Font modification
        font_sizes = [str(i) for i in range(8, 48, 2)]
        font_sizes.extend(['56', '64', '72'])
        self.fontSizeBox = QtWidgets.QComboBox(self)
        self.fontSizeBox.setObjectName('fontSizeBox')
        self.fontSizeBox.setToolTip('Font size')
        self.fontSizeBox.addItems(font_sizes)
        self.fontSizeBox.setEditable(True)

        self.paddingUp = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('format-indent-less'),
            'Increase padding', self)
        self.paddingUp.setObjectName('paddingUp')
        self.paddingDown = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('format-justify-fill'),
            'Decrease padding', self)
        self.paddingDown.setObjectName('paddingDown')

        self.lineSpacingUp = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('format-line-spacing-triple'),
            'Increase line spacing', self)
        self.lineSpacingUp.setObjectName('lineSpacingUp')
        self.lineSpacingDown = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('format-line-spacing-double'),
            'Decrease line spacing', self)
        self.lineSpacingDown.setObjectName('lineSpacingDown')

        self.fontBox = QtWidgets.QFontComboBox()
        self.fontBox.setFontFilters(QtWidgets.QFontComboBox.ScalableFonts)
        self.fontBox.setObjectName('fontBox')

        self.colorBoxFG = FixedPushButton(self)
        self.colorBoxFG.setObjectName('fgColor')
        self.colorBoxFG.setToolTip('Text color')
        self.colorBoxBG = FixedPushButton(self)
        self.colorBoxBG.setToolTip('Background color')
        self.colorBoxBG.setObjectName('bgColor')

        profiles = ['Profile 1', 'Profile 2', 'Profile 3']
        self.profileBox = QtWidgets.QComboBox(self)
        self.profileBox.addItems(profiles)

        self.profileAction = self.addWidget(self.profileBox)
        self.fontSeparator1 = self.addSeparator()
        self.fontBoxAction = self.addWidget(self.fontBox)
        self.fontSizeBoxAction = self.addWidget(self.fontSizeBox)
        self.fontSeparator2 = self.addSeparator()
        self.fgColorAction = self.addWidget(self.colorBoxFG)
        self.bgColorAction = self.addWidget(self.colorBoxBG)
        self.fontSeparator3 = self.addSeparator()
        self.addAction(self.lineSpacingUp)
        self.addAction(self.lineSpacingDown)
        self.fontSeparator4 = self.addSeparator()
        self.addAction(self.paddingUp)
        self.addAction(self.paddingDown)

        self.fontBoxAction.setVisible(False)
        self.fontSizeBoxAction.setVisible(False)
        self.fgColorAction.setVisible(False)
        self.bgColorAction.setVisible(False)
        self.lineSpacingUp.setVisible(False)
        self.lineSpacingDown.setVisible(False)
        self.paddingUp.setVisible(False)
        self.paddingDown.setVisible(False)
        self.profileAction.setVisible(False)
        self.fontSeparator1.setVisible(False)
        self.fontSeparator2.setVisible(False)
        self.fontSeparator3.setVisible(False)
        self.fontSeparator4.setVisible(False)

        self.searchBar = FixedLineEdit(self)
        self.searchBar.setPlaceholderText(
            'Search...')
        self.searchBar.setSizePolicy(sizePolicy)
        self.searchBar.setContentsMargins(10, 0, 0, 0)
        self.searchBar.setObjectName('searchBar')

        # Sorter
        self.tocBox = FixedComboBox(self)
        self.tocBox.setObjectName('sortingBox')
        self.tocBox.setToolTip('Table of Contents')

        # All of these will be put after the spacer
        # This means that the buttons in the left side of
        # the toolbar have to split up and added here
        self.boxSpacer = self.addWidget(spacer)

        self.tocBoxAction = self.addWidget(self.tocBox)
        self.searchBarAction = self.addWidget(self.searchBar)
        self.addAction(self.resetProfile)
        self.resetProfile.setVisible(False)

    def toggle_font_settings(self):
        if self.fontButton.isChecked():
            self.font_settings_on()
        else:
            self.font_settings_off()

    def font_settings_on(self):
        self.fullscreenButton.setVisible(False)
        self.settingsButton.setVisible(False)

        self.fontBoxAction.setVisible(True)
        self.fontSizeBoxAction.setVisible(True)
        self.fgColorAction.setVisible(True)
        self.bgColorAction.setVisible(True)
        self.lineSpacingUp.setVisible(True)
        self.lineSpacingDown.setVisible(True)
        self.paddingUp.setVisible(True)
        self.paddingDown.setVisible(True)
        self.profileAction.setVisible(True)
        self.fontSeparator1.setVisible(True)
        self.fontSeparator2.setVisible(True)
        self.fontSeparator3.setVisible(True)
        self.fontSeparator3.setVisible(True)
        self.fontSeparator4.setVisible(False)

        self.tocBoxAction.setVisible(False)
        self.searchBarAction.setVisible(False)
        self.resetProfile.setVisible(True)

    def font_settings_off(self):
        self.fullscreenButton.setVisible(True)
        self.settingsButton.setVisible(True)

        self.fontBoxAction.setVisible(False)
        self.fontSizeBoxAction.setVisible(False)
        self.fgColorAction.setVisible(False)
        self.bgColorAction.setVisible(False)
        self.lineSpacingUp.setVisible(False)
        self.lineSpacingDown.setVisible(False)
        self.paddingUp.setVisible(False)
        self.paddingDown.setVisible(False)
        self.profileAction.setVisible(False)
        self.fontSeparator1.setVisible(False)
        self.fontSeparator2.setVisible(False)
        self.fontSeparator3.setVisible(False)
        self.fontSeparator4.setVisible(False)

        self.tocBoxAction.setVisible(True)
        self.searchBarAction.setVisible(True)
        self.resetProfile.setVisible(False)


class LibraryToolBar(QtWidgets.QToolBar):
    def __init__(self, parent=None):
        super(LibraryToolBar, self).__init__(parent)

        spacer = QtWidgets.QWidget()
        spacer.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self.setMovable(False)
        self.setIconSize(QtCore.QSize(22, 22))
        self.setFloatable(False)
        self.setObjectName("LibraryToolBar")

        # Buttons
        self.addButton = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('add'), 'Add book', self)
        self.deleteButton = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('remove'), 'Delete book', self)
        self.settingsButton = QtWidgets.QAction(
            QtGui.QIcon.fromTheme('settings'), 'Settings', self)

        # Add buttons
        self.addAction(self.addButton)
        self.addAction(self.deleteButton)
        self.addSeparator()
        self.addAction(self.settingsButton)
        self.settingsButton.setCheckable(True)

        # Filter
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        # self.searchBar = QtWidgets.QLineEdit()
        self.searchBar = FixedLineEdit(self)
        self.searchBar.setPlaceholderText(
            'Search for Title, Author, Tags...')
        self.searchBar.setSizePolicy(sizePolicy)
        self.searchBar.setContentsMargins(10, 0, 0, 0)
        self.searchBar.setObjectName('searchBar')

        # Sorter
        sorting_choices = ['Title', 'Author', 'Year']
        self.sortingBox = FixedComboBox(self)
        self.sortingBox.addItems(sorting_choices)
        self.sortingBox.setObjectName('sortingBox')
        self.sortingBox.setSizePolicy(sizePolicy)
        self.sortingBox.setMinimumContentsLength(10)
        self.sortingBox.setToolTip('Sort by')

        # Add widgets
        self.addWidget(spacer)
        self.addWidget(self.sortingBox)
        self.addWidget(self.searchBar)


# Sublassing these widgets out prevents them from resizing
class FixedComboBox(QtWidgets.QComboBox):
    def __init__(self, parent=None):
        super(FixedComboBox, self).__init__(parent)

    def sizeHint(self):
        return QtCore.QSize(400, 22)


class FixedLineEdit(QtWidgets.QLineEdit):
    def __init__(self, parent=None):
        super(FixedLineEdit, self).__init__(parent)

    def sizeHint(self):
        return QtCore.QSize(400, 22)


class FixedPushButton(QtWidgets.QPushButton):
    def __init__(self, parent=None):
        super(FixedPushButton, self).__init__(parent)

    def sizeHint(self):
        return QtCore.QSize(36, 30)


class Tab(QtWidgets.QWidget):
    def __init__(self, metadata, parent=None):
        # TODO
        # A horizontal slider to control flow
        # Take hint from a position function argument to open the book
        # at a specific page

        super(Tab, self).__init__(parent)
        self.parent = parent
        self.metadata = metadata  # Save progress data into this dictionary

        self.gridLayout = QtWidgets.QGridLayout(self)
        self.gridLayout.setObjectName("gridLayout")

        position = self.metadata['position']

        # TODO
        # Chapter position and vertical scrollbar position
        if position:
            current_chapter = position['current_chapter']
        else:
            self.generate_position()
            current_chapter = 1

        chapter_name = list(self.metadata['content'])[current_chapter - 1]
        chapter_content = self.metadata['content'][chapter_name]

        # The content display widget is, by default a QTextBrowser
        # In case the incoming data is only images
        # such as in the case of comic book files,
        # we want a QGraphicsView widget doing all the heavy lifting
        # instead of a QTextBrowser
        self.are_we_doing_images_only = self.metadata['images_only']

        if self.are_we_doing_images_only:  # Boolean
            self.contentView = PliantQGraphicsView(self.window())
            self.contentView.loadImage(chapter_content)
            self.setStyleSheet("background-color: black;")
        else:
            self.contentView = PliantQTextBrowser(self.window())

            relative_path_root = os.path.join(
                self.window().temp_dir.path(), self.metadata['hash'])
            relative_paths = []
            for i in os.walk(relative_path_root):
                relative_paths.append(os.path.join(relative_path_root, i[0]))
            self.contentView.setSearchPaths(relative_paths)

            self.contentView.setOpenLinks(False)  # Change this when HTML navigation works
            self.contentView.setHtml(chapter_content)

        # The following are common to both the text browser and
        # the graphics view
        self.contentView.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.contentView.setObjectName("contentView")
        self.contentView.verticalScrollBar().setSingleStep(7)
        self.contentView.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOff)

        self.generate_keyboard_shortcuts()

        self.gridLayout.addWidget(self.contentView, 0, 0, 1, 1)
        title = self.metadata['title']
        self.parent.addTab(self, title)

        self.contentView.setFocus()

    def generate_position(self):
        total_chapters = len(self.metadata['content'].keys())
        # TODO
        # Calculate lines
        self.metadata['position'] = {
            'current_chapter': 1,
            'current_line': 0,
            'total_chapters': total_chapters,
            'read_lines': 0,
            'total_lines': 0}

    def generate_keyboard_shortcuts(self):
        self.next_chapter = QtWidgets.QShortcut(
            QtGui.QKeySequence('Right'), self.contentView)
        self.next_chapter.setObjectName('nextChapter')
        self.next_chapter.activated.connect(self.sneaky_change)

        self.prev_chapter = QtWidgets.QShortcut(
            QtGui.QKeySequence('Left'), self.contentView)
        self.prev_chapter.setObjectName('prevChapter')
        self.prev_chapter.activated.connect(self.sneaky_change)

        self.go_fs = QtWidgets.QShortcut(
            QtGui.QKeySequence('F11'), self.contentView)
        self.go_fs.activated.connect(self.window().set_fullscreen)

        self.exit_fs = QtWidgets.QShortcut(
            QtGui.QKeySequence('Escape'), self.contentView)
        self.exit_fs.setContext(QtCore.Qt.ApplicationShortcut)
        self.exit_fs.activated.connect(self.exit_fullscreen)

        # self.exit_all = QtWidgets.QShortcut(
        #     QtGui.QKeySequence('Ctrl+Q'), self.contentView)
        # self.exit_all.activated.connect(self.sneaky_exit)

    def exit_fullscreen(self):
        self.window().show()
        self.contentView.setWindowFlags(QtCore.Qt.Widget)
        self.contentView.setWindowState(QtCore.Qt.WindowNoState)
        self.contentView.show()

    def change_chapter_tocBox(self):
        chapter_name = self.window().bookToolBar.tocBox.currentText()
        required_content = self.metadata['content'][chapter_name]

        if self.are_we_doing_images_only:
            self.contentView.loadImage(required_content)
        else:
            self.contentView.clear()
            self.contentView.setHtml(required_content)

    def format_view(self, font, font_size, foreground, background, padding):
        self.contentView.setViewportMargins(padding, 0, padding, 0)

        if self.are_we_doing_images_only:
            self.contentView.setBackgroundBrush(
                QtGui.QBrush(QtCore.Qt.black, QtCore.Qt.SolidPattern))
        else:
            self.contentView.setStyleSheet(
                "QTextEdit {{font-family: {0}; font-size: {1}px; color: {2}; background-color: {3}}}".format(
                    font, font_size, foreground, background))

    def sneaky_change(self):
        direction = -1
        if self.sender().objectName() == 'nextChapter':
            direction = 1

        self.contentView.common_functions.change_chapter(
            direction, True)

    def sneaky_exit(self):
        self.contentView.hide()
        self.window().closeEvent()


class PliantQGraphicsView(QtWidgets.QGraphicsView):
    def __init__(self, main_window, parent=None):
        super(PliantQGraphicsView, self).__init__(parent)
        self.main_window = main_window
        self.image_pixmap = None
        self.ignore_wheel_event = False
        self.ignore_wheel_event_number = 0
        self.common_functions = PliantWidgetsCommonFunctions(
            self, self.main_window)

    def loadImage(self, image_path):
        self.image_pixmap = QtGui.QPixmap()
        self.image_pixmap.load(image_path)
        self.resizeEvent()

    def resizeEvent(self, event=None):
        if not self.image_pixmap:
            return

        profile_index = self.main_window.bookToolBar.profileBox.currentIndex()
        current_profile = self.main_window.bookToolBar.profileBox.itemData(
            profile_index, QtCore.Qt.UserRole)
        padding = current_profile['padding']

        available_width = self.viewport().width() - 2 * padding

        if self.image_pixmap.width() > available_width:
            image_pixmap = self.image_pixmap.scaledToWidth(
                available_width, QtCore.Qt.SmoothTransformation)
        else:
            image_pixmap = self.image_pixmap

        graphics_scene = QtWidgets.QGraphicsScene()
        graphics_scene.addPixmap(image_pixmap)

        self.setScene(graphics_scene)
        self.show()

    def wheelEvent(self, event):
        self.common_functions.wheelEvent(event, True)

    def keyPressEvent(self, event):
        # This function is sufficiently different to warrant
        # exclusion from the common functions class
        if event.key() == 32:  # Spacebar press
            vertical = self.verticalScrollBar().value()
            maximum = self.verticalScrollBar().maximum()

            if vertical == maximum:
                self.common_functions.change_chapter(1, True)

            else:
                # Increment by following value
                scroll_increment = int((maximum - 0) / 2)
                self.verticalScrollBar().setValue(vertical + scroll_increment)


class PliantQTextBrowser(QtWidgets.QTextBrowser):
    def __init__(self, main_window, parent=None):
        super(PliantQTextBrowser, self).__init__(parent)
        self.main_window = main_window
        self.ignore_wheel_event = False
        self.ignore_wheel_event_number = 0
        self.common_functions = PliantWidgetsCommonFunctions(
            self, self.main_window)

    def wheelEvent(self, event):
        self.common_functions.wheelEvent(event, False)

    def keyPressEvent(self, event):
        if event.key() == 32:
            vertical = self.verticalScrollBar().value()
            maximum = self.verticalScrollBar().maximum()

            if vertical == maximum:
                self.common_functions.change_chapter(1, True)
            else:
                QtWidgets.QTextBrowser.keyPressEvent(self, event)

        else:
            QtWidgets.QTextBrowser.keyPressEvent(self, event)


class PliantWidgetsCommonFunctions():
    def __init__(self, parent_widget, main_window):
        self.pw = parent_widget
        self.main_window = main_window

    def wheelEvent(self, event, are_we_doing_images_only):
        if self.pw.ignore_wheel_event:
            # Ignore first n wheel events after a chapter change
            self.pw.ignore_wheel_event_number += 1
            if self.pw.ignore_wheel_event_number > 20:
                self.pw.ignore_wheel_event = False
                self.pw.ignore_wheel_event_number = 0
            return

        if are_we_doing_images_only:
            QtWidgets.QGraphicsView.wheelEvent(self.pw, event)
        else:
            QtWidgets.QTextBrowser.wheelEvent(self.pw, event)

        # Since this is a delta on a mouse move event, it cannot ever be 0
        vertical_pdelta = event.pixelDelta().y()
        if vertical_pdelta > 0:
            moving_up = True
        elif vertical_pdelta < 0:
            moving_up = False

        if abs(vertical_pdelta) > 100:  # Adjust sensitivity here
            # Implies that no scrollbar movement is possible
            if self.pw.verticalScrollBar().value() == self.pw.verticalScrollBar().maximum() == 0:
                if moving_up:
                    self.change_chapter(-1)
                else:
                    self.change_chapter(1)

            # Implies that the scrollbar is at the bottom
            elif self.pw.verticalScrollBar().value() == self.pw.verticalScrollBar().maximum():
                if not moving_up:
                    self.change_chapter(1)

            # Implies scrollbar is at the top
            elif self.pw.verticalScrollBar().value() == 0:
                if moving_up:
                    self.change_chapter(-1)

    def change_chapter(self, direction, was_button_pressed=None):
        current_toc_index = self.main_window.bookToolBar.tocBox.currentIndex()
        max_toc_index = self.main_window.bookToolBar.tocBox.count() - 1

        if (current_toc_index < max_toc_index and direction == 1) or (
                current_toc_index > 0 and direction == -1):
            self.main_window.bookToolBar.tocBox.setCurrentIndex(current_toc_index + direction)

            # Set page position depending on if the chapter number is increasing or decreasing
            if direction == 1 or was_button_pressed:
                self.pw.verticalScrollBar().setValue(0)
            else:
                self.pw.verticalScrollBar().setValue(
                    self.pw.verticalScrollBar().maximum())

            if not was_button_pressed:
                self.pw.ignore_wheel_event = True


class LibraryDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, temp_dir, parent=None):
        super(LibraryDelegate, self).__init__(parent)
        self.temp_dir = temp_dir

    def paint(self, painter, option, index):
        # This is a hint for the future
        # Color icon slightly red
        # if option.state & QtWidgets.QStyle.State_Selected:
            # painter.fillRect(option.rect, QtGui.QColor().fromRgb(255, 0, 0, 20))

        option = option.__class__(option)
        file_exists = index.data(QtCore.Qt.UserRole + 5)
        position = index.data(QtCore.Qt.UserRole + 7)

        # TODO
        # Calculate progress on the basis of lines

        if not file_exists:
            read_icon = QtGui.QIcon(':/images/error.svg').pixmap(36)
            painter.setOpacity(.7)
            QtWidgets.QStyledItemDelegate.paint(self, painter, option, index)
            painter.setOpacity(1)
            x_draw = option.rect.bottomRight().x() - 30
            y_draw = option.rect.bottomRight().y() - 35
            painter.drawPixmap(x_draw, y_draw, read_icon)
            return

        QtWidgets.QStyledItemDelegate.paint(self, painter, option, index)
        if position:
            current_chapter = position['current_chapter']
            total_chapters = position['total_chapters']
            progress_percent = int(current_chapter * 100 / total_chapters)

            if current_chapter == total_chapters:
                QtWidgets.QStyledItemDelegate.paint(self, painter, option, index)
                read_icon = QtGui.QIcon(':/images/checkmark.svg').pixmap(36)
            elif current_chapter == 1:
                QtWidgets.QStyledItemDelegate.paint(self, painter, option, index)
            else:
                # TODO
                # See if saving the svg to disk can be avoided
                QtWidgets.QStyledItemDelegate.paint(self, painter, option, index)
                pie_chart.GeneratePie(progress_percent, self.temp_dir).generate()
                svg_path = os.path.join(self.temp_dir, 'lector_progress.svg')
                read_icon = QtGui.QIcon(svg_path).pixmap(32)

            x_draw = option.rect.bottomRight().x() - 30
            y_draw = option.rect.bottomRight().y() - 35
            if current_chapter != 1:
                painter.drawPixmap(x_draw, y_draw, read_icon)


class MyAbsModel(QtGui.QStandardItemModel, QtCore.QAbstractItemModel):
    def __init__(self, parent=None):
        # We're using this to be able to access the match() method
        super(MyAbsModel, self).__init__(parent)


class BackGroundTabUpdate(QtCore.QThread):
    def __init__(self, database_path, all_metadata, parent=None):
        super(BackGroundTabUpdate, self).__init__(parent)
        self.database_path = database_path
        self.all_metadata = all_metadata

    def run(self):
        hash_position_pairs = []
        for i in self.all_metadata:
            file_hash = i['hash']
            position = i['position']
            hash_position_pairs.append([file_hash, position])

        database.DatabaseFunctions(
            self.database_path).modify_position(hash_position_pairs)


class BackGroundBookAddition(QtCore.QThread):
    def __init__(self, parent_window, file_list, database_path, parent=None):
        super(BackGroundBookAddition, self).__init__(parent)
        self.parent_window = parent_window
        self.file_list = file_list
        self.database_path = database_path

    def run(self):
        books = sorter.BookSorter(self.file_list, 'addition', self.database_path)
        parsed_books = books.initiate_threads()
        database.DatabaseFunctions(self.database_path).add_to_database(parsed_books)
        self.parent_window.lib_ref.generate_model('addition', parsed_books)
