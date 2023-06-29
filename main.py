import sys

from PyQt5.QtCore import Qt, QThread
from PyQt5.QtWidgets import (QApplication, QSpacerItem, QSizePolicy, QFileSystemModel, QSplitter, QMainWindow, QWidget,
                             QVBoxLayout, QDesktopWidget, QMenuBar, QMenu, QAction,
                             QProgressDialog, QSlider, QLabel, QInputDialog, QHBoxLayout)

from Configuration import *
from CreateResizedDataset import ImageResizeThreadPool
from CreateResultFolder import create_result_folders
from FileSystem import FileSystem
from ImageViewer import ImageViewer
from InitialClusterization import ClusteringThread
from MovePhotosToResults import FileManager
from CommitedLayout import CommitedFilesWidget

thumbnail_size = RESIZED_IMAGES_SIZE


class ImageBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.thread = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Image Browser')

        main_widget = QWidget()
        window_layout = QVBoxLayout()
        main_layout = QHBoxLayout()

        self.splitter = QSplitter()
        self.image_list = ImageViewer()
        self.dir_tree = FileSystem(self.image_list)
        self.CommitedFilesWidget = CommitedFilesWidget()

        self.splitter.addWidget(self.dir_tree)
        self.splitter.addWidget(self.image_list)
        self.splitter.addWidget(self.CommitedFilesWidget)
        self.splitter.setSizes([5, 90, 5])
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(10)
        self.sliderlabel = QLabel()

        main_layout.addWidget(self.splitter)

        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(self.slider)
        bottom_layout.addWidget(self.sliderlabel)
        window_layout.addLayout(main_layout, stretch=95)
        window_layout.addStretch(1)
        window_layout.addLayout(bottom_layout)

        main_widget.setLayout(window_layout)
        self.setCentralWidget(main_widget)

        self.slider.sliderReleased.connect(lambda: self.sliderValueChanged(self.slider.value()))
        self.slider.sliderReleased.connect(lambda: self.image_list.slider_changed(self.slider.value()))
        # Create menu bar
        menu_bar = QMenuBar(self)
        options_menu = QMenu("&Options", self)

        create_resized_action = QAction("Create resized dataset", self)
        create_resized_action.triggered.connect(self.create_resized_dataset)

        # Add new action for perform initial clusterization
        initial_clusterization_action = QAction("Perform initial clusterization", self)
        initial_clusterization_action.triggered.connect(self.prompt_for_cluster_count)

        # Add new action to apply changes and create result folder
        apply_changes_and_create_result_folder_action = QAction("Apply changes and create result folder", self)
        apply_changes_and_create_result_folder_action.triggered.connect(create_result_folders)
        apply_changes_and_create_result_folder_action.triggered.connect(FileManager.copy_files)

        self.image_list.node_changed_signal.connect(self.dir_tree.on_cluster)
        self.image_list.image_deleted.connect(self.dir_tree.on_deleted)
        options_menu.addAction(create_resized_action)
        options_menu.addAction(initial_clusterization_action)
        options_menu.addAction(apply_changes_and_create_result_folder_action)

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
        cluster_count, ok_pressed = QInputDialog.getInt(self, "Get integer", "Number of Clusters:", 4, 0, 100, 1)
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
    def __init__(self, input_path, output_path, parent):
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
