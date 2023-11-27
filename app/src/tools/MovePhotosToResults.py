import sqlite3
import shutil
import os

from app.cfg.Configuration import INITIAL_CLUSTERIZED_FOLDER, RESULTS_PATH, INITIAL_IMAGES_FOLDER

class FileManager:

    @staticmethod
    def copy_files():
        # Połączenie z bazą danych
        conn = sqlite3.connect(os.path.join(INITIAL_CLUSTERIZED_FOLDER, 'Database.db'))
        cursor = conn.cursor()

        # Pobranie informacji o plikach
        cursor.execute("SELECT name, parent_id,path FROM file")
        files = cursor.fetchall()

        for file in files:
            name, parent_id , path = file

            # Pobranie nazwy folderu
            cursor.execute("SELECT name FROM file_system WHERE id = ?", (parent_id,))
            destination_folder_name = cursor.fetchone()[0]

            # Pelna sciezka pliku do skopiowania
            source_file_path = path

            # Sciezka folderu w ktorym bedzie sie znajdowal plik
            destination_folder_path = os.path.join(RESULTS_PATH, destination_folder_name)
            # Pelna sciezka pliku pod ktorym bedzie sie znajdowal plik
            destination_file_path = os.path.join(destination_folder_path, name)

            if os.path.exists(destination_folder_path) and os.path.isdir(destination_folder_path) and name != "Database.db":
                #print("Folder istnieje, kopiuje plik.")
                shutil.copy2(source_file_path, destination_file_path)
            else:
                pass
                #print("Folder nie istnieje, plik nie zostanie skopiowany.")

        # Zamknięcie połączenia z bazą danych
        conn.close()

        # Usuwanie pustych folderów w RESULTS_PATH
        for root, dirs, files in os.walk(RESULTS_PATH, topdown=False):
            for folder in dirs:
                folder_path = os.path.join(root, folder)
                if not os.listdir(folder_path):  # Jesli folder jest pusty
                    os.rmdir(folder_path) # To go usun