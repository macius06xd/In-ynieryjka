import sys

from PyQt5.QtCore import Qt, QThread
from PyQt5.QtWidgets import (QApplication, QSpacerItem, QSizePolicy, QFileSystemModel, QSplitter, QMainWindow, QWidget,
                             QVBoxLayout, QDesktopWidget, QMenuBar, QMenu, QAction,
                             QProgressDialog, QSlider, QLabel, QInputDialog, QHBoxLayout, QMessageBox)
import os
from Configuration import *
from CreateResizedDataset import ImageResizeThreadPool
from CreateResultFolder import create_result_folders
from FileSystem import FileSystem
from ImageViewer import ImageViewer
from InitialClusterization import ClusteringThread
from MovePhotosToResults import FileManager
from CommitedLayout import CommitedFilesWidget
from KMeansParamsWidget import KMeansParamsWidget

thumbnail_size = RESIZED_IMAGES_SIZE

import subprocess
import Configuration


class ImageBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.thread = None
        self.initUI()

    def initUI(self):
        # # Run initial configuration
        self.display_options_window()
        print("running for first time?", Configuration.is_it_run_first_time)

        self.setWindowTitle('Image Browser')

        main_widget = QWidget()
        window_layout = QVBoxLayout()
        main_layout = QHBoxLayout()

        self.splitter = QSplitter()
        self.image_list = ImageViewer()
        self.dir_tree = FileSystem(self.image_list)
        self.CommitedFilesWidget = CommitedFilesWidget()
        self.image_list.setCommitedLayout(self.CommitedFilesWidget)
        self.splitter.addWidget(self.dir_tree)
        self.splitter.addWidget(self.image_list)
        self.splitter.addWidget(self.CommitedFilesWidget)
        splittersize = self.splitter.size().width()
        self.splitter.setSizes([int(element * splittersize) for element in [0.05, 0.9, 0.05]])
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
        self.dir_tree.Node_Commited.connect(self.CommitedFilesWidget.add_commit)
        self.image_list.file_system_changed.connect(self.dir_tree.refresh)
        self.slider.sliderReleased.connect(lambda: self.sliderValueChanged(self.slider.value()))
        self.slider.sliderReleased.connect(lambda: self.image_list.slider_changed(self.slider.value()))

        # Create menu bar
        menu_bar = QMenuBar(self)
        options_menu = QMenu("&Options", self)

        # Add new action to apply changes and create result folder
        apply_changes_and_create_result_folder_action = QAction("Apply changes and create result folder", self)
        apply_changes_and_create_result_folder_action.triggered.connect(create_result_folders)
        apply_changes_and_create_result_folder_action.triggered.connect(FileManager.copy_files)

        self.image_list.node_changed_signal.connect(self.dir_tree.on_cluster)
        self.image_list.image_deleted.connect(self.dir_tree.on_deleted)
        options_menu.addAction(apply_changes_and_create_result_folder_action)

        # Add action to open K-means parameters dialog
        open_kmeans_params_action = QAction("K-means Parameters", self)
        open_kmeans_params_action.triggered.connect(self.open_kmeans_params_dialog)
        options_menu.addAction(open_kmeans_params_action)
        menu_bar.addMenu(options_menu)
        self.setMenuBar(menu_bar)
        self.dir_tree.commit()
        self.showFullScreen()

        if Configuration.is_it_run_first_time == 1:
            self.prompt_for_cluster_count()
            #print("running n prompt")

    def open_kmeans_params_dialog(self):
        # Create and open the KMeansParamsWidget dialog
        kmeans_params_dialog = KMeansParamsWidget()
        kmeans_params_dialog.exec_()

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
        progress_dialog.setWindowTitle("Resizing images progress")
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
        cluster_count, ok_pressed = QInputDialog.getInt(self, "Set number of clusters", "Number of Clusters:", 4, 0,
                                                        1000, 1)
        if ok_pressed:
            self.perform_initial_clusterization(cluster_count)

    def perform_initial_clusterization(self, no_of_clusters):
        progress_dialog = QProgressDialog("Clustering and moving images", "Cancel", 0, 100, self)
        progress_dialog.setWindowModality(Qt.WindowModal)
        progress_dialog.setAutoClose(True)
        progress_dialog.setMinimum(0)
        progress_dialog.setMaximum(100)
        progress_dialog.setAutoReset(True)
        progress_dialog.setWindowTitle("Clustering progress")
        progress_dialog.show()

        self.thread = ClusteringThread(INITIAL_IMAGES_FOLDER, VECTORS_PATH, INITIAL_CLUSTERIZED_FOLDER, no_of_clusters)
        self.thread.progress_updated.connect(progress_dialog.setValue)
        self.thread.finished.connect(progress_dialog.close)
        self.thread.start()

        # Poczekaj na zakonczenie wątku
        # self.thread.wait()

        while self.thread.isRunning():
            QApplication.processEvents()

        # Po zakonczeniu initial clusterization stworz resized dataset
        self.create_resized_dataset()

    def display_options_window(self):
        Configuration.is_it_run_first_time  # Deklaracja zmiennej globalnej is_it_run_first_time

        options = QMessageBox()
        options.setWindowTitle("Options")
        options.setText("Choose an option:")

        button_prepare_datasets = options.addButton("Prepare datasets", QMessageBox.ActionRole)
        button_skip = options.addButton("Skip", QMessageBox.RejectRole)  # Dodano przycisk "Skip"
        
        options.setDefaultButton(button_skip)

        # prompt_for_cluster_count po pobraniu n uruchamia perform_initial_clusterization
        # po zakonczeniu perform_initial_clusterization uruchamia sie create_resized_dataset
        #button_prepare_datasets.clicked.connect(self.prompt_for_cluster_count)
        button_prepare_datasets.clicked.connect(self.set_is_it_run_first_time_one)  # Ustawia is_it_run_first_time na 1 po naciśnięciu przycisku "Prepare datasets"
        button_skip.clicked.connect(self.set_is_it_run_first_time_zero)  # Ustawia is_it_run_first_time na 0 po naciśnięciu przycisku "Skip"

        options.exec_()


    def set_is_it_run_first_time_one(self):
        Configuration.is_it_run_first_time = 1

    def set_is_it_run_first_time_zero(self):
        Configuration.is_it_run_first_time = 0


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

    # Run the GUI loop
    app.exec_()