from PyQt5.QtWidgets import (QDialog, QLabel, QSpinBox, QDoubleSpinBox, QCheckBox, QLineEdit, QFormLayout, QPushButton,
                             QVBoxLayout, QHBoxLayout, QComboBox, QWidget)
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt, QSize

import DataBase
from KMeansParameters import KMeansParameters
import numpy as np

class QuestionMarkWidget(QWidget):
    def __init__(self, title, tooltip_text):
        super().__init__()
        layout = QHBoxLayout()
        label = QLabel(title)
        label.setAlignment(Qt.AlignRight)
        pixmap = QPixmap("assets/question_mark.png").scaledToHeight(16, Qt.SmoothTransformation)
        question_mark_icon = QLabel()
        question_mark_icon.setPixmap(pixmap)
        question_mark_icon.setToolTip(tooltip_text)

        layout.addWidget(label)
        layout.addWidget(question_mark_icon)
        layout.addStretch(1)
        self.setLayout(layout)

class KMeansParamsWidget(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("K-means Parameters")
        self.kmeans_params = KMeansParameters()  # Get the Singleton instance

        self.layout = QVBoxLayout()

        # Create input fields for each parameter
        self.init_input = QComboBox()
        self.init_input.addItems(["k-means++", "random"])
        self.init_input.setCurrentText(self.kmeans_params.init)

        self.n_init_input = QSpinBox()
        self.n_init_input.setMinimum(1)
        self.n_init_input.setMaximum(1000)
        self.set_spinbox_value(self.n_init_input, self.kmeans_params.n_init)

        self.max_iter_input = QSpinBox()
        self.max_iter_input.setMinimum(1)
        self.max_iter_input.setMaximum(10000)
        self.set_spinbox_value(self.max_iter_input, self.kmeans_params.max_iter)

        self.tol_input = QDoubleSpinBox()
        self.tol_input.setMinimum(0.0)
        self.tol_input.setMaximum(1.0)
        self.tol_input.setSingleStep(0.001)
        self.tol_input.setDecimals(4)  # Set the number of decimal places
        self.set_spinbox_value(self.tol_input, self.kmeans_params.tol)

        self.precompute_distances_input = QCheckBox()
        self.precompute_distances_input.setChecked(self.kmeans_params.precompute_distances)

        self.algorithm_input = QComboBox()
        self.algorithm_input.addItems(["lloyd", "elkan", "auto", "full"])
        self.algorithm_input.setCurrentText(self.kmeans_params.algorithm)

        self.n_jobs_input = QSpinBox()
        self.n_jobs_input.setMinimum(1)
        self.n_jobs_input.setMaximum(100)
        self.set_spinbox_value(self.n_jobs_input, self.kmeans_params.n_jobs)

        self.verbose_input = QSpinBox()
        self.verbose_input.setMinimum(0)
        self.verbose_input.setMaximum(100)
        self.set_spinbox_value(self.verbose_input, self.kmeans_params.verbose)

        # Add labels and input fields to the layout
        form_layout = QFormLayout()

        form_layout.addRow(QuestionMarkWidget("Init:", "Initialization method\n"
                                                        "k-means++ (default): Selects initial cluster centroids in a smart way to speed up convergence.\n"
                                                        "random: Chooses k observations (rows) at random from data for the initial centroids."), self.init_input)
        form_layout.addRow(QuestionMarkWidget("Number of Initializations:", "Number of times the k-means algorithm will be run with different centroid seeds.\n"
                                                                             "The final results will be the best output of n_init consecutive runs in terms of inertia (sum of squared distances)."), self.n_init_input)
        form_layout.addRow(QuestionMarkWidget("Max Iterations:", "Maximum number of iterations for each single run of the k-means algorithm."), self.max_iter_input)
        form_layout.addRow(QuestionMarkWidget("Tolerance:", "Relative tolerance with regards to Frobenius norm for stopping criterion."), self.tol_input)
        form_layout.addRow(QuestionMarkWidget("Precompute Distances:", "Whether to precompute distances (faster but takes more memory) for the 'elkan' algorithm.\n"
                                                                        "Set to 'auto' to automatically decide if precomputation should be used or not."), self.precompute_distances_input)
        form_layout.addRow(QuestionMarkWidget("Algorithm:", "The algorithm to use.\n"
                                                            "lloyd: Lloyd's algorithm.\n"
                                                            "elkan: Elkan's algorithm.\n"
                                                            "auto: Choose automatically between 'full' and 'elkan' depending on the dataset.\n"
                                                            "full: Full batch KMeans."), self.algorithm_input)
        form_layout.addRow(QuestionMarkWidget("Number of Jobs:", "The number of parallel jobs to run for the 'elkan' algorithm. Set to None to use 1 job."), self.n_jobs_input)
        form_layout.addRow(QuestionMarkWidget("Verbose:", "The verbosity level. If 0, no messages will be printed. If greater than 0, the process will report at most this number of iterations in the k-means algorithm."), self.verbose_input)

        self.layout.addLayout(form_layout)

        # Create buttons for applying changes and closing the dialog
        button_layout = QHBoxLayout()
        self.apply_button = QPushButton("Apply Changes")
        self.close_button = QPushButton("Close")
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.close_button)

        self.layout.addLayout(button_layout)
        self.setLayout(self.layout)

        # Connect the Apply Changes and Close buttons to their respective functions
        self.apply_button.clicked.connect(self.apply_changes)
        self.close_button.clicked.connect(self.close)

    def set_spinbox_value(self, spinbox, value):
        # Set the value of the spinbox while handling None values
        if value is None:
            spinbox.setValue(0)  # Use 0 as a placeholder for None
        else:
            spinbox.setValue(value)

    def apply_changes(self):
        # Get the values from the input fields
        init = self.init_input.currentText()
        n_init = self.n_init_input.value()
        max_iter = self.max_iter_input.value()
        tol = self.tol_input.value()
        precompute_distances = self.precompute_distances_input.isChecked()
        algorithm = self.algorithm_input.currentText()
        n_jobs = self.n_jobs_input.value()
        verbose = self.verbose_input.value()

        # Update the KMeansParameters Singleton with the new values
        self.kmeans_params.init = init
        self.kmeans_params.n_init = n_init
        self.kmeans_params.max_iter = max_iter
        self.kmeans_params.tol = tol
        self.kmeans_params.precompute_distances = precompute_distances
        self.kmeans_params.algorithm = algorithm
        self.kmeans_params.n_jobs = n_jobs
        self.kmeans_params.verbose = verbose

        # You can add additional logic here, e.g., save the changes to a configuration file, etc.
        db = DataBase.DataBaseConnection()
        db.save_kmeans_parameters()
        # Close the dialog after applying changes
        self.close()
