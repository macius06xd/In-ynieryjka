import os
import shutil
from sklearn.cluster import KMeans
import h5py
import numpy as np
from Configuration import INITIAL_IMAGES_FOLDER, VECTORS_PATH, INITIAL_CLUSTERIZED_FOLDER

def load_feature_vectors(vectors_path, image_files):
    with h5py.File(vectors_path, 'r') as f:
        vectors = []
        for img in image_files:
            for key in f.keys():
                if img in f[key]:
                    vectors.append(f[key][img][:])
                    break
        return vectors

def perform_clustering(images_folder, vectors_path, clusterized_folder, n_clusters):
    image_files = os.listdir(images_folder)
    image_files = [img for img in image_files if img.endswith(".jpg")]

    feature_vectors = load_feature_vectors(vectors_path, image_files)

    kmeans = KMeans(n_clusters=n_clusters)
    kmeans.fit(feature_vectors)

    labels = kmeans.labels_

    for img, label in zip(image_files, labels):
        dest_folder = os.path.join(clusterized_folder, f'Cluster_{label}')  # change here
        os.makedirs(dest_folder, exist_ok=True)
        shutil.copy(os.path.join(images_folder, img), os.path.join(dest_folder, img))

if __name__ == "__main__":
    perform_clustering(INITIAL_IMAGES_FOLDER, VECTORS_PATH, INITIAL_CLUSTERIZED_FOLDER, no_of_clusters)
