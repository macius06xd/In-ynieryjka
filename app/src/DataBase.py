import os
import sqlite3
import time

import app.cfg.Configuration
from app.cfg.Configuration import INITIAL_CLUSTERIZED_FOLDER
from typing import TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from app.src.FileSystem import FileSystemNode
from app.src.KMeansParameters import KMeansParameters

class Mapper:
    pass


class DataBaseConnection:
    def __init__(self):
        self.kmeans_params = KMeansParameters()
        self.db_path = os.path.join(INITIAL_CLUSTERIZED_FOLDER, "Database.db")
        self.connection = sqlite3.connect(self.db_path)
        self.connection.execute("PRAGMA foreign_keys = 1")  # Enable foreign key support
        self.cursor = self.connection.cursor()
        self._create_file_system_table()
        self._create_file_table()
        self._create_kmeans_parameters_table()


    def _create_file_system_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS file_system (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, 
            path TEXT,
            isCluster INTEGER,
            parent_id INTEGER,
            commited INTEGER,
            color_id INTEGER,
            FOREIGN KEY (parent_id) REFERENCES file_system (id)
        );
        """
        self.cursor.execute(query)
        self.connection.commit()

    def _create_file_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS file (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            path TEXT,
            parent_id INTEGER,
            FOREIGN KEY (parent_id) REFERENCES file_system (id)
        );
        """
        self.cursor.execute(query)
        self.connection.commit()

    def build_database_(self, root_node: 'FileSystemNode'):
        self.cursor.execute("DELETE FROM file")
        self.cursor.execute("DELETE FROM file_system")
        self._store_node(root_node, parent_id=None)
        self.connection.commit()

    # Function use to load file_structure
    def rebuild_file_system_model(self):
        self.load_kmeans_parameters()
        self.cursor.execute("SELECT * FROM file_system WHERE parent_id IS NULL")
        file_system_data = self.cursor.fetchone()
        root_node = self._rebuild_node(file_system_data)
        return root_node

    def _create_kmeans_parameters_table(self):
        query = """
          CREATE TABLE IF NOT EXISTS kmeans_parameters (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              init TEXT,
              n_init INTEGER,
              max_iter INTEGER,
              tol REAL,
              random_state INTEGER,
              precompute_distances INTEGER,
              algorithm TEXT,
              n_jobs INTEGER,
              verbose INTEGER
          );
          """
        self.cursor.execute(query)
        self.connection.commit()

    def load_kmeans_parameters(self):
        self.cursor.execute("SELECT * FROM kmeans_parameters")
        row = self.cursor.fetchone()
        if row:
            (id, init, n_init, max_iter, tol, random_state, precompute_distances, algorithm, n_jobs, verbose) = row
            self.kmeans_params.init = init
            self.kmeans_params.n_init = n_init
            self.kmeans_params.max_iter = max_iter
            self.kmeans_params.tol = tol
            self.kmeans_params.random_state = random_state
            self.kmeans_params.precompute_distances = precompute_distances
            self.kmeans_params.algorithm = algorithm
            self.kmeans_params.n_jobs = n_jobs
            self.kmeans_params.verbose = verbose

    def save_kmeans_parameters(self):
        query = """
           INSERT INTO kmeans_parameters (init, n_init, max_iter, tol, random_state, precompute_distances, algorithm, n_jobs, verbose)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
           """
        self.cursor.execute(query, (self.kmeans_params.init, self.kmeans_params.n_init, self.kmeans_params.max_iter,
                                    self.kmeans_params.tol, self.kmeans_params.random_state,
                                    self.kmeans_params.precompute_distances, self.kmeans_params.algorithm,
                                    self.kmeans_params.n_jobs, self.kmeans_params.verbose))
        self.connection.commit()
    # Building a single node
    def _rebuild_node(self, data, parent_id=None, parent=None):
        from app.src.FileSystem import FileSystemNode
        node = None

        # Check if data is not an image
        if not data[1].endswith("jpg"):
            node = FileSystemNode(data[1], data[2], parent, data[3], data[5], data[6])
            node.id = data[0]
            query = "SELECT * FROM file_system WHERE parent_id = ?"
            self.cursor.execute(query, (data[0],))
            children_data = self.cursor.fetchall()

            ## Recursively build child nodes
            for child_data in children_data:
                child_node = self._rebuild_node(child_data, data[0], node)
                node.add_child(child_node)
        else:
            node = FileSystemNode(data[1], data[2], parent, data[3], data[5], data[6])
            node.id = data[0]

        # Retrieve files within the current node (folder)
        query = "SELECT * FROM file WHERE parent_id = ?"
        self.cursor.execute(query, (data[0],))
        files_data = self.cursor.fetchall()

        for file_data in files_data:
            file_node = FileSystemNode(file_data[1], file_data[2], node)
            file_node.id = file_data[0]
            node.add_child(file_node)

        return node

    def _store_node(self, node: 'FileSystemNode', parent_id=None):
        if node.name.endswith("jpg"):
            query = "INSERT INTO file (name, path, parent_id) VALUES (?, ?, ?)"
            self.cursor.execute(query, (node.name, node.path, parent_id))
            file_id = self.cursor.lastrowid
        else:
            query = "INSERT INTO file_system (name, path, isCluster, parent_id, commited, color_id) VALUES (?, ?, ?, ?, ?, ?)"
            self.cursor.execute(query, (node.name, node.path, node.cluster, parent_id, 0, node.color_id))
            file_id = self.cursor.lastrowid

        node.id = file_id
        for child in node.children:
            self._store_node(child, parent_id=file_id)

        self.connection.commit()

    ## Function used to Build Cluster in database Dont Touch (when i wrote this god and me know what's going on, now only god knows)
    ## Na serio nie dotykac
    def cluster(self, parent_node: 'FileSystemNode', clusters: Dict[int, 'FileSystemNode'], cluster_number: int):
        start_time = time.time()

        # Check if there are clusters (entries with isCluster = 1 having parent_node as parent)
        parent_id = self.get_node_id_by_name(parent_node.name)
        self.cursor.execute(
            "SELECT id, name FROM file_system WHERE isCluster = 1 AND parent_id = ? AND (commited IS NULL OR commited <> 1)",
            (parent_id,))
        cluster_entries = self.cursor.fetchall()

        if cluster_entries:
            # Create a dictionary to map cluster names to their corresponding IDs
            cluster_id_map = {entry[1]: entry[0] for entry in cluster_entries}

            # Update child IDs to match the correct clusters
            for cluster_node in clusters.values():
                for child_node in cluster_node.children:
                    if child_node.parent.name in cluster_id_map:
                        parent_id_ = cluster_id_map[child_node.parent.name]
                    else:
                        # Create a new cluster in the database
                        self.cursor.execute(
                            "INSERT INTO file_system (name, path, isCluster, parent_id, color_id) VALUES (?, ?, ?, ?, ?)",
                            (child_node.parent.name, child_node.parent.path, 1, parent_id, child_node.color_id))
                        self.connection.commit()
                        parent_id_ = self.cursor.lastrowid
                        cluster_id_map[child_node.parent.name] = parent_id_

                    self.cursor.execute("UPDATE file SET parent_id = ? WHERE id = ?",
                                        (parent_id_, child_node.id))
                    child_node.parent.id = parent_id_
            self.connection.commit()

            cluster_time = time.time() - start_time
            print(f"Cluster Update Time: {cluster_time} seconds")
        else:
            start_time = time.time()

            # Get the parent ID and name
            parent_name = parent_node.name
            parent_id = self.get_node_id_by_name(parent_name)

            # Step 2: Create database records for parent_node's children and save their IDs
            child_ids = []
            for child_node in parent_node.children:
                if child_node.name.endswith("jpg"):
                    self.cursor.execute("INSERT INTO file (name, path, parent_id) VALUES (?, ?, ?)",
                                        (child_node.name, child_node.path, parent_id))
                else:
                    iden = self.cursor.execute(
                        "INSERT INTO file_system (name, path, isCluster, parent_id, color_id) VALUES (?, ?, ?, ?, ?)",
                        (child_node.name, child_node.path, 1, parent_id, child_node.color_id))
                    child_node.id = iden
                child_id = self.cursor.lastrowid
                child_ids.append(child_id)
            self.connection.commit()
            create_children_time = time.time() - start_time
            print(f"Creating Children Time: {create_children_time} seconds")

            start_time = time.time()


            # Step 3: Update the parent for each child node to the correct cluster
            for cluster_id, cluster_node in clusters.items():
                cluster_parent_id = child_ids[cluster_id]
                cluster_node.id = cluster_parent_id

                for child_node in cluster_node.children:
                    try :
                        self.cursor.execute(
                            "UPDATE file SET parent_id = ? WHERE id = ?",
                            (cluster_parent_id, child_node.id))
                    except:
                        print (child_node)

            self.connection.commit()
            update_clusters_time = time.time() - start_time
            print(f"Updating Clusters Time: {update_clusters_time} seconds")

            total_time = create_children_time + update_clusters_time
            print(f"Total Time: {total_time} seconds")

    def delete_cluster(self,node):
        self.cursor.execute("DELETE FROM file_system WHERE id = ?", (node.id,))
        self.connection.commit()

    def get_node_id_by_name(self, name: str) -> int:
        self.cursor.execute("SELECT id FROM file_system WHERE name = ?", (name,))
        row = self.cursor.fetchone()
        if row:
            return row[0]
        else:
            return -1

    def commit(self, node: 'FileSystemNode'):
        self.cursor.execute("UPDATE file_system set commited = 1 WHERE id = ?", (node.id,))
        self.connection.commit()

    def unCommit(self, node: 'FileSystemNode'):
        self.cursor.execute("UPDATE file_system set commited = 0 WHERE id = ?", (node.id,))
        self.connection.commit()

    # Moves file to trash
    def deletefile(self, node: 'FileSystemNode'):
        self.cursor.execute("select id from file_system where name = 'trash'")
        row = self.cursor.fetchone()
        self.cursor.execute("update file set parent_id = ? where id = ? ", (row[0], node.id))
        self.connection.commit()
    def delete_pernaments(self, node: 'FileSystemNode'):
        self.cursor.execute("delete file where id = ? ", node.id)

    def renamefile(self,name,id):
        self.cursor.execute("update file_system set name = ? where id = ?",(name,id))
        self.connection.commit()

    #TODO write some util functions
    def update_parent(self , file_list : list , node : 'FileSystemNode'):
        for file in file_list:
            self.cursor.execute("update file set parent_id = ? where id = ? ",
                           (node.id, file.node.id if hasattr(file, 'node') and hasattr(file.node, 'id') else file.id))

        self.connection.commit()

    def persist_new_node(self,node):
        self.cursor.execute("select id from file_system where parent_id is NULL")
        id = self.cursor.fetchone()[0]
        self._store_node(node,id)

