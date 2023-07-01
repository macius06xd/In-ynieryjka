import os

from PyQt5.QtCore import Qt, QAbstractListModel, QModelIndex, QSize
from PyQt5.QtGui import QPixmap, QFont, QFontMetrics
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QListView, QLabel, QStyledItemDelegate, QLineEdit, QDialog, QDialogButtonBox,
    QHBoxLayout
)
import Configuration
from typing import TYPE_CHECKING

from DataBase import DataBaseConnection

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


class NameInputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Change Name")

        self.layout = QVBoxLayout()

        self.label = QLabel("New Name:")
        self.layout.addWidget(self.label)

        self.input_edit = QLineEdit()
        self.layout.addWidget(self.input_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self.layout.addWidget(button_box)

        self.setLayout(self.layout)

    def get_new_name(self):
        return self.input_edit.text()


class CommitedFilesWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout()
        self.list_view = QListView()
        self.model = CommitedFolderListModel()

        self.list_view.setModel(self.model)
        self.list_view.setItemDelegate(CommitedFolderDelegate())

        self.list_view.doubleClicked.connect(self.open_name_dialog)

        self.layout.addWidget(self.list_view)
        self.setLayout(self.layout)

    def open_name_dialog(self, index):
        dialog = NameInputDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            new_name = dialog.get_new_name()
            if new_name:
                db = DataBaseConnection()
                db.renamefile(new_name,index.data().id)
                self.model.setData(index, new_name)

    def add_commit(self, nodes: 'FileSystemNode'):
        self.model.add_element(nodes)
        self.model.layoutChanged.emit()


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
            element = self._data[index.row()]
            element.name = value
            self.dataChanged.emit(index, index, [role])
            return True
        return False


    def add_element(self, element: 'FileSystemNode'):
        element.commited = 1
        element.children = list(filter(lambda x: x.cluster == 0, element.children))
        self._data.append(element)