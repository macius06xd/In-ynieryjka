import sys

import h5py
import numpy as np
from PyQt5.QtCore import Qt, QModelIndex, QAbstractListModel, QItemSelectionModel
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QListWidget, QPushButton, QDialog, \
    QStyledItemDelegate, QListView, QAbstractItemView, QListWidgetItem

import sys
from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QListWidget, QPushButton, QCheckBox

import app.cfg.Configuration
import app.src.file_system.FileSystem
import app.src.gui.ImageViewer


class PixmapItemModel(QAbstractListModel):
    def __init__(self, items):
        super().__init__()
        self.items = items

    def rowCount(self, parent=QModelIndex()):
        return len(self.items)

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return self.items[index.row()].path
        if role == Qt.EditRole:
            return self.items[index.row()]

    def remove(self,item):
        self.items.remove(item)

class PixmapItemModel(QAbstractListModel):
    def __init__(self, items):
        super().__init__()
        self.items = items

    def rowCount(self, parent=QModelIndex()):
        return len(self.items)

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return self.items[index.row()].path
        if role == Qt.EditRole:
            return self.items[index.row()]

    def remove(self, item):
        self.items.remove(item)


class FileActionWindow(QDialog):
    def __init__(self, files, signal, vectors):
        super().__init__()
        self.signal = signal
        self.vectors = vectors
        self.setWindowTitle("File Action Window")
        self.setGeometry(100, 100, 400, 400)

        layout = QVBoxLayout(self)

        self.file_list_view = QListView()
        layout.addWidget(self.file_list_view)

        self.model = PixmapItemModel(files)  # Create the custom model
        self.file_list_view.setModel(self.model)

        self.button_action1 = QPushButton("Remove")
        self.button_action2 = QPushButton("Cancel")
        self.button_select_all = QCheckBox("Select All")  # New "Select All" checkbox

        layout.addWidget(self.button_action1)
        layout.addWidget(self.button_action2)
        layout.addWidget(self.button_select_all)  # Add the "Select All" checkbox to layout
        self.button_action1.clicked.connect(self.perform_action1)
        self.button_action2.clicked.connect(self.on_cancel_clicked)
        self.button_select_all.stateChanged.connect(self.toggle_select_all)  # Connect checkbox signal

    def perform_action1(self):
        selected_indexes = self.file_list_view.selectedIndexes()
        for index in reversed(selected_indexes):
            item = self.model.data(index, Qt.EditRole)
            self.signal(item)
            self.model.remove(item)
            self.model.layoutChanged.emit()

    def toggle_select_all(self, state):
        for index in range(self.model.rowCount()):
            self.file_list_view.selectionModel().select(self.model.index(index),
                                                        QItemSelectionModel.Select if state else QItemSelectionModel.Deselect)

    def on_cancel_clicked(self):
        if not self.model.items:  # Check if model is empty
            self.accept()
        else:
            self.reject()

    def exec_(self):
        result = super().exec_()
        if result == QDialog.Rejected:
            return 42
        return result
