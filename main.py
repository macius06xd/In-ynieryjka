import sys
import os
from PyQt5.QtWidgets import (QApplication, QFileSystemModel, QTreeView, QSplitter, QMainWindow, QScrollArea, QWidget,
                             QVBoxLayout, QListView, QAbstractItemView, QDesktopWidget, QMenuBar, QMenu, QAction,
                             QProgressDialog)
from PyQt5.QtGui import QPixmap, QImageReader, QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt, QDir, QSize, QEvent, pyqtSignal, QThread

from CreateResizedDataset import ImageResizeThreadPool
from FileSystem import FileSystem
from ImageViewer import ImageViewer
from Configuration import RESIZED_IMAGES_SIZE , DEFAULT_IMAGES_PATH , RESIZED_IMAGES_PATH

thumbnail_size = RESIZED_IMAGES_SIZE

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

        # Create menu bar
        menu_bar = QMenuBar(self)
        options_menu = QMenu("&Options", self)
        create_resized_action = QAction("Create resized dataset", self)
        create_resized_action.triggered.connect(self.create_resized_dataset)

        options_menu.addAction(create_resized_action)
        menu_bar.addMenu(options_menu)

        self.setMenuBar(menu_bar)

    def create_resized_dataset(self):
        input_folder = DEFAULT_IMAGES_PATH
        output_folder = RESIZED_IMAGES_PATH
        max_threads = 12
        self.thread = QThread()
        # Instantiate the ImageResizeThreadPool class
        self.resize_threadpool = ImageResizeThreadPool(input_folder, output_folder, max_threads)
        self.resize_threadpool.moveToThread(self.thread)
        self.thread.started.connect(self.resize_threadpool.run)

        # Show progress dialog
        progress_dialog = QProgressDialog("Resizing images...", "Cancel", 0, 100, self)
        progress_dialog.setWindowModality(Qt.WindowModal)
        progress_dialog.setAutoClose(True)
        progress_dialog.setMinimum(0)
        progress_dialog.setMaximum(100)
        progress_dialog.setAutoReset(True)
        progress_dialog.setWindowTitle("Progress")
        progress_dialog.show()
        def workerfinishedhandler():
            self.dir_tree.populate()
            progress_dialog.close()
        self.resize_threadpool.finished.connect(
            workerfinishedhandler
        )
        self.resize_threadpool.progress_update.connect(progress_dialog.setValue)
        self.thread.start()





class ResizeThread(QThread):
    def __init__(self, input_path, output_path,parent):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.parent = parent

    def run(self):
        self.parent.create_resized_dataset(self.input_path, self.output_path)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    image_browser = ImageBrowser()
    image_browser.show()
    sys.exit(app.exec_())
