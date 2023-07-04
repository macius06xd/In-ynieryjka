import sqlite3
import os
import shutil

from Configuration import INITIAL_CLUSTERIZED_FOLDER, RESULTS_PATH, INITIAL_IMAGES_FOLDER

def create_result_folders():

    # Wyczysc ewentualne poprzednie wyniki
    folder_path = RESULTS_PATH

    # Usuń wszystkie pliki w folderze
    shutil.rmtree(folder_path)

    # Utwórz pusty folder o tej samej nazwie
    os.mkdir(folder_path)


    # Połącz się z bazą danych
    conn = sqlite3.connect(os.path.join(INITIAL_CLUSTERIZED_FOLDER, 'Database.db'))
    cursor = conn.cursor()

    # Pobranie danych z bazy
    cursor.execute("SELECT id, name, isCluster, parent_id, commited FROM file_system")
    rows = cursor.fetchall()

    # Tworzenie folderów
    for row in rows:
        folder_path = os.path.join(RESULTS_PATH, row[1])
        if is_commited(cursor, row[0]):
            os.makedirs(folder_path, exist_ok=True)

    cursor.close()
    conn.close()

def is_commited(cursor, folder_id):
    # Sprawdzenie, czy folder lub jego przodkowie mają wartość commited == 1
    while folder_id is not None:
        cursor.execute("SELECT commited, parent_id FROM file_system WHERE id=?", (folder_id,))
        result = cursor.fetchone()
        if result[0] == 1:
            return True
        folder_id = result[1]
    return False
