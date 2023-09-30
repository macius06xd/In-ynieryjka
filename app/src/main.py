import sys
import faulthandler
from PyQt5.QtCore import Qt, QThread
from PyQt5.QtWidgets import (QApplication, QSplitter, QMainWindow, QWidget,
                             QVBoxLayout, QMenuBar, QMenu, QAction, QToolBar,
                             QProgressDialog, QSlider, QLabel, QInputDialog, QHBoxLayout, QMessageBox)
import os
import app.test.TestConfiguration
import app.cfg.Configuration
from app.cfg.Configuration import RESIZED_IMAGES_SIZE, INITIAL_CLUSTERIZED_FOLDER, RESIZED_IMAGES_PATH, \
    INITIAL_IMAGES_FOLDER, VECTORS_PATH
from app.src.clusterization.ClusterManager import ClusterManager
from app.src.tools.CreateResizedDataset import ImageResizeThreadPool
from app.src.tools.CreateResultFolder import create_result_folders
from app.src.file_system.FileSystem import FileSystem
from app.src.gui.ImageViewer import ImageViewer
from app.src.clusterization.InitialClusterization import ClusteringThread
from app.src.tools.MovePhotosToResults import FileManager
from app.src.gui.CommitedLayout import CommitedFilesWidget
from app.src.clusterization.kmeans.KMeansParamsWidget import KMeansParamsWidget
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtGui import QPalette, QColor

thumbnail_size = RESIZED_IMAGES_SIZE


class ImageBrowser(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set GUI style here
        QApplication.setStyle("Fusion")
        palette = QPalette()
        palette.setColor(QPalette.Base, QColor(190, 190, 190))
        QApplication.setPalette(palette)

        self.thread = None
        self.initUI()

    def initUI(self):

        # Run initial configuration
        self.display_options_window()
        print("running for first time?", app.cfg.Configuration.is_it_run_first_time)

        self.setWindowTitle('Image Browser')

        main_widget = QWidget()
        window_layout = QVBoxLayout()
        main_layout = QHBoxLayout()

        self.ClusterManager = ClusterManager()
        self.splitter = QSplitter()
        self.image_list = ImageViewer( self.ClusterManager)
        self.dir_tree = FileSystem(self.image_list, self.ClusterManager)
        self.CommitedFilesWidget = CommitedFilesWidget( self.ClusterManager)
        self.image_list.setCommitedLayout(self.CommitedFilesWidget)
        self.splitter.addWidget(self.dir_tree)
        self.splitter.addWidget(self.image_list)
        self.splitter.addWidget(self.CommitedFilesWidget)
        splittersize = self.splitter.size().width()
        self.splitter.setSizes([int(element * splittersize) for element in [0.05, 0.9, 0.05]])
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(1)
        self.slider.setMaximum(30)
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
        self.image_list.image_deleted.connect(self.dir_tree.on_deleted)

        ##################### TOOL BAR - START #######################
        # Set tool bar
        self.tool_bar = QToolBar(self)

        # Add the "Close" button
        close_button = QPushButton("Close", self)
        close_button.clicked.connect(self.close)
        self.tool_bar.addWidget(close_button)

        # Add new action to apply changes and create result folder
        apply_changes_and_create_result_folder_action = QAction("Apply changes and create result folder", self)
        apply_changes_and_create_result_folder_action.triggered.connect(create_result_folders)
        apply_changes_and_create_result_folder_action.triggered.connect(FileManager.copy_files)

        # Add the "Apply changes and create result" button
        create_results_button = QPushButton("Apply changes and create result folders", self)
        create_results_button.clicked.connect(apply_changes_and_create_result_folder_action.trigger)
        create_results_button.move(50, 0)
        self.tool_bar.addWidget(create_results_button)

        self.addToolBar(Qt.TopToolBarArea, self.tool_bar)
        self.tool_bar.setLayoutDirection(Qt.RightToLeft)
        ##################### TOOL BAR - END #######################

        self.dir_tree.commit()
        self.showFullScreen()

        if app.cfg.Configuration.is_it_run_first_time == 1:
            self.prompt_for_cluster_count()

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

        while self.thread.isRunning():
            QApplication.processEvents()

        # Po zakonczeniu initial clusterization stworz resized dataset
        self.create_resized_dataset()

    def display_options_window(self):
        app.cfg.Configuration.is_it_run_first_time  # Deklaracja zmiennej globalnej is_it_run_first_time

        options = QMessageBox()
        options.setWindowTitle("Options")
        options.setText("Choose an option:")

        button_prepare_datasets = options.addButton("Prepare datasets", QMessageBox.ActionRole)
        button_skip = options.addButton("Skip", QMessageBox.RejectRole)  # Dodano przycisk "Skip"

        options.setDefaultButton(button_skip)

        # prompt_for_cluster_count po pobraniu n uruchamia perform_initial_clusterization
        # po zakonczeniu perform_initial_clusterization uruchamia sie create_resized_dataset
        # button_prepare_datasets.clicked.connect(self.prompt_for_cluster_count)
        button_prepare_datasets.clicked.connect(
            self.set_is_it_run_first_time_one)  # Ustawia is_it_run_first_time na 1 po naciśnięciu przycisku "Prepare datasets"
        button_prepare_datasets.clicked.connect(self.open_kmeans_params_dialog)
        button_skip.clicked.connect(
            self.set_is_it_run_first_time_zero)  # Ustawia is_it_run_first_time na 0 po naciśnięciu przycisku "Skip"

        options.exec_()

    def set_is_it_run_first_time_one(self):
        app.cfg.Configuration.is_it_run_first_time = 1

    def set_is_it_run_first_time_zero(self):
        app.cfg.Configuration.is_it_run_first_time = 0


class ResizeThread(QThread):
    def __init__(self, input_path, output_path, parent):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.parent = parent

    def run(self):
        self.parent.create_resized_dataset(self.input_path, self.output_path)


if __name__ == '__main__':
    # Test whether paths exists
    app.test.TestConfiguration.check_paths_exist()

    faulthandler.enable()
    application = QApplication(sys.argv)
    image_browser = ImageBrowser()
    image_browser.show()

    # Run the GUI loop
    application.exec_()
