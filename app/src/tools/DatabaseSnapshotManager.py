import os
import shutil
from datetime import datetime
from app.cfg.Configuration import INITIAL_CLUSTERIZED_FOLDER, DATABASE_SNAPSHOTS

def create_database_snapshot():
    
    if not os.path.exists(DATABASE_SNAPSHOTS):
        os.makedirs(DATABASE_SNAPSHOTS)

    current_datetime = datetime.now()
    timestamp = current_datetime.strftime("%Y-%m-%d-%H-%M")

    database_path = os.path.join(INITIAL_CLUSTERIZED_FOLDER, 'Database.db')

    snapshot_filename = f"Database_{timestamp}.db"
    snapshot_path = os.path.join(DATABASE_SNAPSHOTS, snapshot_filename)

    shutil.copyfile(database_path, snapshot_path)
    print(f"Snapshot created at {snapshot_path}")

def replace_database_file_with_snapshot(filename):

    #Copy chosen snapshot to INITIAL_CLUSTERIZED_FOLDER
    snapshot_path = os.path.join(DATABASE_SNAPSHOTS, filename)
    try:
        # Copy chosen snapshot to DATABASE_SNAPSHOTS
        shutil.copy(snapshot_path, INITIAL_CLUSTERIZED_FOLDER)
        print(f"Snapshot copied to {INITIAL_CLUSTERIZED_FOLDER}")
    except FileNotFoundError:
        print(f"File {snapshot_path} doesn't exist")
    except Exception as e:
        print(f"Error during copying file: {e}")
        
    #Remove old Database file
    current_database_path = os.path.join(INITIAL_CLUSTERIZED_FOLDER, 'Database.py')
    try:
        os.remove(current_database_path)
        print(f"File {current_database_path} was deleted.")
    except FileNotFoundError:
        print(f"File {current_database_path} not found.")
    except Exception as e:
        print(f"Error during deleting file: {e}")

    #Rename new snapshot to Database.py
    filename_filepath = os.path.join(INITIAL_CLUSTERIZED_FOLDER, filename)
    database_filepath = os.path.join(INITIAL_CLUSTERIZED_FOLDER, 'Database.py')
    try:
        os.rename(filename_filepath, database_filepath)
        print(f"File {filename} renamed to {database_filepath}.")
    except FileNotFoundError:
        print(f"File {filename} doesn't exist in {INITIAL_CLUSTERIZED_FOLDER}.")
    except Exception as e:
        print(f"Error during renaming file: {e}")
