from PyQt5.QtCore import QDir, pyqtSignal
from PyQt5.QtWidgets import QFileSystemModel, QTreeView

from ImageViewer import ImageViewer


class CustomFileSystemModel(QFileSystemModel):
    def __init__(self, root_path):
        super().__init__()
        self.setRootPath(root_path)

class FileSystem(QTreeView):
    def __init__(self,image_viewer : ImageViewer):
        super().__init__()
        self.dir_model = CustomFileSystemModel(r"C:\Users\wojte\OneDrive\Pulpit\klockilego\klocki")
        self.dir_model.setFilter(QDir.NoDotAndDotDot | QDir.AllDirs)
        self.setModel(self.dir_model)
        self.clicked.connect(self.on_tree_clicked)
        self.image_viewer = image_viewer
        self.setRootIndex(self.dir_model.index(self.dir_model.rootPath()))

    def on_tree_clicked(self, index):
        folder = self.dir_model.filePath(index)
        self.image_viewer.load_images_from_folder(folder)