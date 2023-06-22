import sqlite3
import shutil
import os

from Configuration import INITIAL_CLUSTERIZED_FOLDER, RESULTS_PATH, INITIAL_IMAGES_FOLDER

class FileManager:

    @staticmethod
    def copy_files():
        # Połączenie z bazą danych
        conn = sqlite3.connect(os.path.join(INITIAL_CLUSTERIZED_FOLDER, 'Database.db'))
        cursor = conn.cursor()

        # Pobranie informacji o plikach
        cursor.execute("SELECT name, parent_id FROM file")
        files = cursor.fetchall()

        for file in files:
            name, parent_id = file

            # Pobranie nazwy folderu
            cursor.execute("SELECT name FROM file_system WHERE id = ?", (parent_id,))
            folder_name = cursor.fetchone()[0]

            # Skopiowanie pliku
            source = os.path.join(INITIAL_IMAGES_FOLDER, name)
            destination = ""

            if "-" in folder_name:  # Format Cluster_X-Y
                cluster_x, cluster_y = folder_name.split("-")
                destination = os.path.join(RESULTS_PATH, cluster_x, folder_name)
            else:  # Format Cluster_X
                destination = os.path.join(RESULTS_PATH, folder_name)
            
            # Kopiowanie pliku
            shutil.copy2(source, destination)

        # Zamknięcie połączenia z bazą danych
        conn.close()
