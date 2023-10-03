from app.cfg.Configuration import DATABASE_SNAPSHOTS, INITIAL_CLUSTERIZED_FOLDER
import os
import shutil
from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QListWidget, QPushButton
from app.src.tools.DatabaseSnapshotManager import create_database_snapshot

class DatabaseSnapshotLoader(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Load database snapshot (YYYY-MM-DD-hh-mm)')
        self.setGeometry(100, 100, 400, 300)

        layout = QVBoxLayout()

        self.lista_plikow = QListWidget(self)
        layout.addWidget(self.lista_plikow)

        self.przycisk_apply = QPushButton('Apply', self)
        self.przycisk_apply.clicked.connect(self.save_current_db_and_swap_with_chosen)
        layout.addWidget(self.przycisk_apply)

        self.setLayout(layout)

        self.wypelnij_liste_plikow()

    def wypelnij_liste_plikow(self):
        folder = DATABASE_SNAPSHOTS

        if os.path.exists(folder) and os.path.isdir(folder):
            pliki = os.listdir(folder)

            for plik in pliki:
                self.lista_plikow.addItem(plik)

    def save_current_db_and_swap_with_chosen(self):
        create_database_snapshot()

        wybrany_plik = self.lista_plikow.currentItem()

        if wybrany_plik is not None:
            nazwa_pliku = wybrany_plik.text()
            
            source_path = os.path.join(DATABASE_SNAPSHOTS, nazwa_pliku)
            destination_path = os.path.join(INITIAL_CLUSTERIZED_FOLDER, nazwa_pliku)
            
            shutil.copy2(source_path, destination_path)

            existing_db_path = os.path.join(INITIAL_CLUSTERIZED_FOLDER, "Database.db")
            if os.path.exists(existing_db_path):
                os.remove(existing_db_path)

            os.rename(destination_path, existing_db_path)
            
            print(f"Wybrano plik: {nazwa_pliku} i przeprowadzono zamianę.")
        else:
            print("Nie wybrano pliku.")
