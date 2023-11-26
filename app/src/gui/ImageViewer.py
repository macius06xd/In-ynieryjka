import time
import re
from array import array
from functools import partial

from PyQt5.QtCore import Qt, QSize, QEvent, pyqtSignal, QModelIndex, QAbstractListModel, QMimeData, QByteArray, \
    QDataStream, QIODevice, QVariant, QRect
from PyQt5.QtGui import QPixmap, QImageReader, QStandardItem, QPen, QColor, QDrag
from PyQt5.QtWidgets import (QListView, QAbstractItemView, QMessageBox,
                             QStyle, QStyledItemDelegate, QWidget, QMenu, QAction, QInputDialog)

import app.cfg.Configuration
from app.cfg.Configuration import RESIZED_IMAGES_PATH
from app.src.database.DataBase import DataBaseConnection
from app.src.file_system.FileSystem import FileSystemNode

thumbnail_size = app.cfg.Configuration.RESIZED_IMAGES_SIZE
import os
from PyQt5.QtGui import QPixmapCache


class ImageViewer(QListView):
    node_changed_signal = pyqtSignal(list, FileSystemNode, int)
    image_deleted = pyqtSignal(str)
    file_system_changed = pyqtSignal()

    def __init__(self, clusterManager):
        super().__init__()
        self.clusterManager = clusterManager
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
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setItemDelegate(ImageDelegate())
        self.selectionModel().selectionChanged.connect(self.manage_selection)
        self.ctrl_pressed = False
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.selected_items = []
        self.image_loader_thread = None
        self.dir = None
        self.cluster = None
        self.commitedLayout = None

        clusterManager.setImageViewerModel(self.model())

    def manage_selection(self, selected, deselected):
        selected_indexes = selected
        self.selected_items = selected
        self.ctrl_pressed = False
        self.viewport().update()

    def setCommitedLayout(self, layout):
        self.commitedLayout = layout

    def contextMenuEvent(self, event):
        index = self.indexAt(event.pos())
        menu = QMenu(self)
        if index.isValid():
            action1 = QAction("Delete", self)
            action1.triggered.connect(partial(self.onImageClicked, index))  # Connect function to the action
            menu.addAction(action1)

            action2 = QAction("Combine with commit", self)
            action2.triggered.connect(partial(self.clusterCombine, index))
            menu.addAction(action2)
            # Add more actions as needed
            action3 = QAction("Delete selected", self)
            action3.triggered.connect(partial(self.delete_images, self.selectedIndexes()))
            menu.addAction(action3)

            action4 = QAction("Open Parent", self)
            action4.triggered.connect(
                lambda: self.recive_notification_from_FileSystem(index.internalPointer().node.parent))
            menu.addAction(action4)

            action5 = QAction("Build new cluster at top level", self)
            action5.triggered.connect(lambda: self.build_new_cluster(toplevel=True))
            menu.addAction(action5)

            action6 = QAction("Build new cluster at current dir", self)
            action6.triggered.connect(lambda: self.build_new_cluster(toplevel=False))
            menu.addAction(action6)

            action = menu.exec_(self.mapToGlobal(event.pos()))
        else:
            action1 = QAction("Back", self)
            action1.triggered.connect(lambda: self.recive_notification_from_FileSystem(self.model().dir.parent))
            menu.addAction(
                action1
            )
            action = menu.exec_(self.mapToGlobal(event.pos()))
            if action is not None:
                # Handle the selected action
                pass

    def build_new_cluster(self, toplevel=True):
        ## get selected images
        indexes = self.selectionModel().selectedIndexes()
        image_list = [element.internalPointer() for element in indexes]
        self.clusterManager.Build_new_cluster(image_list, None if toplevel else self.model().get_current_dir())

    def clusterCombine(self, index):
        data = index.internalPointer()
        parent = data.node.parent
        items = self.clusterManager.get_commited()
        item_names = [item.name for item in items if item != parent]
        # Add a cancel option to the list
        item_names.append("Cancel")
        # Show the input dialog menu
        selected_item, ok = QInputDialog.getItem(self, "Choose Item", "Select an item:", item_names, editable=False)
        if ok and selected_item:
            if selected_item == "Cancel":
                # User chose to cancel the operation
                QMessageBox.information(self, "Cancel", "Operation cancelled.")
            else:
                selected_node = next((item for item in items if item.name == selected_item), None)
                self.clusterManager.clusterCombine(parent, selected_node)

    # Clusterization Behaviour
    def slider_changed(self, value):
        # Todo
        app.cfg.Configuration.time = time.time()
        from app.src.clusterization.Clusterization import Cluster

        if self.model().dir.commited == 0 and not any(item.node.parent.commited == 1 for item in self.model().listdata):
            if self.cluster is None:
                self.cluster = Cluster(self.model().listdata, value, self.onImageClicked)
                self.model().lista_changed.connect(self.cluster.Reevaluate)

            self.cluster.set_clusters(value, self.model().listdata)
            if None not in [x.cluster for x in self.model().listdata]:
                self.model().listdata = sorted(self.model().listdata, key=lambda x: x.cluster)
                self.model().layoutChanged.emit()
            self.clusterManager.Cluster(self.model().listdata, self.model().dir, value)
        else:
            error_message = "Can't Cluster committed folder"
            QMessageBox.critical(self, "Error", error_message)
            if self.model().dir.commited != 0:
                print("Condition self.dir.commited == 0 failed")
            else:
                print("View Contain Commited Folder")

    def delete_images(self, nodes):
        for node in nodes:
            self.onImageClicked(node)
        self.clearSelection()

    def onImageClicked(self, node):
        if not isinstance(node, PixmapItem):
            data = node.internalPointer()
        else:
            data = node
        self.model().remove(data)
        # change to signal later
        self.image_deleted.emit(os.path.basename(data.path))
        self.model().layoutChanged.emit()

    def add_image(self, item):
        self.model().add(item)

    def recive_notification_from_FileSystem(self, dir):
        self.model().load_images_from_folder(dir)

    def remove_from_model(self, data):
        path = data.path
        item = PixmapItem(QPixmap((path)), path)
        i = 0
        for item in self.model().listdata:
            if item.get_path() == path:
                del self.model().listdata[i]
            i = i + 1
        self.model().layoutChanged.emit()


class ImageDelegate(QStyledItemDelegate):
    prev_parent = None

    def paint(self, painter, option, index):
        if not index.isValid():
            return

        cluster_item = index.data(Qt.DisplayRole).node
        painter.save()
        enlarged_rect = option.rect.adjusted(-4, -4, 4, 4)

        # Specify correct color based on the color_id
        color = app.cfg.Configuration.color_mapping[index.data(Qt.DisplayRole).node.parent.color_id]
        painter.fillRect(enlarged_rect, color)

        pixmap = index.data().get_image()
        # Draw the pixmap
        painter.drawPixmap(option.rect.x(), option.rect.y(), pixmap)

        # Check if the item is selected
        if option.state & QStyle.State_Selected:
            # Draw a blue border around the image
            pen = QPen(QColor(0, 0, 255), 3, Qt.SolidLine)
            painter.setPen(pen)
            painter.drawRect(option.rect)

        painter.restore()

    def sizeHint(self, option, index):
        pixmapitem = index.data()
        pixmap_width = pixmapitem.get_image().width()
        pixmap_height = pixmapitem.get_image().height()
        return QSize(pixmap_width + 8, pixmap_height + 10)  # Increased height to account for the square

    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDropEnabled | Qt.ItemIsDragEnabled


class PixmapItem(QStandardItem):
    def __init__(self, path, node, cluster=None):
        super().__init__()
        self.path = path
        self.node = node
        self.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)  # make item selectable
        self.cluster = cluster

    def data(self, role):
        if role == Qt.UserRole:
            return self.get_path()
        if role == Qt.DisplayRole:
            return self
        return QPixmap(self.get_path())

    def get_path(self):
        return self.path

    def get_image(self):
        if QPixmapCache.find(self.path):
            return QPixmapCache.find(self.path)
        else:
            pixmap = QPixmap(self.path)
            QPixmapCache.insert(self.path, pixmap)
            return pixmap


class MyListModel(QAbstractListModel):
    lista_changed = pyqtSignal()
    dir = None

    def __init__(self, datain, parent=None, *args):
        QAbstractListModel.__init__(self, parent, *args)
        self.listdata: array = datain
        self.mime_type = "application/x-qabstractitemmodeldatalist"

    def rowCount(self, parent=QModelIndex()):
        return len(self.listdata)

    def index(self, row, column=0, parent=QModelIndex()):
        if parent.isValid() and parent.column() != 0:
            return QModelIndex()

        if 0 <= row < self.rowCount(parent):
            return self.createIndex(row, column, self.listdata[row])

        return QModelIndex()

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

    def getElementById(self, id):
        for row in range(self.rowCount()):
            index = self.index(row)
            if self.data(index, Qt.DisplayRole).node.id == id:
                return self.itemFromIndex(index)

        return None

    def remove(self, item):
        self.lista_changed.emit()
        self.listdata.remove(item)

    def add(self, item):
        self.lista_changed.emit()
        self.listdata.append(item)

    def load_images_from_folder(self, dir):
        app.cfg.Configuration.time = time.time()
        self.listdata.clear()
        self.dir = dir
        if dir is None:
            return
        image_extensions = QImageReader.supportedImageFormats()
        for file in self.dir.get_images():
            file_name = os.path.basename(file.path)
            item = PixmapItem(os.path.join(RESIZED_IMAGES_PATH, file_name), file)
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.add(item)
        for file in self.dir.children:
            self.load_further(file)
        self.layoutChanged.emit()
        print(f"Loading Data Time: {time.time() - app.cfg.Configuration.time}")

    # Recurssion for loading
    def load_further(self, dir):
        image_extensions = QImageReader.supportedImageFormats()
        if not dir.commited:
            for file in dir.get_images():
                file_name = os.path.basename(file.path)
                item = PixmapItem(os.path.join(RESIZED_IMAGES_PATH, file_name), file)
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.add(item)
            for file in dir.children:
                self.load_further(file)

    def get_current_dir(self):
        return self.dir
