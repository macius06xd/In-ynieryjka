import sqlite3
import os
import shutil

from Configuration import INITIAL_CLUSTERIZED_FOLDER, RESULTS_PATH, INITIAL_IMAGES_FOLDER

def create_result_folders():
    # Połącz się z bazą danych
    conn = sqlite3.connect(os.path.join(INITIAL_CLUSTERIZED_FOLDER, 'Database.db'))
    cursor = conn.cursor()

    # Zapytanie SQL do pobrania wszystkich wierszy
    query = "SELECT id, name, path, isCluster, parent_id FROM file_system"
    cursor.execute(query)

    rows = cursor.fetchall()

    # Funkcja do wyszukiwania ścieżki folderu nadrzędnego na podstawie parent_id
    def find_parent_path(parent_id):
        cursor.execute(f"SELECT name FROM file_system WHERE id = {parent_id}")
        parent_name = cursor.fetchone()[0]
        return os.path.join(RESULTS_PATH, parent_name)

    # Przetwarzanie wierszy
    for row in rows:
        id, name, path, isCluster, parent_id = row
        if path != "-":
            new_folder_path = os.path.join(RESULTS_PATH, name)
        else:
            parent_folder_path = find_parent_path(parent_id)
            new_folder_path = os.path.join(parent_folder_path, name)
        
        # Stworzenie folderu, jeżeli nie istnieje
        os.makedirs(new_folder_path, exist_ok=True)

    conn.close()