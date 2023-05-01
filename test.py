import sys
import os
from PyQt5.QtWidgets import (QApplication, QFileSystemModel, QTreeView, QSplitter, QMainWindow, QScrollArea, QWidget, QVBoxLayout, QListView, QAbstractItemView)
from PyQt5.QtGui import QPixmap, QImageReader, QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt, QDir, QSize

from PyQt5.QtWidgets import QAbstractItemDelegate

thumbnail_size = 64

class ImageDelegate(QAbstractItemDelegate):
    def paint(self, painter, option, index):
        if not index.isValid():
            return

        path = index.data()
        pixmap = QPixmap(path)

        painter.drawPixmap(option.rect.x(), option.rect.y(), pixmap)

    def sizeHint(self, option, index):
        pixmap = QPixmap(index.data())
        return QSize(pixmap.width(), pixmap.height())

class CustomFileSystemModel(QFileSystemModel):
    def __init__(self, root_path, parento=None):
        super().__init__()
        self.setRootPath(root_path)

    def index(self, row, column, parent=None, *args, **kwargs):
        if parent is None or not parent.isValid():
            return super().index(row, column, self.createIndex(-1, -1, self.rootPath()))
        return super().index(row, column, parent, *args, **kwargs)

class ImageListModel(QStandardItemModel):
    def __init__(self):
        super().__init__()
        self.thumbnail_cache = {}

    def load_images_from_folder(self, folder):
        self.clear()
        image_extensions = QImageReader.supportedImageFormats()

        for root, _, files in os.walk(folder):
            for file in files:
                if file.split('.')[-1].encode() in image_extensions:
                    path = os.path.join(root, file)
                    item = QStandardItem(path)
                    self.appendRow(item)
            break

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DecorationRole:
            path = index.data()
            if path in self.thumbnail_cache:
                pixmap = self.thumbnail_cache[path]
            else:
                pixmap = QPixmap(path).scaled(thumbnail_size, thumbnail_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.thumbnail_cache[path] = pixmap
            return pixmap

        return super().data(index, role)

class ImageBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Image Browser')

        main_widget = QWidget()
        main_layout = QVBoxLayout()

        self.splitter = QSplitter(Qt.Vertical)

        script_directory = os.path.dirname(os.path.realpath(sys.argv[0]))
        self.dir_model = CustomFileSystemModel(script_directory)
        self.dir_model.setFilter(QDir.NoDot | QDir.AllDirs)
        self.dir_tree = QTreeView()
        self.dir_tree.setModel(self.dir_model)
        self.dir_tree.clicked.connect(self.on_tree_clicked)
        root_index = self.dir_model.setRootPath(script_directory)
        self.dir_tree.setRootIndex(root_index)
        self.splitter.addWidget(self.dir_tree)

        self.image_model = ImageListModel()
        self.image_list = QListView()
        self.image_list.setModel(self.image_model)
        self.image_list.setViewMode(QListView.IconMode)
        self.image_list.setResizeMode(QListView.Adjust)
        self.image_list.setGridSize(QSize(thumbnail_size, thumbnail_size))
        self.image_list.setSpacing(10)
        self.image_list.setWordWrap(True)
        self.image_list.setUniformItemSizes(True)
        self.image_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.image_list.setItemDelegate(ImageDelegate())

        self.splitter.addWidget(self.image_list)

        main_layout.addWidget(self.splitter)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)


    def on_tree_clicked(self, index):
        folder = self.dir_model.filePath(index)
        self.image_model.load_images_from_folder(folder)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    image_browser = ImageBrowser()
    image_browser.show()
    sys.exit(app.exec_())