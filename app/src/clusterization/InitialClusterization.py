import os
import shutil
from PyQt5.QtCore import pyqtSignal, QThread
from sklearn.cluster import KMeans
import h5py
import numpy as np
from sklearn.cluster import MiniBatchKMeans

import app.cfg.Configuration
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

    def load_feature_vectors_batch(self, vectors_path, image_files, batch_size):
        with h5py.File(vectors_path, 'r') as f:
            for i in range(0, len(image_files), batch_size):
                batch_files = image_files[i:i + batch_size]
                vectors = []
                for img in batch_files:
                    try:
                        values = f[img][:]
                        vectors.append(values)
                    except:
                        continue
                yield vectors, batch_files

    def run(self):
        print("Starting")
        print_memory_usage()
        image_files = os.listdir(self.images_folder)
        image_files = [img for img in image_files if img.endswith(".jpg")]
        count = 0
        batch_size = app.cfg.Configuration.BATCH_SIZE

        kmeans_params = KMeansParameters()
        kmeans = MiniBatchKMeans(
            n_clusters=self.n_clusters,
            init=kmeans_params.init,
            n_init=kmeans_params.n_init,
            max_iter=kmeans_params.max_iter,
            tol=kmeans_params.tol,
            random_state=kmeans_params.random_state,
        )

        for feature_vectors, batch_files in self.load_feature_vectors_batch(self.vectors_path, image_files, batch_size):
            kmeans.partial_fit(feature_vectors)
            labels = kmeans.predict(feature_vectors)

            for img, label in zip(batch_files, labels):
                dest_folder = os.path.join(self.clusterized_folder, f'Cluster_{label}')
                os.makedirs(dest_folder, exist_ok=True)
                shutil.copy(os.path.join(self.images_folder, img), os.path.join(dest_folder, img))
                count += 1
                self.progress_updated.emit(int(count / len(image_files) * 100))

        print_memory_usage()
