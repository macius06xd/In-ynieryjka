import os
import sys
import time
from typing import List

import h5py
import Configuration
import numpy as np
from sklearn.cluster import KMeans
from KMeansParameters import KMeansParameters

# Forward declaration of PixmapItem
class PixmapItem:
    pass


class Cluster:
    def __init__(self, items: List[PixmapItem], clusters):
        self.vector_file = h5py.File(Configuration.VECTORS_PATH, 'r')
        self.items = items
        self.clusters = clusters
        self.data_array = None
        self.data_list = None
        self.perform()

    def set_clusters(self, clusters: int, items: List[PixmapItem]):
        self.clusters = clusters
        if self.items != items:
            self.items = items
            self.perform()
        self.fit()

    def perform(self):
        start = time.time()

        # Preallocate data_list
        self.data_list = [(None, None)] * len(self.items)
        array_size = 0
        print(len(self.items))
        for i, item in enumerate(self.items):

            file_path = item.get_path()
            file_name2, file_extension = os.path.splitext(os.path.basename(file_path))
            file_name2 = file_name2.replace("_small", "")
            file_name = file_name2 + file_extension
            second_folder_name = os.path.basename(os.path.dirname(file_path))
            # TODO load data if not in vector
            data = self.vector_file.get(file_name,None)
            if data is not None:
                data = data[:]
                self.data_list[array_size] = (item, data)  # Store item-data pair in the preallocated list
                array_size += 1
            else:
                item.cluster = self.clusters+1
        self.data_list = self.data_list[:array_size]
        print(len(self.data_list))
        # Create a numpy array directly from data_list
        self.data_array = np.array([data for _, data in self.data_list], dtype='double')
        print(f"Time of clusterization : {time.time() - start}")

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
        kmeans.fit(self.data_array)
        second_elements = [item[1] for item in self.data_list]
        item_clusters = kmeans.predict(second_elements)
        for item, cluster in zip(self.data_list, item_clusters):
            item[0].cluster = cluster
        print(f"Time of clusterization fit2 : {time.time() - start}")
