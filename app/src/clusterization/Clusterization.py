import os
import sys
import time
from typing import List

import h5py
from app.cfg.Configuration import VECTORS_PATH
import numpy as np
from sklearn.cluster import KMeans, dbscan, DBSCAN

import app.src.vectors.VectorFixWindow
from app.src.clusterization.kmeans.KMeansParameters import KMeansParameters

# Forward declaration of PixmapItem
class PixmapItem:
    pass


class Cluster:
    def __init__(self, items: List[PixmapItem], clusters,remove_signal):
        self.vector_file = h5py.File(VECTORS_PATH, 'r')
        self.items = items
        self.clusters = clusters
        self.data_array = None
        self.data_list = None
        self.broken_vectors = []
        self.remove_signal = remove_signal
        self.error = False
        self.rev = True
        self.perform()
        if len(self.broken_vectors) != 0:
            window = app.src.vectors.VectorFixWindow.FileActionWindow(self.broken_vectors,self.remove_signal,self.data_list)
            window.exec_()
    def Reevaluate(self):
        self.rev = True
        self.data_array = None
        self.data_list = None
    def set_clusters(self, clusters: int, items: List[PixmapItem]):
        self.clusters = clusters
        if self.rev:
            self.rev = False
            self.items = items
            self.perform()
            if len(self.broken_vectors) != 0:
                window = app.src.vectors.VectorFixWindow.FileActionWindow(self.broken_vectors, self.remove_signal, self.data_list)
                code = window.exec_()
                if code == 42:
                    return
        self.fit()

    def perform(self):
        start = time.time()
        self.broken_vectors = []
        self.data_array = []  # Initialize as a list
        array_size = 0
        for i, item in enumerate(self.items):
            file_path = item.get_path()
            file_name2, file_extension = os.path.splitext(os.path.basename(file_path))
            file_name2 = file_name2.replace("_small", "")
            file_name = file_name2 + file_extension
            second_folder_name = os.path.basename(os.path.dirname(file_path))

            data = self.vector_file.get(file_name, None)
            if data is not None:
                data = data[:]  # Ensure data is in the correct format
                self.data_array.append(data)  # Append data directly to the list
            else:
                print("Brakuje vektorka")
                self.error = True
                self.broken_vectors.append(item)

        self.data_array = np.array(self.data_array, dtype='double')  # Convert the list to numpy array
        print(f"Time of clusterization: {time.time() - start}")

    def fit(self):
        start = time.time()
        kmeans_params = KMeansParameters()
        kmeans = KMeans(
            n_clusters=self.clusters,
            init=kmeans_params.init,
            n_init=kmeans_params.n_init,
            max_iter=kmeans_params.max_iter,
            tol=kmeans_params.tol,
            random_state=kmeans_params.random_state,
        )
        if self.data_array.size != 0:
            kmeans.fit(self.data_array)
            item_clusters = kmeans.labels_
            for item, cluster in zip(self.items, item_clusters):
                item.cluster = cluster
        print(f"Time of clusterization fit: {time.time() - start}")