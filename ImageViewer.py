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
        pixmap = QPixmap(imagePath)
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
        painter.save()
        if option.state & QStyle.State_Selected:
            # add a border around the pixmap if it's selected
            painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
            painter.drawRect(option.rect.x(), option.rect.y(), option.rect.width()-1, option.rect.height()-1)
        else:
            painter.drawPixmap(option.rect.x(), option.rect.y(), pixmap)
        painter.restore()

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
    def __init__(self, folder, file_chunk,list,mutex):
        super().__init__()
        self.folder = folder
        self.file_chunk = file_chunk
        self.results = list
        self.mutex = mutex

    def run(self):
        image_extensions = QImageReader.supportedImageFormats()

        for file in self.file_chunk:
            if file.split('.')[-1].encode() in image_extensions:
                path = os.path.join(self.folder, file)
                pixmap = QPixmap(path).scaled(thumbnail_size, thumbnail_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.mutex.lock()
                self.results.append((pixmap, path))
                self.mutex.unlock()

class LoadImages(QThread):
    def __init__(self, folder, parent,results):
        super().__init__()
        self.folder = folder
        self.parent = parent
        self.results = results
        self.threadpool = QThreadPool.globalInstance()
        self.mutex = QMutex()
    def run(self):
        start = time.time()
        num_threads = QThreadPool.globalInstance().maxThreadCount()
        all_files = []
        for dirpath, _, filenames in os.walk(self.folder):
            for filename in filenames:
                all_files.append(os.path.join(dirpath, filename))
        chunk_size = (len(all_files) + num_threads - 1) // num_threads  # divide files into equal chunks
        chunks = [all_files[i:i + chunk_size] for i in range(0, len(all_files), chunk_size)]
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
        self.loader = LoadImages(folder, self, self.results)  # create LoadImages instance
        self.loader.start()
        self.loader.finished.connect(
            lambda:self.on_all_images_loaded(self.results)
        )
    def on_all_images_loaded(self, results):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount() + len(results) - 1)
        self.results = results
        self.batch_size = 5  # set the batch size to 100
        self.current_index = 0
        self.process_batch()

    def process_batch(self):
        for i in range(self.current_index, min(self.current_index + self.batch_size, len(self.results))):
            pixmap, filename = self.results[i]
            self.appendRow(PixmapItem(pixmap, filename))
        self.current_index += self.batch_size
        print(f"{self.current_index}, {len(self.results)}")
        if self.current_index < len(self.results):
            QtCore.QTimer.singleShot(10, self.process_batch)  # process next batch in event loop
        else:
            self.endInsertRows()
