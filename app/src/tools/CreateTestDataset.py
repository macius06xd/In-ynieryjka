import os
import shutil
from concurrent.futures import ThreadPoolExecutor

def copy_images(source_folder, destination_folder, limit=10000):
    # Tworzymy folder docelowy, jeśli nie istnieje
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)

    def copy_file(file_path):
        file_name = os.path.basename(file_path)
        destination_path = os.path.join(destination_folder, file_name)

        # Pomijamy plik, jeśli już istnieje w folderze docelowym
        if os.path.exists(destination_path):
            print(f"Pominięto: {file_name}")
            return

        # Kopiujemy plik do folderu docelowego
        shutil.copy2(file_path, destination_path)
        print(f"Skopiowano: {file_name}")

    # Lista plików do skopiowania
    files_to_copy = []

    # Przechodzimy przez pliki w podfolderach, dodając je do listy
    for root, _, files in os.walk(source_folder):
        for file in files:
            files_to_copy.append(os.path.join(root, file))

    # Ograniczamy liczbę plików do skopiowania do wartości limit
    files_to_copy = files_to_copy[:limit]

    # Kopiujemy pliki przy użyciu wielowątkowości
    with ThreadPoolExecutor() as executor:
        executor.map(copy_file, files_to_copy)

if __name__ == "__main__":
    # Source folder to ten oryginalny gdzie jest lego->Bricks,Plates itd. -> 3332, 3432, 3212 itd.
    source_folder = r"C:\Users\wojte\OneDrive\Pulpit\pulpit\klocki"
    # Tutaj bedzie 10k zdjec
    destination_folder = r"C:\Users\wojte\OneDrive\Pulpit\pulpit\testowy"
    copy_images(source_folder, destination_folder, limit=10000)
