import sys

import h5py
import numpy as np
from PyQt5.QtCore import Qt, QModelIndex, QAbstractListModel, QItemSelectionModel
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QListWidget, QPushButton, QDialog, \
    QStyledItemDelegate, QListView, QAbstractItemView, QListWidgetItem

import sys
from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QListWidget, QPushButton, QCheckBox

import app.cfg.Configuration
import app.src.FileSystem
import app.src.ImageViewer


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
        self.button_action2 = QPushButton("Assign average vector")
        self.button_action3 = QPushButton("Move to Broken #not working")
        self.button_select_all = QCheckBox("Select All")  # New "Select All" checkbox

        layout.addWidget(self.button_action1)
        layout.addWidget(self.button_action2)
        layout.addWidget(self.button_action3)
        layout.addWidget(self.button_select_all)  # Add the "Select All" checkbox to layout
        self.button_action1.clicked.connect(self.perform_action1)
        self.button_action2.clicked.connect(self.perform_action2)
        self.button_action3.clicked.connect(self.perform_action3)
        self.button_select_all.stateChanged.connect(self.toggle_select_all)  # Connect checkbox signal

    def perform_action1(self):
        selected_indexes = self.file_list_view.selectedIndexes()
        for index in reversed(selected_indexes):
            item = self.model.data(index,Qt.EditRole)
            self.signal(item)
            self.model.remove(item)
            self.model.layoutChanged.emit()
    def perform_action2(self):
        selected_indexes = self.file_list_view.selectedIndexes()
        data_vector = [item[1] for item in self.vectors]
        average_vector = np.mean(data_vector, axis=0)

        for index in selected_indexes:
            item = self.model.data(index)
            self.vector_file = h5py.File(app.cfg.Configuration.VECTORS_PATH, 'w')
            name = item.text
            self.model.removeRow(index.row())
    def perform_action3(self):
        selected_indexes = self.file_list_view.selectedIndexes()
        for index in selected_indexes:
            item = self.model.data(index)
            filename = item.text
            print(f"Performed Action 3 on: {filename}")
            self.model.removeRow(index.row())  # Remove item from the model

    def toggle_select_all(self, state):
        for index in range(self.model.rowCount()):
            self.file_list_view.selectionModel().select(self.model.index(index),
                                                        QItemSelectionModel.Select if state else QItemSelectionModel.Deselect)


def main():
    app = QApplication(sys.argv)
    files = ["file1.txt", "file2.txt", "file3.txt"]
    window = FileActionWindow(files)
    window.exec_()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
