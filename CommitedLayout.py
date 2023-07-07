import os
from functools import partial
from typing import TYPE_CHECKING

from PyQt5.QtCore import Qt, QAbstractListModel, QModelIndex, QSize, QRect, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont, QFontMetrics
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QListView, QLabel, QStyledItemDelegate, QLineEdit, QDialog, QDialogButtonBox,
    QPushButton, QGridLayout, QStyle, QMenu, QAction
)

import Configuration
from DataBase import DataBaseConnection

if TYPE_CHECKING:
    from FileSystem import FileSystemNode
    from ImageViewer import PixmapItem




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

class CommitedFilesListView(QListView):
    def __init__(self, parent=None):
        super().__init__(parent)

    def contextMenuEvent(self, event):
        index = self.indexAt(event.pos())
        if index.isValid():
            menu = QMenu(self)

            action1 = QAction("Rename", self)
            action1.triggered.connect(partial(self.rename,index))  # Connect function to the action
            menu.addAction(action1)

            action2 = QAction("uncommit", self)
            action2.triggered.connect(partial(self.uncommit,index))  # Connect function to the action
            menu.addAction(action2)

            # Add more actions as needed

            action = menu.exec_(self.mapToGlobal(event.pos()))
            if action is not None:
                # Handle the selected action
                pass

    def uncommit(self,index):
        data = index.internalPointer()
        data.commited = False
        db = DataBaseConnection()
        db.unCommit(data)
        self.model().remove_element(data)
        self.model().layoutChanged.emit()

    def rename(self, index):
        dialog = NameInputDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            new_name = dialog.get_new_name()
            if new_name:
                db = DataBaseConnection()
                db.renamefile(new_name, index.data().id)
                index.internalPointer().name = new_name

    def get_commited(self):
        return self.model().get_data()



class CommitedFilesWidget(QWidget):
    def __init__(self):
        super().__init__()

        # Set the background color for the widget
        self.setStyleSheet("background-color: #F0F0F0;")

        self.layout = QGridLayout()

        self.list_view = CommitedFilesListView()
        self.list_view.setResizeMode(QListView.Adjust)
        self.list_view.setWordWrap(True)
        self.model = CommitedFolderListModel()

        self.list_view.setModel(self.model)
        self.list_view.setItemDelegate(CommitedFolderDelegate())

        self.list_view.doubleClicked.connect(self.open_name_dialog)

        self.grid_view_button = QPushButton("Grid View")
        self.grid_view_button.setCheckable(True)
        self.grid_view_button.clicked.connect(self.toggle_view)

        # Set the background color for the grid view button
        self.grid_view_button.setStyleSheet("background-color: #E0E0E0;")

        self.layout.addWidget(self.grid_view_button, 0, 0)
        self.layout.addWidget(self.list_view, 1, 0)

        self.setLayout(self.layout)

        self.is_grid_view = False

    def toggle_view(self):
        self.list_view.setViewMode(QListView.IconMode if self.grid_view_button.isChecked() else QListView.ListMode)
        self.list_view.itemDelegate().grid_view = self.grid_view_button.isChecked()
        self.list_view.update()

    def open_name_dialog(self, index):
        dialog = NameInputDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            new_name = dialog.get_new_name()
            if new_name:
                db = DataBaseConnection()
                db.renamefile(new_name, index.data().id)
                self.model.setData(index, new_name)

    def add_commit(self, nodes: 'FileSystemNode'):
        self.model.add_element(nodes)
        self.model.layoutChanged.emit()

    def get_commited(self):
        return self.list_view.get_commited()





class CommitedFolderListModel(QAbstractListModel):
    def __init__(self, data=None):
        super().__init__()
        self._data = data or []
    def get_data(self):
        return self._data
    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            element = parent.internalPointer()
            if element.cluster:
                return len(self.children())
            else:
                return 0
        else:
            return len(self._data)

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if index.isValid():
                element = index.internalPointer()
                return element
            else:
                return None

    def index(self, row, column, parent=QModelIndex()):
        if parent.isValid():
            element = parent.internalPointer()
            if element.cluster and 0 <= row < len(element.children):
                child = element.children[row]
                return self.createIndex(row, column, child)
            else:
                return QModelIndex()
        else:
            if 0 <= row < len(self._data):
                element = self._data[row]
                return self.createIndex(row, column, element)
            else:
                return QModelIndex()

    def parent(self, index):
        if index.isValid():
            element = index.internalPointer()
            parent = element.parent
            if parent is None:
                return QModelIndex()
            else:
                grandparent = parent.parent
                if grandparent is None:
                    parent_index = self._data.index(parent)
                    return self.createIndex(parent_index, 0, parent)
                else:
                    parent_index = grandparent.children.index(parent)
                    return self.createIndex(parent_index, 0, parent)
        else:
            return QModelIndex()

    def add_element(self, element: 'FileSystemNode'):
        element.commited = 1
        if self.is_parent_commited(element):
            if element in self._data:
                self._data.remove(element)
            index = self._data.find(element.parent)
            self._data.insert(index+1,element)
            self.add_child_clusters(element)
        else:
            if element in self._data:
                self._data.remove(element)
            self._data.append(element)
            self.add_child_clusters(element)


    def is_parent_commited(self,element: 'FileSystemNode'):
        if element.parent is None:
            return False
        else:
            return self.is_parent_commited(element.parent)

    def add_child_clusters(self, element: 'FileSystemNode', parent_index=QModelIndex()):

        # Remove elements with the same parent from the list

        for child in element.children:
            if child.cluster:
                if child in self._data:
                    self._data.remove(child)
                parent_row = self._data.index(element)
                row = parent_row + 1
                child.commited = 1
                self._data.insert(row, child)
                self.add_child_clusters(child, self.index(row, 0, parent_index))
                parent_row += 1  # Increment parent_row to account for the added child

    def remove_elements_with_parent(self, parent_element):
        elements_to_remove = [element for element in self._data if element.parent.id == parent_element.id]

        for element in elements_to_remove:
            self.remove_element(element)

    def remove_element(self, element: 'FileSystemNode'):
        if element not in self._data:
            return

        # Find the index of the element
        index = self.index(self._data.index(element), 0, QModelIndex())

        # Remove the element and its children clusters recursively
        self.beginRemoveRows(index.parent(), index.row(), index.row() + self.count_child_clusters(element))

        self.remove_child_clusters(element)

        self._data.remove(element)

        self.endRemoveRows()

    def remove_child_clusters(self, element: 'FileSystemNode'):
        children_clusters = [child for child in element.children if child.cluster]
        for child in children_clusters:
            child.commited = 0
            db = DataBaseConnection()
            db.unCommit(child)
            self.remove_element(child)

    def count_child_clusters(self, element: 'FileSystemNode') -> int:
        return sum(1 for child in element.children if child.cluster)

class CommitedFolderDelegate(QStyledItemDelegate):
    font = None
    grid_view = False

    def paint(self, painter, option, index):
        # Retrieve the data from the model
        element = index.data(Qt.DisplayRole)
        name = element.name
        try:
            image_path = os.path.join(Configuration.RESIZED_IMAGES_PATH, element.children[0].name)
            image = QPixmap(image_path)
        except:
            icon = QApplication.style().standardIcon(QStyle.SP_DialogOkButton)
            image = icon.pixmap(Configuration.RESIZED_IMAGES_SIZE, Configuration.RESIZED_IMAGES_SIZE)

        if not self.grid_view:
            # Load the image
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

            # Draw child indicator
            if element.parent and element.parent.commited:
                indicator_rect = QRect(option.rect.x() + 5, option.rect.y() + 5, 10, 10)
                painter.fillRect(indicator_rect, Qt.red)

        else:
            image = QPixmap(image_path)
            painter.drawPixmap(option.rect.x(), option.rect.y(), image)

    def sizeHint(self, option, index):
        # Set the size hint to accommodate both the image and the name
        element = index.data(Qt.DisplayRole)
        name = element.name

        # Load the image
        try:
            image_path = os.path.join(Configuration.RESIZED_IMAGES_PATH, element.children[0].name)
            image = QPixmap(image_path)
        except:
            icon = QApplication.style().standardIcon(QStyle.SP_DialogOkButton)
            image = icon.pixmap(Configuration.RESIZED_IMAGES_SIZE, Configuration.RESIZED_IMAGES_SIZE)
        if( self.grid_view):
            return QSize(image.size())
        if self.font is None:
            self.font = QFont()
            self.font.setBold(True)
            self.font.setPointSize(12)

        name_size = QFontMetrics(self.font).size(Qt.TextSingleLine, name)
        width = image.width() + name_size.width()
        height = max(image.height(), name_size.height())
        size = QSize(width, height)
        return size