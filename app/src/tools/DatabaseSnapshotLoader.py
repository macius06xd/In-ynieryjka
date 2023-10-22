from app.cfg.Configuration import DATABASE_SNAPSHOTS, INITIAL_CLUSTERIZED_FOLDER
import os
import shutil
from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QListWidget, QPushButton, QDesktopWidget
from app.src.tools.DatabaseSnapshotManager import create_database_and_configuration_snapshot, replace_database_and_configuration_snapshot

class DatabaseSnapshotLoader(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Load database and config snapshot (YYYY-MM-DD # hh-mm-ss)')
        self.setGeometry(200, 200, 500, 400)

        layout = QVBoxLayout()

        self.lista_plikow = QListWidget(self)
        layout.addWidget(self.lista_plikow)

        self.przycisk_apply = QPushButton('Apply', self)
        self.przycisk_apply.clicked.connect(self.save_current_db_and_swap_with_chosen)
        layout.addWidget(self.przycisk_apply)

        self.przycisk_skip = QPushButton('Next', self)
        self.przycisk_skip.clicked.connect(self.close)  # Connect to QDialog's close() method to close the window
        layout.addWidget(self.przycisk_skip)

        self.setLayout(layout)

        self.wypelnij_liste_plikow()

        self.center_on_screen()

    def wypelnij_liste_plikow(self):
        folder = DATABASE_SNAPSHOTS

        if os.path.exists(folder) and os.path.isdir(folder):
            pliki = os.listdir(folder)

            for plik in pliki:
                self.lista_plikow.addItem(plik)

    def save_current_db_and_swap_with_chosen(self):
        create_database_and_configuration_snapshot()

        wybrany_plik = self.lista_plikow.currentItem()

        if wybrany_plik is not None:
            nazwa_pliku = wybrany_plik.text()
            replace_database_and_configuration_snapshot(nazwa_pliku)

        else:
            print("Nie wybrano pliku.")

    def center_on_screen(self):
        resolution = QDesktopWidget().screenGeometry()
        self.move(int((resolution.width() / 2) - (self.frameSize().width() / 2)),
                int((resolution.height() / 2) - (self.frameSize().height() / 2)))
