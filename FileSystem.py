import os
import shutil
from typing import List, Iterable

from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QModelIndex, QAbstractItemModel, QDataStream, QIODevice, QMimeData, QByteArray
from os import scandir
from Configuration import RESIZED_IMAGES_PATH

from PyQt5.QtWidgets import QTreeView, QWidget, QVBoxLayout, QMenu, QAbstractItemView


class FileSystem(QTreeView):
    def __init__(self,image_viewer, parent=None):
        super().__init__(parent)
        self.image_viewer = image_viewer
        self.clicked.connect(self.on_tree_clicked)
        model = FileSystemModel()
        self.setModel(model)
        self.model().populate()
        self.setModel(self.model())
        self.setIndentation(20)
        self.setSortingEnabled(True)
        self.setSelectionBehavior(QTreeView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setHeaderHidden(True)
        self.setExpandsOnDoubleClick(False)
        self.setAllColumnsShowFocus(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.model().rowsAboutToBeRemoved.connect(self.rowsRemoved)
        self.model().layoutChanged.connect(self.changed)

        layout = QVBoxLayout(self)
        layout.addWidget(self)
        self.setLayout(layout)
    def changed(self):
        print("elo")
    def populate(self):
        self.model().populate()

    def showContextMenu(self, point):
        index = self.indexAt(point)
        if index.isValid():
            menu = QMenu(self)
            # Add actions to the menu for interacting with the selected item
            menu.exec_(self.viewport().mapToGlobal(point))

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        event.setDropAction(Qt.MoveAction)
        data = event.mimeData().data("application/x-qabstractitemmodeldatalist")
        stream = QDataStream(data, QIODevice.ReadOnly)
        row = self.indexAt(event.pos())
        parent = row
        if len(row.data(Qt.UserRole).children) == 0:
            parent = row.data(Qt.UserRole).parent
        else:
            parent = parent.data(Qt.UserRole)

        new_items = []
        indexed = []
        indexed.append(row)
        while not stream.atEnd():
            name = (stream.readQString())
            path = (stream.readQString())
            indexed.append(stream.readQString())
            new_node = FileSystemNode(name, path, parent)
            new_items.append(new_node)

        if len(new_items) > 0:
            first_row = self.model().rowCount(row)
            last_row = first_row + len(new_items) - 1
            self.model().beginInsertRows(row, first_row, last_row)
            for item in new_items:
                parent.add_child(item)
            self.model().endInsertRows()
            self.model().layoutChanged.emit()

        event.accept()




    def rowsInserted(self, parent: QModelIndex, first: int, last: int) -> None:
        print("dodaje")
        dir = self.image_viewer.active_directory
        if parent == dir:
            list = [child.path for child in parent.data(Qt.UserRole).children[first-1:last+1]]
            self.image_viewer.add_to_model(list)

    def rowsRemoved(self, parent: QModelIndex, first: int, last: int) -> None:
        print("removed")
        dir = self.image_viewer.active_directory
        if parent == dir:
            self.image_viewer.remove_from_model(parent.data(Qt.UserRole).children[first])


    def on_tree_clicked(self, index):
        if len(index.data(Qt.UserRole).children) != 0:
         self.image_viewer.load_images_from_folder(index)

from PyQt5.QtCore import Qt, QModelIndex, QAbstractItemModel
from os import scandir, rename

class FileSystemNode:
    def __init__(self, name, path, parent=None):
        self.name = name
        self.path = path
        self.parent = parent
        self.children = []

    def add_child(self, child):
        if isinstance(child, Iterable):
            for c in child:
                self.children.append(c)
        else:
            self.children.append(child)

    def child(self, row):
        if row >= len(self.children):
            return self.children[len(self.children)-1]
        return self.children[row]

    def row(self):
        if self.parent:
            return self.parent.children.index(self)
        return 0
    def remove_child(self , child):
        self.children.remove(child)

class FileSystemModel(QAbstractItemModel):
    def __init__(self):
        super().__init__()
        self.root_node = FileSystemNode("/", RESIZED_IMAGES_PATH)
        self.mime_type = "application/x-qabstractitemmodeldatalist"

    def index(self, row, column, parent=QModelIndex()):
        if not parent.isValid():
            parent_node = self.root_node
        else:
            parent_node = parent.internalPointer()

        child_node = parent_node.child(row)
        if child_node:
            return self.createIndex(row, column, child_node)
        else:
            return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        child_node = index.internalPointer()
        parent_node = child_node.parent

        if parent_node == self.root_node:
            return QModelIndex()

        return self.createIndex(parent_node.row(), 0, parent_node)

    def supportedDropActions(self):
        return  Qt.MoveAction | Qt.CopyAction

    def flags(self, index):
        default_flags = super().flags(index)
        if index.isValid():
            return default_flags | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled
        else:
            return default_flags | Qt.ItemIsDropEnabled

    def dropMimeData(self, data, action, row, column, parent):
        if action == Qt.IgnoreAction:
            return True

        if not data.hasFormat(self.mime_type):
            return False

        if column > 0:
            return False

        if not parent.isValid():
            parent_node = self.root_node
        else:
            parent_node = parent.internalPointer()

        if row == -1:
            row = parent_node.rowCount()

        items = data.data(self.mime_type)
        stream = QDataStream(items, QIODevice.ReadOnly)
        print("czemu to nie wchodzi")
        new_items = []
        while not stream.atEnd():
            row_count = len(parent_node.children)
            if row >= row_count:
                row = row_count
            name = ""
            path = ""
            stream >> name >> path
            new_node = FileSystemNode(name, path, parent_node)
            parent_node.add_child(new_node)
            new_items.append(new_node)
            row += 1
        return True

    def mimeTypes(self):
        return [self.mime_type]

    def mimeData(self, indexes):
        mime_data = QMimeData()
        encoded_data = QByteArray()
        stream = QDataStream(encoded_data, QIODevice.WriteOnly)

        for index in indexes:
            if index.isValid():
                node = index.internalPointer()
                stream.writeQString(node.name)
                stream.writeQString(node.path)
                stream.writeQString(node.parent.path)

        mime_data.setData(self.mime_type, encoded_data)
        return mime_data

    def rowCount(self, parent=QModelIndex()):
        if not parent.isValid():
            parent_node = self.root_node
        else:
            parent_node = parent.internalPointer()

        return len(parent_node.children)

    def columnCount(self, parent=QModelIndex()):
        return 1

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        node = index.internalPointer()

        if role == Qt.DisplayRole:
            return node.name
        elif role == Qt.UserRole:
            return node

    def removeRows(self, row, count, parent=QModelIndex()):
        if not parent.isValid():
            parent_node = self.root_node
        else:
            parent_node = parent.internalPointer()

        self.beginRemoveRows(parent, row, row + count - 1)
        for i in range(row, row + count):
            node = parent_node.child(i)
            parent_node.remove_child(node)
        self.endRemoveRows()

        return True

    def populate(self):
        self.beginResetModel()
        self.populate_recursively(self.root_node)
        self.endResetModel()

    def populate_recursively(self, parent_node):
        for child_entry in scandir(parent_node.path):
            if child_entry.is_dir():
                child_node = FileSystemNode(child_entry.name, child_entry.path, parent_node)
                parent_node.add_child(child_node)
                self.populate_recursively(child_node)
            else:
                child_node = FileSystemNode(child_entry.name, child_entry.path, parent_node)
                parent_node.add_child(child_node)