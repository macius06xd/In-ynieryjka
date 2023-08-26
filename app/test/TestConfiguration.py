import os, sys

from app.cfg.Configuration import (
    INITIAL_IMAGES_FOLDER,
    INITIAL_CLUSTERIZED_FOLDER,
    DEFAULT_IMAGES_PATH,
    RESIZED_IMAGES_PATH,
    VECTORS_PATH,
    RESULTS_PATH
)

paths_to_check = [
    INITIAL_IMAGES_FOLDER,
    INITIAL_CLUSTERIZED_FOLDER,
    RESIZED_IMAGES_PATH,
    DEFAULT_IMAGES_PATH,
    VECTORS_PATH,
    RESULTS_PATH
]

def check_paths_exist():
    for path in paths_to_check:
        if os.path.exists(path):
            print(f"Path exists: {path}")
        else:
            print(f"Path does not exist: {path}")
            sys.exit()

if __name__ == "__main__":
    check_paths_exist(paths_to_check)