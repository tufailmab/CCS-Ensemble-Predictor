import sys
import pickle
import pandas as pd
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QGridLayout,
    QMessageBox, QVBoxLayout, QHBoxLayout, QGroupBox, QScrollArea
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

plt.rcParams['font.family'] = 'Times New Roman'

with open("ccs_model.pkl", "rb") as f:
    model = pickle.load(f)

class CCSPredictor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Compressive Strength Predictor")
        self.setMinimumSize(1300, 750)
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e2f;
                color: #f0f0f0;
                font-family: 'Times New Roman';
            }
            QGroupBox {
                background-color: #2e2e44;
                border: 1px solid #444466;
                border-radius: 12px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 5px;
                font-size: 15px;
                font-weight: bold;
                color: #ffffff;
            }
            QLabel {
                color: #f0f0f0;
            }
            QLineEdit {
                border: 1px solid #555577;
                border-radius: 6px;
                padding: 5px;
                background-color: #3a3a55;
                color: #f0f0f0;
            }
            QLineEdit:focus {
                border: 1px solid #6c63ff;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #6c63ff, stop:1 #4a47c8);
                color: white;
                border-radius: 8px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #7d72ff, stop:1 #5a57d8);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #5a57d8, stop:1 #4a47c8);
            }
            QLabel#prediction {
                background-color: #4a47c8;
                border-radius: 10px;
                padding: 10px;
                font-size: 16px;
                font-weight: bold;
                color: #ffffff;
                qproperty-alignment: AlignCenter;
            }
        """)
        self.initUI()

    def initUI(self):
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(25)

        # ===== Input Layout =====
        input_layout = QGridLayout()
        input_layout.setHorizontalSpacing(18)
        input_layout.setVerticalSpacing(12)

        self.features = {
            'cmt': 'kg/m³',
            'slag': 'kg/m³',
            'flyash': 'kg/m³',
            'wtr': 'kg/m³',
            'sp': 'kg/m³',
            'ca': 'kg/m³',
            'fa': 'kg/m³',
            'age': 'days'
        }
        self.inputs = {}

        row = 0
        for feature, unit in self.features.items():
            label = QLabel(f"{feature.capitalize()} ({unit}):")
            label.setFont(QFont("Times New Roman", 12))
            input_layout.addWidget(label, row, 0, alignment=Qt.AlignmentFlag.AlignRight)
            self.inputs[feature] = QLineEdit()
            self.inputs[feature].setFont(QFont("Times New Roman", 12))
            input_layout.addWidget(self.inputs[feature], row, 1)
            row += 1

        # Predict button
        self.predict_btn = QPushButton("Predict")
        self.predict_btn.setFont(QFont("Times New Roman", 12))
        self.predict_btn.clicked.connect(self.predict)
        input_layout.addWidget(self.predict_btn, row, 0, 1, 2, alignment=Qt.AlignmentFlag.AlignCenter)

        # Prediction label
        self.pred_label = QLabel("Predicted CCS: --- MPa")
        self.pred_label.setObjectName("prediction")
        input_layout.addWidget(self.pred_label, row+1, 0, 1, 2)

        input_group = QGroupBox("Input Features")
        input_group.setLayout(input_layout)
        main_layout.addWidget(input_group, 30)

        # ===== Graph Layout =====
        self.fig = Figure(figsize=(10, 8))
        self.canvas = FigureCanvas(self.fig)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.canvas)

        graph_group = QGroupBox("Feature Influence Graphs")
        graph_layout = QVBoxLayout()
        graph_layout.addWidget(scroll)
        graph_group.setLayout(graph_layout)
        main_layout.addWidget(graph_group, 70)

        self.setLayout(main_layout)

    def predict(self):
        try:
            values = [float(self.inputs[f].text()) for f in self.features]
            df = pd.DataFrame([values], columns=self.features.keys())
            pred = model.predict(df)[0]
            self.pred_label.setText(f"Predicted CCS: {pred:.2f} MPa")
            self.plot_graphs(df.values[0], pred)
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Please enter valid numbers for all fields.")

    def plot_graphs(self, input_values, prediction):
        self.fig.clear()
        feature_names = list(self.features.keys())
        axes = self.fig.subplots(4, 2, sharey=True).flatten()

        for i, ax in enumerate(axes):
            f_name = feature_names[i]
            f_val = input_values[i]
            test_vals = np.linspace(f_val*0.8, f_val*1.2, 50)
            X_test = np.tile(input_values, (50,1))
            X_test[:,i] = test_vals
            y_pred = model.predict(pd.DataFrame(X_test, columns=feature_names))

            ax.plot(test_vals, y_pred, color='#6c63ff', marker='o', markersize=3, label=f_name)
            ax.set_xlabel(f"{f_name} ({self.features[f_name]})", fontsize=10)
            ax.set_ylabel("CCS (MPa)" if i%2==0 else "", fontsize=10)
            ax.set_title(f"{f_name} Influence", fontsize=11, weight='bold')
            ax.grid(True, color='#444466')
            ax.legend(fontsize=8)

        self.fig.tight_layout()
        self.canvas.draw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CCSPredictor()
    window.show()
    sys.exit(app.exec())
