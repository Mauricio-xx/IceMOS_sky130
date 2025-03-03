#!/usr/bin/env python3
"""
IceMOS_sky130_calibrator.py

This module implements a calibration GUI for the IceMOS Sky130 flow.
It integrates the parameter extraction functionality from a BSIM model .lib file.
The .lib file is located at:
    /circuits/<device_type>/bin_<bin_number>/bin_<bin_number>_<device_type>_original.lib

The GUI lets the user:
  - Select which parameters to tune (via a search-enabled list).
  - Adjust the selected parameters using horizontal sliders and spin boxes.
  - Reset parameters to their default values.
  - Save and load calibration sessions.
  - (Placeholder) Run the simulation with the updated parameters in a loop.

Requirements:
  - PyQt5 (pip install PyQt5)

A dark theme is applied to match the current plot aesthetics.
"""

import sys
import os
import re
import json
from PyQt5 import QtWidgets, QtCore, QtGui

# --- GUI Components ---

class ParameterSelectionDialog(QtWidgets.QDialog):
    """
    Dialog for selecting which parameters to calibrate.
    Displays a searchable list of available parameter names.
    """
    def __init__(self, available_parameters, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Parameters to Calibrate")
        self.resize(400, 300)
        self.available_parameters = available_parameters  # List of parameter names
        self.setup_ui()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        self.search_edit = QtWidgets.QLineEdit()
        self.search_edit.setPlaceholderText("Search parameters...")
        layout.addWidget(self.search_edit)

        self.list_widget = QtWidgets.QListWidget()
        self.list_widget.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        for param in sorted(self.available_parameters):
            item = QtWidgets.QListWidgetItem(param)
            self.list_widget.addItem(item)
        layout.addWidget(self.list_widget)

        btn_layout = QtWidgets.QHBoxLayout()
        self.ok_button = QtWidgets.QPushButton("OK")
        self.cancel_button = QtWidgets.QPushButton("Cancel")
        btn_layout.addWidget(self.ok_button)
        btn_layout.addWidget(self.cancel_button)
        layout.addLayout(btn_layout)

        self.search_edit.textChanged.connect(self.filter_list)
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    def filter_list(self, text):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setHidden(text.lower() not in item.text().lower())

    def get_selected_parameters(self):
        """
        Returns a list of selected parameter names.
        """
        return [item.text() for item in self.list_widget.selectedItems()]


class ParameterTunerWindow(QtWidgets.QWidget):
    """
    Main widget for tuning selected parameters.
    Displays each parameter with a horizontal slider and a QDoubleSpinBox.
    Includes a "Reset Selected" button to revert values to defaults.
    """
    def __init__(self, current_params, default_params, parent=None):
        super().__init__(parent)
        self.parameters = current_params.copy()  # Not "current_parameters"
        self.default_parameters = default_params.copy()
        self.setup_ui()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        toolbar = QtWidgets.QHBoxLayout()
        self.add_button = QtWidgets.QPushButton("Add Parameter")
        self.remove_button = QtWidgets.QPushButton("Remove Selected")
        self.reset_button = QtWidgets.QPushButton("Reset Selected")
        self.save_button = QtWidgets.QPushButton("Save Calibration")
        self.load_button = QtWidgets.QPushButton("Load Calibration")
        self.run_sim_button = QtWidgets.QPushButton("Run Simulation")
        toolbar.addWidget(self.add_button)
        toolbar.addWidget(self.remove_button)
        toolbar.addWidget(self.reset_button)
        toolbar.addWidget(self.save_button)
        toolbar.addWidget(self.load_button)
        toolbar.addWidget(self.run_sim_button)
        layout.addLayout(toolbar)

        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.param_widget = QtWidgets.QWidget()
        self.form_layout = QtWidgets.QFormLayout(self.param_widget)
        self.scroll_area.setWidget(self.param_widget)
        layout.addWidget(self.scroll_area)

        self.setLayout(layout)
        self.populate_parameters()

        self.add_button.clicked.connect(self.open_selection_dialog)
        self.remove_button.clicked.connect(self.remove_selected_parameter)
        self.reset_button.clicked.connect(self.reset_selected)
        self.save_button.clicked.connect(self.save_calibration)
        self.load_button.clicked.connect(self.load_calibration)
        self.run_sim_button.clicked.connect(self.run_simulation)

        self.setStyleSheet("""
            QWidget { background-color: #2b2b2b; color: #f0f0f0; }
            QLineEdit, QSpinBox, QDoubleSpinBox, QSlider, QPushButton { background-color: #3c3c3c; }
        """)

    def populate_parameters(self):
        """
        Populate the form layout with the current parameters.
        For each parameter, create a horizontal slider and a spin box.
        A dynamic scaling factor is used so that the slider's integer range does not overflow.
        """
        # Clear the layout first
        while self.form_layout.count():
            child = self.form_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self.controls = {}  # Map param name to its controls
        for param, values in self.parameters.items():
            current = float(values["value"])
            default = float(self.default_parameters[param]["value"]) if param in self.default_parameters else current
            # Define min and max as 50% and 150% of the default
            min_val = default * 0.5
            max_val = default * 1.5

            # Determine a scaling factor to convert the float values to integers without overflow.
            scale = 1e6
            max_int = 2_147_483_647
            if max_val * scale > max_int:
                scale = max_int / max_val

            slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
            slider.setMinimum(int(min_val * scale))
            slider.setMaximum(int(max_val * scale))
            slider.setValue(int(current * scale))
            tick_interval = (int(max_val * scale) - int(min_val * scale)) // 10
            slider.setTickInterval(tick_interval if tick_interval > 0 else 1)
            slider.setTickPosition(QtWidgets.QSlider.TicksBelow)

            spin = QtWidgets.QDoubleSpinBox()
            spin.setRange(min_val, max_val)
            spin.setDecimals(6)
            spin.setValue(current)

            slider.valueChanged.connect(lambda val, s=spin, sc=scale: s.setValue(val / sc))
            spin.valueChanged.connect(lambda val, s=slider, sc=scale: s.setValue(int(val * sc)))
            spin.valueChanged.connect(lambda val, key=param: self.update_parameter(key, val))

            container = QtWidgets.QWidget()
            h_layout = QtWidgets.QHBoxLayout(container)
            h_layout.addWidget(slider)
            h_layout.addWidget(spin)
            h_layout.setContentsMargins(0, 0, 0, 0)
            self.form_layout.addRow(param, container)
            self.controls[param] = (slider, spin)

    def update_parameter(self, param, value):
        self.parameters[param] = value
        print(f"{param} updated to {value}")

    def open_selection_dialog(self):
        from IceMOS_sky130_param_extractor import extract_parameters_with_values
        # Try to obtain available parameters from the parent MainWindow if present.
        if hasattr(self.parent(), 'available_parameters'):
            all_params = self.parent().available_parameters
        else:
            # Fallback: extract from a fixed lib path
            lib_path = "circuits/pch/bin_10/bin_10_pch_original.lib"
            all_params = extract_parameters_with_values(lib_path)
        available = list(all_params.keys())
        available = [p for p in available if p not in self.parameters]
        if not available:
            QtWidgets.QMessageBox.information(self, "Info", "No more parameters to add.")
            return

        dialog = ParameterSelectionDialog(available, self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            selected = dialog.get_selected_parameters()
            for param in selected:
                self.parameters[param] = all_params[param]
                self.default_parameters[param] = all_params[param]
            self.populate_parameters()


    def remove_selected_parameter(self):
        param, ok = QtWidgets.QInputDialog.getText(self, "Remove Parameter", "Enter parameter name to remove:")
        if ok and param in self.parameters:
            del self.parameters[param]
            del self.default_parameters[param]
            self.populate_parameters()

    def reset_selected(self):
        for param, (slider, spin) in self.controls.items():
            if param in self.default_parameters:
                default_val = float(self.default_parameters[param])
                self.parameters[param] = default_val
                spin.setValue(default_val)
                slider.setValue(int(default_val * 1e6))
        QtWidgets.QMessageBox.information(self, "Reset", "Parameters have been reset to default values.")

    def save_calibration(self):
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Calibration Session", "", "JSON Files (*.json)")
        if filename:
            with open(filename, "w") as f:
                json.dump(self.parameters, f, indent=4)
            QtWidgets.QMessageBox.information(self, "Saved", "Calibration session saved successfully.")

    def load_calibration(self):
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Load Calibration Session", "", "JSON Files (*.json)")
        if filename:
            with open(filename, "r") as f:
                self.parameters = json.load(f)
            self.populate_parameters()
            QtWidgets.QMessageBox.information(self, "Loaded", "Calibration session loaded successfully.")

    def run_simulation(self):
        QtWidgets.QMessageBox.information(self, "Simulation", "Simulation executed with current calibration parameters.")


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, device_type, bin_number, lib_root="circuits"):
        super().__init__()
        self.device_type = device_type.lower()
        self.bin_number = bin_number
        self.lib_file_path = os.path.join(lib_root, self.device_type, f"bin_{bin_number}",
                                          f"bin_{bin_number}_{self.device_type}_original.lib")
        from IceMOS_sky130_param_extractor import extract_parameters_with_values
        # Extract parameters (a dict mapping parameter names to float values)
        from IceMOS_sky130_param_extractor import extract_parameters_with_values
        self.available_parameters = extract_parameters_with_values(self.lib_file_path)
        self.default_parameters = {}  # Start empty
        self.current_parameters = {}  # Start empty

        self.init_ui()


    def init_ui(self):
        self.setWindowTitle("IceMOS Sky130 Calibrator")
        self.setStyleSheet("background-color: #2b2b2b; color: #f0f0f0;")
        self.param_selector = ParameterSelectionDialog(list(self.default_parameters.keys()), self)
        self.tuner = ParameterTunerWindow(self.current_parameters, self.default_parameters)
        self.run_button = QtWidgets.QPushButton("Run Calibration Loop")
        central_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout(central_widget)
        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        splitter.addWidget(self.param_selector)
        splitter.addWidget(self.tuner)
        main_layout.addWidget(splitter)
        main_layout.addWidget(self.run_button)
        self.setCentralWidget(central_widget)
        self.run_button.clicked.connect(self.run_calibration)

    def run_calibration(self):
        print("Running calibration with parameters:")
        for k, v in self.current_parameters.items():
            print(f"  {k}: {v}")
        QtWidgets.QMessageBox.information(self, "Calibration", "Calibration loop executed (placeholder).")


def main():
    app = QtWidgets.QApplication(sys.argv)
    main_win = MainWindow("pch", 10)
    main_win.resize(1200, 800)
    main_win.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
