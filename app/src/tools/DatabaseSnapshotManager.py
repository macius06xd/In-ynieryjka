import os
import shutil
from datetime import datetime
from app.cfg.Configuration import INITIAL_CLUSTERIZED_FOLDER, DATABASE_SNAPSHOTS

def create_database_and_configuration_snapshot():
    
    if not os.path.exists(DATABASE_SNAPSHOTS):
        os.makedirs(DATABASE_SNAPSHOTS)

    current_datetime = datetime.now()
    timestamp = current_datetime.strftime("%Y-%m-%d # %H-%M-%S")

    # Tworzenie folderu o nazwie 'timestamp' w ścieżce DATABASE_SNAPSHOTS
    snapshot_folder_path = os.path.join(DATABASE_SNAPSHOTS, timestamp)
    os.makedirs(snapshot_folder_path)

    # Kopiowanie pliku Database.db z dodanym timestamp w nazwie
    database_path = os.path.join(INITIAL_CLUSTERIZED_FOLDER, 'Database.db')
    snapshot_database_path = os.path.join(snapshot_folder_path, f'Database_{timestamp}.db')
    shutil.copyfile(database_path, snapshot_database_path)

    # Kopiowanie pliku Configuration.py z pakietu app.cfg z dodanym timestamp w nazwie
    configuration_path = os.path.join('app', 'cfg', 'Configuration.py')
    snapshot_configuration_path = os.path.join(snapshot_folder_path, f'Configuration_{timestamp}.py')
    shutil.copyfile(configuration_path, snapshot_configuration_path)

    print(f"Snapshot including Database.db and Configuration.py created at {snapshot_folder_path}")

def replace_database_and_configuration_snapshot(timestamp):
    
    snapshot_database_path = os.path.join(DATABASE_SNAPSHOTS, timestamp, f'Database_{timestamp}.db')
    temp_snapshot_database_path = os.path.join(INITIAL_CLUSTERIZED_FOLDER, f'Database_{timestamp}.db')
    current_database_path = os.path.join(INITIAL_CLUSTERIZED_FOLDER, 'Database.db')

    snapshot_configuration_path = os.path.join(DATABASE_SNAPSHOTS, timestamp, f'Configuration_{timestamp}.py')
    temp_snapshot_configuration_path = os.path.join('app', 'cfg', f'Configuration_{timestamp}.py')
    current_configuration_path = os.path.join('app', 'cfg', 'Configuration.py')

    try:
        # Usuń stary plik Database.db
        if os.path.exists(current_database_path):
            os.remove(current_database_path)
            print(f"File {current_database_path} was deleted.")
        
        # Kopiuj wybrany plik Database_timestamp.db do folderu INITIAL_CLUSTERIZED_FOLDER
        shutil.copy(snapshot_database_path, temp_snapshot_database_path)
        print(f"Database snapshot copied to {temp_snapshot_database_path}")

        # Zmień nazwę skopiowanego pliku bazy danych na Database.db
        os.rename(temp_snapshot_database_path, current_database_path)
        print(f"File {temp_snapshot_database_path} renamed to {current_database_path}.")

        # Usuń stary plik Configuration.py
        if os.path.exists(current_configuration_path):
            os.remove(current_configuration_path)
            print(f"File {current_configuration_path} was deleted.")
        
        # Kopiuj plik Configuration_timestamp.py do folderu app/cfg
        shutil.copy(snapshot_configuration_path, temp_snapshot_configuration_path)
        print(f"Configuration snapshot copied to {temp_snapshot_configuration_path}")

        # Zmień nazwę skopiowanego pliku konfiguracji na Configuration.py
        os.rename(temp_snapshot_configuration_path, current_configuration_path)
        print(f"File {temp_snapshot_configuration_path} renamed to {current_configuration_path}.")

    except FileNotFoundError:
        print(f"Some file doesn't exist")
    except Exception as e:
        print(f"Error during operation: {e}")

