import sys
from PyQt5.QtCore import Qt, QAbstractListModel, QModelIndex
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QListView, QLabel, QStyledItemDelegate
import Configuration
from typing import TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from FileSystem import FileSystemNode



class CommitedFolderDelegate(QStyledItemDelegate):
    def displayText(self, value, locale):
        return value.name


class CommitedFolderListModel(QAbstractListModel):
    def __init__(self, data=None):
        super().__init__()
        self._data = data or []

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            element = self._data[index.row()]
            return element

    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            self._data[index.row()] = value
            self.dataChanged.emit(index, index, [role])
            return True
        return False

    def add_element(self, element: 'FileSystemNode'):
        self._data.append(element)


class CommitedFilesWidget(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()  # Create a QVBoxLayout instance
        # Create a custom model and set the custom elements as data
        model = CommitedFolderListModel()

        # Create a QListView widget and set the model and item delegate
        list_view = QListView()
        list_view.setModel(model)
        list_view.setItemDelegate(CommitedFolderDelegate())

        layout.addWidget(list_view)  # Add the list view to the layout

        self.setLayout(layout)  # Set the layout for the widget

    def add_commit(self,node:'FileSystemNode'):
        self.model().add_element(node)


