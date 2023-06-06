import os
import cv2
import numpy as np
from PyQt5.QtCore import QRunnable, QThreadPool, pyqtSignal, QObject, QThread, pyqtSlot  , Qt
from PyQt5.QtWidgets import QApplication

from Configuration import DEFAULT_IMAGES_PATH
from Configuration import RESIZED_IMAGES_PATH
from Configuration import RESIZED_IMAGES_SIZE

class WorkerSignals(QObject):
    mem_signal = pyqtSignal(int)
class ImageResizeWorker(QRunnable):
    progress_update = pyqtSignal(int)  # Signal to update progress bar

    def __init__(self, input_path, output_path):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.signal = WorkerSignals()

    @pyqtSlot()
    def run(self):
        try:

            img = cv2.imread(self.input_path)
            original_height, original_width, _ = img.shape
            aspect_ratio = original_width / original_height

            target_height = RESIZED_IMAGES_SIZE
            target_width = int(target_height * aspect_ratio)

            resized_img = cv2.resize(img, (target_width, target_height), interpolation=cv2.INTER_AREA)

            # Create a new blank canvas with the desired size
            canvas = np.zeros((target_height, target_width, 3), dtype=np.uint8)

            # Calculate the position to place the resized image on the canvas
            left = (target_width - resized_img.shape[1]) // 2

            # Copy the resized image onto the canvas
            canvas[:, left:left + resized_img.shape[1]] = resized_img

            cv2.imwrite(self.output_path, canvas)
        except Exception as e:
            print(f"Error processing file: {self.input_path}")
            print(f"Error message: {e}")
        finally:
            self.signal.mem_signal.emit(1)
            QApplication.processEvents()


class ImageResizeThreadPool (QThread):
    progress_update = pyqtSignal(int)
    def __init__(self, input_folder, output_folder, max_threads=5):
        super().__init__()
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.max_threads = max_threads

        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(self.max_threads)

        self.total_files = 0
        for subdir, dirs, files in os.walk(self.input_folder):
            self.total_files += len(files)
        print("elo")
        self.files_processed = 0

    def run(self):
        for subdir, dirs, files in os.walk(self.input_folder):
            for file in files:
                input_path = os.path.join(subdir, file)
                output_path = os.path.join(self.output_folder, file)
                os.makedirs(self.output_folder, exist_ok=True)
                worker = ImageResizeWorker(input_path, output_path)
                worker.signal.mem_signal.connect(self.update_progress, type=Qt.DirectConnection)
                self.thread_pool.start(worker)
        self.thread_pool.waitForDone()
        self.finished.emit()

    def update_progress(self, value):
        self.files_processed += value
        progress = int(self.files_processed / self.total_files * 100)
        self.progress_update.emit(progress)

    def wait_for_completion(self):
        self.thread_pool.waitForDone()

