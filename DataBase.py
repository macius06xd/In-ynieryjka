import os
import sqlite3
import Configuration
from typing import TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from FileSystem import FileSystemNode


class Mapper:
    pass


class DataBaseConnection:
    def __init__(self):
        self.db_path = os.path.join(Configuration.INITIAL_CLUSTERIZED_FOLDER, "Database.db")
        self.connection = sqlite3.connect(self.db_path)
        self.connection.execute("PRAGMA foreign_keys = 1")  # Enable foreign key support
        self.cursor = self.connection.cursor()
        self._create_file_system_table()

    def _create_file_system_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS file_system (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            path TEXT,
            isCluster INTEGER,
            parent_id INTEGER,
            FOREIGN KEY (parent_id) REFERENCES file_system (id)
        );
        """
        self.cursor.execute(query)
        self.connection.commit()

    def build_database_(self, root_node: 'FileSystemNode'):
        self.cursor.execute("DELETE FROM file_system")
        self._store_node(root_node, parent_id=None)
        self.connection.commit()

    def rebuild_file_system_model(self):
        self.cursor.execute("SELECT * FROM file_system WHERE parent_id IS NULL")
        file_system_data = self.cursor.fetchone()
        root_node = self._rebuild_node(file_system_data)
        return root_node

    def _rebuild_node(self, data, parent_id=None,parent = None):
        from FileSystem import FileSystemNode
        node = FileSystemNode(data[1], data[2], parent, data[3])
        if not data[1].endswith("jpg"):
            query = "SELECT * FROM file_system WHERE parent_id = ?"
            self.cursor.execute(query, (data[0],))
            children_data = self.cursor.fetchall()

            for child_data in children_data:
                child_node = self._rebuild_node(child_data, data[0],node)
                node.add_child(child_node)

        return node

    def _store_node(self, node: 'FileSystemNode', parent_id=None):
        query = "INSERT INTO file_system (name, path, isCluster, parent_id) VALUES (?, ?, ?, ?)"
        self.cursor.execute(query, (node.name, node.path, node.cluster, parent_id))
        node_id = self.cursor.lastrowid

        for child in node.children:
            self._store_node(child, parent_id=node_id)

        self.connection.commit()


    def cluster(self, parent_node: 'FileSystemNode', clusters: Dict[int, 'FileSystemNode'], cluster_number: int):
        # Delete all values with parent as parent_node (search by name)
        parent_name = parent_node.name
        parent_id = self.get_node_id_by_name(parent_name)
        self.cursor.execute("DELETE FROM file_system WHERE parent_id = ?", (parent_id,))
        self.connection.commit()

        # Create database records for parent_node's children and save their IDs
        child_ids = []
        for child_node in parent_node.children:
            self.cursor.execute("INSERT INTO file_system (name, path, isCluster, parent_id) VALUES (?, ?, ?, ?)",
                                (child_node.name, child_node.path, 1, parent_id))
            self.connection.commit()
            child_id = self.cursor.lastrowid
            child_ids.append(child_id)

        # Create database records for children from the clusters dictionary, using the saved child IDs
        for cluster_id, cluster_node in clusters.items():
            cluster_parent_id = child_ids[cluster_id]
            for child_node in cluster_node.children:
                self.cursor.execute(
                    "INSERT INTO file_system (name, path, isCluster, parent_id) VALUES (?, ?, ?, ?)",
                    (child_node.name, child_node.path, 0, cluster_parent_id))
                self.connection.commit()

    def cluster(self, parent_node: 'FileSystemNode', clusters: Dict[int, 'FileSystemNode'], cluster_number: int):
        # Check if there are clusters (entries with isCluster = 1 having parent_node as parent)
        parent_id = self.get_node_id_by_name(parent_node.name)
        self.cursor.execute("SELECT id, name FROM file_system WHERE isCluster = 1 AND parent_id = ?",
                            (parent_id,))
        cluster_entries = self.cursor.fetchall()

        if cluster_entries:
            # Create a dictionary to map cluster names to their corresponding IDs
            cluster_id_map = {entry[1]: entry[0] for entry in cluster_entries}

            # Update child IDs to match the correct clusters
            for cluster_node in clusters.values():
                cluster_parent_name = cluster_node.name
                cluster_parent_id = cluster_id_map[cluster_parent_name]

                for child_node in cluster_node.children:
                    child_id = self.get_node_id_by_name(child_node.name)
                    self.cursor.execute("UPDATE file_system SET parent_id = ? WHERE id = ?",
                                        (cluster_parent_id, child_id))
                    self.connection.commit()

            # Delete clusters with no children
            self.cursor.execute("DELETE FROM file_system WHERE isCluster = 1 AND parent_id = ? AND id NOT IN "
                                "(SELECT DISTINCT parent_id FROM file_system)",
                                (parent_id,))
            self.connection.commit()

        else:
            # Delete all values with parent as parent_node (search by name)
            parent_name = parent_node.name
            parent_id = self.get_node_id_by_name(parent_name)
            self.cursor.execute("DELETE FROM file_system WHERE parent_id = ?", (parent_id,))
            self.connection.commit()

            # Create database records for parent_node's children and save their IDs
            child_ids = []
            for child_node in parent_node.children:
                self.cursor.execute("INSERT INTO file_system (name, path, isCluster, parent_id) VALUES (?, ?, ?, ?)",
                                    (child_node.name, child_node.path, 1, parent_id))
                self.connection.commit()
                child_id = self.cursor.lastrowid
                child_ids.append(child_id)

            # Create database records for children from the clusters dictionary, using the saved child IDs
            for cluster_id, cluster_node in clusters.items():
                cluster_parent_id = child_ids[cluster_id]
                for child_node in cluster_node.children:
                    self.cursor.execute(
                        "INSERT INTO file_system (name, path, isCluster, parent_id) VALUES (?, ?, ?, ?)",
                        (child_node.name, child_node.path, 0, cluster_parent_id))
                    self.connection.commit()

    def get_node_id_by_name(self, name: str) -> int:
        self.cursor.execute("SELECT id FROM file_system WHERE name = ?", (name,))
        row = self.cursor.fetchone()
        if row:
            return row[0]
        else:
            return -1