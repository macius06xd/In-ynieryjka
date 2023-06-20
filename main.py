import sys
import os
from PyQt5.QtWidgets import (QApplication, QFileSystemModel, QTreeView, QSplitter, QMainWindow, QScrollArea, QWidget,
                             QVBoxLayout, QListView, QAbstractItemView, QDesktopWidget, QMenuBar, QMenu, QAction,
                             QProgressDialog, QSlider, QLabel, QInputDialog)
from PyQt5.QtGui import QPixmap, QImageReader, QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt, QDir, QSize, QEvent, pyqtSignal, QThread

from CreateResizedDataset import ImageResizeThreadPool
from FileSystem import FileSystem
from ImageViewer import ImageViewer
from Configuration import *
from InitialClusterization import  ClusteringThread

thumbnail_size = RESIZED_IMAGES_SIZE

from PyQt5.QtWidgets import QAbstractItemDelegate

class CustomFileSystemModel(QFileSystemModel):
    def __init__(self, root_path):
        super().__init__()
        self.setRootPath(root_path)

class ImageBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.thread = None
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
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(10)
        self.sliderlabel = QLabel()
        main_layout.setAlignment(Qt.AlignHCenter)
        self.slider.sliderReleased.connect(lambda : self.sliderValueChanged(self.slider.value()))
        self.slider.sliderReleased.connect(lambda : self.image_list.slider_changed(self.slider.value()))
        main_layout.addWidget(self.splitter)
        main_layout.addWidget(self.sliderlabel)
        main_layout.addWidget(self.slider)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Create menu bar
        menu_bar = QMenuBar(self)
        options_menu = QMenu("&Options", self)

        create_resized_action = QAction("Create resized dataset", self)
        create_resized_action.triggered.connect(self.create_resized_dataset)

        # Add new action for perform initial clusterization
        initial_clusterization_action = QAction("Perform initial clusterization", self)
        initial_clusterization_action.triggered.connect(self.prompt_for_cluster_count)

        self.image_list.node_changed_signal.connect(self.dir_tree.on_cluster)
        self.image_list.image_deleted.connect(self.dir_tree.on_deleted)
        options_menu.addAction(create_resized_action)
        options_menu.addAction(initial_clusterization_action)

        menu_bar.addMenu(options_menu)
        self.setMenuBar(menu_bar)

        self.showFullScreen()

    def sliderValueChanged(self, value):
        self.sliderlabel.setText(f"Clusters: {value}")

    def create_resized_dataset(self):
        input_folder = INITIAL_CLUSTERIZED_FOLDER
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

    def prompt_for_cluster_count(self):
        cluster_count, ok_pressed = QInputDialog.getInt(self, "Get integer","Number of Clusters:", 4, 0, 100, 1)
        if ok_pressed:
            self.perform_initial_clusterization(cluster_count)

    def perform_initial_clusterization(self, no_of_clusters):
        progress_dialog = QProgressDialog("Clustering and moving images", "Cancel", 0, 100, self)
        progress_dialog.setWindowModality(Qt.WindowModal)
        progress_dialog.setAutoClose(True)
        progress_dialog.setMinimum(0)
        progress_dialog.setMaximum(100)
        progress_dialog.setAutoReset(True)
        progress_dialog.setWindowTitle("Progress")
        progress_dialog.show()

        self.thread = ClusteringThread(INITIAL_IMAGES_FOLDER, VECTORS_PATH, INITIAL_CLUSTERIZED_FOLDER, no_of_clusters)
        self.thread.progress_updated.connect(progress_dialog.setValue)
        self.thread.finished.connect(progress_dialog.close)
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
