import os
import cv2
from PyQt5.QtCore import QRunnable, QThreadPool, pyqtSignal, QObject, QThread

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

    def run(self):
        try:
            img = cv2.imread(self.input_path)
            resized_img = cv2.resize(img, (RESIZED_IMAGES_SIZE, RESIZED_IMAGES_SIZE), interpolation=cv2.INTER_AREA)
            cv2.imwrite(self.output_path, resized_img)
        except Exception as e:
            print(f"Error processing file: {self.input_path}")
            print(f"Error message: {e}")
        finally:
            self.signal.mem_signal.emit(1)


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

        self.files_processed = 0

    def run(self):
        for subdir, dirs, files in os.walk(self.input_folder):
            for file in files:
                input_path = os.path.join(subdir, file)
                output_subdir = subdir.replace(self.input_folder, self.output_folder)
                output_path = os.path.join(output_subdir, file.replace(".", "_small."))
                os.makedirs(output_subdir, exist_ok=True)

                worker = ImageResizeWorker(input_path, output_path)
                worker.signal.mem_signal.connect(self.update_progress)
                self.thread_pool.start(worker)

    def update_progress(self, value):
        self.files_processed += value
        progress = int(self.files_processed / self.total_files * 100)
        print(progress)
        self.progress_update.emit(progress)

    def wait_for_completion(self):
        self.thread_pool.waitForDone()

