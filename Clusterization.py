import os
from typing import List

import h5py
import Configuration
import numpy as np
from sklearn.cluster import KMeans




class Cluster:
    from ImageViewer import PixmapItem
    def __init__(self,items:List[PixmapItem],clusters):
        self.vector_file = h5py.File(Configuration.VECTORS_PATH,'r')
        self.items = items
        self.clusters = clusters;
        self.perform()
    def set_clusters(self,clusters):
        self.clusters=clusters

    def perform(self):
        kmeans = KMeans(n_clusters=self.clusters)
        data_list = []  # List to store item-data pairs
        for item in self.items:
            file_path = item.get_path()
            file_name2, file_extension = os.path.splitext(os.path.basename(file_path))
            file_name2 = file_name2.replace("_small", "")
            file_name = file_name2 + file_extension
            second_folder_name = os.path.basename(os.path.dirname(file_path))
            data = self.vector_file[second_folder_name][file_name][:]
            data_list.append((item, data))  # Store item-data pair in the list

        # Extract the data values from data_list and create a 2D array
        data_array = np.array([data for _, data in data_list])
        data_array = data_array.astype('double')
        kmeans.fit(data_array)

        for item, data in data_list:
            # Convert data to dtype 'double' before predicting
            data = data.astype('double')
            item.cluster = kmeans.predict([data])[0]






