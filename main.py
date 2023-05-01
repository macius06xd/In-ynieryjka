import sys
import os
from PyQt5.QtWidgets import (QApplication, QFileSystemModel, QTreeView, QSplitter, QMainWindow, QScrollArea, QWidget,
                             QVBoxLayout, QListView, QAbstractItemView, QDesktopWidget)
from PyQt5.QtGui import QPixmap, QImageReader, QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt, QDir, QSize, QEvent, pyqtSignal, QThread

from FileSystem import FileSystem
from ImageViewer import ImageViewer

thumbnail_size = 64

from PyQt5.QtWidgets import QAbstractItemDelegate

class CustomFileSystemModel(QFileSystemModel):
    def __init__(self, root_path):
        super().__init__()
        self.setRootPath(root_path)

class ImageBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Image Browser')
        screen = QDesktopWidget().screenGeometry()
        width, height = screen.width(), screen.height()

        # resize window to match screen size
        self.resize(width, height)
        main_widget = QWidget()
        main_layout = QVBoxLayout()

        self.splitter = QSplitter(Qt.Vertical)
        self.image_list = ImageViewer()
        self.dir_tree = FileSystem(self.image_list)
        self.splitter.addWidget(self.dir_tree)


        self.splitter.addWidget(self.image_list)

        main_layout.addWidget(self.splitter)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)




if __name__ == '__main__':
    app = QApplication(sys.argv)
    image_browser = ImageBrowser()
    image_browser.show()
    sys.exit(app.exec_())
