import os
import sys
from PyQt5.QtCore import Qt, QAbstractListModel, QModelIndex, QSize
from PyQt5.QtGui import QPixmap, QFont, QFontMetrics
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QListView, QLabel, QStyledItemDelegate
import Configuration
from typing import TYPE_CHECKING, Dict, Union, List

if TYPE_CHECKING:
    from FileSystem import FileSystemNode


class CommitedFolderDelegate(QStyledItemDelegate):
    font = None

    def paint(self, painter, option, index):
        # Retrieve the data from the model
        element = index.data(Qt.DisplayRole)
        name = element.name

        # Load the image
        image_path = os.path.join(Configuration.RESIZED_IMAGES_PATH, element.children[0].name)
        image = QPixmap(image_path)

        # Draw the image
        painter.drawPixmap(option.rect.x(), option.rect.y(), image)

        # Draw the name
        if self.font is None:
            self.font = QFont()
            self.font.setBold(True)
            self.font.setPointSize(12)
        name_rect = option.rect.adjusted(image.width(), 0, 0, 0)
        painter.setFont(self.font)
        painter.drawText(name_rect, Qt.AlignVCenter, name)

    def sizeHint(self, option, index):
        # Set the size hint to accommodate both the image and the name
        element = index.data(Qt.DisplayRole)
        name = element.name

        # Load the image
        image_path = os.path.join(Configuration.RESIZED_IMAGES_PATH, element.children[0].name)
        image = QPixmap(image_path)

        if self.font is None:
            self.font = QFont()
            self.font.setBold(True)
            self.font.setPointSize(12)

        name_size = QFontMetrics(self.font).size(Qt.TextSingleLine, name)
        width = image.width() + name_size.width()
        height = max(image.height(), name_size.height())
        size = QSize(width, height)
        return size


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
        print("siema")
        self._data.append(element)


class CommitedFilesWidget(QListView):
    def __init__(self):
        super().__init__()

        model = CommitedFolderListModel()

        # Create a QListView widget and set the model and item delegate
        self.setModel(model)
        self.setItemDelegate(CommitedFolderDelegate())

    def add_commit(self, nodes: 'FileSystemNode'):
        print("siema")
        self.model().add_element(nodes)
        self.model().layoutChanged.emit()


