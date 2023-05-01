import time

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import (QApplication, QFileSystemModel, QTreeView, QSplitter, QMainWindow, QScrollArea, QWidget,
                             QVBoxLayout, QListView, QAbstractItemView, QAbstractItemDelegate, QLabel, QMessageBox,
                             QStyle)
from PyQt5.QtGui import QPixmap, QImageReader, QStandardItemModel, QStandardItem, QPen, QIcon
from PyQt5.QtCore import Qt, QDir, QSize, QEvent, pyqtSignal, QThread, QObject, QRunnable, QThreadPool, QMutex, \
    QModelIndex

thumbnail_size = 64
import sys
import os

class ImageViewer(QListView):
    def __init__(self):
        super().__init__()

        self.image_model = ImageListModel()
        self.setModel(self.image_model)
        self.setViewMode(QListView.IconMode)
        self.setResizeMode(QListView.Adjust)
        self.setGridSize(QSize(thumbnail_size + 16, thumbnail_size + 16))
        self.setSpacing(10)
        self.setWordWrap(True)
        self.setUniformItemSizes(True)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setItemDelegate(ImageDelegate())
        self.itemDelegate().imageClicked.connect(self.onImageClicked)
        self.image_viewer_window = None

    def onImageClicked(self, imagePath):
        print("Image clicked:", imagePath)

        # create a label widget to display the image
        image_label = QLabel()
        # Example filename
        filename = imagePath

        # Split the filename by '/'
        fragments = filename.split('/')

        # Get the last fragment
        last_fragment = fragments[-1]

        # Remove the '_small' suffix from the last fragment
        last_fragment = last_fragment.replace('_small', '')

        # Remove the 'small' string from the next fragment
        next_fragment = fragments[-2]
        next_fragment = next_fragment.replace('small', '')

        # Replace the last fragment and next fragment in the list
        fragments[-1] = last_fragment
        fragments[-2] = next_fragment

        # Join the fragments back into a path string
        new_filename = '/'.join(fragments)
        pixmap = QPixmap(new_filename)
        image_label.setPixmap(pixmap)

        # create a message box and set its layout
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Image Viewer")
        msg_box.setText("")

        layout = msg_box.layout()
        layout.addWidget(image_label, 0, 0, Qt.AlignHCenter | Qt.AlignVCenter)

        msg_box.exec_()
    def load_images_from_folder(self,path):
        self.image_model.load_images_from_folder(path)
class ImageDelegate(QAbstractItemDelegate):
    imageClicked = pyqtSignal(str)
    def paint(self, painter, option, index):
        if not index.isValid():
            return
        pixmap = index.data()
        painter.drawPixmap(option.rect.x(), option.rect.y(), pixmap)

    def sizeHint(self, option, index):
        return QSize(thumbnail_size + 16, thumbnail_size + 16)

    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
            self.imageClicked.emit(index.data(Qt.UserRole))
            return True
        return False


class PixmapItem(QStandardItem):
    def __init__(self, pixmap,path):
        super().__init__()
        self.pixmap = pixmap
        self.path = path

    def data(self, role):
        if role == Qt.UserRole:
            return self.get_path()
        return self.pixmap
    def get_path(self):
        return self.path


class LoadImagesWorker(QRunnable):
    imageLoaded = pyqtSignal(QPixmap,str)
    def __init__(self, folder, file_chunk,list,mutex,i):
        super().__init__()
        self.folder = folder
        self.file_chunk = file_chunk
        self.results = list
        self.mutex = mutex
        self.i = i
    def run(self):
        image_extensions = QImageReader.supportedImageFormats()

        for file in self.file_chunk:
            if file.split('.')[-1].encode() in image_extensions:
                path = os.path.join(self.folder, file)
                pixmap = QPixmap(path)
                self.mutex.lock()

                self.mutex.unlock()
                self.results.append((pixmap, path))


class LoadImages(QThread):
    def __init__(self, folder, parent,results):
        super().__init__()
        self.folder = folder
        self.parent = parent
        self.results = results
        self.threadpool = QThreadPool.globalInstance()
        self.mutex = QMutex()
    def run(self):

        num_threads = QThreadPool.globalInstance().maxThreadCount()
        all_files = []
        for dirpath, _, filenames in os.walk(self.folder):
            for filename in filenames:
                all_files.append(os.path.join(dirpath, filename))
        chunk_size = (len(all_files) + num_threads - 1) // num_threads  # divide files into equal chunks
        chunks = [all_files[i:i + chunk_size] for i in range(0, len(all_files), chunk_size)]
        self.results = [None] * len(all_files)
        for chunk in chunks:
            worker = LoadImagesWorker(self.folder, chunk, self.results,self.mutex)
            self.threadpool.start(worker)

        self.threadpool.waitForDone()
class ImageListModel(QStandardItemModel):
    def __init__(self):
        super().__init__()
        self.loader = None
        self.mutex = QMutex()
        self.results = []

    def load_images_from_folder(self, folder):
            self.clear()
            image_extensions = QImageReader.supportedImageFormats()
            for root, _, files in os.walk(folder):
                for file in files:
                    if file.split('.')[-1].encode() in image_extensions:
                        path = os.path.join(root, file)
                        item = PixmapItem(QPixmap(path),path)
                        self.results.append(item)
                        self.appendRow(item)
                break
    def on_all_images_loaded(self, results):

        self.end = time.time()
        print(self.end-self.start)
        self.start=time.time()
        self.results = results
        self.current_index = 0
        self.batch_size = 200
        self.process_batch()
    def process_batch(self):
        for i in range(self.current_index, min(self.current_index + self.batch_size, len(self.results))):
            pixmap, filename = self.results[i]
            self.appendRow(PixmapItem(pixmap,filename))
        self.current_index += self.batch_size
        if self.current_index < len(self.results):
            QtCore.QTimer.singleShot(0, self.process_batch)  # process next batch in event loop
        else:
            self.end = time.time()
            print(self.end - self.start)