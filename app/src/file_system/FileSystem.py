import os
import re
import time
import sys
from functools import partial

import typing
from typing import Iterable

from PyQt5.QtCore import QModelIndex, QDataStream, QIODevice, QMimeData, QByteArray, pyqtSignal, \
    pyqtSlot
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import QTreeView, QVBoxLayout, QMenu, QAbstractItemView, QDialog

from app.cfg.Configuration import INITIAL_CLUSTERIZED_FOLDER
import app.cfg.Configuration
import app.src.database.DataBase
from app.src.tools.NameInputDialog import NameInputDialog


class FileSystemNode:

    def __init__(self, name, path, parent=None, cluster=False, commited=False, color_id=0):
        self.id = 0
        self.name = name
        self.path = path
        self.parent = parent
        self.children: list[FileSystemNode] = []
        self.cluster = cluster
        if commited is None:
            commited = False
        self.commited = commited
        self.color_id = color_id

    def add_child(self, child):
        if isinstance(child, Iterable):
            for c in child:
                self.children.append(c)
                c.parent = self
        else:
            self.children.append(child)
            child.parent = self

    def child(self, row):
        if row >= len(self.children):
            return self.children[len(self.children) - 1]
        return self.children[row]

    def row(self):
        if self.parent:
            return self.parent.children.index(self)
        return 0

    def remove_child(self, child):
        if isinstance(child, Iterable):
            for c in child:
                self.children.remove(c)
        else:
            self.children.remove(child)

    def clear_childs(self):
        self.children.clear()

    def get_cluster_count(self):
        count = 0
        cluster_list = []

        if self.cluster and self.children:
            count += 1
            cluster_list.append(self)

        for child in self.children:
            if child.children:
                child_count, child_clusters = child.get_cluster_count()
                count += child_count
                cluster_list.extend(child_clusters)

        return count, cluster_list

    def is_in_parent(self, node):
        if node.parent is None:
            return False
        if node == self.parent:
            return True
        return self.parent.is_in_parent(node)


class FileSystem(QTreeView):
    Node_Commited = pyqtSignal(FileSystemNode)

    def refresh(self):
        self.model().layoutChanged.emit()

    def __init__(self, image_viewer, clusterManager, parent=None):
        super().__init__(parent)
        self.clusterManager = clusterManager
        self.image_viewer = image_viewer
        self.doubleClicked.connect(self.on_tree_clicked)
        model = FileSystemModel()
        self.setModel(model)
        if app.cfg.Configuration.is_it_run_first_time == 0:
            self.model().populate(self)
        self.setModel(self.model())
        self.setIndentation(20)
        self.setSortingEnabled(True)
        self.setSelectionBehavior(QTreeView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setHeaderHidden(True)
        self.setExpandsOnDoubleClick(False)
        self.setAllColumnsShowFocus(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.setToolTipDuration(1000)
        self.customContextMenuRequested.connect(self.showContextMenu)
        self.model().rowsAboutToBeRemoved.connect(self.rowsRemoved)
        self.model().layoutChanged.connect(self.changed)
        self.current_index = None
        layout = QVBoxLayout(self)
        layout.addWidget(self)
        self.db = app.src.database.DataBase.DataBaseConnection()
        self.setLayout(layout)
        self.clusterManager.setFileSystemModel(self.model())

    def commit(self):
        for node in self.model().get_commited_nodes():
            self.Node_Commited.emit(node)

    def on_deleted(self, filenames):
        if isinstance(filenames, str):
            filenames = [filenames]  # Convert single filename to a list
        for filename in filenames:
            child_node = self.model().get_node_by_name(filename)
            if child_node is not None:
                node = child_node.parent
                node.children.remove(child_node)

                self.db.deletefile(child_node)

                trash = self.model().get_node_by_name("trash")

                child_node.parent = trash
                trash.add_child(child_node)

        self.model().layoutChanged.emit()

    def changed(self):
        print("elo")

    def populate(self):
        self.model().populate(self)

    def showContextMenu(self, point):
        index = self.indexAt(point)
        selected = self.selectedIndexes()
        if index.isValid():
            menu = QMenu(self)
            menu.setToolTipsVisible(True)
            menu.setToolTipDuration(1000)
            commit_action = menu.addAction("Commit")
            commit_action.setToolTip("Commits chosen folder")
            merge_action = menu.addAction("Merge")
            merge_action.setToolTip("Unfolds and combines chosen clusters")
            merge_action2 = menu.addAction(f"Merge into {selected[0].data(Qt.DisplayRole)}")
            merge_action2.setToolTip("Unfolds and combines chosen clusters")
            combine_action = menu.addAction("Combine")
            combine_action.setToolTip("combines chosen clusters")
            combine_action2 = menu.addAction("Combine into {selected[0].data(Qt.DisplayRole)}")
            combine_action2.setToolTip("combines chosen clusters")
            rename_action = menu.addAction("rename")
            if len(selected) == 1:
                merge_action.setEnabled(False)
                merge_action2.setEnabled(False)
                combine_action.setEnabled(False)
                combine_action2.setEnabled(False)

            merge_action.triggered.connect(partial(self.merge,selected ,True,None))
            merge_action2.triggered.connect(partial(self.merge,selected, True,selected[0]))
            combine_action.triggered.connect(partial(self.merge,selected, False,None))
            combine_action2.triggered.connect(partial(self.merge,selected, False,selected[0]))
            commit_action.triggered.connect(partial(self.commitNode, index))
            rename_action.triggered.connect(partial(self.rename_cluster, index))

            # Add other actions to the menu if needed

            menu.exec_(self.viewport().mapToGlobal(point))

    def rename_cluster(self, index):
        dialog = NameInputDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            new_name = dialog.get_new_name()
            if new_name:
                self.clusterManager.renameCluster(index, new_name)

    def merge(self, selectedNodes: typing.List[QModelIndex],recursive = True , parent = None):
        print(recursive)
        self.clusterManager.merge([y.internalPointer() for y in selectedNodes],recursive = recursive , parent= parent if parent is None else parent.internalPointer())

    def commitNode(self, index):
        self.clusterManager.commit(index)

    def rowsInserted(self, parent: QModelIndex, first: int, last: int) -> None:
        print("dodaje")
        dir = self.image_viewer.active_directory
        if parent == dir:
            list = [child.path for child in parent.data(Qt.UserRole).children[first - 1:last + 1]]
            self.image_viewer.add_to_model(list)

    def rowsRemoved(self, parent: QModelIndex, first: int, last: int) -> None:
        print("removed")
        dir = self.image_viewer.active_directory
        if parent == dir:
            self.image_viewer.remove_from_model(parent.data(Qt.UserRole).children[first])

    def on_tree_clicked(self, index):
        self.current_index = index
        if len(index.data(Qt.UserRole).children) != 0:
            self.clusterManager.load_images_from_folder(index)


from PyQt5.QtCore import Qt, QModelIndex, QAbstractItemModel
from os import scandir


class FileSystemModel(QAbstractItemModel):
    def __init__(self):
        super().__init__()
        self.root_node = FileSystemNode("/", INITIAL_CLUSTERIZED_FOLDER)
        self.mime_type = "application/x-qabstractitemmodeldatalist"

    def get_root_node(self):
        return self.root_node

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
        return Qt.MoveAction | Qt.CopyAction

    def flags(self, index):
        default_flags = super().flags(index)
        if index.isValid():
            return default_flags | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled
        else:
            return default_flags | Qt.ItemIsDropEnabled

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
            if role == Qt.DisplayRole:
                name = node.name
                count = len(node.children)
                return f"{name} ({count})"
        elif role == Qt.UserRole:
            return node
        elif role == Qt.FontRole:
            if node.commited == 1:
                font = QFont()
                font.setBold(True)
                return font
        elif role == Qt.ForegroundRole:
            return app.cfg.Configuration.color_mapping[node.color_id]

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

    @pyqtSlot()
    def populate(self, parent):
        # If dataset/database is already prepared application will just load it. Otherwise it will be created
        if app.cfg.Configuration.is_it_run_first_time == 1:
            app.cfg.Configuration.is_it_run_first_time = 0
            print("Creating database")
            self.beginResetModel()
            self.populate_recursively(self.root_node)
            self.endResetModel()
            db = app.src.database.DataBase.DataBaseConnection()
            db.build_database_(self.root_node)

        elif app.cfg.Configuration.is_it_run_first_time == 0:
            print("Database exists")
            db = app.src.database.DataBase.DataBaseConnection()
            self.beginResetModel()
            self.root_node = db.rebuild_file_system_model()
            self.endResetModel()

        else:
            print("is_it_run_first_time value error, it should be either 0 or 1, but is:",
                  app.cfg.Configuration.is_it_run_first_time)
            sys.exit()

    def populate_recursively(self, parent_node):
        for child_entry in scandir(parent_node.path):
            if child_entry.is_dir():
                child_node = FileSystemNode(child_entry.name, child_entry.path, parent_node)
                parent_node.add_child(child_node)
                self.populate_recursively(child_node)
            else:
                child_node = FileSystemNode(child_entry.name, child_entry.path, parent_node)
                parent_node.add_child(child_node)

    def get_node_by_name(self, name):
        return self.get_node_recursively(self.root_node, name)

    def rebuild_file_system_model(self):
        db = app.src.database.DataBase.DataBaseConnection()
        return db.rebuild_file_system_model('/')

    def get_node_recursively(self, parent_node, name):
        if parent_node.name == name:
            return parent_node

        for child_node in parent_node.children:
            if child_node.name == name:
                return child_node

            if child_node.children:
                node = self.get_node_recursively(child_node, name)
                if node:
                    return node

        return None

    def get_commited_nodes(self):
        commited_nodes = []

        def traverse_node(node):
            if node.commited:
                commited_nodes.append(node)
            for child_node in node.children:
                traverse_node(child_node)

        traverse_node(self.root_node)
        return commited_nodes
