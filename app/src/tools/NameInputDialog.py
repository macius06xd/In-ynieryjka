from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QDialogButtonBox


class NameInputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Change Name")

        self.layout = QVBoxLayout()

        self.label = QLabel("New Name:")
        self.layout.addWidget(self.label)

        self.input_edit = QLineEdit()
        self.layout.addWidget(self.input_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self.layout.addWidget(button_box)

        self.setLayout(self.layout)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.accept()  # Trigger accept action on Enter key
        else:
            super().keyPressEvent(event)

    def get_new_name(self):
        return self.input_edit.text()
