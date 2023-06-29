import string
import time
from array import array

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import (QApplication, QFileSystemModel, QTreeView, QSplitter, QMainWindow, QScrollArea, QWidget,
                             QVBoxLayout, QListView, QAbstractItemView, QAbstractItemDelegate, QLabel, QMessageBox,
                             QStyle, QListWidget, QStyledItemDelegate, QDialog, QSlider, QHBoxLayout)
from PyQt5.QtGui import QPixmap, QImageReader, QStandardItemModel, QStandardItem, QPen, QIcon, QColor, QDrag, QCursor, \
    QPainter
from PyQt5.QtCore import Qt, QDir, QSize, QEvent, pyqtSignal, QThread, QObject, QRunnable, QThreadPool, QMutex, \
    QModelIndex, QAbstractListModel, QMimeData, QByteArray, QDataStream, QIODevice, QPoint, QItemSelectionModel, \
    QVariant

import Configuration
from Configuration import RESIZED_IMAGES_SIZE

thumbnail_size = RESIZED_IMAGES_SIZE
import sys
import os


class ImageLoader(QThread):
    image_loaded = pyqtSignal(object)
    def __init__(self, file_list):
        super().__init__()
        self.file_list = file_list

    def run(self):
        image_extensions = QImageReader.supportedImageFormats()
        for file in self.file_list:
            file_name = os.path.basename(file.path)
            if file_name.split('.')[-1].encode() in image_extensions:
                pixmap = QPixmap(file.path)
                item = PixmapItem(pixmap, file_name)
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.image_loaded.emit(item)
class ImageViewer(QListView):
    node_changed_signal = pyqtSignal(list, str, int)
    image_deleted = pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self.files = None
        self.active_directory = None
        self.setViewMode(QListView.IconMode)
        self.setResizeMode(QListView.Adjust)
        model = MyListModel(list())
        self.setModel(model)
        self.setSpacing(10)
        self.results = []
        self.setDragEnabled(True)
        self.acceptDrops()
        self.setWordWrap(True)
        self.setSelectionMode(QAbstractItemView.ContiguousSelection)
        self.setItemDelegate(ImageDelegate())
        self.selectionModel().selectionChanged.connect(self.manage_selection)
        self.itemDelegate().imageClicked.connect(self.onImageClicked)
        self.ctrl_pressed = False
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.selected_items = []
        self.image_loader_thread = None
        self.dir = None
        self.cluster = None



    def slider_changed(self, value):
        # Todo
        from Clusterization import Cluster
        if self.cluster is None:
            self.cluster = Cluster(self.model().listdata,value)
        self.cluster.set_clusters(value,self.model().listdata)
        self.model().listdata = sorted(self.model().listdata,key = lambda x:x.cluster)
        self.model().layoutChanged.emit()
        self.node_changed_signal.emit(self.model().listdata,self.dir,value)


    def manage_selection(self, selected, deselected):
        selected_indexes = selected
        self.selected_items = selected
        self.ctrl_pressed = False
        self.viewport().update()

    def onImageClicked(self, imagePath: str):
        self.model().remove(self.model().getElementByPath(imagePath))
        # change to signal later
        self.image_deleted.emit(os.path.basename(imagePath))
        self.model().layoutChanged.emit()





    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and event.modifiers() == Qt.ControlModifier:
            self.ctrl_pressed = True
            selected_indexes = self.selectionModel().selectedIndexes()
            self.selected_items = [self.model().itemFromIndex(index) for index in selected_indexes]
        else:
            self.ctrl_pressed = False
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.ctrl_pressed and self.selected_items:
            mime_data = QMimeData()
            paths = [item.get_path() for item in self.selected_items]
            mime_data.setData("text/plain", "\n".join(paths).encode())
            drag = QDrag(self)
            drag.setMimeData(mime_data)

            pixmap = QPixmap(self.selected_items[0].pixmap)
            drag.setPixmap(pixmap)

            # Get the bounding rectangle of the selected items
            rect = self.visualRect(self.selectionModel().selection().indexes()[0])
            for index in self.selectionModel().selection().indexes()[1:]:
                rect = rect.united(self.visualRect(index))

            # Calculate the offset from the mouse position to the top-left corner of the bounding rectangle
            offset = event.pos() - rect.topLeft()

            drag.setHotSpot(offset)

            drag.exec_()
        super().mouseMoveEvent(event)

    def dragEnterEvent(self, event):
        event.accept()

    def dragMoveEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        print("elo23")
        mime_data = event.mimeData()
        event.setDropAction(Qt.CopyAction)
        if mime_data.hasUrls():
            urls = [url.toLocalFile() for url in mime_data.urls()]
            self.add_to_model(urls)

        elif mime_data.hasText():
            paths = mime_data.text().split('\n')
            self.add_to_model(paths)
        event.acceptProposedAction()

    def load_images_from_folder(self, dir):
        self.model().listdata.clear()
        self.dir = dir.data(Qt.UserRole).name
        image_extensions = QImageReader.supportedImageFormats()
        for file in dir.data(Qt.UserRole).children:
            file_name = os.path.basename(file.path)
            if file_name.split('.')[-1].encode() in image_extensions:
                pixmap = QPixmap(os.path.join(Configuration.RESIZED_IMAGES_PATH, file_name))
                item = PixmapItem(pixmap, os.path.join(Configuration.RESIZED_IMAGES_PATH, file_name))
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.model().listdata.append(item)
            if file.cluster:
                self.load_further(file)
        self.model().layoutChanged.emit()

    def load_further(self, dir):
        image_extensions = QImageReader.supportedImageFormats()
        if not dir.commited:

            for file in dir.children :
                file_name = os.path.basename(file.path)
                if file_name.split('.')[-1].encode() in image_extensions:
                    pixmap = QPixmap(os.path.join(Configuration.RESIZED_IMAGES_PATH, file_name))
                    item = PixmapItem(pixmap, os.path.join(Configuration.RESIZED_IMAGES_PATH, file_name))
                    item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                    self.model().listdata.append(item)
    def add_image(self, item):
        self.model().listdata.append(item)

    def add_to_model(self, data):
        results = []

        # iterate over paths and check if there is a matching item
        for path in data:
            if not any(item.path == path for item in self.model().listdata):
                results.append(path)
        for result in results:
            self.model().listdata.append(PixmapItem(QPixmap(result), result))
        self.model().layoutChanged.emit()

    def recive_notification_from_FileSystem(self, dir):
        self.load_images_from_folder(dir)

    def remove_from_model(self, data):
        path = data.path
        item = PixmapItem(QPixmap((path)), path)
        i = 0
        for item in self.model().listdata:
            if item.get_path() == path:
                del self.model().listdata[i]
            i = i + 1
        self.model().layoutChanged.emit()

color_mapping = {
    0: QColor(255, 0, 0),
    1: QColor(0, 255, 0),
    2: QColor(0, 0, 255),
    3: QColor(0,125,0),
    4: QColor(0,125,125),
    5: QColor(125,125,0),
    6: QColor(255,255,0),
    7: QColor(0,255,255),
    8: QColor(255,125,0),
    9: QColor(0,125,255),
    10: QColor(255,125,255),
    # Add more cluster-color mappings as needed
}
class ImageDelegate(QStyledItemDelegate):
    imageClicked = pyqtSignal(str)

    def paint(self, painter, option, index):
        if not index.isValid():
            return
        cluster = index.data(Qt.DisplayRole)
        painter.save()
                # Fill the background with the appropriate color
        enlarged_rect = option.rect.adjusted(-8, -8, 8, 8)
        if cluster is not None:
            color = color_mapping.get(cluster.cluster,QColor(0, 0, 0))  # Default to black if cluster value not found in mapping
            painter.fillRect(enlarged_rect, color)

        pixmap = index.data()
        # Draw the pixmap
        painter.drawPixmap(option.rect.x(), option.rect.y(), pixmap.pixmap)

        # Check if the item is selected
        if option.state & QStyle.State_Selected:
            # Draw a blue border around the image
            pen = QPen(QColor(0, 0, 255), 3, Qt.SolidLine)
            painter.setPen(pen)
            painter.drawRect(option.rect)

        painter.restore()

    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:

            return True

        elif event.type() == QEvent.MouseButtonPress and event.button() == Qt.RightButton:
            self.imageClicked.emit(index.data().path)
            return True

        return super().editorEvent(event, model, option, index)

    def sizeHint(self, option, index):
        pixmapitem = index.data()
        pixmap_width = pixmapitem.pixmap.width()
        pixmap_height = pixmapitem.pixmap.height()
        return QSize(pixmap_width, pixmap_height)

    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDropEnabled | Qt.ItemIsDragEnabled


class PixmapItem(QStandardItem):
    def __init__(self, pixmap, path, cluster=None):
        super().__init__()
        self.pixmap = pixmap
        self.path = path
        self.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)  # make item selectable
        self.cluster = cluster

    def data(self, role):
        if role == Qt.UserRole:
            return self.get_path()
        if role == Qt.DisplayRole:
            return self.cluster
        return self.pixmap

    def get_path(self):
        print(self.path)
        return self.path


class MyListModel(QAbstractListModel):
    def __init__(self, datain, parent=None, *args):
        QAbstractListModel.__init__(self, parent, *args)
        self.listdata: array = datain
        self.mime_type = "application/x-qabstractitemmodeldatalist"

    def rowCount(self, parent=QModelIndex()):
        return len(self.listdata)

    def data(self, index, role):
        if index.isValid() and role == Qt.DisplayRole:
            return self.listdata[index.row()]
        else:
            return QVariant()

    def itemFromIndex(self, index):
        return self.listdata[index.row()]

    def indexFromItem(self, item):
        for row in range(self.rowCount()):
            index = self.index(row)
            if self.data(index, Qt.UserRole) == item.get_path():
                return index
        return QModelIndex()

    def supportedDropActions(self):
        return Qt.MoveAction

    def mimeTypes(self):
        return [self.mime_type]

    def mimeData(self, indexes):
        mime_data = QMimeData()
        encoded_data = QByteArray()
        stream = QDataStream(encoded_data, QIODevice.WriteOnly)

        for index in indexes:
            if index.isValid():
                node = index.internalPointer()
                stream.writeQString(node.path)

        mime_data.setData(self.mime_type, encoded_data)
        return mime_data

    def getElementByPath(self, path):
        for row in range(self.rowCount()):
            index = self.index(row)
            if self.data(index, Qt.DisplayRole).path == path:
                return self.itemFromIndex(index)

        return None
    def remove(self,item):
        self.listdata.remove(item)
