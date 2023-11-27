import os
import shutil
from PyQt5.QtCore import pyqtSignal, QThread
from sklearn.cluster import KMeans
import h5py
import numpy as np

from app.cfg.Configuration import print_memory_usage
# Import the KMeansParameters class
from app.src.clusterization.kmeans.KMeansParameters import KMeansParameters

def load_feature_vectors(vectors_path, image_files):
    with h5py.File(vectors_path, 'r') as f:
        vectors = []
        for img in image_files:
            try:
                values = f[img][:]
                vectors.append(values)
                continue
            except:
                image_files.remove(img)
                continue
        return vectors

class ClusteringThread(QThread):
    progress_updated = pyqtSignal(int)

    def __init__(self, images_folder, vectors_path, clusterized_folder, n_clusters):
        super().__init__()
        self.images_folder = images_folder
        self.vectors_path = vectors_path
        self.clusterized_folder = clusterized_folder
        self.n_clusters = n_clusters

    def run(self):
        print("zaczynam")
        print_memory_usage()
        image_files = os.listdir(self.images_folder)
        image_files = [img for img in image_files if img.endswith(".jpg")]
        count = 0
        feature_vectors = load_feature_vectors(self.vectors_path, image_files)

        # Use KMeansParameters
        kmeans_params = KMeansParameters()
        kmeans = KMeans(
            n_clusters=self.n_clusters,
            init=kmeans_params.init,
            n_init=kmeans_params.n_init,
            max_iter=kmeans_params.max_iter,
            tol=kmeans_params.tol,
            random_state=kmeans_params.random_state,
        )
        print("MAX ITERACJI", kmeans_params.max_iter)

        kmeans.fit(feature_vectors)
        labels = kmeans.labels_

        for img, label in zip(image_files, labels):
            dest_folder = os.path.join(self.clusterized_folder, f'Cluster_{label}')
            os.makedirs(dest_folder, exist_ok=True)
            shutil.copy(os.path.join(self.images_folder, img), os.path.join(dest_folder, img))
            count = count + 1
            self.progress_updated.emit(int(count/len(image_files)*100))
        print_memory_usage()

