import itertools
import time
import typing

from PyQt5.QtCore import QModelIndex, Qt
from PyQt5.QtWidgets import QInputDialog, QMessageBox

import app.cfg.Configuration
from app.src.gui.CommitedLayout import CommitedFolderListModel
from app.src.database.DataBase import DataBaseConnection
from app.src.gui.ImageViewer import MyListModel
from app.src.file_system.FileSystem import FileSystemModel, FileSystemNode , Image


# every operations on the clusters should be perfomed here
# Widget -> ClusterManager -> Database
# TODO move initialization (Creating database,loading database) here
# TODO Add Clusterization logic here
class ClusterManager:
    ImageViewerModel: MyListModel = None
    FileSystemModel: FileSystemModel = None
    CommitedModel: CommitedFolderListModel = None
    db: DataBaseConnection = None

    def __init__(self):
        if self.db is None:
            self.db = DataBaseConnection()

    def setImageViewerModel(self, model):
        self.ImageViewerModel = model

    def setFileSystemModel(self, model):
        self.FileSystemModel = model

    def setCommitedModel(self, model):
        self.CommitedModel = model

    def renameCluster(self, index: QModelIndex, new_name: str):
        self.db.renamefile(new_name, index.internalPointer().id)
        index.internalPointer().name = new_name

    def get_commited(self):
        return self.CommitedModel.get_data()

    def clusterCombine(self, source, target):
        self.uncommit(source)
        if target:
            files = [item for item in self.ImageViewerModel.listdata if item.node.parent == source]
            is_view = files[0].node.is_in_parent(self.ImageViewerModel.dir)
            for file in files:
                if is_view:
                    self.ImageViewerModel.remove(file)
                file.node.parent = target
            source.clear_images()
            target.add_image([element.node for element in files])
            self.FileSystemModel.layoutChanged.emit()
            self.ImageViewerModel.layoutChanged.emit()
            db = DataBaseConnection()
            db.update_parent(files, target)

        else:
            # User cancelled the operation
            QMessageBox.information(self, "Cancel", "Operation cancelled.")

    def uncommit(self, data):
        data.commited = False
        db = DataBaseConnection()
        db.unCommit(data)
        self.CommitedModel.remove_element(data)
        self.CommitedModel.layoutChanged.emit()

    def commit(self, index):
        node: FileSystemNode = index.data(Qt.UserRole)
        node.cluster = True
        count, childs = node.get_cluster_count()
        for child in childs:
            self.db.commit(child)
        self.db.commit(node)
        self.CommitedModel.add_element(node)
        self.FileSystemModel.layoutChanged.emit()
        self.CommitedModel.layoutChanged.emit()

    def load_images_from_folder(self, index):

        self.ImageViewerModel.load_images_from_folder(index.internalPointer())

    def Cluster(self, items: list, dir: QModelIndex, cluster_number):
        start = time.time()
        map = {}
        node: FileSystemNode = dir
        dir_name = node.name
        ready_clusters = [element for element in node.children if element.cluster and not element.commited]
        for i, cluster in enumerate(ready_clusters):
            map[i] = cluster
        if node is not None:
            for i in range(len(ready_clusters), cluster_number):
                cluster_node = FileSystemNode(dir_name + "-" + str(i), "-", node, True)
                cluster_node.color_id = i
                map[i] = cluster_node
                node.add_child(cluster_node)
        clusters = [[] for _ in range(cluster_number + 1)]  # Create k empty lists to hold the items
        for item in items:
            cluster = item.cluster
            if cluster is not None and 0 <= cluster < cluster_number:
                node2 = item.node
                node2.parent.remove_images(node2)
                node2.parent = map[item.cluster]
                clusters[cluster].append(node2)
        for i in range(0, cluster_number):
            map[i].add_image(clusters[i])
        print(f"File System Clusters : {time.time() - start}")
        self.db.cluster(node, map, cluster_number)
        print(time.time() - app.cfg.Configuration.time)
        self.delete_empty_clusters(dir)
        self.FileSystemModel.layoutChanged.emit()
        pass

    # TODO Move to model IDK WHAT THSI CODE IS AND I HAVE WRITTEN IT XD
    def delete_empty_clusters(self, dir):
        lista = []
        for inner_child in dir.children:
            if  inner_child.combined_children() == 0 and (inner_child.commited == 0 or inner_child.commited is None):
                lista.append(inner_child)
        dir.remove_child(lista)

    # TODO Move to model DEPRECIATED
    def remove_recursion(self, dir):
        list = []
        for inner_child in dir.children:
            if inner_child.cluster and inner_child.commited == 0:
                self.remove_recursion(inner_child)
                list.append(inner_child)
        for i in list:
            dir.remove_child(i)
        self.db.delete_cluster(dir)

    def merge(self, nodes: typing.List['FileSystemNode'], recursive=True, parent=None):
        # Build new node if necessary
        name = "Merged" if recursive else "Combined"
        if parent is None:
            parent = FileSystemNode(name, "-", self.FileSystemModel.get_root_node(), True, False)
            self.db.persist_new_node(parent)
            self.FileSystemModel.get_root_node().add_child(parent)
        # Recursive handling
        if recursive :
            nodes_set = set()
            for node in nodes:
                nodes_set.add(node)
                _,childs  = node.get_cluster_count()
                for child in childs:
                    nodes_set.add(child)
            image_list = []
            for child in nodes_set:
                image_list.extend(child.get_images())
                child.clear_images()
            parent.add_image(image_list)
            self.db.update_parent(image_list, parent)
            to_delete = [element for element in nodes_set if nodes_set != parent]
            self.db.delete_clusters(to_delete)
            self.FileSystemModel.layoutChanged.emit()
            self.ImageViewerModel.layoutChanged.emit()
        else:
            for node1, node2 in itertools.combinations(nodes,2):
                if node1.is_in_parent(node2) or node2.is_in_parent(node1):
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Critical)
                    msg.setText("Error")
                    msg.setInformativeText(f"Nodes {node1.name} and {node2.name} have a parent-child relationship. Operation not performed")
                    msg.setWindowTitle("Error")
                    msg.exec_()  # Display the message box
                    return

            if parent in nodes:
                nodes.remove(parent)
            image_list = []
            node_list = []
            for node in nodes:
                image_list.extend(node.get_images())
                node.clear_images()
                node_list.extend(node.children)
                node.clear_childs()
            parent.add_image(image_list)
            parent.add_child(node_list)
            self.db.update_parent(image_list, parent)
            self.db.update_parent(node_list, parent)
            to_delete = [element for element in nodes if nodes != parent]
            self.db.delete_clusters(to_delete)
            self.FileSystemModel.layoutChanged.emit()
            self.ImageViewerModel.layoutChanged.emit()
    def Build_new_cluster(self, images , parent):
        if parent is None:
            for img in images:
                self.ImageViewerModel.remove(img)
        images = [element.node for element in images]
        ### Construct new Node
        if parent is None:
            parent = self.FileSystemModel.get_root_node()
        new_parent = FileSystemNode("CustomNode", "-", parent, True, False)
        self.db.persist_new_node(new_parent)
        parent.add_child(new_parent)
        ### add images
        for img in images:
            self.change_parent(img,new_parent)
        ### update database
        self.db.update_parent(images,new_parent)
        self.FileSystemModel.layoutChanged.emit()
        self.ImageViewerModel.layoutChanged.emit()

    def change_parent(self, img: 'Image', new_parent : 'FileSystemNode'):
        img.parent.remove_images(img)
        new_parent.add_image(img)


