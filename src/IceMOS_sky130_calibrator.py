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
        self.parameters = current_params
        self.default_parameters = default_params
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

    def sync_parameter_ui(self, param):
        """
        Recompute the slider's range and update controls based on the parameter's
        stored (value, min, max). This method is called after any update.
        It updates only the controls for the given parameter, then forces a repaint.
        """
        DESIRED_INT_RANGE = 100_000
        EPSILON = 1e-18

        if param not in self.controls:
            return
        # Unpack the eight controls (order: slider, displayCurrent, minEdit, maxEdit, manualCurrentEdit, setMinBtn, setMaxBtn, setCurrentBtn)
        slider, displayCurrent, minEdit, maxEdit, manualCurrentEdit, _, _, _ = self.controls[param]

        # 1. Retrieve min and max from their spin boxes.
        new_min = minEdit.value()
        new_max = maxEdit.value()
        if new_min > new_max:
            new_min, new_max = new_max, new_min
            minEdit.blockSignals(True)
            maxEdit.blockSignals(True)
            minEdit.setValue(new_min)
            maxEdit.setValue(new_max)
            minEdit.blockSignals(False)
            maxEdit.blockSignals(False)

        # 2. Compute the range; if it's nearly zero, use a fallback range.
        rng = new_max - new_min
        if abs(rng) < 1e-30:
            new_min, new_max = -1e-9, 1e-9
            rng = new_max - new_min
            minEdit.blockSignals(True)
            maxEdit.blockSignals(True)
            minEdit.setValue(new_min)
            maxEdit.setValue(new_max)
            minEdit.blockSignals(False)
            maxEdit.blockSignals(False)

        # 3. Compute the scale factor for mapping float range to slider integers.
        scale = DESIRED_INT_RANGE / rng
        MAX_INT = 2147483647
        largest_abs = max(abs(new_min), abs(new_max))
        if largest_abs < EPSILON:
            largest_abs = 1e-9
        if (new_max * scale) > MAX_INT or (new_min * scale) < -MAX_INT:
            scale = 0.9 * MAX_INT / largest_abs

        # 4. Get the current value from the parameter dictionary and clamp it.
        cur_val = self.parameters[param]["value"]
        if cur_val < new_min:
            cur_val = new_min
        elif cur_val > new_max:
            cur_val = new_max

        # 5. Block signals and update the slider and display.
        slider.blockSignals(True)
        displayCurrent.blockSignals(True)

        # Use round with floor/ceil for the slider endpoints:
        slider.setMinimum(math.floor(new_min * scale) - 1)
        slider.setMaximum(math.ceil(new_max * scale) + 1)
        slider.setValue(round(cur_val * scale))
        displayCurrent.setText(f"{cur_val:.6g}")

        slider.blockSignals(False)
        displayCurrent.blockSignals(False)

        # 6. Update the parameter dictionary.
        self.parameters[param]["min"] = new_min
        self.parameters[param]["max"] = new_max
        self.parameters[param]["value"] = cur_val

        # 7. Force a repaint of the slider asynchronously so the new limits are applied.
        QtCore.QTimer.singleShot(0, slider.update)

    import math
    from PyQt5 import QtWidgets

    # def update_slider_range(self, param):
    #     desired_int_range = 100_000
    #     if param not in self.controls:
    #         return
    #     slider, spin, minSpin, maxSpin, manualEdit = self.controls[param]
    #
    #     # 1. Get new min and max from their spin boxes; swap if reversed.
    #     new_min = minSpin.value()
    #     new_max = maxSpin.value()
    #     if new_min > new_max:
    #         new_min, new_max = new_max, new_min
    #         minSpin.blockSignals(True)
    #         maxSpin.blockSignals(True)
    #         minSpin.setValue(new_min)
    #         maxSpin.setValue(new_max)
    #         minSpin.blockSignals(False)
    #         maxSpin.blockSignals(False)
    #
    #     # 2. Compute the float range; if too small, use a fallback range.
    #     rng = new_max - new_min
    #     if abs(rng) < 1e-30:
    #         new_min, new_max = -1e-9, 1e-9
    #         rng = new_max - new_min
    #         minSpin.blockSignals(True)
    #         maxSpin.blockSignals(True)
    #         minSpin.setValue(new_min)
    #         maxSpin.setValue(new_max)
    #         minSpin.blockSignals(False)
    #         maxSpin.blockSignals(False)
    #
    #     # 3. Calculate the scale factor mapping float range to integer range.
    #     scale = desired_int_range / rng
    #     MAX_INT = 2147483647
    #     largest_abs = max(abs(new_min), abs(new_max))
    #     if largest_abs < 1e-18:
    #         largest_abs = 1e-9
    #     if (new_max * scale) > MAX_INT or (new_min * scale) < -MAX_INT:
    #         scale = 0.9 * MAX_INT / largest_abs
    #
    #     # 4. Clamp the current value from the data model.
    #     cur_val = self.parameters[param]["value"]
    #     if cur_val < new_min:
    #         cur_val = new_min
    #     elif cur_val > new_max:
    #         cur_val = new_max
    #
    #     # 5. Block signals and update slider/spin ranges.
    #     slider.blockSignals(True)
    #     spin.blockSignals(True)
    #     # Use floor for min and ceil for max to ensure extremes are reachable.
    #     slider.setMinimum(math.floor(new_min * scale))
    #     slider.setMaximum(math.ceil(new_max * scale))
    #     slider.setValue(round(cur_val * scale))
    #     spin.setRange(new_min, new_max)
    #     spin.setValue(cur_val)
    #
    #     # 6. Adjust step sizes (e.g. ~1% for single step, ~10% for page step).
    #     int_range = slider.maximum() - slider.minimum()
    #     if int_range > 0:
    #         slider.setSingleStep(max(1, int_range // 100))
    #         slider.setPageStep(max(1, int_range // 10))
    #     else:
    #         slider.setSingleStep(1)
    #         slider.setPageStep(1)
    #
    #     slider.blockSignals(False)
    #     spin.blockSignals(False)
    #
    #     # 7. Update the parameter dictionary.
    #     self.parameters[param]["min"] = new_min
    #     self.parameters[param]["max"] = new_max
    #     self.parameters[param]["value"] = cur_val
    #
    #     # 8. Force the slider to repaint and process events.
    #     slider.repaint()
    #     QtWidgets.QApplication.processEvents()

    def update_slider_range(self, param):
        desired_int_range = 100_000
        if param not in self.controls:
            return
        slider, spin, minSpin, maxSpin, manualEdit = self.controls[param]

        # 1. Get new min and max from the spin boxes; swap if reversed.
        new_min = minSpin.value()
        new_max = maxSpin.value()
        if new_min > new_max:
            new_min, new_max = new_max, new_min
            minSpin.blockSignals(True)
            maxSpin.blockSignals(True)
            minSpin.setValue(new_min)
            maxSpin.setValue(new_max)
            minSpin.blockSignals(False)
            maxSpin.blockSignals(False)

        # 2. Compute range; if too small, force a fallback.
        rng = new_max - new_min
        if abs(rng) < 1e-30:
            new_min, new_max = -1e-9, 1e-9
            rng = new_max - new_min
            minSpin.blockSignals(True)
            maxSpin.blockSignals(True)
            minSpin.setValue(new_min)
            maxSpin.setValue(new_max)
            minSpin.blockSignals(False)
            maxSpin.blockSignals(False)

        # 3. Compute the scaling factor.
        new_scale = desired_int_range / rng
        MAX_INT = 2147483647
        largest_abs = max(abs(new_min), abs(new_max))
        if largest_abs < 1e-18:
            largest_abs = 1e-9
        if (new_max * new_scale) > MAX_INT or (new_min * new_scale) < -MAX_INT:
            new_scale = 0.9 * MAX_INT / largest_abs

        # 4. Clamp current value from the model.
        cur_val = self.parameters[param]["value"]
        if cur_val < new_min:
            cur_val = new_min
        elif cur_val > new_max:
            cur_val = new_max

        # 5. Block signals and update slider and spin.
        slider.blockSignals(True)
        spin.blockSignals(True)
        slider.setMinimum(round(new_min * new_scale))
        slider.setMaximum(round(new_max * new_scale))
        slider.setValue(round(cur_val * new_scale))
        spin.setRange(new_min, new_max)
        spin.setValue(cur_val)

        # Adjust step sizes based on the integer range.
        int_range = slider.maximum() - slider.minimum()
        if int_range > 0:
            slider.setSingleStep(max(1, int_range // 100))
            slider.setPageStep(max(1, int_range // 10))
        else:
            slider.setSingleStep(1)
            slider.setPageStep(1)

        slider.blockSignals(False)
        spin.blockSignals(False)

        self.parameters[param]["min"] = new_min
        self.parameters[param]["max"] = new_max
        self.parameters[param]["value"] = cur_val

        # 6. Force geometry updates on the slider and its parent container.
        slider.updateGeometry()
        slider.adjustSize()
        parent = slider.parentWidget()
        if parent:
            parent.updateGeometry()
            parent.adjustSize()
        # Use a short single-shot timer to schedule a repaint.
        QtCore.QTimer.singleShot(0, lambda: slider.repaint())
        QtWidgets.QApplication.processEvents()

    def set_min_value(self, param, new_min):
        if param in self.parameters:
            self.parameters[param]["min"] = new_min
        if param in self.controls:
            # Refresh the slider and other controls for this parameter
            self.sync_parameter_ui(param)

    def set_max_value(self, param, new_max):
        if param in self.parameters:
            self.parameters[param]["max"] = new_max
        if param in self.controls:
            self.sync_parameter_ui(param)

    def populate_parameters(self):
        EPSILON = 1e-18
        desired_int_range = 100_000

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

            # Retrieve default value from default_parameters if available
            if param in self.default_parameters and isinstance(self.default_parameters[param], dict):
                default_val = float(self.default_parameters[param]["value"])
            else:
                default_val = current

            # Compute min and max if not already set:
            if "min" not in values or "max" not in values:
                if default_val == 0.0:
                    # If the default is exactly zero, set a fixed range [-1, 1]
                    min_val = -1.0
                    max_val = 1.0
                elif abs(default_val) < EPSILON:
                    # For near-zero values (but not exactly zero), use a very small range.
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

            # Compute initial scale factor for the slider range
            range_width = max_val - min_val
            scale = 1e6 if range_width == 0 else desired_int_range / range_width

            slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
            # Use round() to include endpoints properly.
            slider.setMinimum(round(min_val * scale))
            slider.setMaximum(round(max_val * scale))
            slider.setValue(round(current * scale))
            tick_interval = (round(max_val * scale) - round(min_val * scale)) // 10
            slider.setTickInterval(tick_interval if tick_interval > 0 else 1)
            slider.setTickPosition(QtWidgets.QSlider.TicksBelow)

            spin = QtWidgets.QDoubleSpinBox()
            spin.setRange(min_val, max_val)
            spin.setDecimals(6)
            spin.setValue(current)
            # Make spin read-only (current value display)
            spin.setReadOnly(True)
            spin.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)

            # Create spin boxes for editing min and max values
            minEdit = QtWidgets.QDoubleSpinBox()
            minEdit.setRange(-1e20, 1e9)
            minEdit.setDecimals(8)
            minEdit.setValue(min_val)

            maxEdit = QtWidgets.QDoubleSpinBox()
            maxEdit.setRange(-1e20, 1e9)
            maxEdit.setDecimals(8)
            maxEdit.setValue(max_val)

            # Create buttons to apply the new min and max
            setMinBtn = QtWidgets.QPushButton("Set Min")
            setMaxBtn = QtWidgets.QPushButton("Set Max")

            # Create a QLineEdit for manual current value entry and a button to apply it.
            manualCurrentEdit = QtWidgets.QLineEdit()
            manualCurrentEdit.setFixedWidth(80)
            manualCurrentEdit.setText(f"{current:.6g}")
            setCurrentBtn = QtWidgets.QPushButton("Set Current")

            # Connect the "Set" buttons:
            setMinBtn.clicked.connect(lambda _, p=param, val=minEdit.value(): self.set_min_value(p, val))
            setMaxBtn.clicked.connect(lambda _, p=param, val=maxEdit.value(): self.set_max_value(p, val))
            setCurrentBtn.clicked.connect(
                lambda _, p=param, edit=manualCurrentEdit: self.update_parameter_from_text(p, edit.text()))

            # Connect slider changes to update the read-only spin display and parameter value.
            slider.valueChanged.connect(lambda val, s=spin, sc=scale: s.setValue(val / sc))
            slider.valueChanged.connect(lambda val, key=param, sc=scale: self.update_parameter(key, val / sc))

            container = QtWidgets.QWidget()
            h_layout = QtWidgets.QHBoxLayout(container)
            # Order: Slider | current display (spin) | minEdit | Set Min | maxEdit | Set Max | manualCurrentEdit | Set Current
            h_layout.addWidget(slider)
            h_layout.addWidget(spin)
            h_layout.addWidget(QtWidgets.QLabel("Min:"))
            h_layout.addWidget(minEdit)
            h_layout.addWidget(setMinBtn)
            h_layout.addWidget(QtWidgets.QLabel("Max:"))
            h_layout.addWidget(maxEdit)
            h_layout.addWidget(setMaxBtn)
            h_layout.addWidget(manualCurrentEdit)
            h_layout.addWidget(setCurrentBtn)
            h_layout.setContentsMargins(0, 0, 0, 0)
            self.form_layout.addRow(param, container)
            self.controls[param] = (
            slider, spin, minEdit, maxEdit, manualCurrentEdit, setMinBtn, setMaxBtn, setCurrentBtn)

            #self.sync_parameter_ui(param)

    def sync_parameter_ui(self, param):
        """
        Recompute the slider's range and update controls based on the parameter's
        stored (value, min, max). This method is called after any update.
        """
        DESIRED_INT_RANGE = 100_000
        EPSILON = 1e-18

        if param not in self.controls:
            return
        # Note: our controls tuple now has 8 items.
        slider, spin, minEdit, maxEdit, manualCurrentEdit, _, _, _ = self.controls[param]

        new_min = minEdit.value()
        new_max = maxEdit.value()
        if new_min > new_max:
            new_min, new_max = new_max, new_min
            minEdit.blockSignals(True)
            maxEdit.blockSignals(True)
            minEdit.setValue(new_min)
            maxEdit.setValue(new_max)
            minEdit.blockSignals(False)
            maxEdit.blockSignals(False)

        rng = new_max - new_min
        if abs(rng) < 1e-30:
            new_min, new_max = -1e-9, 1e-9
            rng = new_max - new_min
            minEdit.blockSignals(True)
            maxEdit.blockSignals(True)
            minEdit.setValue(new_min)
            maxEdit.setValue(new_max)
            minEdit.blockSignals(False)
            maxEdit.blockSignals(False)

        scale = DESIRED_INT_RANGE / rng
        MAX_INT = 2147483647
        largest_abs = max(abs(new_min), abs(new_max))
        if largest_abs < EPSILON:
            largest_abs = 1e-9
        if (new_max * scale) > MAX_INT or (new_min * scale) < -MAX_INT:
            scale = 0.9 * MAX_INT / largest_abs

        # Clamp the current value from the parameter dictionary.
        cur_val = self.parameters[param]["value"]
        if cur_val < new_min:
            cur_val = new_min
        elif cur_val > new_max:
            cur_val = new_max

        slider.blockSignals(True)
        spin.blockSignals(True)

        slider.setMinimum(round(new_min * scale))
        slider.setMaximum(round(new_max * scale))
        slider.setValue(round(cur_val * scale))
        spin.setRange(new_min, new_max)
        spin.setValue(cur_val)

        # Optionally set singleStep/pageStep based on the integer range.
        int_range = slider.maximum() - slider.minimum()
        if int_range > 0:
            slider.setSingleStep(max(1, int_range // 100))
            slider.setPageStep(max(1, int_range // 10))
        else:
            slider.setSingleStep(1)
            slider.setPageStep(1)

        slider.blockSignals(False)
        spin.blockSignals(False)

        self.parameters[param]["min"] = new_min
        self.parameters[param]["max"] = new_max
        self.parameters[param]["value"] = cur_val

        

    def spin_changed(self, param, val):
        # user changed the spin box => store val, then re-sync
        self.parameters[param]["value"] = val
        self.sync_parameter_ui(param)

    def update_parameter(self, param, value):
        self.parameters[param] = {"value": value,
                                  "min": self.parameters[param].get("min", value * 0.5),
                                  "max": self.parameters[param].get("max", value * 1.5)}
        print(f"{param} updated to {value}")

    def update_parameter_from_text(self, param, text):
        try:
            new_val = float(text)
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Invalid Input", f"'{text}' is not a valid number for {param}.")
            return
        if param not in self.controls:
            return
        self.parameters[param]["value"] = new_val
        # Call sync_parameter_ui to update only this parameter's controls.
        self.sync_parameter_ui(param)
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
        # Remove the left pane; we rely on the tuner.
        self.tuner = ParameterTunerWindow(self.current_parameters, self.default_parameters, self.available_parameters)
        self.run_button = QtWidgets.QPushButton("Run Calibration Loop")
        self.updateLibButton = QtWidgets.QPushButton("Update Modified LIB")
        self.simulationButton = QtWidgets.QPushButton("Open Simulation Window")

        central_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout(central_widget)
        # Place buttons on a horizontal toolbar.
        toolbarLayout = QtWidgets.QHBoxLayout()
        toolbarLayout.addWidget(self.run_button)
        toolbarLayout.addWidget(self.updateLibButton)
        toolbarLayout.addWidget(self.simulationButton)
        main_layout.addLayout(toolbarLayout)
        main_layout.addWidget(self.tuner)
        self.setCentralWidget(central_widget)

        self.run_button.clicked.connect(self.run_calibration)
        self.updateLibButton.clicked.connect(self.update_modified_lib)
        self.simulationButton.clicked.connect(self.open_simulation_window)

    def update_modified_lib(self):
        # Import ModelModifier from the param handler module.
        from IceMOS_sky130_param_handler import ModelModifier
        # Construct the modified file path (assumes _original.lib is in self.lib_file_path)
        modified_file_path = self.lib_file_path.replace("_original.lib", "_modified.lib")
        modifier = ModelModifier(self.lib_file_path, modified_file_path, device_type=self.device_type)
        print('------ Parameters ---------')
        print(self.current_parameters.items())
        for param, val in self.current_parameters.items():
            # Assume val is a dict with key "value"
            if isinstance(val, dict):
                new_val = val.get("value", None)
                print(f'new_val ({self.device_type}) ({param}) = {new_val}')
                if new_val is not None:
                    # Modify the parameter in the given bin.
                    modifier.modify_parameter(self.bin_number, param, str(new_val))
        QtWidgets.QMessageBox.information(self, "LIB Update", "Modified LIB file has been updated.")

    def open_simulation_window(self):
        simWin = SimulationWindow(self.device_type, self.bin_number, self.lib_file_path)
        simWin.resize(800, 600)
        simWin.show()

    def run_calibration(self):
        print("Running calibration with parameters:")
        for k, v in self.current_parameters.items():
            print(f"  {k}: {v}")
        QtWidgets.QMessageBox.information(self, "Calibration", "Calibration loop executed (placeholder).")


class SimulationWindow(QtWidgets.QDialog):
    """
    A window to configure and run IV simulations.
    It allows the user to choose the simulation type, configure sweep parameters,
    and then run the simulation with continuous plot updating.
    """

    def __init__(self, device_type, bin_number, lib_file_path, parent=None):
        super().__init__(parent)
        self.device_type = device_type.lower()
        self.bin_number = bin_number
        self.lib_file_path = lib_file_path
        self.setWindowTitle("Simulation Configuration")
        # Define the timer here so it exists for later connections.
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.run_simulation_and_update_plot)
        # Now set up the UI.
        self.setup_ui()
        # Create a simulator instance.
        from IceMOS_sky130_simulator import IceMOS_simulator_sky130
        self.simulator = IceMOS_simulator_sky130(self.lib_file_path)

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        # Simulation type selection.
        self.simTypeCombo = QtWidgets.QComboBox()
        self.simTypeCombo.addItems(["IV vs VG", "IV vs VDS"])
        layout.addWidget(QtWidgets.QLabel("Select Simulation Type:"))
        layout.addWidget(self.simTypeCombo)

        # Simulation configuration fields.
        self.vgStartEdit = QtWidgets.QLineEdit("0")
        self.vgStopEdit = QtWidgets.QLineEdit("1.8")
        self.vgStepEdit = QtWidgets.QLineEdit("0.1")
        self.vdsStartEdit = QtWidgets.QLineEdit("0")
        self.vdsStopEdit = QtWidgets.QLineEdit("1.8")
        self.vdsStepEdit = QtWidgets.QLineEdit("1.0")

        configLayout = QtWidgets.QFormLayout()
        configLayout.addRow("VG Start:", self.vgStartEdit)
        configLayout.addRow("VG Stop:", self.vgStopEdit)
        configLayout.addRow("VG Step:", self.vgStepEdit)
        configLayout.addRow("VDS Start:", self.vdsStartEdit)
        configLayout.addRow("VDS Stop:", self.vdsStopEdit)
        configLayout.addRow("VDS Step:", self.vdsStepEdit)
        layout.addLayout(configLayout)

        # Buttons to run simulation.
        self.runOnceBtn = QtWidgets.QPushButton("Run Simulation Once")
        self.runContinuousBtn = QtWidgets.QPushButton("Start Continuous Simulation")
        self.stopBtn = QtWidgets.QPushButton("Stop Continuous Simulation")
        btnLayout = QtWidgets.QHBoxLayout()
        btnLayout.addWidget(self.runOnceBtn)
        btnLayout.addWidget(self.runContinuousBtn)
        btnLayout.addWidget(self.stopBtn)
        layout.addLayout(btnLayout)

        # Plot area.
        self.plotWidget = pg.GraphicsLayoutWidget(title="Simulation Plot")
        layout.addWidget(self.plotWidget)

        self.runOnceBtn.clicked.connect(self.run_simulation_and_update_plot)
        self.runContinuousBtn.clicked.connect(lambda: self.timer.start(5000))  # Update every 5 seconds.
        self.stopBtn.clicked.connect(self.timer.stop)

        self.setLayout(layout)

    def run_simulation_and_update_plot(self):
        sim_type = self.simTypeCombo.currentText()
        try:
            vg_start = float(self.vgStartEdit.text())
            vg_stop = float(self.vgStopEdit.text())
            vg_step = float(self.vgStepEdit.text())
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Invalid Input", "Check VG simulation values.")
            return
        if sim_type == "IV vs VG":
            # Run IV vs VG simulation.
            output = self.simulator.simulate_iv(self.device_type, bin_number=self.bin_number,
                                                vgate_start=vg_start, vgate_stop=vg_stop, vgate_step=vg_step)
            # Plot results.
            plotWin = self.simulator.plot_iv_results_qt(self.device_type, self.bin_number,
                                                        csv_filename="IV_ID_vs_VG.csv")
        else:
            try:
                vds_start = float(self.vdsStartEdit.text())
                vds_stop = float(self.vdsStopEdit.text())
                vds_step = float(self.vdsStepEdit.text())
            except ValueError:
                QtWidgets.QMessageBox.warning(self, "Invalid Input", "Check VDS simulation values.")
                return
            output = self.simulator.simulate_id_vs_vds_sweep_vg(self.device_type, bin_number=self.bin_number,
                                                                vgs_start=vg_start, vgs_stop=vg_stop, vgs_step=vg_step,
                                                                vds_start=vds_start, vds_stop=vds_stop,
                                                                vds_step=vds_step)
            plotWin = self.simulator.plot_iv_vds_results_qt(self.device_type, self.bin_number)
        # Clear previous plot and update with the new one.
        self.plotWidget.clear()
        plotWin.show()
        print("Simulation run and plot updated.")


def main():
    app = QtWidgets.QApplication(sys.argv)
    main_win = MainWindow("pch", 10)
    main_win.resize(1200, 800)
    main_win.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
