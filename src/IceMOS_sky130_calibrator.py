#!/usr/bin/env python3
"""
IceMOS_sky130_calibration_simulator.py

This module implements a complete calibration and simulation GUI for the IceMOS Sky130 flow.
It integrates parameter extraction from a BSIM model .lib file, allows the user to select and tune
parameters via sliders (with configurable min/max and manual entry), update the modified .lib file,
and then configure and run IV simulations with continuous plot updating.

The .lib file is located at:
    /circuits/<device_type>/bin_<bin_number>/bin_<bin_number>_<device_type>_original.lib
The modified file has the same structure and is updated with the tuned parameter values if the user chooses.

Requirements:
    - PyQt5
    - PyQtGraph
    - JSON for calibration session save/load

Note: This code uses placeholder functions for simulation and file updating. You should integrate
your actual simulation code (e.g. from IceMOS_sky130_simulator and model modifier modules) as needed.
"""

import sys, os, json, re
from PyQt5 import QtWidgets, QtCore, QtGui
import pyqtgraph as pg

# Import the parameter extraction function (assumed to be defined in IceMOS_sky130_param_extractor.py)
from IceMOS_sky130_param_extractor import extract_parameters_with_values

# ---------------------
# Calibration GUI Components
# ---------------------

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
        return [item.text() for item in self.list_widget.selectedItems()]

class ParameterTunerWindow(QtWidgets.QWidget):
    """
    Widget for tuning parameters.
    For each selected parameter, displays:
      - A horizontal slider (with dynamically adjustable range).
      - A spin box showing the current value (editable).
      - Two spin boxes for min and max slider limits.
      - A QLineEdit for manual entry of the current value.
    Also includes buttons to add/remove parameters, and save/load calibration sessions.
    """
    def __init__(self, current_params, default_params, available_parameters, parent=None):
        super().__init__(parent)
        self.parameters = current_params.copy()
        self.default_parameters = default_params.copy()
        self.available_parameters = available_parameters.copy()
        self.setup_ui()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        toolbar = QtWidgets.QHBoxLayout()
        self.add_button = QtWidgets.QPushButton("Add Parameter")
        self.remove_button = QtWidgets.QPushButton("Remove Parameter")
        self.reset_button = QtWidgets.QPushButton("Reset Selected")
        self.save_button = QtWidgets.QPushButton("Save Calibration")
        self.load_button = QtWidgets.QPushButton("Load Calibration")
        toolbar.addWidget(self.add_button)
        toolbar.addWidget(self.remove_button)
        toolbar.addWidget(self.reset_button)
        toolbar.addWidget(self.save_button)
        toolbar.addWidget(self.load_button)
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

        self.setStyleSheet("""
            QWidget { background-color: #2b2b2b; color: #f0f0f0; }
            QLineEdit, QSpinBox, QDoubleSpinBox, QSlider, QPushButton { background-color: #3c3c3c; }
        """)

    def populate_parameters(self):
        EPSILON = 1e-18
        desired_int_range = 1e6

        while self.form_layout.count():
            child = self.form_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self.controls = {}

        for param, values in self.parameters.items():
            if not isinstance(values, dict):
                current = float(values)
                self.parameters[param] = {"value": current}
                values = self.parameters[param]

            current = float(values["value"])

            # Retrieve default_val from default_parameters if available
            if param in self.default_parameters and isinstance(self.default_parameters[param], dict):
                default_val = float(self.default_parameters[param]["value"])
            else:
                default_val = current

            # Only compute min/max if not already set
            if "min" not in values or "max" not in values:
                if abs(default_val) < EPSILON:
                    # For near-zero defaults, define a small range around zero
                    offset = 1e-9
                    min_val = -offset
                    max_val = offset
                else:
                    candidate1 = default_val * 0.5
                    candidate2 = default_val * 1.5
                    min_val = min(candidate1, candidate2)
                    max_val = max(candidate1, candidate2)
                values["min"] = min_val
                values["max"] = max_val
            else:
                min_val = float(values["min"])
                max_val = float(values["max"])

            range_width = max_val - min_val
            scale = 1e6 if range_width == 0 else desired_int_range / range_width

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

            minSpin = QtWidgets.QDoubleSpinBox()
            minSpin.setRange(-1e20, 1e9)
            minSpin.setDecimals(8)
            minSpin.setValue(min_val)
            maxSpin = QtWidgets.QDoubleSpinBox()
            maxSpin.setRange(-1e20, 1e9)
            maxSpin.setDecimals(8)
            maxSpin.setValue(max_val)

            # Manual entry field for current value
            manualEdit = QtWidgets.QLineEdit()
            manualEdit.setFixedWidth(80)
            manualEdit.setText(f"{current:.6g}")
            manualLabel = QtWidgets.QLabel("Manual:")

            # Define helper function for updating slider range for this parameter.
            # Define helper function for updating slider range for this parameter.
            def update_slider_range(param, slider, spin, minSpin, maxSpin):
                new_min = minSpin.value()
                new_max = maxSpin.value()
                new_range = new_max - new_min
                new_scale = 1e6 if new_range == 0 else desired_int_range / new_range

                slider.blockSignals(True)
                spin.blockSignals(True)
                slider.setMinimum(int(new_min * new_scale))
                slider.setMaximum(int(new_max * new_scale))
                spin.setRange(new_min, new_max)
                current_val = spin.value()
                if current_val < new_min:
                    current_val = new_min
                elif current_val > new_max:
                    current_val = new_max
                spin.setValue(current_val)
                slider.setValue(int(current_val * new_scale))
                slider.blockSignals(False)
                spin.blockSignals(False)
                self.parameters[param]["min"] = new_min
                self.parameters[param]["max"] = new_max

            minSpin.valueChanged.connect(lambda _: update_slider_range(param, slider, spin, minSpin, maxSpin))
            maxSpin.valueChanged.connect(lambda _: update_slider_range(param, slider, spin, minSpin, maxSpin))

            slider.valueChanged.connect(lambda val, s=spin, sc=scale: s.setValue(val / sc))
            spin.valueChanged.connect(lambda val, s=slider, sc=scale: s.setValue(int(val * sc)))
            spin.valueChanged.connect(lambda val, key=param: self.update_parameter(key, val))
            manualEdit.editingFinished.connect(
                lambda key=param, edit=manualEdit: self.update_parameter_from_text(key, edit.text()))

            container = QtWidgets.QWidget()
            h_layout = QtWidgets.QHBoxLayout(container)
            h_layout.addWidget(slider)
            h_layout.addWidget(spin)
            h_layout.addWidget(QtWidgets.QLabel("Min:"))
            h_layout.addWidget(minSpin)
            h_layout.addWidget(QtWidgets.QLabel("Max:"))
            h_layout.addWidget(maxSpin)
            h_layout.addWidget(manualLabel)
            h_layout.addWidget(manualEdit)
            h_layout.setContentsMargins(0, 0, 0, 0)
            self.form_layout.addRow(param, container)
            self.controls[param] = (slider, spin, minSpin, maxSpin, manualEdit)

    def update_parameter(self, param, value):
        self.parameters[param] = {"value": value,
                                  "min": self.parameters[param].get("min", value * 0.5),
                                  "max": self.parameters[param].get("max", value * 1.5)}
        print(f"{param} updated to {value}")

    def update_parameter_from_text(self, param, text):
        desired_int_range = 1e6  # desired integer range for slider mapping
        try:
            new_val = float(text)
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Invalid Input", f"'{text}' is not a valid number for {param}.")
            return

        # Retrieve controls for the parameter.
        if param not in self.controls:
            return
        slider, spin, minSpin, maxSpin, manualEdit = self.controls[param]

        # Get the current min and max values from the spin boxes.
        current_min = minSpin.value()
        current_max = maxSpin.value()

        # If new_val is less than current_min, update minSpin.
        if new_val < current_min:
            current_min = new_val
            minSpin.blockSignals(True)
            minSpin.setValue(new_val)
            minSpin.blockSignals(False)
        # If new_val is greater than current_max, update maxSpin.
        if new_val > current_max:
            current_max = new_val
            maxSpin.blockSignals(True)
            maxSpin.setValue(new_val)
            maxSpin.blockSignals(False)

        # Update the parameter dictionary.
        self.parameters[param]["value"] = new_val
        self.parameters[param]["min"] = current_min
        self.parameters[param]["max"] = current_max

        # Recalculate the range and the new scaling factor.
        new_range = current_max - current_min
        new_scale = 1e6 if new_range == 0 else desired_int_range / new_range

        # Update the current value spin box.
        spin.blockSignals(True)
        spin.setRange(current_min, current_max)
        spin.setValue(new_val)
        spin.blockSignals(False)

        # Update the slider's range and value using the new scale.
        slider.blockSignals(True)
        slider.setMinimum(int(current_min * new_scale))
        slider.setMaximum(int(current_max * new_scale))
        try:
            slider.setValue(int(new_val * new_scale))
        except OverflowError:
            QtWidgets.QMessageBox.warning(self, "Overflow Error", f"Calculated slider value is too large for {param}.")
            slider.setValue(slider.maximum())
        slider.blockSignals(False)

        # Update the manual edit text to reflect the new value.
        manualEdit.setText(f"{new_val:.6g}")
        print(f"{param} updated manually to {new_val}")

    def open_selection_dialog(self):
        all_params = self.available_parameters
        available = [p for p in all_params.keys() if p not in self.parameters]
        if not available:
            QtWidgets.QMessageBox.information(self, "Info", "No more parameters to add.")
            return
        dialog = ParameterSelectionDialog(available, self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            selected = dialog.get_selected_parameters()
            for param in selected:
                self.parameters[param] = self.available_parameters[param]
                self.default_parameters[param] = self.available_parameters[param]
            self.populate_parameters()

    def remove_selected_parameter(self):
        param, ok = QtWidgets.QInputDialog.getText(self, "Remove Parameter", "Enter parameter name to remove:")
        if ok and param in self.parameters:
            del self.parameters[param]
            del self.default_parameters[param]
            self.populate_parameters()

    def reset_selected(self):
        for param, controls in self.controls.items():
            slider, spin, minSpin, maxSpin, manualEdit = controls
            if param in self.default_parameters:
                default_val = float(self.default_parameters[param]["value"]) if isinstance(self.default_parameters[param], dict) else float(self.default_parameters[param])
                self.parameters[param]["value"] = default_val
                spin.setValue(default_val)
                slider.setValue(int(default_val * 1e6))
                manualEdit.setText(f"{default_val:.6g}")
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
        self.available_parameters = extract_parameters_with_values(self.lib_file_path)
        self.default_parameters = {}  # start empty
        self.current_parameters = {}  # start empty
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("IceMOS Sky130 Calibrator")
        self.setStyleSheet("background-color: #2b2b2b; color: #f0f0f0;")
        # Removed the left pane; we rely on the "Add Parameter" button
        self.tuner = ParameterTunerWindow(self.current_parameters, self.default_parameters, self.available_parameters)
        self.run_button = QtWidgets.QPushButton("Run Calibration Loop")
        central_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout(central_widget)
        main_layout.addWidget(self.tuner)
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
