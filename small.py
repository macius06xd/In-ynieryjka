import os
import cv2
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def resize_image(input_path, output_path):
    try:
        img = cv2.imread(input_path)
        resized_img = cv2.resize(img, (64, 64), interpolation=cv2.INTER_AREA)
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


if __name__ == "__main__":
    input_folder = "C:/Users/wojte/OneDrive/Pulpit/klockilego/klocki"
    output_folder = "C:/Users/wojte/OneDrive/Pulpit/klockilego/klockismall"

    create_new_folder_and_resize_images(input_folder, output_folder)