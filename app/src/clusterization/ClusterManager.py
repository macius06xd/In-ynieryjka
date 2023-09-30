import time
import typing

from PyQt5.QtCore import QModelIndex, Qt
from PyQt5.QtWidgets import QInputDialog, QMessageBox

import app.cfg.Configuration
from app.src.gui.CommitedLayout import CommitedFolderListModel
from app.src.database.DataBase import DataBaseConnection
from app.src.gui.ImageViewer import MyListModel
from app.src.file_system.FileSystem import FileSystemModel, FileSystemNode


# every operations on the clusters should be perfomed here
# Widget -> ClusterManager -> Database
# TODO move initialization (Creating database,loading database) here
# TODO Add Clusterization logic here
class ClusterManager:
    ImageViewerModel: MyListModel = None
    FileSystemModel: FileSystemModel = None
    CommitedModel: CommitedFolderListModel = None
    db: DataBaseConnection = DataBaseConnection()

    def setImageViewerModel(self, model):
        self.ImageViewerModel = model

    def setFileSystemModel(self, model):
        self.FileSystemModel = model

    def setCommitedModel(self, model):
        self.CommitedModel = model

    def renameCluster(self, index: QModelIndex, new_name: str):
        self.db.renamefile(new_name, index.data().id)
        index.internalPointer().name = new_name

    def get_commited(self):
        return self.CommitedModel.get_data()

    def clusterCombine(self, source, target):

        # User selected an item
        self.uncommit(source)
        if target:
            files = [item for item in self.ImageViewerModel.listdata if item.node.parent == source]
            is_view = files[0].node.is_in_parent(self.ImageViewerModel.dir)
            for file in files:
                if is_view:
                    self.ImageViewerModel.remove(file)
                file.node.parent = target
            source.clear_childs()
            target.add_child([element.node for element in files])
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
        self.ImageViewerModel.load_images_from_folder(index)

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
                node2: FileSystemNode = item.node
                node2.parent.remove_child(node2)
                node2.parent = map[item.cluster]
                clusters[cluster].append(node2)
        for i in range(0, cluster_number):
            map[i].add_child(clusters[i])
        print(f"File System Clusters : {time.time() - start}")
        self.db.cluster(node, map, cluster_number)
        print(time.time() - app.cfg.Configuration.time)
        self.delete_empty_clusters(dir)
        self.FileSystemModel.layoutChanged.emit()
        pass

    # TODO Move to model
    def delete_empty_clusters(self, dir):
        child_clusters = [element for element in dir.children if element.cluster]
        for child in child_clusters:
            list = []
            for inner_child in child.children:
                if inner_child.cluster and inner_child.commited == 0:
                    self.remove_recursion(inner_child)
                    list.append(inner_child)
            for i in list:
                child.remove_child(i)

    # TODO Move to model
    def remove_recursion(self, dir):
        list = []
        for inner_child in dir.children:
            if inner_child.cluster and inner_child.commited == 0:
                self.remove_recursion(inner_child)
                list.append(inner_child)
        for i in list:
            dir.remove_child(i)
        self.db.delete_cluster(dir)

    def merge(self, nodes: typing.List['FileSystemNode']):
        # Build list of nodes to transfer
        cluster_set = set()
        for node in nodes:
            cluster_set.add(node)
            _, childs = node.get_cluster_count()
            self.CommitedModel.remove_element(node)
            for child in childs:
                cluster_set.add(child)
                self.CommitedModel.remove_element(child)
        # Create new cluster
        new_node = FileSystemNode("Merged", "-", self.FileSystemModel.get_root_node(), True, False)
        self.db.persist_new_node(new_node)
        self.FileSystemModel.get_root_node().add_child(new_node)
        # Build File List
        # TODO nie budować tylko podać liste nodów
        node_list = list()
        for node in cluster_set:
            for child in node.children:
                node_list.append(child)
        for node in cluster_set:
            node.clear_childs()
        # Update Tree and Database
        new_node.add_child(node_list)
        self.db.update_parent(node_list, new_node)
        self.FileSystemModel.layoutChanged.emit()
        self.ImageViewerModel.layoutChanged.emit()
