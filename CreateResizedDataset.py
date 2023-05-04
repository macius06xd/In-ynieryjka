import os
import cv2
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from Configuration import DEFAULT_IMAGES_PATH
from Configuration import RESIZED_IMAGES_PATH
from Configuration import RESIZED_IMAGES_SIZE


def resize_image(input_path, output_path):
    try:
        img = cv2.imread(input_path)
        resized_img = cv2.resize(img, (RESIZED_IMAGES_SIZE, RESIZED_IMAGES_SIZE), interpolation=cv2.INTER_AREA)
        cv2.imwrite(output_path, resized_img)
    except Exception as e:
        print(f"Error processing file: {input_path}")
        print(f"Error message: {e}")


def create_new_folder_and_resize_images(input_folder, output_folder):
    with ThreadPoolExecutor() as executor:
        for subdir, dirs, files in os.walk(input_folder):
            for file in files:
                input_path = os.path.join(subdir, file)
                output_subdir = subdir.replace(input_folder, output_folder)
                output_path = os.path.join(output_subdir, file.replace(".", "_small."))

                os.makedirs(output_subdir, exist_ok=True)

                executor.submit(resize_image, input_path, output_path)


def create_resized_dataset():
    input_folder = DEFAULT_IMAGES_PATH
    output_folder = RESIZED_IMAGES_PATH
    create_new_folder_and_resize_images(input_folder, output_folder)