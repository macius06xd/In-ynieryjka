import time
from array import array
from functools import partial

from PyQt5.QtCore import Qt, QSize, QEvent, pyqtSignal, QModelIndex, QAbstractListModel, QMimeData, QByteArray, \
    QDataStream, QIODevice, QVariant
from PyQt5.QtGui import QPixmap, QImageReader, QStandardItem, QPen, QColor, QDrag
from PyQt5.QtWidgets import (QListView, QAbstractItemView, QMessageBox,
                             QStyle, QStyledItemDelegate, QWidget, QMenu, QAction, QInputDialog)

import app.cfg.Configuration
from app.cfg.Configuration import RESIZED_IMAGES_PATH
from app.src.DataBase import DataBaseConnection
from app.src.FileSystem import FileSystemNode

thumbnail_size = app.cfg.Configuration.RESIZED_IMAGES_SIZE
import os
from PyQt5.QtGui import QPixmapCache

class ImageViewer(QListView):
    node_changed_signal = pyqtSignal(list, FileSystemNode, int)
    image_deleted = pyqtSignal(str)
    file_system_changed = pyqtSignal()

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
        self.ctrl_pressed = False
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.selected_items = []
        self.image_loader_thread = None
        self.dir = None
        self.cluster = None
        self.commitedLayout = None

    def manage_selection(self, selected, deselected):
        selected_indexes = selected
        self.selected_items = selected
        self.ctrl_pressed = False
        self.viewport().update()
    def setCommitedLayout(self, layout):
        self.commitedLayout = layout

    def contextMenuEvent(self, event):
        index = self.indexAt(event.pos())
        if index.isValid():
            menu = QMenu(self)

            action1 = QAction("Delete", self)
            action1.triggered.connect(partial(self.onImageClicked, index))  # Connect function to the action
            menu.addAction(action1)

            action2 = QAction("Combine with commit", self)
            action2.triggered.connect(partial(self.clusterCombine, index))
            menu.addAction(action2)
            # Add more actions as needed

            action = menu.exec_(self.mapToGlobal(event.pos()))
            if action is not None:
                # Handle the selected action
                pass

    def clusterCombine(self, index):
        data = index.internalPointer()
        parent = data.node.parent
        items = self.commitedLayout.get_commited()

        # Create a list of item names
        item_names = [item.name for item in items if item != parent]

        # Add a cancel option to the list
        item_names.append("Cancel")

        # Show the input dialog menu
        selected_item, ok = QInputDialog.getItem(self, "Choose Item", "Select an item:", item_names, editable=False)

        # Check if the user made a selection or cancelled
        if ok and selected_item:
            if selected_item == "Cancel":
                # User chose to cancel the operation
                QMessageBox.information(self, "Cancel", "Operation cancelled.")
            else:
                # User selected an item
                self.commitedLayout.un_commit(parent)
                selected_node = next((item for item in items if item.name == selected_item), None)
                if selected_node:
                    files = [item for item in self.model().listdata if item.node.parent == parent]
                    is_view = files[0].node.is_in_parent(self.dir)
                    for file in files:
                        if is_view:
                            self.model().remove(file)
                        file.node.parent = selected_node
                    parent.clear_childs()
                    selected_node.add_child([element.node for element in files])
                    self.model().layoutChanged.emit()
                    self.file_system_changed.emit()
                    db = DataBaseConnection()
                    db.update_parent(files,selected_node)

        else:
            # User cancelled the operation
            QMessageBox.information(self, "Cancel", "Operation cancelled.")

    # Clusterization Behaviour
    def slider_changed(self, value):
        # Todo
        TIME = time.time()
        from app.src.Clusterization import Cluster

        if self.dir.commited == 0 and not any(item.node.parent.commited == 1 for item in self.model().listdata):
            if self.cluster is None:
                self.cluster = Cluster(self.model().listdata, value,self.onImageClicked)
                self.model().lista_changed.connect(self.cluster.Reevaluate)

            self.cluster.set_clusters(value, self.model().listdata)
            if None not in [x.cluster for x in self.model().listdata]:
                self.model().listdata = sorted(self.model().listdata, key=lambda x: x.cluster)
                self.model().layoutChanged.emit()
            self.node_changed_signal.emit(self.model().listdata, self.dir, value)
        else:
            error_message = "Can't Cluster committed folder"
            QMessageBox.critical(self, "Error", error_message)
            if self.dir.commited != 0:
                print("Condition self.dir.commited == 0 failed")
            else:
                print("View Contain Commited Folder")

    def onImageClicked(self, node):
        if not isinstance(node,PixmapItem):
         data = node.internalPointer()
        else:
            data = node
        self.model().remove(data)
        # change to signal later
        self.image_deleted.emit(os.path.basename(data.path))
        self.model().layoutChanged.emit()

    # Loading images when folder (File System is clicked)
    def load_images_from_folder(self, dir):
        app.cfg.Configuration.time = time.time()
        self.model().listdata.clear()
        self.dir = dir.internalPointer()
        image_extensions = QImageReader.supportedImageFormats()
        for file in dir.data(Qt.UserRole).children:
            file_name = os.path.basename(file.path)
            if file_name.split('.')[-1].encode() in image_extensions:
                item = PixmapItem(os.path.join(RESIZED_IMAGES_PATH, file_name), file)
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.model().add(item)
            if file.cluster:
                self.load_further(file)
        self.model().layoutChanged.emit()
        print(f"Loading Data Time: {time.time() - app.cfg.Configuration.time}")

    # Recurssion for loading
    def load_further(self, dir):
        image_extensions = QImageReader.supportedImageFormats()
        if not dir.commited:
            for file in dir.children:
                file_name = os.path.basename(file.path)
                if file_name.split('.')[-1].encode() in image_extensions:

                    item = PixmapItem(os.path.join(RESIZED_IMAGES_PATH, file_name), file)
                    item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                    self.model().add(item)
                if file.cluster:
                    self.load_further(file)

    def add_image(self, item):
        self.model().add(item)

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
    3: QColor(0, 125, 0),
    4: QColor(0, 125, 125),
    5: QColor(125, 125, 0),
    6: QColor(255, 255, 0),
    7: QColor(0, 255, 255),
    8: QColor(255, 125, 0),
    9: QColor(0, 125, 255),
    10: QColor(255, 125, 255),
    # Add more cluster-color mappings as needed
}


class ImageDelegate(QStyledItemDelegate):

    def paint(self, painter, option, index):
        if not index.isValid():
            return
        cluster_parent = index.data(Qt.DisplayRole).node.parent
        painter.save()
        # Fill the background with the appropriate color
        enlarged_rect = option.rect.adjusted(-8, -8, 8, 8)
        color = color_mapping[hash(id(cluster_parent)) % len(color_mapping)]
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
        return QSize(pixmap_width + 8, pixmap_height + 8)

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

    # NOT USED DEPRECEATED (MOVING IMAGES)
    def supportedDropActions(self):
        return Qt.MoveAction

    # NOT USED DEPRECEATED (MOVING IMAGES)
    def mimeTypes(self):
        return [self.mime_type]

    # NOT USED DEPRECEATED (MOVING IMAGES)
    def mimeData(self, indexes):
        mime_data = QMimeData()
        encoded_data = QByteArray()
        stream = QDataStream(encoded_data, QIODevice.WriteOnly)

        for index in indexes:
            if index.isValid():
                node = index.internalPointer()
                stream.writeQString(node.node.id)

        mime_data.setData(self.mime_type, encoded_data)
        return mime_data

    def getElementById(self, id):
        for row in range(self.rowCount()):
            index = self.index(row)
            if self.data(index, Qt.DisplayRole).node.id == id:
                return self.itemFromIndex(index)

        return None

    def remove(self, item):
        self.lista_changed.emit()
        self.listdata.remove(item)
    def add(self,item):
        self.lista_changed.emit()
        self.listdata.append(item)
