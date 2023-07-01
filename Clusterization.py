import os
from typing import List

import h5py
import Configuration
import numpy as np
from sklearn.cluster import KMeans


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

    def set_clusters(self, clusters:int, items: List[PixmapItem]):
        self.clusters = clusters
        if self.items != items:
            self.items = items
            self.perform()
        self.fit()
    def perform(self):
        kmeans = KMeans(n_clusters=self.clusters)

        # Preallocate data_list
        self.data_list = [(None, None)] * len(self.items)

        for i, item in enumerate(self.items):
            file_path = item.get_path()
            file_name2, file_extension = os.path.splitext(os.path.basename(file_path))
            file_name2 = file_name2.replace("_small", "")
            file_name = file_name2 + file_extension
            second_folder_name = os.path.basename(os.path.dirname(file_path))
            #TODO load data if not in vector
            data = self.vector_file[file_name][:]
            self.data_list[i] = (item, data)  # Store item-data pair in the preallocated list

        # Create a numpy array directly from data_list
        self.data_array = np.array([data for _, data in self.data_list], dtype='double')

    def fit(self):
        kmeans = KMeans(n_clusters=self.clusters)
        kmeans.fit(self.data_array)

        for item, data in self.data_list:
            # Convert data to dtype 'double' before predicting
            item.cluster = kmeans.predict(data.astype('double').reshape(1, -1))[0]
