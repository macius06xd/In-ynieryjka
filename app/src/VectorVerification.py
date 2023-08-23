import h5py

from app.cfg.Configuration import VECTORS_PATH, DEFAULT_IMAGES_PATH

import os
def verify_vectors():
    vector_file = h5py.File(VECTORS_PATH, 'r')
    file_path = DEFAULT_IMAGES_PATH
    paths = vector_file.keys()
    print(vector_file.get("0lDm_Bs5_1620809531797.jpg"))
    for value in paths:
        if value  not in paths:
            print (value)


if __name__ == "__main__":
    verify_vectors()