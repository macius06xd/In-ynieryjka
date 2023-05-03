import time

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import (QApplication, QFileSystemModel, QTreeView, QSplitter, QMainWindow, QScrollArea, QWidget,
                             QVBoxLayout, QListView, QAbstractItemView, QAbstractItemDelegate, QLabel, QMessageBox,
                             QStyle, QListWidget, QStyledItemDelegate)
from PyQt5.QtGui import QPixmap, QImageReader, QStandardItemModel, QStandardItem, QPen, QIcon, QColor, QDrag
from PyQt5.QtCore import Qt, QDir, QSize, QEvent, pyqtSignal, QThread, QObject, QRunnable, QThreadPool, QMutex, \
    QModelIndex, QAbstractListModel, QMimeData, QByteArray, QDataStream, QIODevice, QPoint, QItemSelectionModel, \
    QVariant

thumbnail_size = 64
import sys
import os

class ImageViewer(QListView):
    def __init__(self):
        super().__init__()

        self.setViewMode(QListView.IconMode)
        self.setResizeMode(QListView.Adjust)
        model = MyListModel(list())
        self.setModel(model)
        self.setGridSize(QSize(thumbnail_size + 16, thumbnail_size + 16))
        self.setSpacing(10)
        self.results = []
        self.setWordWrap(True)
        self.setUniformItemSizes(True)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setItemDelegate(ImageDelegate())
        self.selectionModel().selectionChanged.connect(self.manage_selection)
        self.itemDelegate().imageClicked.connect(self.onImageClicked)

    def handle_image_clicked(self, path):
        selected_paths = [item.get_path() for item in self.selectedIndexes()]
        print("Selected images:", selected_paths)

    def manage_selection(self, selected, deselected):
        selected_indexes = self.selectionModel().selectedIndexes()
        for index in selected_indexes:
            item = self.model().itemFromIndex(index)
            print(item.get_path())
        self.viewport().update()
    def onImageClicked(self, imagePath):
        print("Image clicked:", imagePath)
        for row in range(self.model().rowCount()):
            index = self.model().index(row, 0)
            if index.data(Qt.UserRole) == imagePath:
                self.selectionModel().select(index, QItemSelectionModel.Select)
                break

        # create a label widget to display the image
        image_label = QLabel()
        # Example filename
        filename = imagePath
        filename = filename.replace("_small", "")
        filename = filename.replace("small", "")
        pixmap = QPixmap(filename)
        image_label.setPixmap(pixmap)

        # create a message box and set its layout
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Image Viewer")
        msg_box.setText("")

        layout = msg_box.layout()
        layout.addWidget(image_label, 0, 0, Qt.AlignHCenter | Qt.AlignVCenter)

        msg_box.exec_()
    def load_images_from_folder(self,path):
        self.model().listdata.clear()
        image_extensions = QImageReader.supportedImageFormats()
        for root, _, files in os.walk(path):
            for file in files:
                if file.split('.')[-1].encode() in image_extensions:
                    path = os.path.join(root, file)
                    item = PixmapItem(QPixmap(path), path)
                    item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                    self.results.append(item)
                    self.model().listdata.append(item)
                    self.model().layoutChanged.emit()
            break
class ImageDelegate(QStyledItemDelegate):
    imageClicked = pyqtSignal(str)

    def paint(self, painter, option, index):
        if not index.isValid():
            return
        painter.save()
        # Fill the background with the appropriate color
        painter.fillRect(option.rect, option.palette.base())

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


    def sizeHint(self, option, index):
        return QSize(thumbnail_size, thumbnail_size)

    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable


class PixmapItem(QStandardItem):
    def __init__(self, pixmap,path):
        super().__init__()
        self.pixmap = pixmap
        self.path = path
        self.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)  # make item selectable

    def data(self, role):
        if role == Qt.UserRole:
            return self.get_path()
        return self.pixmap
    def get_path(self):
        return self.path




class MyListModel(QAbstractListModel):
    def __init__(self, datain, parent=None, *args):
        QAbstractListModel.__init__(self, parent, *args)
        self.listdata : list = datain

    def rowCount(self, parent=QModelIndex()):
        return len(self.listdata)

    def data(self, index, role):
        if index.isValid() and role == Qt.DisplayRole:
            return self.listdata[index.row()]
        else:
            return QVariant()
    def itemFromIndex(self,index):
        return self.listdata[index.row()]